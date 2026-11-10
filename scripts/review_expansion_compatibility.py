"""Audit model configurations against unchanged engines; never calculate replacement fees.

This is an offline review and release index, not a runtime adapter. Unsafe native
results become unavailable. No profile, tariff or engine is patched during probes.
"""

import argparse
import base64
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kita_costs.engine import evaluate_city, row_matches, valid_on

BUILD = ROOT / "build/expansion-review"
OUTPUT = ROOT / "data/expansion/calculation_review.json"
REPORT = ROOT / "docs/ERWEITERUNGSBERECHNUNG.md"
POLICY = ROOT / "data/reviews/expansion_compatibility_policy.json"
REFERENCES = ROOT / "data/reviews/expansion_calculation_cases.json"
PROBE_INPUTS = ["data/expansion/manifest.json","data/models/configuration.json","data/profiles/default.json",
    "web/src/site/features.ts","scripts/probe_expansion_engines.mjs","kita_costs/engine.py",
    "web/src/domain/engine.ts","web/src/domain/model-family.ts","web/src/domain/money.ts",
    "web/src/domain/profile.ts","web/src/domain/index.ts","web/src/domain/types.ts","kita_costs/registry.py","package-lock.json"]
RESULT_FIELDS = ["status","reasons","monthly_care_cents","annual_care_cents","monthly_equivalent_cents",
    "offer_id","offer_label","selected_price_id","booked_weekly_minutes","extra_weekly_minutes","payment_months","care_rank"]
COMPONENT_FIELDS = ["id","kind","amount_cents","unit","required","payment_months","value_status","annual_equivalent_cents"]
REASONS = {
    "engine_error":"Die native Berechnung bricht mit einem Fehler ab.",
    "schedule_not_confirmed":"Eine benötigte Tagesverteilung ist nicht ausreichend belegt.",
    "no_offer_covers_daily_need":"Kein belegtes Angebot deckt den Bedarf an allen fünf Tagen.",
    "price_or_income_input_missing":"Passende Preiszelle oder örtliche Einkommensangabe fehlt.",
    "multiple_equivalent_tariffs_require_scope_clarification":"Die native Auswahl liefert mehrere gleichwertige Tarifvarianten.",
    "care_rank_allocation_unresolved":"Die Rangverteilung erlaubt keinen eindeutigen Familienbetrag.",
    "known_included_meal_not_separated":"Der native Kartenbetrag enthält einen bekannten abzutrennenden Essensanteil.",
    "included_meal_treated_as_additional":"Enthaltenes Essen wird von der Ergebnisaufbereitung nicht als inklusive behandelt.",
    "smaller_offer_schedule_unverified":"Ein möglicherweise kleineres passendes Angebot ist nicht ausreichend zeitlich geklärt.",
    "partial_gt_price_not_complete":"Ein Teilbeitrag wird ohne die übrigen Betreuungstage als Gesamtpreis verwendet.",
    "component_age_scope_ignored":"Eine Zusatzkostenvariante außerhalb der Alterszuordnung wird mit ausgegeben.",
    "formula_not_supported":"Die gespeicherte Formelart wird von der bestehenden Engine nicht unterstützt.",
    "approved_friday_exception_not_supported":"Die genehmigte Freitagsausnahme ist nicht in die bestehende Auswahl integriert.",
    "single_parent_band_shift_not_applied":"Die erforderliche Alleinerziehenden-Stufenverschiebung wird nicht angewendet.",
    "simultaneous_u3_band_shift_not_applied":"Die zusätzliche Stufe bei gleichzeitigem U3-Besuch wird nicht angewendet.",
    "o3_rank_population_differs_from_all_care_children":"Ü3-Rang und Rang aller Kita-Kinder sind verschieden.",
    "o3_rank_allocation_unresolved":"Die preiswirksame Ü3-Rangzuordnung bleibt offen.",
    "third_o3_rank_not_published":"Ein dritter Ü3-Tabellensatz fehlt für diese Familienstufe.",
    "single_parent_household_shift_not_applied":"Das zusätzliche Haushaltskind bei Alleinerziehung wird nicht berücksichtigt.",
    "simultaneous_gt_surcharge_discount_not_applied":"Die Ermäßigung des GT-Zuschlags bei gleichzeitigem Besuch fehlt.",
    "birth_rank_differs_from_care_rank":"Der Familien-Geburtsrang wird nicht durch den Betreuungsrang abgebildet.",
    "single_parent_selector_not_supported":"Die zusätzliche Haushaltsbedingung an der Preiszelle wird nicht ausgewertet.",
    "local_income_model_not_defined":"Eine ausdrücklich bestätigte örtliche Einkommens-Modellannahme fehlt.",
    "local_net_income_model_not_defined":"Für monatliches Haushaltsnetto liegt keine bestätigte Modellannahme vor.",
    "family_discount_not_applied":"Die zusätzliche Familienermäßigung wird nicht angewendet.",
    "single_parent_discount_not_applied":"Die zusätzliche Alleinerziehendenermäßigung wird nicht angewendet.",
    "income_percentage_formula_not_supported":"Die örtliche Prozentformel ist nicht ausführbar.",
    "included_meal_display_not_supported":"Die vereinbarte Inklusivdarstellung ist noch nicht umgesetzt.",
    "provider_scope_confirmation_required":"Der Geltungsbereich der ausgewählten Trägervariante ist noch zu bestätigen.",
    "meal_requirement_scope_not_represented":"Die Pflicht zur Verpflegung ist noch nicht passend nach Betreuungsumfang zugeordnet.",
    "regular_and_vo_offer_scope_unverified":"Regel- und VÖ-Angebote sind noch nicht ausreichend getrennt und zeitlich belegt.",
}


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_result(row):
    return {**{key:row.get(key) for key in RESULT_FIELDS},
        "components":[{key:part.get(key) for key in COMPONENT_FIELDS} for part in row.get("components",[])]}


