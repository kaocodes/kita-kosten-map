"""Normalize archived expansion tariffs without changing the engine or live registry.

Inputs are the reviewed source archive and visual transcriptions. Outputs use the
existing municipality schema and stay in an isolated import area until acceptance.
All source-specific adapters fail on unexpected table shapes.
"""

import argparse
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/research/neighbor_expansion_2026-11-10.json"
OUTPUT = ROOT / "data/expansion/municipalities"
REGISTER = json.loads(RESEARCH.read_text())
TRANSCRIPTIONS = json.loads((ROOT / REGISTER["transcriptions_path"]).read_text())
RECORDS = {item["id"]: item for item in REGISTER["municipalities"]}
MONEY = re.compile(r"(?<![\d.,])\d[\d.]*(?:,\d{1,2})?(?=\s*(?:€|Euro|EUR))")


def read_text(source_id):
    return (ROOT / "data/sources" / source_id / "text.txt").read_text()


def money(value):
    if value is None or value in {"-", "–"}:
        return None
    if isinstance(value, int):
        return value * 100
    return int(Decimal(str(value).replace(".", "").replace(",", ".")) * 100)


def amounts(line):
    return [money(value) for value in MONEY.findall(line)]


def evidence(source_id, locator, original=None):
    return {"source_id": source_id, "locator": locator, "original": original}


def stable_id(city, kind, key):
    return f"{city['id']}-{kind}-{hashlib.sha256(key.encode()).hexdigest()[:12]}"


def write_if_changed(path, content):
    """Do not invalidate downstream probe freshness for byte-identical outputs."""
    if not path.exists() or path.read_text()!=content:
        path.write_text(content)


def create_city(city_id, family_basis="under_18"):
    record = RECORDS[city_id]
    primary = record["reference_price"]["source_id"]
    city = {
        "schema_version": "1.0", "id": city_id, "name": record["name"],
        "reviewed_at": REGISTER["review_date"], "reference_date": REGISTER["reference_date"],
        "scope": {"included": ["municipal"], "other_providers": "only_with_explicit_source_evidence"},
        "family_basis": family_basis,
        "family_evidence": evidence(primary, "Familienbegriff und Fußnoten der Gebührenunterlagen"),
        "supporting_source_ids": list(record["key_source_ids"]),
        "offers": [], "prices": [], "income_bands": [], "components": [], "rules": [],
        "issues": [{"code": "pending_calculation_review", "detail": "Strukturierter Import; noch keine Freigabe des Rechners oder der Website."}],
        "coverage": {"publication_status": "not_active", "integration_status": "normalized_pending_calculation_review",
                     "history_in_scope": False, "source_register": str(RESEARCH.relative_to(ROOT)),
                     "research_id": city_id, "unavailable_configurations": deepcopy(record.get("unavailable_configurations", []))},
        "_source": primary, "_from": record["current_tariff_valid_from"] or "2026-09-01",
    }
    if record.get("current_tariff_period") == "2026/2027" and not record["current_tariff_valid_from"]:
        city["_until"]="2027-08-31"
        city["coverage"]["validity_basis"]="published_school_year_2026_2027"
        city["coverage"]["validity_start_verification"]="derived_school_year_start_not_independently_dated"
    for index, gap in enumerate(record["gaps"], 1):
        city["issues"].append({"code": f"research_limitation_{index}", "detail": gap})
    for key in ["comparison_policy", "provider_scope", "family_rules", "tariffs_by_age_group"]:
        if key in record:
            rule(city, key, record[key], primary, "Dokumentierte Forschungs- und Nutzerfestlegungen", provenance="research_and_user_decisions")
    for decision_id in record.get("decision_ids", []):
        decision = next(value for value in REGISTER["decisions"] if value["id"] == decision_id)
        rule(city, decision_id, decision, primary, "Nutzerfestlegung; keine zusätzliche amtliche Quellenbestätigung", provenance="user_instruction")
    return city


def payment(city, age=None):
    months = RECORDS[city["id"]]["payment_months"]
    if months["verification"] == "age_group_specific":
        months = months["by_age_group"][age]
    ref = evidence(months.get("source_id", city["_source"]), months.get("locator", months.get("notes", "Beitragspflicht")))
    ref["verification"] = months["verification"]
    if "decision_id" in months:
        ref.update(provenance="user_instruction", decision_id=months["decision_id"])
    return months["count"], ref


def offer(city, label, age, hours=None, *, source=None, locator="Gebührentabelle", start=None, end=None,
          daily=None, continuous=True, minimum=None, maximum=None, category="childcare", **extra):
    source = source or city["_source"]
    start = start or city["_from"]
    key = f"{label}:{age}:{start}"
    item = {
        "id": stable_id(city, "offer", key), "original_label": label,
        "age_group": age, "age_min_months": minimum if minimum is not None else (12 if age == "u3" else 36),
        "age_max_months_exclusive": maximum if maximum is not None else (36 if age == "u3" else None),
        "until_school_entry": age == "o3", "valid_from": start, "valid_to": end or city.get("_until"),
        "original_price_valid_from": start, "scope": "municipal", "category": category,
        "weekly_minutes": int((Decimal(str(hours)) * 60).quantize(Decimal("1"))) if hours is not None else None,
        "weekday_minutes": daily, "continuous": continuous,
        "schedule_status": "verified" if daily is not None else "daily_distribution_unverified",
        "schedule_evidence": evidence(source, locator),
        "payment_months": payment(city, age)[0], "payment_evidence": payment(city, age)[1],
        "evidence": evidence(source, locator), "formula": None, **extra,
    }
    if any(value["id"] == item["id"] for value in city["offers"]):
        raise ValueError(f"Duplicate offer: {key}")
    city["offers"].append(item)
    return item


def price(city, item, value, family, *, band=None, rank=None, pass_id="none", minimum=True,
          source=None, locator=None, status=None, included=None, selectors=None, cents=False):
    selection = {"family_count": family, "family_count_is_minimum": minimum and family == 4,
                 "income_band_id": band, "pass_id": pass_id, "care_rank": rank, **(selectors or {})}
    ref = evidence(source or item["evidence"]["source_id"], locator or item["evidence"]["locator"], value)
    amount = value if cents else money(value)
    included_parts=[]
    for part in included or []:
        if isinstance(part,str):
            original=next(c for c in city["components"] if c["id"]==part)
            included_parts.append({"component_id":part,"kind":original["kind"],"amount_cents":original["amount_cents"],"additional_charge":False})
        else:included_parts.append(deepcopy(part))
    row = {"id": stable_id(city, "price", item["id"] + json.dumps(selection, sort_keys=True)),
           "offer_id": item["id"], "amount_cents": amount, "unit": "per_month",
           "value_status": status or ("known" if amount is not None else "not_offered"),
           "selectors": selection, "included_components": included_parts, "evidence": ref}
    city["prices"].append(row)
    return row


def matrix(city, label, age, hours, values, **kwargs):
    pricing = {key: kwargs.pop(key) for key in list(kwargs) if key in {"band", "pass_id", "rank", "included", "cents", "selectors"}}
    item = offer(city, label, age, hours, **kwargs)
    for family, value in enumerate(values, 1):
        price(city, item, value, family, **pricing)
    return item


def component(city, label, value, *, source=None, locator="Verpflegung / Zusatzkosten", unit="per_month",
              age=None, required=None, months=None, kind="meal", offers=None, **extra):
    if "meal_days_per_week" in extra:
        extra["days_per_week"]=extra.pop("meal_days_per_week")
    item = {"id": stable_id(city, "component", label + str(extra.get("valid_from", city["_from"]))),
            "kind": kind, "original_label": label, "amount_cents": money(value), "unit": unit,
            "age_group": age, "required": required, "payment_months": months,
            "offer_ids": [o["id"] for o in offers] if offers else None,
            "valid_from": city["_from"], "valid_to": None,
            "value_status": "known" if value is not None else "unknown",
            "evidence": evidence(source or city["_source"], locator), **extra}
    city["components"].append(item)
    return item


def band(city, name, low, high, *, basis, source=None, period="year", reference="not_specified",
         lower_inclusive=True, upper_inclusive=True, **extra):
    identifier = stable_id(city, "income", name)
    city["income_bands"].append({"id": identifier, "basis": basis, "period": period,
        "reference_period": reference, "lower_cents": money(low), "upper_cents": money(high),
        "lower_inclusive": lower_inclusive, "upper_inclusive": upper_inclusive,
        "is_highest": high is None, "original_label": name,
        "evidence": evidence(source or city["_source"], "Einkommensstaffel: " + name), **extra})
    return identifier


def rule(city, name, parameters, source=None, locator="Gebührenbedingungen", **extra):
    city["rules"].append({"id": stable_id(city, "rule", name), "kind": name,
        "execution_status": "documented_not_implemented", "parameters": deepcopy(parameters),
        "evidence": evidence(source or city["_source"], locator), **extra})


def canonical_parameters(value):
    """Use scalar cent fields and evidence locators throughout nested parameters."""
    if isinstance(value, list):
        return [canonical_parameters(item) for item in value]
    if not isinstance(value, dict):
        return value
    output = {}
    for key, item in value.items():
        if key.endswith("_cents") and isinstance(item, list):
            output[key[:-6]] = [canonical_parameters({"amount_cents":amount}) if not isinstance(amount,(list,dict)) else canonical_parameters(amount) for amount in item]
        elif key.endswith("_cents") and isinstance(item, dict):
            output[key[:-6]] = {name:canonical_parameters(amount) for name,amount in item.items()}
        else:
            output[key] = canonical_parameters(item)
    if "source_id" in output and not output.get("locator"):
        output["locator"] = "Quellenzuordnung aus dem dokumentierten Recherche-Datensatz"
    return output


def money_rows(source, pattern=None):
    rows = []
    for page_number, page in enumerate(read_text(source).split("\f"), 1):
        for line_number, line in enumerate(page.splitlines(), 1):
            if (pattern is None or re.search(pattern, line)) and amounts(line):
                rows.append((amounts(line), f"PDF S. {page_number}, Textzeile {line_number}", line.strip()))
    return rows


def finish(city):
    record = RECORDS[city["id"]]
    # Included components must remain associated with their published offer variants.
    for part in city["components"]:
        if part.get("inclusion")=="included" and part.get("offer_ids") is None:
            part["offer_ids"] = sorted({row["offer_id"] for row in city["prices"]
                if any(p.get("component_id")==part["id"] for p in row["included_components"])})
    city["original_research"] = {"path": str(RESEARCH.relative_to(ROOT)), "section": city["name"],
        "text": "\n".join(record["findings"] + record["gaps"]), "source_clauses": []}
    for sid in record["key_source_ids"]:
        text = read_text(sid)
        if len(text.strip()) < 50:
            continue
        # Preserve complete provisions and footnotes alongside the structured tables.
        # Their execution status never claims support by the current calculator.
        rule(city, "source_provisions_" + sid, {"archive_text_path": f"data/sources/{sid}/text.txt",
             "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
             "review_status": "archived_provisions_preserved"}, sid, "Vollständiger archivierter Dokumenttext einschließlich Fußnoten")
        for page_number, page in enumerate(text.split("\f"), 1):
            for paragraph_index, paragraph in enumerate(re.split(r"\n\s*\n", page), 1):
                if len(paragraph.split()) < 8 or not re.search(
                    r"[Gg]ebühr|[Bb]eitr[aä]g|[Ee]rmäß|[Ee]inkomm|[Gg]eschwister|[Kk]indergeld|[Vv]erpfleg|[Rr]ückerstatt|[Rr]undung",
                    paragraph,
                ):
                    continue
                clause_index=len(city["original_research"]["source_clauses"])
                city["original_research"]["source_clauses"].append({"text": paragraph.strip(),
                    "evidence": evidence(sid,f"PDF-/Textseite {page_number}, Absatzblock {paragraph_index}")})
                rule(city, f"source_clause_{sid}_{page_number}_{paragraph_index}",
                     {"original_research_clause_index": clause_index, "interpretation_status": "documented_not_executed"},
                     sid, f"PDF-/Textseite {page_number}, Absatzblock {paragraph_index}")
    city["coverage"].update(offers=len(city["offers"]), price_cells=len(city["prices"]),
        income_bands=len(city["income_bands"]), components=len(city["components"]),
        rule_records=len(city["rules"]), tariff_table_transcription="complete_for_declared_scope")
    city["coverage"]["declared_scope"] = "Aktuelle und bereits veröffentlichte künftige Krippen- und Kindergartentarife; Zusatzkosten und Gebührenregeln."
    city["coverage"]["excluded_from_regular_price_rows"] = ["superseded_historical_tariffs", "school_childcare", "takki_and_childminding", "separate_playgroups"]
    city["coverage"]["calculation_engine_changed"] = False
    city["coverage"]["rule_transcription"] = "typed_parameters_and_source_clauses_with_explicit_unimplemented_status"
    return canonical_parameters({key: value for key, value in city.items() if not key.startswith("_")})