def case_context(selection):
    children=selection["children"]
    active=[c for c in children if c["category"] in {"nursery","kindergarten"}]
    return {"household":selection["household"],"family_count":len(children),"care_count":len(active),
        "nursery_count":sum(c["category"]=="nursery" for c in active),
        "kindergarten_count":sum(c["category"]=="kindergarten" for c in active),
        "long_care_count":sum(c["daily_minutes"]==480 for c in active),
        "has_six_hour_care":any(c["daily_minutes"]==360 for c in active),
        "has_eight_hour_care":any(c["daily_minutes"]==480 for c in active),
        "has_non_care_children":len(active)<len(children),
        "different_kindergarten_hours":len({c["daily_minutes"] for c in active if c["category"]=="kindergarten"})>1}


def conditions_match(when, context):
    for key, expected in when.items():
        if key.endswith("_min"):
            if context[key[:-4]]<expected:return False
        elif key.endswith("_max"):
            if context[key[:-4]]>expected:return False
        elif context[key]!=expected:return False
    return True


def review_result(city, case, raw, policy, research):
    """Reject unsupported outcomes; do not adjust amounts or waive requirements."""
    context=case_context(case["selection"])
    if not context["care_count"]:
        if raw.get("status")!="comparable" or raw.get("annual_care_cents")!=0:
            raise ValueError("The unchanged family function failed the no-care zero case")
        return {"status":"comparable","reasons":[],"monthly_care_cents":0,"annual_care_cents":0,"monthly_equivalent_cents":0}
    reasons=[]
    if raw.get("engine_error"):reasons.append("engine_error")
    elif raw["status"]!="comparable":reasons.extend(raw.get("reasons") or ["engine_unavailable_without_reason"])
    for item in policy.get("rules",[]):
        if conditions_match(item["when"],context):reasons.append(item["code"])
    if context["has_eight_hour_care"] and research.get("comparison_policy",{}).get("show_schedule_shortfall"):
        reasons.append("approved_friday_exception_not_supported")
    offers={o["id"]:o for o in city["offers"]}
    prices={p["id"]:p for p in city["prices"]}
    parts={p["id"]:p for p in city["components"]}
    for child in raw.get("children",[]):
        if not child["in_care"]:continue
        result=child["result"]
        age=case["profile"]["children"][child["index"]]["age_months"]
        applicable=[o for o in city["offers"] if valid_on(o,case["profile"]["as_of"]) and
            o["age_min_months"]<=age and (o["age_max_months_exclusive"] is None or age<o["age_max_months_exclusive"])]
        for candidate in applicable:
            formula=candidate.get("formula")
            if formula and not {"threshold_minutes","below_or_equal_rate_cents","above_rate_cents","family_discount_percent","minimum_cents","rounding"}<=formula.keys():
                reasons.append("formula_not_supported")
        if not result or result["status"]!="comparable":continue
        selected=offers[result["offer_id"]]
        price=prices.get(result.get("selected_price_id"))
        if price and price.get("care_only_amount_cents") is not None and price["care_only_amount_cents"]!=result["monthly_care_cents"]:
            reasons.append("known_included_meal_not_separated")
        if price and price.get("price_role") not in {None,"full_month_total"}:reasons.append("partial_gt_price_not_complete")
        for part in result["components"]:
            source=parts[part["id"]]
            if source.get("inclusion")=="included":reasons.append("included_meal_treated_as_additional")
            if (source.get("age_min_months",0)>age or (source.get("age_max_months_exclusive") is not None and age>=source["age_max_months_exclusive"])):
                reasons.append("component_age_scope_ignored")
        profile={**case["profile"],"target_child":child["index"],"weekday_minutes":[child["daily_minutes"]]*5,
            "care_rank":result.get("care_rank") or 1,"school_entry":False}
        requested=child["daily_minutes"]*5
        for other in applicable:
            if other["weekday_minutes"] is not None and other["schedule_status"] in {"published","verified"}:continue
            if not other["continuous"]:continue
            minutes=other["weekly_minutes"]
            if minutes is not None and (minutes<requested or minutes>result["booked_weekly_minutes"]):continue
            pattern=other.get("weekday_pattern")
            if pattern and pattern["long_days"]<5 and pattern["other_day_minutes"]<child["daily_minutes"]:continue
            matching=[p for p in city["prices"] if p["offer_id"]==other["id"] and row_matches(p,city,profile,context["family_count"])]
            if matching and all(p["value_status"]=="not_offered" for p in matching):continue
            if minutes==result["booked_weekly_minutes"] and matching and all(p["amount_cents"]==result["monthly_care_cents"] for p in matching):continue
            reasons.append("smaller_offer_schedule_unverified")
    reasons=sorted(set(reasons))
    if reasons:
        return {"status":"unavailable","reasons":reasons,"monthly_care_cents":None,"annual_care_cents":None,"monthly_equivalent_cents":None}
    if raw.get("status")!="comparable" or raw["annual_care_cents"] is None:
        raise ValueError("An unavailable native result escaped the compatibility review")
    return {key:raw[key] for key in ["status","reasons","monthly_care_cents","annual_care_cents","monthly_equivalent_cents"]}