ADAPTERS = {}


def adapter(name):
    def register(function):
        ADAPTERS[name] = function
        return function
    return register


@adapter("affalterbach")
def affalterbach():
    city = create_city("affalterbach")
    city["family_basis"] = "under_18"
    for age, label, values in [("o3", "Verlängerte Öffnungszeiten Ü3", [155, 116, 77, 0]),
                                ("o3", "Ganztagsbetreuung Ü3", [340, 340, 300, 0]),
                                ("u3", "Ganztagsbetreuung ab dem dritten Lebensmonat", [503, 503, 447, 0])]:
        matrix(city, label, age, None, values, minimum=3 if age == "u3" else 36, locator="§ 3 Gebührentabellen")
    component(city, "Essensgeld zusätzlich", None, required=None)
    rule(city, "adult_children_on_application", {"condition": "school_or_vocational_training", "application_required": True}, locator="§ 3 nach den Tabellen")
    rule(city, "partial_month", {"admission_from_day": 15, "admission_fraction": "1/2", "departure_until_day": 14, "departure_fraction": "1/2"}, locator="§ 5 Abs. 5")
    return city


@adapter("aichwald")
def aichwald():
    city = create_city("aichwald", "under_18_or_child_benefit")
    sid = "d9055ebd6801"
    matrix(city, "Regelkindergarten", "o3", 30, [166,129,88,29], source=sid, continuous=False, locator="§ 6 Abs. 1")
    matrix(city, "Regelkindergarten unter drei Jahren", "u3", 30, [332,258,176,58], source=sid, continuous=False, minimum=24, category="mixed_age", locator="§ 6 Abs. 1")
    matrix(city, "VÖ7 ohne Mittagessen", "o3", 35, ["207,50","161,50",110,"36,50"], daily=[420]*5, source=sid, locator="§ 6 Abs. 2")
    meal = component(city, "VÖ7 Ü3 enthaltenes Mittagessen", 75, age="o3", months=12, source=sid, locator="Differenz § 6 Abs. 2 und 3", inclusion="included", additional_charge=False)
    base = matrix(city, "VÖ7 mit Mittagessen", "o3", 35, ["282,50","236,50",185,"111,50"], daily=[420]*5, source=sid, included=[meal["id"]], locator="§ 6 Abs. 3")
    for days, add in [(5,[110,"85,50","58,50","19,50"]),(4,[88,"68,50","46,50","15,50"]),(3,[66,"51,50",35,"11,50"])]:
        item = offer(city, f"VÖ7 + {days} GT-Nachmittage bis 16:30", "o3", 35 + days*2.5, source=sid, daily=[570]*5 if days==5 else None, locator=f"§ 6 Abs. 3 und 4, {days} Tage")
        for family, (original, supplement) in enumerate(zip(["282,50","236,50",185,"111,50"],add),1):
            row = price(city,item,money(original)+money(supplement),family,cents=True,included=[meal["id"]])
            row["derivation"]={"operation":"sum_published_cells","base_cents":money(original),"supplement_cents":money(supplement)}
    matrix(city, "Krippe 7–12 Uhr ohne Mittagessen", "u3",25,[410,305,206,81],daily=[300]*5,source=sid,locator="§ 6 Abs. 5, ohne Essen")
    food = component(city,"U3 enthaltenes Mittagessen",53,age="u3",months=12,source=sid,locator="Nutzerfestlegung 2026-11-10-aichwald-u3-meals",inclusion="included",additional_charge=False,verification="user_confirmed",decision_id="2026-11-10-aichwald-u3-meals")
    for label,hours,values,days in [("Krippe 7–12 Uhr mit Mittagessen",25,[463,358,259,134],5),
            ("Krippe 7–14 Uhr mit Mittagessen",35,[594,"455,50",325,160],5),
            ("Krippe GT fünf Nachmittage bis 16:30",47.5,["753,50","574,50",405,"191,50"],5),
            ("Krippe GT vier Nachmittage bis 16:30",None,[722,"550,50",389,185],4),
            ("Krippe GT drei Nachmittage bis 16:30",None,[690,527,373,179],3)]:
        item=matrix(city,label,"u3",hours,values,source=sid,daily=[int(hours*12)]*5 if hours else None,included=[food["id"]],locator="§ 6 Abs. 5–7; ursprüngliche Preise einschließlich Mittagessen")
        for row in [p for p in city["prices"] if p["offer_id"]==item["id"]]:
            row["care_only_amount_cents"]=row["amount_cents"]-5300
            row["normalization"]={"operation":"subtract_known_included_meal","deduction_cents":5300,"decision_id":"2026-11-10-aichwald-u3-meals"}
    for row in city["prices"]:
        if any(p.get("component_id")==meal["id"] for p in row["included_components"]):
            row["care_only_amount_cents"]=row["amount_cents"]-7500
            row["normalization"]={"operation":"subtract_known_included_meal","deduction_cents":7500,"provenance":"published_difference_between_meal_and_no_meal_tables"}
    return city


@adapter("altbach")
def altbach():
    city=create_city("altbach")
    for age,label,hours,values,category in [
        ("o3","Kindergarten VÖ30",30,[227,177,120,60],"kindergarten"),
        ("o3","Kindergarten GT40",40,[370,288,194,97],"kindergarten"),
        ("u3","Kindergarten U3 VÖ30",30,[432,337,228,114],"mixed_age"),
        ("u3","Kindergarten U3 GT40",40,[703,548,369,185],"mixed_age"),
        ("u3","Kinderkrippe VÖ30",30,[537,399,269,135],"nursery"),
        ("u3","Kinderkrippe GT40",40,[716,532,359,180],"nursery")]:
        matrix(city,label,age,hours,values,category=category,locator="Gebührenjahr 2026/2027, Ziffern 1–4")
    for days,value in [(1,21),(2,41),(3,62),(4,82),(5,102)]:
        component(city,f"Mittagessen {days} Tage/Woche",value,months=11,meal_days_per_week=days,locator="Ziffer 5 Mittagessen")
    return city


@adapter("asperg")
def asperg():
    city=create_city("asperg")
    sid="c039257120e8"
    for age,label,hours,values in [("o3","VÖ6",30,[175,"135,50","92,50",40]),
            ("o3","GT7,5",37.5,[248,"206,50","165,50",110]),
            ("o3","GT9,5",47.5,[320,"276,50",238,180]),
            ("u3","GT7,5",37.5,["373,50","336,50",299,"266,50"]),
            ("u3","GT9,5",47.5,[473,426,379,"336,50"])]:
        matrix(city,label,age,hours,values,source=sid,daily=[int(hours*12)]*5,locator="§ 5 Abs. 6 a–e, Spalte ab 01.09.2025")
    for label,hours,values in [("GT7,5 je Betreuungstag/Woche",7.5,["85,50",78,"71,50","63,50"]),("GT9,5 je Betreuungstag/Woche",9.5,[107,98,90,80])]:
        matrix(city,label,"u3",hours,values,source=sid,locator="§ 5 Abs. 6 f–g, tageweise U3-Beiträge",days_per_week=1)
    component(city,"Mittagessen je Portion","4,20",source=sid,unit="per_meal",locator="§ 5 Abs. 6 h")
    component(city,"Verspätete Abholung",25,source=sid,unit="per_started_hour",kind="late_pickup",required=False,locator="§ 6 Abs. 6")
    rule(city,"pass_discounts",{"single_parent_state_family_pass_percent":30,"municipal_family_pass_percent":50,"meal_hardship_discount_percent":50,"application_required":True},sid,"§ 6 Abs. 1–5")
    rule(city,"mixed_age_u3_surcharge",{"percent":50,"applies_to":"kindergarten_admission_before_age_three"},sid,"§ 6 Abs. 4")
    for item in city["offers"]:item["valid_to"]="2026-12-31"
    for item in city["components"]:
        if item["kind"]=="meal":item["valid_to"]="2026-12-31"
    future="b67815bb6fad"
    pairs=[]
    for line in read_text(future).split("p)   Verpflegungsaufwand")[0].splitlines():
        match=re.search(r"(\d+,\d{2})[ \t]+(\d+,\d{2})[ \t]*$",line)
        if match:pairs.append([money(value) for value in match.groups()])
    assert len(pairs)==60
    groups=[("o3",6,5),("o3",7.5,5),("o3",9.5,5)]+[("u3",hours,days) for hours in [6,7.5,9.5] for days in [5,4,3,2]]
    for group,(age,hours,days) in enumerate(groups):
        for col,start,end in [(0,"2027-01-01","2027-08-31"),(1,"2027-09-01",None)]:
            matrix(city,f"{'VÖ' if hours==6 else 'GT'}{str(hours).replace('.',',')} an {days} Tagen",age,hours*days,[r[col] for r in pairs[group*4:group*4+4]],
                source=future,start=start,end=end,cents=True,daily=[int(hours*60)]*5 if days==5 else None,locator=f"§ 5 Abs. 5 {chr(97+group)}, ab {start}",days_per_week=days)
    for days,value in [(2,"34,50"),(3,52),(4,69),(5,"86,50")]:component(city,f"Mittagessen ab 2027, {days} Tage",value,months=12,source=future,meal_days_per_week=days,valid_from="2027-01-01",locator="§ 5 Abs. 5 p")
    component(city,"Mittagessen während Eingewöhnung ab 2027","4,50",unit="per_meal",source=future,valid_from="2027-01-01",locator="§ 5 Abs. 5 p")
    city["issues"].append({"code":"published_non_monotone_future_cell","detail":"Asperg ab September 2027, U3 GT9,5 drei Tage: vier Kinder 284,50 Euro laut Quelle; nicht auf einen vermuteten niedrigeren Betrag korrigiert."})
    return city


@adapter("benningen")
def benningen():
    city=create_city("benningen", "resident_children")
    for age,minimum,maximum,values in [("o3",36,None,[[217,417,356],[169,325,277],[115,221,189],[38,73,62]]),
            ("u3",24,36,[[434,834,712],[338,650,554],[230,442,378],[76,146,124]]),
            ("u3",12,24,[[582,895,None],[432,665,None],[291,448,None],[115,177,None]])]:
        for column,label,hours in [(0,"VÖ",None),(1,"GT fünf Tage",45.5),(2,"GT drei Tage",None)]:
            matrix(city,f"Ab {minimum//12}. Geburtstag: {label}",age,hours,[row[column] for row in values],minimum=minimum,maximum=maximum,locator="Elternbeiträge 2026/2027; Zeile der Altersgruppe",daily=[570]*4+[450] if column==1 else None)
    for row in city["prices"]:
        row["selectors"]["family_count_is_minimum"]=False
    rule(city,"conflicting_vo_hours",{"printed_daily_hours":"6,5","printed_opening_times":"7:00–14:30","resolved_daily_minutes":None},locator="Fußzeile der Gebührentabelle")
    for group,values in [("ab zwei Jahren",[13,25,37,48,61]),("ab einem Jahr",[6,14,20,27,33])]:
        for days,value in enumerate(values,1):
            component(city,f"Mittagessen {group}, {days} Tage",value,meal_days_per_week=days,locator="Mittagessen neben den Altersgruppentabellen")
    component(city,"Verspätetes Abholen ab drittem Verstoß",50,unit="per_started_half_hour",kind="late_pickup",required=False)
    return city


@adapter("deizisau")
def deizisau():
    city=create_city("deizisau","under_18_or_child_benefit")
    base=[228,175,118,40]
    gt={1:[274,204,138,46],2:[308,232,155,54],3:[344,258,173,60],4:[382,287,190,64],5:[418,311,210,71]}
    for age,factor in [("o3",1),("u3",2)]:
        matrix(city,"VÖ 7–13 Uhr",age,30,[v*factor for v in base],daily=[360]*5,locator="VÖ-Tabelle ab September 2026")
        for days,values in gt.items():
            matrix(city,f"GT 7–17 Uhr an {days} Tagen, sonst VÖ",age,30+4*days,[v*factor for v in values],daily=[600]*5 if days==5 else None,locator=f"GT-Tabelle, {days} Tage/Woche",gt_days_per_week=days,
                   weekday_pattern={"long_days":days,"long_day_minutes":600,"other_day_minutes":360})
    component(city,"Mittagessen",None,required=True,offers=[o for o in city["offers"] if o.get("gt_days_per_week",0)>0],applies_when={"gt_days_per_week_min":1})
    rule(city,"gt_eligibility",{"annual_employer_certificate_required":True},locator="Einleitung zur Beitragstabelle")
    rule(city,"older_children",{"max_age_years":25,"child_benefit_proof_required":True},locator="Fußnote unter der Beitragstabelle")
    return city


@adapter("denkendorf")
def denkendorf():
    city=create_city("denkendorf")
    city["scope"]={"included":["municipally_published_shared_tariff"],"other_providers":"evangelical_and_catholic_providers_listed_by_municipality"}
    bands=[]
    for low,high in [(None,52700),(52701,66100),(66101,79600),(79601,92700),(92701,105800),(105800,None)]:
        bands.append(band(city,f"{low or 0}–{high or 'offen'} Euro",low,high,basis="gross_income",lower_inclusive=high is not None))
    data={
      "u3":[("VÖ30",30,[[376,279,188,74],[430,319,215,85],[483,359,242,95],[537,399,269,106],[591,439,296,117],[644,479,323,127]]),
              ("Vier GT-Tage und Freitag VÖ, 45 Wochenstunden",45,[[543,402,272,109],[621,459,310,124],[698,517,349,140],[776,574,388,155],[854,632,427,171],[931,689,466,186]])],
      "o3":[("VÖ30",30,[[127,99,67,22],[145,113,77,26],[163,127,86,29],[181,141,96,32],[199,155,106,35],[217,169,115,38]]),
              ("VÖ35",35,[[185,142,98,33],[211,163,112,38],[238,183,126,43],[264,203,140,48],[290,224,154,52],[317,244,168,57]]),
              ("Vier GT-Tage und Freitag VÖ, 45 Wochenstunden",45,[[293,226,155,53],[335,258,177,60],[377,290,200,68],[419,322,222,75],[460,354,244,83],[502,387,266,90]])]}
    for age,tables in data.items():
        source="08b47127170a" if age=="u3" else "a19eb9cb9cf3"
        for label,hours,rows in tables:
            item=offer(city,label,age,hours,source=source,daily=[570]*4+[420] if hours==45 else [int(hours*12)]*5,minimum=0 if age=="u3" else 36,locator=f"PDF S. 1, {label}; Bruttoeinkommensgruppen")
            for income,values in zip(bands,rows,strict=True):
                for family,value in enumerate(values,1):price(city,item,value,family,band=income)
    component(city,"Mittagessen bei Ganztag verpflichtend; Kosten nicht bekannt",None,required=True,applies_when={"care_type":"full_day"},meal_days_per_week=5)
    rule(city,"proportional_care_time",{"basis":"actually_offered_hours","minimum_gt_afternoons":2,"no_fictitious_daily_schedule":True},locator="Letzter Absatz der U3-/Ü3-Tabelle")
    return city


@adapter("hemmingen")
def hemmingen():
    city=create_city("hemmingen")
    tables=[("Regelgruppe bis 30 Wochenstunden",30,[[166,"306,80"],["124,50","230,10"],[83,"153,40"],[29,"76,70"],["132,80","245,40"]],False),
            ("VÖ bis 35 Wochenstunden",35,[["199,10","342,70"],["149,30",257],["99,60","171,40"],["49,80","85,70"],["159,30","274,20"]],True),
            ("GT bis 45 Wochenstunden",45,[["431,60","595,40"],["391,90","549,30"],["348,80","505,50"],["293,80","426,20"],["345,30","476,30"]],True),
            ("Spielgruppe und VÖ bis 45 Wochenstunden",45,[["303,50","447,10"],["253,70","361,40"],[204,"275,80"],["154,20","190,10"],["263,70","378,60"]],True)]
    for label,hours,rows,continuous in tables:
        for col,age in enumerate(["o3","u3"]):
            item=matrix(city,label,age,hours,[r[col] for r in rows[:4]],continuous=continuous,locator="§ 3 Abs. 2 a–d")
            price(city,item,rows[4][col],1,selectors={"single_parent":True})
            for row in city["prices"]:
                if row["offer_id"]==item["id"] and row["selectors"]["family_count"]==1 and "single_parent" not in row["selectors"]:
                    row["selectors"]["single_parent"]=False
    rule(city,"rounding",{"unit_cents":10,"mode":"source_does_not_specify_direction"},locator="§ 3 Abs. 7")
    return city


@adapter("magstadt")
def magstadt():
    city=create_city("magstadt")
    for age,label,hours,values in [("o3","VÖ6",30,[166,129,88,None]),("o3","GT8",40,[394,305,201,79]),("o3","GT9",45,[443,343,226,89]),
          ("u3","VÖ6",30,[482,356,243,None]),("u3","GT8",40,[595,441,300,118]),("u3","GT9",45,[669,496,338,133])]:
        item=matrix(city,label,age,hours,values,daily=[int(hours*12)]*5,locator="Gebührentabelle ab 01.09.2026")
        if hours==30:
            city["prices"]=[p for p in city["prices"] if not(p["offer_id"]==item["id"] and p["selectors"]["family_count"]==4)]
            for rank,amount in [(1,values[2]),(2,values[2]),(3,values[2]),(4,0)]:
                row=price(city,item,amount,4,rank=rank,selectors={"care_rank_is_minimum":rank==4,"rank_basis":"birth_order"})
    component(city,"Mittagessen je Portion","3,95",unit="per_meal")
    rule(city,"gt_day_combination",{"age_group":"o3","minimum_gt_days":2,"daily_fraction":"1/5","remaining_days":"vo"},locator="Fußnote unter der Tabelle")
    return city


@adapter("moeglingen")
def moeglingen():
    city=create_city("moeglingen")
    data={"o3":[[208,243,288,323,358],[166,194,230,258,286],[125,146,173,194,215],[83,97,115,129,143]],
          "u3":[[312,365,432,485,537],[249,291,345,387,429],[186,219,260,291,323],[125,146,173,194,215]]}
    reduced={"o3":[["135,20","157,95","187,20","209,95","232,70"],["107,90","126,10","149,50","167,70","185,90"],["81,25","94,90","112,45","126,10","139,75"],["53,95","63,05","74,75","83,85","92,95"]],
       "u3":[["202,80","237,25","280,80","315,25","349,05"],["161,85","189,15","224,25","251,55","278,85"],["120,90","142,35","169,00","189,15","209,95"],["81,25","94,90","112,45","126,10","139,75"]]}
    for age,rows in data.items():
        for index,hours in enumerate(range(6,11)):
            item=matrix(city,f"{'VÖ' if hours<8 else 'GT'}{hours}",age,hours*5,[r[index] for r in rows],daily=[hours*60]*5,locator="PDF S. 1: veröffentlichte Endbeträge einschließlich GT-Pauschale")
            for family,row in enumerate(reduced[age],1):price(city,item,row[index],family,pass_id="moeglingen_family_pass",locator="PDF S. 2: veröffentlichte Familienpassbeträge")
    for age,value in [("u3",61),("o3",72)]:component(city,"Mittagessen "+age,value,age=age,required=True,offers=[o for o in city["offers"] if o["age_group"]==age and o["original_label"].startswith("GT")],applies_when={"care_type":"full_day"},locator="Unterhalb der Beitragstabellen; keine Passermäßigung")
    component(city,"Einrichtungsabhängiger Elternbeiratsbeitrag",None,kind="supplies",required=True,locator="Fußnote: Vesperrunde, pädagogische Kochtage")
    rule(city,"pass_eligibility",{"eligible_groups":["A","C","D"],"discount_percent":35,"application_required":True,"meals_excluded":True},"362f70fede0a","Abschnitte I–III")
    rule(city,"admission_and_age_transition",{"billing_dates":[1,16],"depends_on":"admission_start_or_birthday","transition":"following_billing_half_month"},locator="Fußnoten unter beiden Tabellen")
    return city


@adapter("schwieberdingen")
def schwieberdingen():
    city=create_city("schwieberdingen")
    rows=[[492,526,559,593,626],[366,395,424,454,483],[247,273,299,325,351],[97,118,139,160,181]]
    for index,hours in enumerate(range(6,11)):
        matrix(city,f"U3 bis {hours} Stunden", "u3", hours*5,[r[index] for r in rows],locator="PDF S. 1, U3-Tabelle",provider_restriction="catholic_only" if hours==7 else None)
    rows={1:[[176,186,186,196,206]],2:[[139,149,149,159,169],[70,75,75,80,85]],3:[[98,108,108,118,128],[49,54,54,59,64]],4:[[40,49,49,59,69]]}
    for col,label,hours in [(0,"VÖ",None),(1,"VÖ mit MeKi",None),(2,"8 Stunden",40),(3,"9 Stunden",45),(4,"10 Stunden",50)]:
        item=offer(city,label,"o3",hours,locator="PDF S. 2, Ü3-Tabelle")
        for family,ranks in rows.items():
            for rank,values in enumerate(ranks,1):price(city,item,values[col],family,rank=rank if family in {2,3} else None)
    component(city,"U3 Pflegeartikel",7,age="u3",required=True,kind="supplies")
    component(city,"U3 Windeln bei Bedarf",7,age="u3",required=None,kind="supplies",condition="diapers_needed")
    component(city,"U3 Verpflegung",85,age="u3")
    component(city,"Ü3 Mittagessen",None,age="o3",unit="per_meal")
    component(city,"Ü3 Frühstück falls angeboten",15,age="o3",required=None,condition="breakfast_offered")
    for item in city["offers"]:
        daily=360 if item["original_label"] in {"U3 bis 6 Stunden","VÖ"} else 480 if item["original_label"] in {"U3 bis 8 Stunden","8 Stunden"} else None
        if daily is not None:
            item.update(weekly_minutes=daily*5,weekday_minutes=[daily]*5,schedule_status="verified",
                schedule_evidence=evidence("483de900d001","Gemeindeseite: Sonnenschein Krippe VÖ 7:30–13:30 / GT 7:30–15:30; Herrenwiesenweg Kindergarten VÖ 8–14 / GT 7–15 Uhr"))
        elif item["original_label"]=="VÖ mit MeKi":
            item["weekly_minutes"]=2400
            item["schedule_evidence"]=evidence("483de900d001","Pusteblume: MeKi 7:30–15:30, bis acht Stunden; konkrete Einrichtungsvariante separat dokumentiert")
    return city


def transcription(name):
    return next(s for s in TRANSCRIPTIONS["sources"] if s["municipality"] == name)


@adapter("aidlingen")
def aidlingen():
    city=create_city("aidlingen")
    source=transcription("Aidlingen")
    for table in source["tables"]:
        start=table["valid_from"]
        for row in table["rows"]:
            hours={"VÖ":30,"VÖ+":32.5,"GT8":40}[row["original_label"]]
            matrix(city,row["original_label"],table["age_group"],hours,row["amounts_cents"],source=source["source_id"],start=start,
                end="2027-08-31" if start=="2026-09-01" else None,daily=[int(hours*12)]*5,cents=True,locator="Bildbasierte Änderungssatzung S. 1–2, " + start)
    for item in city["offers"]:
        item["schedule_evidence"]=evidence("f990b6b54a41","§ 2 Abs. 2: VÖ sechs, VÖ+ sechseinhalb und GT8 acht Stunden täglich")
    component(city,"Essensgeld",None,required=None,source="f990b6b54a41",locator="Benutzungsordnung: zusätzliche Verpflegung")
    return city