def ranges(indices):
    output=[]
    for index in indices:
        if output and index==output[-1][1]+1:output[-1][1]=index
        else:output.append([index,index])
    return output


def bitset(indices, count):
    packed=bytearray((count+7)//8)
    for index in indices:packed[index//8]|=1<<(index%8)
    return base64.b64encode(packed).decode()


def engine_fingerprints():
    fingerprints={path:digest(ROOT/path) for path in PROBE_INPUTS}
    for city in read(ROOT/"data/expansion/manifest.json")["municipalities"]:
        actual=digest(ROOT/city["path"])
        if actual!=city["sha256"]:raise ValueError("Catalog differs from its normalized manifest: "+city["id"])
        fingerprints[city["path"]]=actual
    return fingerprints


def verify_probe_cache():
    path=BUILD/"cases.json"
    if not path.exists() or not (BUILD/"probe-summary.json").exists():return False
    paths=PROBE_INPUTS+[m["path"] for m in read(ROOT/"data/expansion/manifest.json")["municipalities"]]
    return all((ROOT/path).stat().st_mtime_ns <= (BUILD/"cases.json").stat().st_mtime_ns for path in paths)


def configuration_status(review, city_id, selection):
    """Read the offline review index without evaluating or modifying any tariff."""
    unavailable=lambda reasons:{"status":"unavailable","reasons":reasons,"monthly_care_cents":None,"annual_care_cents":None,"monthly_equivalent_cents":None}
    space=review["configuration_space"]
    states=[("nursery",360),("nursery",480),("kindergarten",360),("kindergarten",480),("school",480),("home",480)]
    try:
        if not isinstance(selection,dict) or set(selection)!={"household","income_id","children"}:return unavailable(["outside_review_scope"])
        if not 1<=len(selection["children"])<=review["scope"]["max_children"]:return unavailable(["outside_review_scope"])
        children=[]
        for child in selection["children"]:
            if set(child)!={"category","daily_minutes"} or child["daily_minutes"] not in {360,480}:return unavailable(["outside_review_scope"])
            state=(child["category"],480 if child["category"] in {"school","home"} else child["daily_minutes"])
            children.append(states.index(state))
        composition=[{"category":states[i][0],"daily_minutes":states[i][1]} for i in sorted(children)]
        index=(space["households"].index(selection["household"])*len(space["income_ids"])+space["income_ids"].index(selection["income_id"]))*len(space["child_compositions"])+space["child_compositions"].index(composition)
        city=next(c for c in review["municipalities"] if c["id"]==city_id)
    except (ValueError,TypeError,KeyError,StopIteration):return unavailable(["outside_review_scope"])
    mask=base64.b64decode(city["supported_scenarios_bitset_base64"],validate=True)
    if mask[index//8] & (1<<(index%8)):return {"status":"comparable","reasons":[],"scenario_index":index}
    for group in city["unavailable_groups"]:
        if any(start<=index<=end for start,end in group["scenario_index_ranges_inclusive"]):
            return {**unavailable(group["reasons"]),"scenario_index":index}
    return unavailable(["incomplete_review_index"])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-probes",action="store_true",help="Use fresh native probes already produced in build/")
    parser.add_argument("--check",action="store_true",help="Verify the stored review without rewriting it")
    args=parser.parse_args()
    inputs_before=engine_fingerprints()
    if not (args.reuse_probes and verify_probe_cache()):
        subprocess.run(["npm","run","build:domain"],cwd=ROOT,check=True)
        subprocess.run(["node","scripts/probe_expansion_engines.mjs"],cwd=ROOT,check=True)
    case_file=read(BUILD/"cases.json")
    cases=case_file["cases"]
    catalog_manifest=read(ROOT/"data/expansion/manifest.json")
    catalogs={item["id"]:read(ROOT/item["path"]) for item in catalog_manifest["municipalities"]}
    research={item["id"]:item for item in read(ROOT/"data/research/neighbor_expansion_2026-11-10.json")["municipalities"]}
    policy=read(POLICY)
    profiles=read(BUILD/"primitive-profiles.json")
    parity_count=0
    with (BUILD/"primitive-probes.jsonl").open() as stream:
        for line in stream:
            probe=json.loads(line)
            try:actual=compact_result(evaluate_city(catalogs[probe["municipality_id"]],profiles[probe["profile_index"]]))
            except Exception as error:actual={"engine_error":type(error).__name__,"message":str(error)}
            if actual!=probe["result"]:
                raise ValueError(f"Cross-engine mismatch: {probe['municipality_id']} profile {probe['profile_index']}")
            parity_count+=1
    count=len(cases)
    by_id={c["id"]:c for c in cases}
    default=read(ROOT/"data/models/configuration.json")["default"]
    default_index=next(c["index"] for c in cases if c["selection"]==default)
    results={city:{"raw_status_counts":Counter(),"care_status_counts":Counter(),"reason_counts":Counter(),
        "supported":[],"groups":defaultdict(list),"unsafe_native_comparable":0,"native_errors":0} for city in catalogs}
    references=read(REFERENCES)
    reference_by_key=defaultdict(list)
    for reference in references["cases"]:
        if reference["scenario_id"] not in by_id:raise ValueError("Reference case outside the reviewed UI grid")
        reference_by_key[(reference["municipality_id"],by_id[reference["scenario_id"]]["index"])].append(reference)
    reference_results=[]
    processed=0
    seen=set()
    with (BUILD/"family-probes.jsonl").open() as stream:
        for line in stream:
            probe=json.loads(line);city_id=probe["municipality_id"];case=cases[probe["case_index"]];raw=probe["result"]
            identity=(city_id,probe["case_index"])
            if identity in seen or case["index"]!=probe["case_index"]:raise ValueError("Duplicate or inconsistent model probe")
            seen.add(identity)
            reviewed=review_result(catalogs[city_id],case,raw,policy["entries"].get(city_id,{}),research[city_id])
            stats=results[city_id]
            stats["raw_status_counts"][raw.get("status","engine_error")]+=1
            if raw.get("engine_error"):stats["native_errors"]+=1
            if raw.get("status")=="comparable" and reviewed["status"]=="unavailable":stats["unsafe_native_comparable"]+=1
            if case_context(case["selection"])["care_count"]:stats["care_status_counts"][reviewed["status"]]+=1
            if reviewed["status"]=="comparable":stats["supported"].append(case["index"])
            else:
                stats["reason_counts"].update(reviewed["reasons"])
                stats["groups"][tuple(reviewed["reasons"])].append(case["index"])
            if case["index"]==default_index:
                stats["default_result"]={"scenario_index":default_index,**reviewed}
                stats["raw_default_status"]=raw.get("status","engine_error")
            for reference in reference_by_key.get((city_id,case["index"]),[]):
                for key,value in reference["expected"].items():
                    if reviewed.get(key)!=value:raise ValueError(f"Reference mismatch {reference['id']}: {key}: {reviewed.get(key)} != {value}")
                if not set(reference.get("required_reasons",[]))<=set(reviewed["reasons"]):raise ValueError("Missing expected rejection reason: "+reference["id"])
                reference_results.append({"id":reference["id"],"status":"passed"})
            processed+=1
    if len(reference_results)!=len(references["cases"]):raise ValueError("Not all source reference cases were checked")
    probe_summary=read(BUILD/"probe-summary.json")
    if (processed!=count*len(catalogs) or parity_count!=probe_summary["primitive_probes"]
            or probe_summary["order_reversal_mismatches"]):raise ValueError("Incomplete model probe coverage")
    entries=[]
    for city_id,city in sorted(catalogs.items()):
        stats=results[city_id];supported=stats["care_status_counts"]["comparable"];unavailable=stats["care_status_counts"]["unavailable"]
        entries.append({"id":city_id,"name":city["name"],"status":"supported_for_reviewed_care_models" if not unavailable else "partially_supported" if supported else "unavailable_for_reviewed_care_models",
            "checked_configurations":count,"care_status_counts":dict(stats["care_status_counts"]),"raw_status_counts":dict(stats["raw_status_counts"]),
            "unsafe_native_comparable":stats["unsafe_native_comparable"],"native_errors":stats["native_errors"],"default_result":stats["default_result"],
            "raw_default_status":stats["raw_default_status"],"reason_counts":dict(sorted(stats["reason_counts"].items())),
            "supported_scenarios_bitset_base64":bitset(stats["supported"],count),
            "unavailable_groups":[{"reasons":list(reasons),"scenario_index_ranges_inclusive":ranges(indices)} for reasons,indices in sorted(stats["groups"].items())]})
    models=read(ROOT/"data/models/configuration.json")
    compositions=[c["selection"]["children"] for c in cases if c["selection"]["household"]=="couple" and c["selection"]["income_id"]==models["income_scenarios"][0]["id"]]
    output={"schema_version":"1.0","reviewed_at":catalog_manifest["normalized_at"],"as_of":probe_summary["as_of"],
        "status":"compatibility_review_completed_with_unavailable_configurations","purpose":"offline_release_review_not_runtime_adapter",
        "scope":{"max_children":case_file["max_children"],"care_durations_minutes":[360,480],"passes":"none","future_tariff_dates_reviewed":False,
            "child_order":"all_multisets_plus_reversal_check","outside_review_scope_status":"unavailable"},
        "configuration_space":{"households":["couple","single"],"income_ids":[s["id"] for s in models["income_scenarios"]],"child_compositions":compositions,
            "index_order":["household","income_id","child_composition"],"configurations_per_municipality":count,"default_scenario_index":default_index},
        "verification":{"family_probes":processed,"cross_engine_primitive_probes":parity_count,"order_reversal_checks":probe_summary["order_reversal_checks"],
            "order_reversal_mismatches":0,"source_reference_cases":len(reference_results),"source_reference_results":sorted(reference_results,key=lambda x:x["id"])},
        "summary":{"municipalities":len(entries),"default_comparable":sum(e["default_result"]["status"]=="comparable" for e in entries),
            "default_unavailable":sum(e["default_result"]["status"]=="unavailable" for e in entries),"municipality_status_counts":dict(Counter(e["status"] for e in entries)),
            "unsafe_native_comparable":sum(e["unsafe_native_comparable"] for e in entries),"native_errors":sum(e["native_errors"] for e in entries)},
        "input_sha256":{**inputs_before,"data/reviews/expansion_compatibility_policy.json":digest(POLICY),"data/reviews/expansion_calculation_cases.json":digest(REFERENCES),
            "scripts/review_expansion_compatibility.py":digest(Path(__file__))},
        "engine_changed":False,"production_registry_changed":False,"website_activated":False,
        "publication_requires_enforcing_review_index":True,"reason_labels":REASONS,"municipalities":entries}
    if engine_fingerprints()!=inputs_before:raise ValueError("Probe inputs changed during the review")
    content=json.dumps(output,ensure_ascii=False,indent=2)+"\n"
    report=render_report(output,policy)
    if args.check:
        if OUTPUT.read_text()!=content or REPORT.read_text()!=report:raise ValueError("Stored compatibility review is outdated")
    else:
        OUTPUT.write_text(content);REPORT.write_text(report)
    print(json.dumps(output["summary"],ensure_ascii=False))


def render_report(review,policy):
    summary=review["summary"];verified=review["verification"]
    lines=["# Berechenbarkeit der 33 Erweiterungskataloge","",
        f"**Prüfstand:** {review['reviewed_at']}. **Schritt 2 abgeschlossen:** Kompatibilitätsprüfung der bestehenden Engine und Kennzeichnung nicht berechenbarer Modellkonfigurationen.","",
        f"Für die bisherige Modellfamilie sind **{summary['default_comparable']} Kommunen berechenbar** und **{summary['default_unavailable']} nicht berechenbar**. "
        "Das ist keine Freischaltung. Die gemeinsame Engine und das produktive Kommunenregister bleiben unverändert.","",
        "## Prüfumfang","",
        f"Geprüft wurden **{review['configuration_space']['configurations_per_municipality']} Konfigurationen je Kommune**, insgesamt **{verified['family_probes']} Familienfälle**: "
        "ein bis vier Haushaltskinder, beide Haushaltskonstellationen, alle sechs Einkommensszenarien, Krippe/Kindergarten mit sechs oder acht Stunden sowie Schul- und zu Hause betreute Kinder. "
        "Kindreihenfolgen wurden als Multimengen abgedeckt und durch Umkehrung zusätzlich geprüft. Familien mit fünf bis zwölf Kindern, persönliche Eingaben, Pässe, außergewöhnliche Aufnahmefälle und künftige Tarifstichtage sind nicht freigegeben.","",
        f"**{verified['cross_engine_primitive_probes']} Einzelberechnungen** wurden zwischen unveränderter Python- und TypeScript-Engine abgeglichen; "
        f"**{verified['order_reversal_checks']} Reihenfolgeprüfungen** ergaben identische Familienbeträge/-status. "
        f"Zusätzlich bestanden **{verified['source_reference_cases']} ausdrücklich hinterlegte Quellen- und Ablehnungsfälle**. "
        "Diese technische Kompatibilitätsprüfung ersetzt die nachfolgende umfassende fachliche Quellenabnahme aus Schritt 3 nicht.","",
        "## Sicherheitsentscheidung","",
        f"Die native Berechnung lieferte in **{summary['unsafe_native_comparable']} geprüften Fällen** einen als vergleichbar bezeichneten Betrag, der wegen einer nicht berücksichtigten Bedingung oder ungeklärten Angebotsauswahl verworfen wurde. "
        "Die geprüften Ausgaben verwenden dann `status: unavailable`, konkrete Gründe und leere Geldfelder. Weder null Euro noch ein geratener Ersatzpreis wird ausgegeben. "
        "Ein separater Schutzschritt in der Offline-Prüfung erzeugt diese Freigabeentscheidung; die bestehende Engine selbst wurde nicht nachträglich umdefiniert.","",
        "Unbekannte separat zu erhebende Essenspreise sperren einen ansonsten belastbaren Betreuungskostenwert nicht automatisch. Ein falscher Essensabzug, Doppelansatz oder eine falsch zugeordnete Kostenvariante verhindert dagegen die Freigabe.","",
        "## Ergebnisse nach Kommune","",
        "| Kommune | Bisherige Modellfamilie | Berechenbare / geprüfte Konfigurationen mit Kita-Betreuung | Einschränkung |",
        "|---|---|---:|---|"]
    for city in review["municipalities"]:
        result=city["default_result"]
        amount="Nicht berechenbar" if result["status"]!="comparable" else f"{result['monthly_equivalent_cents']/100:.2f} €".replace('.',',')
        counts=city["care_status_counts"];total=sum(counts.values())
        prominent=sorted(city["reason_counts"],key=lambda code:(-city["reason_counts"][code],code))[:2]
        detail="; ".join(REASONS.get(code,code).rstrip('.') for code in prominent) or "Innerhalb des geprüften Modellumfangs unterstützt."
        lines.append(f"| {city['name']} | {amount} | {counts.get('comparable',0)} / {total} | {detail} |")
    lines += ["","Die Zahlen schließen Familien ohne Kita-Kind aus; deren belegter Betreuungskostenwert null wird separat mitgeprüft. Ein berechenbarer Teilbereich bedeutet keine pauschale Freigabe der Kommune für alle Einstellungen.","",
        "## Konkrete Einschränkungen und nächste Arbeit","",
        "- **Schwieberdingen:** reguläre Tabellen können nur dort verwendet werden, wo die native Rechnung stimmt. Nicht ausgeführte Alleinerziehenden-/U3-Stufenverschiebungen, eine falsche Rangpopulation und ungeklärte Ü3-Ränge bleiben nicht berechenbar. Keine Sonderlogik wurde in die Engine eingebaut.",
        "- **Denkendorf:** die genehmigte Freitagsausnahme ist dokumentiert; die unveränderte tägliche Bedarfsprüfung berücksichtigt diese noch nicht. Sechs-Stunden-Fälle werden davon getrennt geprüft.",
        "- **Aichwald / Erdmannhausen:** die Originalpreise einschließlich Essen sind erhalten. Die laufende Engine liest ergänzende reine Betreuungsanteile nicht automatisch; solche Beträge werden nicht ungeprüft als Kartenwert freigegeben.",
        "- **Freiberg / Kernen / Ostfildern / Waiblingen:** fehlende örtliche Modellannahmen werden nicht durch eine Brutto-Konvertierung ersetzt. Waiblingens Prozentformel und Inklusivdarstellung sowie Renningens Ü3-Stundenformel benötigen eine abgestimmte Lösung.",
        "- **Weitere Datenarbeit:** fehlende Tagesverteilungen, unterschiedliche Kostenvarianten und besondere Preis-Selektoren werden mit konkretem Grund im Freigabeindex geführt. Datenkorrekturen sind von Änderungen der gemeinsamen Rechenlogik zu unterscheiden.","",
        "Änderungen der gemeinsamen Berechnungslogik für einzelne Kommunen werden vorab mit dem Nutzer besprochen. Für Schwieberdingen ist keine Engineänderung beauftragt. Schritt 3 bleibt die vertiefte Quellenabnahme der freizugebenden Ergebnisse, Schritt 4 die kontrollierte Integration.","",
        "## Ablage und Wiederholung","",
        "- [Maschinenlesbarer Freigabeindex](../data/expansion/calculation_review.json): geprüfter Umfang, Fallgruppen, Ablehnungsgründe und Standardergebnisse. Nicht berechenbare Standardergebnisse haben ausschließlich leere Geldfelder.",
        "- [Prüfbedingungen](../data/reviews/expansion_compatibility_policy.json) und [Referenzfälle](../data/reviews/expansion_calculation_cases.json): Quellenbelege und ausdrückliche Entscheidungen.",
        "- Rohproben und Profile bleiben unter `build/expansion-review/` und werden nicht veröffentlicht. Der produktive Export liest weiterhin nur die bisherigen zwölf Kommunen.","",
        "Der Freigabeindex ist ein Offline-Prüfergebnis, noch keine angeschlossene Laufzeitsperre. Eine spätere Veröffentlichung muss ihn wirksam beachten; die Importkataloge dürfen nicht ungeprüft aktiviert werden. Änderungen an Quellen, Katalogen, Modellprofilen, Engine oder Prüflogik machen die jeweilige Freigabe anhand gespeicherter Prüfsummen ungültig.","",
        "```bash","python3 scripts/review_expansion_compatibility.py","# Bereits vorhandene, unveränderte Rohproben erneut auswerten:",
        "python3 scripts/review_expansion_compatibility.py --reuse-probes --check","```",""]
    return "\n".join(lines)


if __name__=="__main__":main()