@adapter("eberdingen")
def eberdingen():
    city=create_city("eberdingen")
    source=transcription("Eberdingen")
    for table in source["tables"]:
        for row in table["rows"]:
            hours=7.5 if "7,5" in row["original_label"] else 6
            item=offer(city,row["original_label"],table["age_group"],hours*5,source=source["source_id"],daily=[int(hours*60)]*5,locator="PDF S. 6–7 und 14–15, neues Beitragssystem ab November 2025",contract_regime="new_contribution_system")
            for rank,value in enumerate(row["amounts_cents"],1):
                price(city,item,value,1,rank=rank,minimum=True,cents=True,selectors={"family_count_is_minimum":True,"care_rank_is_minimum":rank==3,"rank_basis":"simultaneous_care_youngest_first"})
    for label,low,high,percent in [("unter 25.000 Euro",None,25000,50),("25.000,01–35.000 Euro","25000,01",35000,25)]:
        b=band(city,label,low,high,basis="gross_income",source=source["source_id"],upper_inclusive=percent!=50)
        rule(city,"income_reduction_"+str(percent),{"income_band_id":b,"discount_percent":percent,"condition":source["reduction_condition"]},source["source_id"],"§ 6 Abs. 9")
    rule(city,"contract_regime",{"scope":"new_contribution_system","legacy_contracts":"preserved_in_original_not_automatically_reclassified"},source["source_id"],"Übergangsregelungen und alte Vertragssystematik")
    component(city,"Einrichtungsabhängiges Mittagessen zum Selbstkostenpreis",None,source=source["source_id"],required=None,locator="Satzung: Verpflegung")
    return city


@adapter("ehningen")
def ehningen():
    city=create_city("ehningen")
    s=transcription("Ehningen")
    for age,base in s["base_amounts_cents"].items():
        for group in s["published_module_groups"]:
            options=[None] if "weekday_minutes" in group else group["long_days"]
            for days in options:
                schedule=group.get("weekday_minutes")
                total=sum(schedule) if schedule else days*group["long_day_minutes"]+(5-days)*group["other_day_minutes"]
                label=group["original_label"]+(f", {days} lange Tage" if days else "")
                item=offer(city,label,age,total/60,source=s["source_id"],daily=schedule,locator="PDF S. 1–3, Grundgebühr und veröffentlichte Modulgruppen")
                if days is not None:
                    item["weekday_pattern"]={"long_days":days,"long_day_minutes":group["long_day_minutes"],"other_day_minutes":group["other_day_minutes"]}
                for family,value in enumerate(base,1):
                    amount=value+(total-1800)//60*s["additional_weekly_hour_monthly_amounts_cents"][family-1]
                    if "amounts_cents" in group:amount=group["amounts_cents"][age][family-1]
                    row=price(city,item,amount,family,cents=True)
                    row["derivation"]={"base_cents":value,"additional_weekly_hours":(total-1800)//60,"per_weekly_hour_cents":s["additional_weekly_hour_monthly_amounts_cents"][family-1],"published_final_cell":"amounts_cents" in group}
        rule(city,"weekly_hour_formula_"+age,{"base_weekly_minutes":1800,"base_amounts_cents":base,"additional_weekly_hour_monthly_amounts_cents":s["additional_weekly_hour_monthly_amounts_cents"]},s["source_id"],"Grundbeitrag und Zuschlag je weiterer Wochenstunde")
    component(city,"Mittagessen",None,source="da4b793532b5",required=None,locator="Verpflegung gesondert")
    return city


@adapter("erdmannhausen")
def erdmannhausen():
    city=create_city("erdmannhausen")
    s=transcription("Erdmannhausen")
    for category,base in s["base_amounts_cents"].items():
        age="o3" if category=="o3" else "u3"
        for reduced,values in [(False,base),(True,s["published_reduced_base_amounts_cents"][category])]:
            income=band(city,category+(" Einkommen unter 2.826 Euro" if reduced else " regulärer Beitrag"),None,2826,basis="gross_income",period="month",upper_inclusive=False) if reduced else None
            for gt_days in [0]+s["gt_days"]:
                label=f"{category} VÖ"+(f" + {gt_days} GT-Nachmittage" if gt_days else "")+(" ermäßigter Grundbeitrag" if reduced else "")
                base_minutes=410 if category=="u3" else 420
                daily=[base_minutes]*5 if gt_days==0 else [600]*5 if gt_days==5 else None
                weekly=base_minutes*5+(600-base_minutes)*gt_days
                item=offer(city,label,age,weekly/60,source=s["source_id"],daily=daily,minimum=30 if category=="u3_mixed" else None,category="mixed_age" if category=="u3_mixed" else "childcare",locator="PDF S. 3–7: Öffnungszeiten, Grundbeiträge und GT-Gesamttabellen",gt_days_per_week=gt_days)
                surcharge=s["gt_monthly_surcharges_cents"][gt_days-1] if gt_days else 0
                meal=s["published_meal_monthly_amounts_cents"][gt_days-1] if gt_days else 0
                for family,value in enumerate(values,1):
                    row=price(city,item,value+surcharge+meal,family,cents=True,band=income,minimum=False)
                    row["derivation"]={"base_cents":value,"gt_surcharge_cents":surcharge,"included_meal_cents":meal}
                    row["care_only_amount_cents"]=value+surcharge
                    if gt_days:
                        row["included_components"]=[{"kind":"meal","amount_cents":meal,"unit":"per_month"}]
            rule(city,"gt_formula_"+category+("_reduced" if reduced else ""),{"base_amounts_cents":values,"gt_days":s["gt_days"],"gt_surcharges_cents":s["gt_monthly_surcharges_cents"],"meal_amounts_cents":s["published_meal_monthly_amounts_cents"]},s["source_id"],"PDF S. 3–7")
    for days,value in zip(s["gt_days"],s["published_meal_monthly_amounts_cents"],strict=True):
        component(city,f"Mittagessen {days} Tage/Woche",str(Decimal(value)/100).replace('.',','),source=s["source_id"],meal_days_per_week=days,locator="Verpflegungsstaffel in den GT-Tabellen")
    rule(city,"family_and_income_discounts",s["additional_rules"],s["source_id"],"Ermäßigungsregeln und Fußnoten")
    return city


@adapter("freiberg")
def freiberg():
    city=create_city("freiberg","child_benefit")
    s=transcription("Freiberg am Neckar")
    sid=s["source_id"]
    city["scope"]={"included":["municipal_o3","zwergenstueble_freiberg_u3"],"other_providers":"explicit_user_authorization_for_named_u3_provider"}
    bands={}
    for family,threshold in enumerate(s["income_bands"]["household_child_thresholds_euros"],1):
        for n,low,high in [(1,None,threshold["band_1_upper_inclusive"]),(2,threshold["band_2_lower_inclusive"],None)]:
            bands[family,n]=band(city,f"{family} Kinder, Stufe {n}",low,high,basis="freiberg_household_net",source="5f09f91f5eb1",period="month",family_count=family,family_count_is_minimum=family==4)
    for table in s["tables"]:
        if table["age_group"]!="u3":continue
        variant=table["offer_variant"]
        for row in table["rows"]:
            label=row["original_label"]
            hours=None;daily=None
            if variant=="Flattichstraße":
                hours=32.5 if "13:30" in label else 35 if "14:00" in label else 40 if "40" in label else 45
                daily=[int(hours*12)]*5
            elif variant=="Riedstraße" and "plus" not in label:
                hours=32.5 if "halbtags" in label else 44
                daily=[390]*5 if hours==32.5 else [540]*4+[480]
            elif variant=="Murmel" and "plus" not in label:
                hours=30 if "13:30" in label else 32.5 if "14:00" in label else 45
                daily=[int(hours*12)]*5
            elif variant=="Marienstraße" and label.startswith("5 Tage"):
                hours=32.5 if "halbtags" in label else 50
                daily=[int(hours*12)]*5
            item=offer(city,variant+": "+label,"u3",hours,start=s["valid_from"],daily=daily,source=sid,locator="Gebührenordnung S. 1–3, Standorttabelle "+variant,provider_id=s["provider"]["id"],scope="authorized_provider")
            for family in range(1,5):
                for n,amount in enumerate(row["amounts_cents"],1):price(city,item,amount,family,band=bands[family,n],cents=True)
    for label,hours,rows in [("Vormittag 6 Stunden",30,[[229,"263,50"],["137,50",158],[46,"52,50"],[0,0]]),
        ("Vormittag 7 Stunden",35,[["242,50",279],["145,50","167,50"],["48,50",56],[0,0]]),
        ("GT40",40,[[355,408],[213,245],[71,"81,50"],[0,0]]),
        ("GT45",45,[[430,"494,50"],[258,"296,50"],[86,99],[0,0]])]:
        item=offer(city,label,"o3",hours,source="5f09f91f5eb1",start="2026-09-01",daily=[int(hours*12)]*5 if hours in [30,35] else None,locator="Anlage A S. 1–2, "+label)
        for family in range(1,5):
            for rank,row in enumerate(rows,1):
                for n,value in enumerate(row,1):price(city,item,value,family,rank=rank,band=bands[family,n],selectors={"care_rank_is_minimum":rank==4,"rank_basis":"simultaneous_care_youngest_first"})
    for part in s["components"]:
        if part.get("age_group")=="o3":continue
        rows=part.get("rows",[part])
        for index,row in enumerate(rows,1):
            label=part.get("original_label",part["kind"])+" "+str(index)
            component(city,label,str(Decimal(row["amount_cents"])/100).replace('.',','),source=sid,age=part.get("age_group"),months=part.get("payment_months"),required=part.get("required"),kind=part["kind"],locator="Gebührenordnung S. 1 und 4–5",conditions=deepcopy(row),valid_from=s["valid_from"])
    component(city,"Städtisches Ü3 VÖ Lebensmittelbeitrag",5,source="5f09f91f5eb1",age="o3",months=11,required=True,kind="supplies",locator="Anlage A S. 1")
    component(city,"Städtisches Ü3 GT Mittagessen fünf Tage",82,source="5f09f91f5eb1",age="o3",months=11,required=True,locator="Anlage A S. 2")
    rule(city,"authorized_provider_supplementary_o3_tables",{"tables":[t for t in s["tables"] if t["age_group"]=="o3"],"components":[p for p in s["components"] if p.get("age_group")=="o3"],"use_as_municipal_o3_reference":False},sid,"S. 3–5, ergänzende Ü3-Anbietertarife; städtisches Ü3 bleibt maßgeblich")
    for index,value in enumerate(s["rules"]):rule(city,"provider_rule_"+str(index),value,sid,"Gebührenordnung S. 5")
    return city


@adapter("baltmannsweiler")
def baltmannsweiler():
    city=create_city("baltmannsweiler")
    sid="dbe696bf2305"
    text=read_text(sid).split("III.")[0]
    rows=[amounts(line) for line in text.splitlines() if re.match(r"\s*[1-4] Kind",line) and amounts(line)]
    assert len(rows)==32 and all(len(row)==3 for row in rows)
    groups=[("u3",25),("u3",30),("u3",35),("o3",25),("o3",30),("o3",35),("o3",40.5),("o3",44.5)]
    for index,(age,hours) in enumerate(groups):
        for column,year in [(0,2026),(1,2027)]:
            matrix(city,f"{hours} Stunden/Woche",age,hours,[r[column] for r in rows[index*4:index*4+4]],source=sid,cents=True,start=f"{year}-09-01",end=f"{year+1}-08-31" if year==2026 else None,locator=f"Abschnitt {'I' if age=='u3' else 'II'}, {hours} Wochenstunden; Spalte ab 01.09.{year}")
    rule(city,"mandatory_meals",{"u3_all_models":True,"o3_vo_xl_and_gt":True,"u3_meal_days":5},sid,"Abschnitte I und II")
    for age,values in [("u3",[16,31,46,61,77]),("o3",[19,37,55,73,91])]:
        for days,value in enumerate(values,1):
            component(city,f"Mittagessen {age} {days} Tage/Woche",value,age=age,source=sid,meal_days_per_week=days,locator="Abschnitt V, aktuelle Essensbeiträge (nicht Klammerwerte)")
    return city


@adapter("grafenau")
def grafenau():
    city=create_city("grafenau")
    sid="2dda8afa554c"
    for year in [2026,2027]:
        text=read_text(sid).split(f"Gebühren für das Kindergartenjahr {year}/{year+1}")[1].split("3. Gebührensätze")[0]
        rows=[amounts(line) for line in text.splitlines() if amounts(line)]
        assert len(rows)==8
        for age,section in [("o3",rows[:4]),("u3",rows[4:])]:
            for days in range(6 if age=="o3" else 4):
                matrix(city,"VÖ"+(f" + {days} GT-Nachmittage" if days else ""),age,30+days*3.5,[r[days] for r in section],source=sid,cents=True,
                    start=f"{year}-09-01",end="2027-08-31" if year==2026 else None,daily=[360]*5 if days==0 else [570]*5 if days==5 else [570]*3+[360]*2 if age=="u3" and days==3 else None,
                    locator=f"Gebührenverzeichnis {year}/{year+1}, Nr. {'1' if age=='o3' else '2'}, VÖ + {days} GT",gt_days_per_week=days)
    component(city,"Mittagessen bei GT-Nachmittagen verpflichtend",None,required=True,applies_when={"gt_days_per_week_min":1},source=sid,locator="§ 3 Abs. 3")
    rule(city,"gt_booking",{"minimum_gt_afternoons":1,"u3_gt_days_available":["monday","tuesday","wednesday"],"o3_gt_days_available":["monday","tuesday","wednesday","thursday","friday"]},sid,"§ 2–3")
    return city


@adapter("holzgerlingen")
def holzgerlingen():
    city=create_city("holzgerlingen")
    sid="08a2ada2b7fc"
    for age,label,hours,values,continuous in [("o3","Regelkindergarten",30,[159,123,82,28],False),
          ("o3","VÖ Modell 30",30,[180,138,92,31],True),
          ("o3","VÖ Modell 35",35,[210,161,107,36],True),
          ("o3","GT Modell 37,5",37.5,[291,224,149,48],True),
          ("o3","GT Modell 42,5",42.5,[329,252,168,56],True),
          ("u3","Krippe bis 6 Stunden",30,[471,350,236,93],True),
          ("u3","Krippe bis 7,5 Stunden",37.5,[591,455,302,100],True),
          ("u3","Krippe bis 8,5 Stunden",42.5,[670,516,341,113],True)]:
        matrix(city,label,age,hours,values,source=sid,daily=[int(hours*12)]*5 if continuous else None,continuous=continuous,locator="§ 4 Abs. 7, Nr. 1–4, ab September 2025")
    rule(city,"mixed_age_admission",{"age_months_min":24,"age_months_max_exclusive":36,"additional_percent":125,"condition":"new_kindergarten_admission_not_transition_from_municipal_nursery","ends":"end_of_third_birthday_month"},sid,"§ 4 Abs. 6")
    rule(city,"daily_gt_booking",{"allowed_days":[1,2,3,4],"fee_fraction_per_day":"1/5","remaining_days":"corresponding_vo_or_regular_fee"},sid,"§ 4 Abs. 8")
    for days,value in enumerate(["24,50",45,69,91,"113,50"],1):
        component(city,f"Mittagessen {days} Tage",value,source=sid,months=12,meal_days_per_week=days,locator="§ 5 Abs. 3",required=None)
    rule(city,"meal_refund",{"minimum_consecutive_calendar_weeks":2,"daily_fraction":"1/20","ceil_to_euro":True,"monthly_cap":True,"application_and_medical_proof_required":True},sid,"§ 5 Abs. 4–5")
    return city


@adapter("filderstadt")
def filderstadt():
    city=create_city("filderstadt")
    sid="7b3a2062d94d"
    page=read_text(sid).split("\f")[13]
    rows=[]
    for line in page.splitlines():
        match=re.search(r"(?:Grundbuchung\)\s*)?(\d{2})\s+(?=\d[\d.,]*\s*€)",line)
        if match and 30<=int(match[1])<=40:
            values=amounts(line)
            assert len(values)==8
            rows.append((int(match[1]),values,line.strip()))
    assert len(rows)==22
    for section,age in [(rows[:11],"u3"),(rows[11:],"o3")]:
        for hours,values,original in section:
            for column,year in [(0,2026),(4,2027)]:
                matrix(city,f"{hours} gebuchte Wochenstunden",age,hours,values[column:column+4],source=sid,cents=True,start=f"{year}-09-01",end="2027-08-31" if year==2026 else None,
                       locator=f"PDF S. 14, {age}, {hours} Stunden, Spalte {year}/{year+1}")
    for age,rates in [("u3",[[537,399,269,106],["5,37","3,99","2,69","1,06"]]),("o3",[[181,141,96,32],["1,81","1,41","0,96","0,32"]])]:
        rule(city,"weekly_hour_formula_"+age,{"base_weekly_minutes":1800,"base_amounts_cents":[money(v) for v in rates[0]],"additional_hour_amounts_cents":[money(v) for v in rates[1]],"weeks_per_month":4},sid,"PDF S. 14, Formel zur Zubuchung; aktuelle Spalte 2026/2027")
    rule(city,"weekly_hour_formula_2027",{"u3_rates_cents":[559,416,280,110],"o3_rates_cents":[189,146,100,33],"weeks_per_month":4,"valid_from":"2027-09-01"},sid,"PDF S. 14, künftige Stundenpreise")
    for age,rate in [("u3","15,20"),("o3","16,80")]:
        for days in range(1,6):component(city,f"Mittagessen {age} {days} Tage",str(Decimal(rate.replace(',','.'))*days).replace('.',','),age=age,meal_days_per_week=days,source=sid,locator="PDF S. 15, Nr. 5")
    rule(city,"refund_daily_rates",{"u3_cents":[2685,1995,1345,530],"o3_cents":[905,705,480,160],"conditions":"§ 19; nicht bei gewöhnlicher Krankheit oder Urlaub"},sid,"PDF S. 15, Nr. 4; § 19")
    rule(city,"refund_daily_rates_2027",{"u3_cents":[2795,2080,1400,550],"o3_cents":[945,730,500,165],"valid_from":"2027-09-01"},sid,"PDF S. 15, Nr. 4, künftige Spalte")
    for age,value in [("u3","3,80"),("o3","4,20")]:
        component(city,"Mittagessen Einzelpreis "+age,value,age=age,source=sid,unit="per_meal",locator="§ 20, Einzelpreis als Grundlage der veröffentlichten Pauschalen",included_in_monthly_meal_flat_rate=True)
    return city


@adapter("marbach")
def marbach():
    city=create_city("marbach","under_18_or_child_benefit")
    sid="02a52f0ce010"
    tables={"u3":[(6,[[537,399,269,106],[559,416,280,110]]),(6.5,[[582,432,292,115],[605,449,303,119]]),(8,[[715,531,359,142],[743,552,373,147]])],
      "o3":[(6,[[218,168,114,0],[226,174,118,0]]),(6.5,[[236,182,123,0],[245,189,128,0]]),(7,[[254,196,133,0],[264,203,138,0]]),
            (8,[[319,214,142,0],[331,222,147,0]]),(10,[[400,267,178,0],[416,278,185,0]])]}
    for age,groups in tables.items():
        for hours,years in groups:
            for year,values in zip([2026,2027],years,strict=True):
                matrix(city,f"{'VÖ' if hours<8 else 'GT'} {hours} Stunden",age,hours*5,values,source=sid,start=f"{year}-09-01",end="2027-08-31" if year==2026 else None,
                       daily=[int(hours*60)]*5,locator=f"Anlage A, PDF S. 5, {age}, {hours} Stunden, {year}")
    component(city,"Mittagessen U3",65,age="u3",required=True,source=sid,locator="Krippentabelle und Fußnoten")
    component(city,"Mittagessen Ü3",75,age="o3",source=sid,locator="Kindergartentabelle; GT grundsätzlich verpflichtend, VÖ freiwillig")
    component(city,"Getränkegeld Ü3",2,age="o3",required=True,source=sid,kind="drinks",locator="Kindergartentabelle")
    rule(city,"pass_reduction",{"pass":"culture_and_leisure_pass","discount_percent":50,"meals_excluded":True,"application_required":True},"02a52f0ce010","§ 4 Abs. 4")
    rule(city,"older_children_on_application",{"child_benefit_required":True,"application_required":True},"02a52f0ce010","§ 4 Abs. 2")
    rule(city,"mandatory_meals",{"u3_required":True,"u3_exception":"Wiesenzauber","o3_required_when_daily_minutes_exceed":420,"municipal_order_takes_precedence_over_provider_webpage":True},sid,"§ 4 Abs. 7 und § 6")
    city["issues"].append({"code":"supporting_provider_meal_note_conflict","detail":"Die ergänzende Trägerseite bezeichnet Essen bei GT8 als freiwillig; die kommunale Satzung nennt GT verpflichtend. Kommunale Satzung als maßgeblichen Beleg verwenden."})
    return city


@adapter("remseck")
def remseck():
    city=create_city("remseck")
    sid="5ebe63b06876"
    for age,label,hours,values in [("o3","VÖ6",30,[225,173,116,39]),("o3","GT7,5",37.5,[304,234,153,49]),("o3","GT10",50,[406,313,203,64]),
          ("u3","VÖ6 Altersmischung",30,[356,277,184,61]),("u3","VÖ6 Kinderkrippe",30,[468,359,234,74]),("u3","GT7,5",37.5,[609,469,306,97]),("u3","GT10",50,[813,623,406,120])]:
        item=matrix(city,label,age,hours,values,source=sid,daily=[int(hours*12)]*5,locator="Anlage 1 S. 6, Nr. 1")
        for row in city["prices"]:
            if row["offer_id"]==item["id"]:row["selectors"]["family_count_is_minimum"]=False
        price(city,item,0,5,selectors={"family_count_is_minimum":True},locator="Anlage 1 Fußnote: ab fünftem Kind gebührenfrei")
    component(city,"Mittagessen ein bis zwei Jahre",45,age="u3",required=True,months=10,source=sid,locator="Anlage 1 Nr. 2",age_max_months_exclusive=24)
    component(city,"Mittagessen über zwei Jahre",90,required=True,months=10,source=sid,locator="Anlage 1 Nr. 2",age_min_months=24)
    rule(city,"family_pass",{"pass":"remseck_family_pass","meal_discount":False,"rate":"see_current_pass_rules"},sid,"§ 6")
    return city


@adapter("schoenaich")
def schoenaich():
    city=create_city("schoenaich")
    for age,label,hours,values in [("o3","VÖ30",30,[166,129,88,29]),("u3","VÖ30",30,[492,366,247,97]),("o3","GT51,5",51.5,[530,380,234,150]),("u3","GT37,5",37.5,[690,513,349,138])]:
        matrix(city,label,age,hours,values,locator="Anlage § 1 a–d, Spalte ab September 2026")
    component(city,"Mittagessen",85,required=True,locator="Anlage S. 3")
    for family,value in enumerate([140,120,100],1):component(city,f"Ferienbetreuung Familiengröße {family}",value,unit="per_week",kind="holiday_care",required=False,selectors={"family_count":family,"family_count_is_minimum":family==3},valid_from="2026-08-01",locator="Anlage S. 2, wöchentliche Feriengebühr")
    rule(city,"vo_proportional_extension",{"base_weekly_minutes":1800,"proportional_fee":True,"requires_offered_hours":True},locator="Anlage a–b")
    return city


@adapter("steinenbronn")
def steinenbronn():
    city=create_city("steinenbronn")
    matrix(city,"VÖ32,5","o3",32.5,[248,190,128,54],locator="Anlage 1 S. 1")
    rows={35:([267,197,128,62],[411,273,133,68]),37:([276,204,132,63],[433,295,155,78]),39:([285,211,138,64],[454,317,178,89]),41:([294,218,142,65],[476,339,200,99])}
    for hours,(o3,u3) in rows.items():
        matrix(city,f"{hours} Wochenstunden","o3",hours,o3,locator="Anlage 1 S. 1, VÖ/GT-Module")
        matrix(city,f"Krippe {hours} Wochenstunden","u3",hours,u3,locator="Anlage 1 S. 2, Krippengruppen")
        matrix(city,f"Altersmischung 2–3 Jahre {hours} Wochenstunden","u3",hours,u3,minimum=24,category="mixed_age",locator="Anlage 1 S. 1, zweite Spalte")
    matrix(city,"Splitting U3-20 an fünf Tagen","u3",20,[318,229,133,68],daily=[240]*5,locator="Anlage 1 S. 2, Modul U3-20")
    matrix(city,"Splitting U3-21 an drei Tagen","u3",21,[330,248,146,83],locator="Anlage 1 S. 2, Modul U3-21",days_per_week=3)
    component(city,"Verpflegung",None,source="04fd37644a31",locator="Benutzungsordnung: Verpflegung gesondert")
    return city


@adapter("tamm")
def tamm():
    city=create_city("tamm")
    for age,label,hours,values in [("o3","VÖ6",30,[199,150,100,50]),("o3","GT15",40,[315,237,158,79]),("o3","GT17",50,[402,302,201,101]),("u3","KR VÖ6",30,[471,350,236,93]),("u3","KR GT15",40,[628,471,314,157])]:
        matrix(city,label,age,hours,values,daily=[int(hours*12)]*5,locator="Webseite: Elternbeiträge ab 01.09.2025")
    for row in city["prices"]:row["selectors"]["family_count_is_minimum"]=False
    for age,group,value in [("u3","VÖ",73),("o3","VÖ",81),("u3","GT",85),("o3","GT",93)]:
        component(city,f"Verpflegung {age} {group}",value,age=age,months=11,offers=[o for o in city["offers"] if o["age_group"]==age and (("GT" in o["original_label"])==(group=="GT"))],care_type=group,locator="Webseite: Verpflegungskosten")
    component(city,"Getränkepauschale","2,50",required=True,kind="drinks",locator="Webseite: alle Betreuungsformen")
    rule(city,"age_transition",{"effective":"month_after_third_birthday"},locator="Absatz unter der Beitragstabelle")
    return city


@adapter("waldenbuch")
def waldenbuch():
    city=create_city("waldenbuch")
    data=[("VÖ30",30,[[237,183,123],[426,330,222]]),
          ("VÖ mit Frühbetreuung",35,[[291,225,152],[524,405,274]]),
          ("VÖ + GT5",35,[[311,240,162],[559,433,292]]),
          ("VÖ + GT9",39,[[370,286,193],[666,516,348]]),
          ("VÖ + GT5 mit Frühbetreuung",40,[[365,282,190],[657,509,343]]),
          ("VÖ + GT9 mit Frühbetreuung",44,[[424,328,221],[764,591,399]])]
    for label,hours,rows in data:
        for age,values in zip(["o3","u3"],rows,strict=True):
            item=matrix(city,label,age,hours,values,daily=[360]*5 if hours==30 else [420]*5 if label=="VÖ mit Frühbetreuung" else [480]*4+[420] if label=="VÖ + GT9" else [540]*4+[480] if hours==44 else None,locator="§ 3 Angebotsformen; § 4 a–f")
            for row in city["prices"]:
                if row["offer_id"]==item["id"] and row["selectors"]["family_count"]==3:row["selectors"]["family_count_is_minimum"]=True
    rule(city,"partial_month",{"admission_after_day":15,"departure_until_day":15,"fraction":"1/2"},locator="§ 2 Abs. 3")
    rule(city,"age_transition_source_wording",{"source_text":"Bei Wechsel bis einschließlich 15. U3-Gebühr für Restmonat; bei späterem Wechsel Ü3-Gebühr für Restmonat.","execution_requires_review":True},locator="§ 2 Abs. 4")
    component(city,"Mittagessen",None,required=None,source="7fc33f1805ec",locator="In den gesicherten Gebührenunterlagen kein Betrag")
    return city


@adapter("ostfildern")
def ostfildern():
    city=create_city("ostfildern","child_benefit")
    sid="af550fae0296"
    bands=[]
    for index in range(12):
        low=None if index==0 else 20000+10000*index
        high=30000 if index==0 else 30000+10000*index if index<11 else None
        bands.append(band(city,f"Stufe {index+1}: {'unter' if index==0 else 'ab'} {high if index==0 else low} Euro",low,high,basis="ostfildern_assessable_income",reference="previous_calendar_year",upper_inclusive=False))
    pages=read_text(sid).split("\f")
    for page_index in range(9,17):
        age="o3" if page_index<13 else "u3"
        year=2026+(page_index-9)%4
        rows=[(amounts(line),line.strip()) for line in pages[page_index].splitlines() if len(amounts(line))==5]
        assert len(rows)==48,(page_index,len(rows))
        for column,hours in enumerate([30,35,40,45,50]):
            item=offer(city,f"{hours} Wochenstunden",age,hours,source=sid,start=f"{year}-09-01",end=f"{year+1}-08-31",minimum=0 if age=="u3" else 36,
                locator=f"PDF S. {page_index+1}, {age}, {hours} Wochenstunden, Tarifjahr {year}/{year+1}",booking_status="requires_cross_check_with_published_offer_structure")
            for row_index,(values,original) in enumerate(rows):
                price(city,item,values[column],row_index%4+1,band=bands[row_index//4],cents=True,locator=f"PDF S. {page_index+1}, Stufe {row_index//4+1}, Familie {row_index%4+1}, {hours} Stunden")
    component(city,"Mittagessen",None,source=sid,locator="§ 5; Verpflegung zusätzlich")
    rule(city,"income_definition",{"basis":"positive_income_under_estg_plus_listed_benefits","reference_period":"previous_calendar_year","include_child_income":True,
        "loss_offset_allowed":False,"exclude":["child_benefit","care_insurance_benefits"],"additional_benefits":["maternity_pay","parental_allowance","pensions_except_basic_pension","maintenance","bafog","scholarships","unemployment_and_replacement_benefits","housing_benefit","child_supplement","honorary_work","minijob"],
        "higher_work_expenses_on_application":True,"application_required_for_reduced_band":True,"no_proof":"highest_band"},sid,"§ 6 Abs. 2–9, PDF S. 4–5")
    rule(city,"booking_and_closure",{"table_price_does_not_prove_booking_availability":True,"nursery_base_weekly_minutes":2100,"kindergarten_base_weekly_minutes":1800,"gt_base_weekly_minutes":2400,
        "long_term_shortage":"proportion_of_actual_to_booked_hours_with_20_hour_charge_cap"},sid,"§ 6a, PDF S. 6–7")
    return city


@adapter("weissach")
def weissach():
    city=create_city("weissach")
    sid="f5d4fce7afeb"
    page=read_text(sid).split("\f")[11]
    section=page.split("Snack- und Getränkekostenpauschale")[0]
    rows=[amounts(line) for line in section.splitlines() if len(amounts(line))==3]
    assert len(rows)==40
    for group,age in enumerate(["u3","o3"]):
        for index,hours in enumerate([30,35,37.5,40,50]):
            values=rows[group*20+index*4:group*20+index*4+4]
            for column,year in [(1,2026),(2,2027)]:
                item=matrix(city,f"bis {hours} Wochenstunden",age,hours,[row[column] for row in values],source=sid,cents=True,start=f"{year}-09-01",end="2027-08-31" if year==2026 else None,locator=f"PDF S. 12, {age}, bis {hours} Stunden, Spalte {year}")
                for row in city["prices"]:
                    if row["offer_id"]==item["id"]:row["selectors"]["family_count_is_minimum"]=False
    component(city,"Snack und Getränke 30 Stunden",5,required=True,kind="supplies",source=sid,locator="PDF S. 12, aktuelle Spalten 2026/2027",weekly_minutes=1800)
    component(city,"Snack und Getränke ab 35 Stunden",7,required=True,kind="supplies",source=sid,locator="PDF S. 12",weekly_minutes_min=2100)
    component(city,"Verpflegung ab 37,5 Stunden fünf Tage",60,required=True,source=sid,locator="PDF S. 12",weekly_minutes_min=2250,meal_days_per_week=5)
    return city


@adapter("plochingen")
def plochingen():
    city=create_city("plochingen")
    matrix(city,"Regelgruppe und flexible/VÖ-Gruppe","o3",None,[186,150,106,50],continuous=False,locator="PDF S. 1, Regelbetreuung")
    matrix(city,"Regelgruppe ab zwei Jahren","u3",None,[372,300,212,100],minimum=24,category="mixed_age",continuous=False,locator="PDF S. 1, Regelbetreuung U3")
    for age,rows in [("o3",[[340,303,266],[262,234,209],[181,164,143],[56,55,54]]),("u3",[[700,654,604],[544,521,481],[380,356,329],[108,100,93]])]:
        for col,days in enumerate([4,3,2]):
            matrix(city,f"{days} GT-Tage bis 16 Uhr, sonst Regelgruppe",age,42 if days==4 else None,[r[col] for r in rows],daily=[540]*4+[360] if days==4 else None,locator=f"PDF S. 1, {age}, {days} GT-Tage",gt_days_per_week=days)
    rows=[[335,304,276,245],[256,235,213,194],[175,159,148,135],[50,50,50,50]]
    for col,days in enumerate([5,4,3,2]):
        matrix(city,f"St. Johann: {days} GT-Tage 7:30–15:30, sonst Regelgruppe","o3",40 if days==5 else None,[r[col] for r in rows],daily=[480]*5 if days==5 else None,
               locator="PDF S. 2, ausschließlich Kindergarten Sankt Johann",scope="named_provider_offer",gt_days_per_week=days)
    matrix(city,"Kinderkrippe 7:30–15:30 fünf Tage","u3",40,[666,532,359,106],daily=[480]*5,locator="PDF S. 2, Kinderkrippe")
    for label,age,values in [("GT bis 16 Uhr", "o3",["40,80","61,20","81,60",102]),("St. Johann","o3",["37,60","56,40","75,20",94])]:
        for days,value in zip([2,3,4,5],values,strict=True):component(city,f"Mittagessen {label} {days} Tage",value,age=age,months=11,meal_days_per_week=days,locator="Mittagessen unter den jeweiligen Tabellen")
    for label,value in [("Kinderkrippe bis 16 Uhr fünf Tage",98),("Kinderkrippe bis 15:30 fünf Tage",94)]:component(city,"Mittagessen "+label,value,age="u3",months=11,meal_days_per_week=5)
    rule(city,"meal_refund",{"refund_from_absence_day":6,"planned_absence_notice_days":14,"august_charge":False},locator="PDF S. 1, wichtige Hinweise")
    return city


@adapter("rutesheim")
def rutesheim():
    city=create_city("rutesheim")
    sid="3ffe1980c0fd"
    for year,regular,nursery,gt in [(2026,[166,129,88,29],[380,490,620],[365,490]),(2027,[173,134,92,30],[395,500,640],[375,500])]:
        source=sid if year==2026 else "2189c4f26a64"
        end="2027-08-31" if year==2026 else None
        matrix(city,"Kindergarten bis 13:30 Uhr","o3",None,regular,source=source,start=f"{year}-09-01",end=end,locator=f"Gebühren Kindergarten {year}/{year+1}")
        for index,time in enumerate(["13:30","15:00","17:00"]):
            for days in [5,3,2]:
                item=offer(city,f"Kinderkrippe bis {time}, {days} Tage","u3",None,source=source,start=f"{year}-09-01",end=end,locator="Kinderkrippe Vollzeit / Sharingplätze; Anteilsberechnung bei Sharing",days_per_week=days)
                row=price(city,item,money(nursery[index])*days//5,1,cents=True,selectors={"family_count_is_minimum":True})
                row["derivation"]={"full_time_cents":money(nursery[index]),"days_numerator":days,"days_denominator":5}
        for index,time in enumerate(["15:00","17:00"]):
            for days in [5,4,3,2]:
                item=offer(city,f"GT bis {time}, {days} Tage + übrige Tage Kindergarten","o3",None,source=source,start=f"{year}-09-01",end=end,locator="Ganztagesbetreuung; übrige Regelgruppentage zusätzlich anteilig",gt_days_per_week=days)
                for rank in [1,2]:
                    row=price(city,item,(money(gt[index])-(5000 if rank==2 else 0))*days//5,1,rank=rank,cents=True,selectors={"family_count_is_minimum":True,"care_rank_is_minimum":rank==2,"rank_basis":"simultaneous_krippe_gt_hort"})
                    row["price_role"]="full_month_total" if days==5 else "gt_portion_requires_regular_fee_for_remaining_days"
        for time,value in [("13:30",210 if year==2026 else 215),("15:00",gt[0])]:
            for days in [1,5]:
                item=offer(city,f"U3 Kindergarten Richard-Wagner bis {time}, {days} Tage","u3",None,minimum=24,category="mixed_age",source=source,start=f"{year}-09-01",end=end,locator="U3 im Kindergarten Richard-Wagner; § 3 Abs. 4",days_per_week=days)
                price(city,item,money(value)*days//5,1,cents=True,selectors={"family_count_is_minimum":True})
    for age,values in [("o3",{2:32,3:48,4:64,5:80}),("u3",{2:24,3:36,5:60})]:
        for days,value in values.items():component(city,f"Mittagessen {age} {days} Tage",value,age=age,meal_days_per_week=days,source=sid,locator="PDF S. 2, Mittagessen")
    rule(city,"simultaneous_sibling_discount",{"amount_cents":5000,"applies_to":"additional_children_in_krippe_gt_hort","rank_assignment":"not_defined_in_overview"},sid,"PDF S. 1–2, Geschwisterhinweis")
    rule(city,"family_pass_contribution",{"own_share_percent_of_income":10,"income_definition":"requires_separate_review","application_required":True},sid,"Ermäßigungsspalte; keine allgemeine Netto-/Bruttoumrechnung")
    return city


@adapter("renningen")
def renningen():
    city=create_city("renningen")
    s=transcription("Renningen")
    for table in s["tables"]:
        year=table["valid_from"][:4]
        if table["age_group"]=="u3":
            for row in table["rows"]:
                hours=30 if "30" in row["original_label"] else 40
                matrix(city,row["original_label"],"u3",hours,row["amounts_cents"],source=s["source_id"],cents=True,start=table["valid_from"],end="2027-08-31" if year=="2026" else None,locator=f"PDF S. 9, Krippe ab {table['valid_from']}")
        else:
            matrix(city,"VÖ monatlicher Festbetrag","o3",None,table["rows"][0]["amounts_cents"],source=s["source_id"],cents=True,start=table["valid_from"],end="2027-08-31" if year=="2026" else None,locator=f"PDF S. 10, VÖ ab {table['valid_from']}")
            rule(city,"hourly_fee_parameters_"+year,{"valid_from":table["valid_from"],"base_amounts_cents_per_hour":table["rows"][1]["amounts_cents"],"additional_hour_from_31_cents":table["additional_hour_from_31_cents"],"monthly_conversion_factor":None,"conversion_status":"requires_calculation_review_not_inferred"},s["source_id"],"PDF S. 10, Gebühr je Stunde der wöchentlichen Betreuungszeit; kein Monatsbeitrag")
            for hours in [40,46]:
                item=offer(city,f"GT{hours} nach Stundenformel","o3",hours,source=s["source_id"],start=table["valid_from"],end="2027-08-31" if year=="2026" else None,locator="§ 3 Angebotszeiten; S. 10 Stundenparameter")
                item["formula"]={"type":"documented_hourly_parameters","base_amounts_cents_per_hour":table["rows"][1]["amounts_cents"],"additional_hour_from_31_cents":table["additional_hour_from_31_cents"],"execution_status":"requires_calculation_review"}
    component(city,"Mittagessen kostendeckend zusätzlich",None,required=None,source=s["source_id"],locator="Fußnote unter den Tabellen")
    rule(city,"playgroups_outside_comparison",{"monthly_amounts_cents_by_date":s["playgroup_monthly_cents"],"not_regular_nursery":True},s["source_id"],"§ 7 und gesonderte Spielgruppentarife")
    return city


@adapter("waiblingen")
def waiblingen():
    city=create_city("waiblingen","under_18")
    sid="59ecf75191ad"
    tables={"o3":[("Bis 30 Stunden ohne Mittagessen",30,"0,25",100,300,False),("Bis 30 Stunden mit Mittagessen",30,"0,30",120,360,True),
      ("31–35 Stunden mit Mittagessen",35,"0,40",160,480,True),("36–40 Stunden mit Mittagessen",40,"0,42",168,504,True),("41–50 Stunden mit Mittagessen",50,"0,50",200,600,True),
      ("Kombination 1: zwei Tage VÖ ohne Essen, drei GT",42,"0,40",160,480,True),("Kombination 2: zwei Tage VÖ mit Essen, drei GT",42,"0,42",168,504,True)],
      "u3":[("Bis 20 Stunden ohne Mittagessen",20,"0,25",100,300,False),("Bis 30 Stunden ohne Mittagessen",30,"0,30",120,360,False),("Bis 30 Stunden mit Mittagessen",30,"0,40",160,480,True),
      ("31–35 Stunden mit Mittagessen",35,"0,50",200,600,True),("36–40 Stunden mit Mittagessen",40,"0,52",208,624,True),("41–50 Stunden mit Mittagessen",50,"0,60",240,720,True),
      ("Kombination 3: zwei Tage VÖ ohne Essen, drei GT",42,"0,48",192,576,True),("Kombination 4: zwei Tage VÖ mit Essen, drei GT",42,"0,52",208,624,True)]}
    for age,rows in tables.items():
        for label,hours,percent,minimum,maximum,included in rows:
            item=offer(city,label,age,hours,source=sid,locator="Gebührentabelle ab April 2026, "+label,minimum=0 if age=="u3" else 36,
                       weekly_minutes_is_upper_bound=True,schedule_status="published_tariff_limits_not_verified_booking")
            if label.startswith("31–35"):item["weekly_minutes_lower_exclusive"]=1800
            elif label.startswith("36–40"):item["weekly_minutes_lower_exclusive"]=2100
            elif label.startswith("41–50"):item["weekly_minutes_lower_exclusive"]=2400
            elif age=="u3" and label=="Bis 30 Stunden ohne Mittagessen":item["weekly_minutes_lower_exclusive"]=1200
            if label.startswith("Kombination"):
                item["time_derivation"]={"short_days":2,"short_day_maximum_minutes":360,"long_days":3,"long_day_maximum_minutes":600,"result_is_upper_bound":True}
            item["formula"]={"type":"percentage_of_annual_income","income_basis":"waiblingen_household_gross_including_child_benefit","percent":percent.replace(',','.'),
                "income_floor_cents":4000000,"income_cap_cents":12000000,"minimum_monthly_cents":money(minimum),"maximum_monthly_cents":money(maximum),"published_min_max_before_child_discount":True,"no_income_proof":"maximum_monthly_fee"}
            if included:
                food=component(city,"Im Tarif enthalten: "+age+" "+label,None,age=age,required=True,source="dae7d9e3a67b",locator="§ 6 Nr. 9; Nutzerfestlegung 2026-11-10-waiblingen-included-meals",offers=[item],inclusion="included",additional_charge=False,value_status="included",decision_id="2026-11-10-waiblingen-included-meals")
                item["included_components"]=[{"component_id":food["id"],"kind":"meal","amount_cents":None,"additional_charge":False}]
    rule(city,"child_discount_by_birth_rank",{"discount_percent":[0,50,75,"87.5",100],"free_from_rank":5,"rank_basis":"birth_order_of_family_children_under_18","not_simultaneous_care_rank":True},"dae7d9e3a67b","§ 5")
    rule(city,"income_definition",{"include_child_benefit":True,"include_other_household_income":True,"period":"year","formula_assessment":"source_defined_household_gross"},"dae7d9e3a67b","§ 4")
    return city


@adapter("kernen")
def kernen():
    city=create_city("kernen","child_benefit")
    sid="fd9c3aef8652"
    pages=read_text(sid).split("\f")
    regular=[list(map(int,m.groups())) for m in re.finditer(r"(\d+)[ \t]+(\d+)[ \t]+(\d+)[ \t]*$",pages[3],re.M)]
    nursery=[list(map(int,m.groups())) for m in re.finditer(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s*$",pages[5],re.M)]
    assert len(regular)==4 and len(nursery)==12
    for col,year in enumerate([2026,2027,2028]):
        start=f"{year}-01-01";end=f"{year}-12-31" if year<2028 else None
        base=[r[col] for r in regular]
        matrix(city,"Regelgruppe geteilt 30 Stunden","o3",30,base,source=sid,start=start,end=end,continuous=False,locator=f"PDF S. 4, Regelgruppen {year}")
        for hours,extra in [(30,12),(35,45)]:
            matrix(city,f"VÖ{hours//5}","o3",hours,[v+extra for v in base],source=sid,start=start,end=end,daily=[hours*12]*5,locator=f"PDF S. 4–5, Grundbetrag {year} plus VÖ-Zuschlag")
        for index,hours in enumerate([4,5,6]):
            matrix(city,f"Krippe bis {hours} Stunden","u3",hours*5,[nursery[family*3+index][col] for family in range(4)],source=sid,start=start,end=end,daily=[hours*60]*5,locator=f"PDF S. 6, Kinderkrippe {year}, {hours} Stunden")
        for max_hours,percent in [(15,65),(17,75),(20,85),(30,100)]:
            rule(city,f"special_groups_{year}_{max_hours}",{"valid_from":start,"weekly_hours_max":max_hours,"percent_of_regular_base":percent,"regular_base_amounts_cents":[money(v) for v in base],"rounding":"ceil_to_euro","last_class_lower_exclusive_hours":20 if max_hours==30 else None},sid,"§ 7 Abs. 1 c und Abs. 3")
    bands=[]
    for i in range(19):
        high=1500+250*i;low=None if i==0 else high-250
        bands.append(band(city,f"Stufe {i+1} bis {high} Euro",low,high,basis="kernen_household_gross",period="month",lower_inclusive=False if i else True))
    bands.append(band(city,"Unermäßigter Vollsatz",6000,None,basis="kernen_household_gross",period="month",lower_inclusive=False))
    pattern=r"^\s*(\d+)\s+bis\s+([\d.]+)\s*€\s+((?:\d+\s*){6})$"
    current=[list(map(int,m[3].split())) for m in re.finditer(pattern,pages[6],re.M)]
    future_o3=[list(map(int,m[3].split())) for m in re.finditer(pattern,pages[7],re.M)]
    future_u3=[list(map(int,m[3].split())) for m in re.finditer(pattern,pages[8],re.M)]
    assert len(current)==len(future_o3)==len(future_u3)==19
    full={2026:{"o3":[315,295,275],"u3":[567,531,495]},2027:{"o3":[329,308,287],"u3":[593,555,517]},2028:{"o3":[342,320,298],"u3":[617,577,538]}}
    for year in [2026,2027,2028]:
        for age in ["o3","u3"]:
            values=[r[(0 if age=="o3" else 3):(3 if age=="o3" else 6)] for r in current] if year==2026 else [r[(0 if year==2027 else 3):(3 if year==2027 else 6)] for r in (future_o3 if age=="o3" else future_u3)]
            values.append(full[year][age])
            for col,(low,high) in enumerate([(46,48),(43,46),(40,43)]):
                item=offer(city,f"GT Angebotsklasse {col+1}: über {low} bis {high} Stunden",age,high,source=sid,start=f"{year}-01-01",end=f"{year}-12-31" if year<2028 else None,
                    locator=f"PDF S. {7 if year==2026 else 8 if age=='o3' else 9}, GT {year}, Klasse {col+1}",weekly_minutes_lower_exclusive=low*60,weekly_minutes_upper_inclusive=high*60,weekly_minutes_is_upper_bound=True)
                for income,row in zip(bands,values,strict=True):price(city,item,row[col],1,band=income,selectors={"family_count_is_minimum":True})
    for age,value in [("o3",5),("u3",10)]:component(city,"Zusatzbuchung bis zwei Stunden "+age,value,age=age,kind="extra_care",unit="per_booked_day",source=sid,locator="§ 6a und § 7 Abs. 1 h")
    for days,value in [(3,54),(5,90)]:component(city,f"Mittagessen {days} Tage",value,meal_days_per_week=days,source=sid,locator="§ 7 Abs. 1 i")
    rule(city,"family_discounts",{"second_child_benefit_child_discount_percent":20,"single_parent_discount_percent":10,"order":["income_band","sibling_discount","single_parent_discount"],"meals_and_extra_bookings_excluded":True},sid,"§ 7 Abs. 8 a, PDF S. 12")
    rule(city,"u3_mixed_age_surcharge",{"percent":100,"applies_to":"admission_before_age_three_to_kindergarten","includes_vo_supplement":True,"rounding":"ceil_to_euro"},sid,"§ 7 Abs. 1 d und Abs. 3")
    rule(city,"income_assessment",{"reference":"source_defined_income_and_benefits","application_required":True,"incomplete_proof":"full_fee","no_automatic_gross_conversion":True},sid,"§ 7 Abs. 4–5, PDF S. 10–12")
    return city


def render_report(manifest):
    totals=manifest["totals"]
    lines=["# Aufbereitung der 33 Erweiterungskataloge", "",
        f"**Stand:** {manifest['normalized_at']}. **Schritt 1 abgeschlossen:** Übertragung der aktuellen und bereits veröffentlichten künftigen Krippen-/Kindergartentarife in ein einheitliches Datenformat.", "",
        f"Erfasst sind **{totals['municipalities']} Kommunen**, **{totals['offers']} Angebote**, **{totals['prices']} Preiszellen**, **{totals['income_bands']} Einkommensstufen** und **{totals['components']} Zusatzkostenbausteine**. Formeltarife werden zusätzlich mit ihren Parametern gespeichert; eine fehlende Anzahl diskreter Preiszellen ist dort keine fehlende Tarifquelle.", "",
        "## Ablage und Status", "",
        "- Je Kommune eine JSON unter [`data/expansion/municipalities/`](../data/expansion/municipalities/), nach dem bestehenden [`municipality.schema.json`](../data/municipality.schema.json).",
        "- [`data/expansion/manifest.json`](../data/expansion/manifest.json): vollständige Zuordnung, AGS, Dateipfade, Prüfsummen, Mengen und Umsetzungsgrenzen.",
        "- [`Erweiterungsrecherche`](ERWEITERUNGSRECHERCHE.md): Quellenbewertungen, vereinbarte Annahmen und offene fachliche Fälle.",
        "- `data/municipalities/` bleibt der produktive Bestand der zwölf bisherigen Kommunen. Der Importbereich wird weder von der laufenden Website noch vom normalen Export geladen.", "",
        "Die Importdateien sind strukturiert und technisch geprüft. **Sie sind noch nicht pauschal für die Berechnung oder Veröffentlichung freigegeben.** Welche Modellkonfigurationen die bestehende Engine abbildet, ist inzwischen in der [Kompatibilitätsprüfung aus Schritt 2](ERWEITERUNGSBERECHNUNG.md) und ihrem eigenen Prüfindex dokumentiert. Manifest und Importstatus beschreiben den reproduzierbaren Normalisierungsstand; die zusätzliche Freigabe ist konfigurationsabhängig. Die gemeinsame Python-/TypeScript-Berechnungsengine und das produktive Register wurden nicht verändert. Für Schwieberdingen erfolgen keine Engineänderungen; Änderungen an der gemeinsamen Logik für einzelne Kommunen werden vorher mit dem Nutzer besprochen.", "",
        "## Inhalt je Katalog", "",
        "- `offers`: Originalmodell, Altersgruppe und gegebenenfalls Altersmischung, Anbieter-/Zeitvariante, Gültigkeit, Originalpreisstand, Beitragsmonate und belegte Tages-/Wochenzeiten. Unbelegte Tagesverteilungen bleiben `null`; Tarifobergrenzen sind als Obergrenzen gekennzeichnet.",
        "- `prices`: veröffentlichte Monatsbeträge mit Familien-, Einkommens-, Pass- oder Rangzuordnung und Quellenfundstelle. Aus belegten Tarifbausteinen zusammengesetzte Beträge haben einen Rechenweg. Teilbeträge, etwa tageweise Rutesheimer GT-Gebühren ohne übrige Regelgruppentage, werden ausdrücklich als Teilbetrag gekennzeichnet.",
        "- `income_bands`: Einkommensbegriff, Monats-/Jahresbezug, zeitlicher Bezug und wörtliche Grenzen. Keine erfundene Brutto-Netto-Umrechnung und kein Auffüllen unbekannter Grenzfälle.",
        "- `components`: Verpflegung und weitere Kosten mit eigener Einheit, Pflichtstatus, Zuordnung und Beitragsmonaten. Unbekannt ist `null`, belegte Gebührenfreiheit `0`; enthaltenes Essen wird nicht als kostenlos ausgegeben oder nochmals addiert.",
        "- `rules`: typisierte Parameter für Formeln, Ermäßigungen, Rundung, Alterswechsel und Nutzerentscheidungen sowie Verweise auf erhaltene Gebührenklauseln. `documented_not_implemented` beschreibt den Importstatus und behauptet keine Unterstützung durch die bestehende Engine.",
        "- `original_research`: erhaltene Originalklauseln mit Fundstellen und Forschungsnotizen. Die vorhandene Browserprojektion entfernt dieses Feld; die dokumentarischen Texte müssen nicht in den Browser übertragen werden.",
        "- `issues` / `coverage`: Quellenprobleme, nicht berechenbare Konfigurationen, Erfassungsumfang und noch ausstehende Rechenfreigabe.", "",
        "Alle Geldbeträge sind ganzzahlige Centwerte, Zeiten Minuten. Beitragsmonate bleiben je Angebot/Kostenbaustein gespeichert. Bei Freiberg sind es U3 zwölf und Ü3 elf. Amtlicher Nachweis, Ableitung und ausdrückliche Nutzerangabe bleiben unterscheidbar.", "",
        "## Erfassungsgrenzen", "",
        "Aktuelle Krippen- und Kindergartentarife sowie in denselben Quellen bereits veröffentlichte künftige Fassungen sind übertragen. Überholte historische Tabellen, Schulkindbetreuung, TAKKI/Kindertagespflege und separate Spielgruppen gehören nicht zu den regulären Vergleichspreiszeilen. Ihre Originalunterlagen bleiben erhalten; ergänzende Klauseln sind dokumentiert. Es wird keine historische Preisreihe angelegt.", "",
        "Eine Tabelle kann einen Tarif nennen, ohne die Buchbarkeit einer konkreten Tagesverteilung zu belegen. Dies bleibt beispielsweise bei einzelnen Ostfilderner Stundenklassen und bei der widersprüchlichen Benninger VÖ-Zeit offen. Der Schuljahresbeginn für die nur als 2026/2027 bezeichneten Tabellen in Altbach und Benningen ist ausdrücklich als Ableitung gekennzeichnet.", "",
        "## Besonderheiten für Rechenprüfung und Integration", "",
        "- **Denkendorf:** Jahresbrutto direkt verwenden; die genehmigte Ausnahme betrifft ausschließlich einen kürzeren Freitag bei ausreichender Betreuung Montag bis Donnerstag. Tatsächliche Zeiten und verpflichtendes GT-Essen mit unbekanntem Betrag bleiben sichtbar zu machen.",
        "- **Schwieberdingen:** elf Monate gemäß Nutzerbestätigung; die vereinbarte kumulative U3-Stufenregel ist als Modellannahme dokumentiert. Preiswirksame ungeklärte Ü3-Ränge und fehlende dritte Rangzellen bleiben `unavailable` / „Nicht berechenbar“.",
        "- **Aichwald:** Originalpreise einschließlich Verpflegung bleiben erhalten; die getrennten Betreuungsanteile stehen ergänzend daneben. Für U3 gelten die vereinbarten 53 Euro, für Ü3 die belegte Differenz zwischen den Tabellen mit und ohne Essen. Kein pauschaler 53-Euro-Abzug bei Ü3.",
        "- **Waiblingen:** Prozentformeln mit Mindest-/Höchstbeitrag und Geburtsrang bleiben unverändert; enthaltenes Mittagessen bleibt Bestandteil des Kartenwerts und wird ohne weiteren Zuschlag als enthalten gekennzeichnet.",
        "- **Renningen:** stündlicher Sockelbetrag und Zuschlag ab der 31. Stunde sind als Parameter erhalten. Die monatliche Umsetzung der Ü3-Stundenformel benötigt noch die folgende Rechenprüfung; der Stundenwert wird nicht als fertiger Monatsbeitrag gespeichert.",
        "- **Asperg:** künftige Fassungen ab Januar und September 2027 getrennt. Die auffällige veröffentlichte Zelle für U3 GT9,5 an drei Tagen, vier Kinder, September 2027 bleibt unverändert; keine vermutete Korrektur.",
        "- **Marbach:** kommunale Satzung als maßgeblicher Preis- und Pflichtessensbeleg; abweichender Essenshinweis der ergänzenden Trägerseite als Konflikt dokumentiert.", "",
        "## Übersicht", "",
        "| Kommune | Angebote | Preiszellen | Einkommensstufen | Zusatzkosten | Status |",
        "|---|---:|---:|---:|---:|---|"]
    for city in manifest["municipalities"]:
        lines.append(f"| [{city['name']}](../{city['path']}) | {city['offers']} | {city['price_cells']} | {city['income_bands']} | {city['components']} | Kompatibilität separat bewertet |")
    lines += ["", "## Reproduzierbare Prüfung", "", "```bash",
        "python3 scripts/normalize_expansion_tariffs.py --check",
        "python3 scripts/validate_expansion_catalogs.py",
        "python3 -m unittest discover -s tests -v", "```", "",
        "Ohne `--check` erzeugt der Normalisierer die 33 Importdateien, das Manifest und diesen Bericht neu. Alle Kataloge werden vor dem Schreiben gemeinsam geprüft. Die Validierung verwendet ein ausschließlich im Speicher ergänztes inaktives Register für die geografische Zuordnung; die produktive Registerdatei bleibt unverändert.", "",
        "Die Prüfungen sichern Format, IDs, Selektoren, Geld-/Zeitwerte, Quellenfundstellen, archivierte Prüfsummen und reproduzierbare Ausgabe. Die Importtests gleichen außerdem alle 1.920 Ostfilderner U3-/Ü3-Preiszellen gegen den archivierten PDF-Text und die bisherigen Kontrollzellen aller 33 Kommunen gegen die Kataloge ab. Dies ersetzt weder die vollständige fachliche Rechenprüfung noch die Website-Abnahme.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check reproducibility without writing")
    args = parser.parse_args()
    if set(ADAPTERS) != set(RECORDS):
        raise ValueError(f"Missing adapters: {sorted(set(RECORDS) - set(ADAPTERS))}")
    from validate_expansion_catalogs import validate_imports
    catalogs = [finish(function()) for function in ADAPTERS.values()]
    errors = validate_imports(catalogs)
    if errors:
        raise ValueError("Invalid normalized imports:\n" + "\n".join(errors))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    totals = {"municipalities": len(ADAPTERS), "offers": 0, "prices": 0, "income_bands": 0, "components": 0}
    outputs=[]
    for city in sorted(catalogs, key=lambda value:value["id"]):
        name=city["id"]
        content = json.dumps(city, ensure_ascii=False, indent=2) + "\n"
        path = OUTPUT / (name + ".json")
        if args.check:
            if path.read_text() != content:
                raise ValueError(f"Outdated normalized catalog: {name}")
        else:
            write_if_changed(path, content)
        for field in ["offers", "prices", "income_bands", "components"]:
            totals[field] += len(city[field])
        outputs.append({"id":name,"name":city["name"],"ags":RECORDS[name]["ags"],
            "path":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(content.encode()).hexdigest(),
            "offers":len(city["offers"]),"price_cells":len(city["prices"]),"income_bands":len(city["income_bands"]),
            "components":len(city["components"]),"rules":len(city["rules"]),"publication_status":"not_active"})
    manifest={"schema_version":"1.0","normalized_at":REGISTER["review_date"],
        "status":"normalized_pending_calculation_review","municipality_schema_path":"data/municipality.schema.json",
        "research_path":str(RESEARCH.relative_to(ROOT)),"research_sha256":hashlib.sha256(RESEARCH.read_bytes()).hexdigest(),
        "visual_transcriptions_sha256":hashlib.sha256((ROOT / REGISTER["transcriptions_path"]).read_bytes()).hexdigest(),
        "totals":totals,"municipalities":outputs,"production_registry_changed":False,
        "calculation_engine_changed":False,"website_activated":False,
        "implementation_constraints":deepcopy(REGISTER["implementation_constraints"])}
    manifest_content=json.dumps(manifest,ensure_ascii=False,indent=2)+"\n"
    manifest_path=OUTPUT.parent/"manifest.json"
    if args.check:
        if manifest_path.read_text()!=manifest_content:raise ValueError("Outdated expansion manifest")
    else:write_if_changed(manifest_path, manifest_content)
    report_path=ROOT / "docs/ERWEITERUNGSDATEN.md"
    report_content=render_report(manifest)
    if args.check:
        if report_path.read_text()!=report_content:raise ValueError("Outdated expansion catalog report")
    else:write_if_changed(report_path, report_content)
    print(json.dumps(totals))


if __name__ == "__main__":
    main()
