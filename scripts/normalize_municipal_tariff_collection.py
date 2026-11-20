"""Normalize the second tariff collection without registering it for the map."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

from normalize_expansion_tariffs import ROOT, amounts, band, component, evidence, offer, price, read_text, rule
from validate_expansion_catalogs import load_cities, load_registry, shape_errors, validate_dataset

REGISTER_PATH = "data/research/municipal_tariff_collection_2026-11-20.json"
OUTPUT = ROOT / "data/expansion/batches/2026-11-20"

# Visual transcription of Markgröningen's scanned annex, pp. 8–13.
# The rows run from the highest to the lowest income band.
MARKGROENINGEN = [
    (2026, 1, 8, [[19575,15025,10475,5925],[17317,13292,9267,5242],[15058,11558,8058,4558],[12799,9824,6849,3874],[10541,8091,5641,3191]]),
    (2026, 2, 8, [[21207,16657,12107,7557],[18760,14735,10710,6685],[16313,12813,9313,5813],[13866,10891,7916,4941],[11419,8969,6519,4069]]),
    (2026, 3, 9, [[26100,21550,17000,12450],[23089,19064,15039,11014],[20077,16577,13077,9577],[17065,14090,11115,8140],[14054,11604,9154,6704]]),
    (2026, 4, 9, [[27732,23182,18632,14082],[24532,20507,16482,12457],[21332,17832,14332,10832],[18132,15157,12182,9207],[14932,12482,10032,7582]]),
    (2025, 5, 10, [[65000,52000,39000,26000],[57500,46000,34500,23000],[50000,40000,30000,20000],[42500,34000,25500,17000],[35000,28000,21000,14000]]),
    (2025, 6, 10, [[70200,57200,44200,31200],[62100,50600,39100,27600],[54000,44000,34000,24000],[45900,37400,28900,20400],[37800,30800,23800,16800]]),
    (2025, 7, 11, [[86450,73450,60450,47450],[76475,64975,53475,41975],[66500,56500,46500,36500],[56525,48025,39525,31025],[46550,39550,32550,25550]]),
    (2025, 8, 11, [[92300,79300,66300,53300],[81650,70150,58650,47150],[71000,61000,51000,41000],[60350,51850,43350,34850],[49700,42700,35700,28700]]),
    (2027, 1, 12, [[20358,15808,11258,6708],[18009,13984,9959,5934],[15660,12160,8660,5160],[13311,10336,7361,4386],[10962,8512,6062,3612]]),
    (2027, 2, 12, [[22056,17506,12956,8406],[19511,15486,11461,7436],[16966,13466,9966,6466],[14421,11446,8471,5496],[11876,9426,6976,4526]]),
    (2027, 3, 13, [[27144,22594,18044,13494],[24012,19987,15962,11937],[20880,17380,13880,10380],[17748,14773,11798,8823],[14616,12166,9716,7266]]),
    (2027, 4, 13, [[28841,24291,19741,15191],[25513,21488,17463,13438],[22185,18685,15185,11685],[18857,15882,12907,9932],[15530,13080,10630,8180]]),
]


def catalog(record, reference_date, source, start, months, locator, family_basis="under_18"):
    return {
        "schema_version": "1.0", "id": record["id"], "name": record["name"],
        "reviewed_at": reference_date, "reference_date": reference_date,
        "scope": {"included": ["municipal"], "other_providers": "only_with_explicit_source_evidence"},
        "family_basis": family_basis, "family_evidence": evidence(source, locator),
        "supporting_source_ids": [item["source_id"] for item in record["sources"]],
        "offers": [], "prices": [], "income_bands": [], "components": [], "rules": [],
        "issues": [], "coverage": {"publication_status": "not_active", "history_in_scope": False,
                                   "source_register": REGISTER_PATH},
        "_source": source, "_from": start,
        "_payment": {"count": months, "verification": "explicit", "source_id": source, "locator": locator},
    }


def markgroeningen(record, reference_date):
    source = "c5ba47bb39c1"
    city = catalog(record, reference_date, source, "2026-09-01", 12, "§ 7 Abs. 6–8",
                   family_basis="under_18_or_child_benefit")
    ranges = [(125000, None), (90000, 125000), (65000, 90000), (50000, 65000), (None, 50000)]
    names = ["Erhöhter Beitrag II", "Erhöhter Beitrag I", "Regelbeitrag", "Ermäßigungsstufe I", "Ermäßigungsstufe II"]
    bands = [band(city, name, low, high, basis="gross_income", upper_inclusive=False)
             for name, (low, high) in zip(names, ranges, strict=True)]
    for year, number, page, rows in MARKGROENINGEN:
        age = "o3" if number < 5 else "u3"
        daily_minutes = [360, 390, 480, 510][(number - 1) % 4]
        hours = daily_minutes * 5 / 60
        kind = "VÖ" if daily_minutes < 480 else "GT"
        item = offer(city, f"Modul {number} · {kind} {hours:g} Stunden/Woche", age, hours,
                     start=f"{year}-09-01", end="2027-08-31" if year == 2026 else None,
                     daily=[daily_minutes] * 5, locator=f"Satzungsanlage S. {page}, Modul {number}",
                     applies_to_mixed_age_groups=age == "o3" and kind == "VÖ")
        for income_band, amounts_in_cents in zip(bands, rows, strict=True):
            for family_count, amount in enumerate(amounts_in_cents, 1):
                price(city, item, amount, family_count, band=income_band, cents=True)
    gt = [item for item in city["offers"] if item["weekly_minutes"] >= 2400]
    vo = [item for item in city["offers"] if item["weekly_minutes"] == 1950]
    component(city, "Mittagessen im Ganztag", 88, required=True, offers=gt,
              locator="Satzungsanlage S. 11 und 13; Angebotsübersicht Ganztagsgruppen inklusive Essen")
    component(city, "Mittagessen bei VÖ im Nonnenpfad", 88, required=False, offers=vo,
              locator="Satzungsanlage S. 11 und 13; freiwilliges Essen in der Einrichtung Im Nonnenpfad")
    rule(city, "income_definition",
         {"income_basis": "gross_income", "include_other_income_and_benefits": True,
          "excluded_income": ["child_benefit", "long_term_care_benefits", "children_earned_income"],
          "no_income_proof": "Erhöhter Beitrag II", "model_assumption": "only_selected_annual_gross_income"},
         locator="§ 7 Abs. 6–7, 14–15")
    rule(city, "holiday_care", {"age_group": "o3", "half_month_fee_up_to_weeks": 2,
                              "full_month_fee_for_longer_booking": True}, locator="§ 7 Abs. 9")
    rule(city, "age_transition", {"effective": "month_after_third_birthday"}, locator="§ 7 Abs. 11")
    city["issues"].append({"code": "meal_payment_months_not_explicit",
                           "detail": "Essenspauschale bei Teilnahme. Die Satzung nennt keine feste Anzahl von Essensmonaten."})
    return city


def bietigheim_bissingen(record, reference_date):
    source = "edebe0ffd22e"
    city = catalog(record, reference_date, source, "2026-09-01", 12, "§ 3 Abs. 2 und 4")
    city["model_tariff"] = "birth_order"
    schedules = "cfd856901fab"
    for page, text in enumerate(read_text(source).split("\f"), 1):
        date_match = re.search(r"gültig vom 01\.09\.(20\d\d) bis 31\.08\.(20\d\d)", text)
        if not date_match or int(date_match[1]) < 2026:
            continue
        start, end = f"{date_match[1]}-09-01", f"{date_match[2]}-08-31"
        table_rows = [values for line in text.splitlines() if len(values := amounts(line)) == 5]
        assert len(table_rows) == 12, (page, table_rows)
        for age, rows in [("o3", table_rows[:6]), ("u3", table_rows[6:])]:
            for index, hours in enumerate(range(6, 11)):
                label = f"{'VÖ' if hours < 8 else 'GT'} {hours}"
                item = offer(city, label, age, 5 * hours, start=start, end=end,
                             daily=[hours * 60] * 5 if hours <= 8 else None,
                             locator=f"Satzungsanlage 1 S. {page}, {label}, {age.upper()}",
                             nominal_daily_minutes=hours * 60,
                             schedule_evidence=evidence(schedules if hours <= 8 else "d8578489979d",
                                 "Kinderhaus Buch: buchbare VÖ 6, VÖ 7 und GT 8; Benutzungsordnung § 4 Abs. 3"
                                 if hours <= 8 else "GT 9 ohne Angebotsnachweis; GT 10 laut Anmeldeportal derzeit nicht angeboten"))
                amounts_at_hours = [row[index] for row in rows]
                for family_count, base_index in [(1, 0), (2, 1), (3, 2), (4, 4)]:
                    amounts_by_rank = [amounts_at_hours[base_index]]
                    if family_count >= 3 and amounts_at_hours[base_index + 1] != amounts_by_rank[0]:
                        amounts_by_rank = [amounts_by_rank[0]] * 2 + [amounts_at_hours[base_index + 1]]
                    for index_by_rank, amount in enumerate(amounts_by_rank, 1):
                        rank = index_by_rank if len(amounts_by_rank) > 1 else None
                        price(city, item, amount, family_count, cents=True, rank=rank,
                              selectors={"rank_basis": "birth_order", "care_rank_is_minimum": rank == 3}
                              if rank else None)
        offers = [item for item in city["offers"] if item["valid_from"] == start]
        gt = [item for item in offers if item["weekly_minutes"] >= 2400]
        vo = [item for item in offers if item["weekly_minutes"] < 2400]
        meal_amounts = [values for line in text.splitlines() if len(values := amounts(line)) == 3]
        gt_amount = next(amounts(line)[0] for line in text.splitlines() if "Verpflegungspauschale von" in line)
        locator = f"Satzungsanlage 1 S. {page}, II; § 4"
        component(city, "Pflichtmittagessen im Ganztag", f"{gt_amount // 100:d},{gt_amount % 100:02d}",
                  source=source, required=True, months=12, offers=gt, valid_from=start, valid_to=end, locator=locator)
        for days, amount in zip([2, 3, 5], meal_amounts[0], strict=True):
            component(city, f"Optionales Mittagessen bei VÖ · {days} Tage", f"{amount // 100:d},{amount % 100:02d}",
                      source=source, required=False, months=12, offers=vo, valid_from=start, valid_to=end, locator=locator)
    rule(city, "family_pass", {"reduction_percent": 50, "applies_to": "care"}, locator="§ 5")
    rule(city, "late_pickup", {"amount_cents": 3000, "interval_minutes": 30}, locator="§ 3 Abs. 9")
    city["issues"].extend([
        {"code": "gt9_gt10_no_current_booking", "detail": "Die Preiszellen bleiben erhalten. GT 9 ist nicht als aktuell buchbar belegt. GT 10 wird laut Anmeldeportal derzeit nicht angeboten."},
        {"code": "birth_order_for_vo", "detail": "VÖ ist ab Rang 3 bei mindestens drei Haushaltskindern beitragsfrei. Für eine Kartenintegration den Geburtsrang der berücksichtigten Haushaltskinder verwenden."},
    ])
    return city


def neuhausen(record, reference_date):
    city = catalog(record, reference_date, "1fe941069a2d", "2026-04-01", 11,
                   "Entgeltübersicht; Tabellenfuß: August entgeltfrei und Kinder unter 18 mit Erstwohnsitz")
    # Each tuple describes one published rate column and the associated current booking.
    tables = [
        ("777192e93399", "dd3e952d070a", "u3", [("GT 8", 480, 5)]),
        ("b23f241fdee3", "dd3e952d070a", "o3", [("GT 8", 480, 5), ("GT 10", 600, None)]),
        ("cfe9dee5c692", "6133f7667fac", "u3", [(f"GT 8 · {days} Tage", 480, days) for days in [5, 4, 3, 2]]),
        ("93811d30f87d", "e61763663d37", "u3", [(f"GT 7:15 · {days} Tage", 435, days) for days in [5, 3, 2]]),
        ("265bb4d2baaa", "db99211e39dd", "o3", [("Halbtags 5 Stunden", 300, None), ("Halbtags 5:45 Stunden", 345, 5)]),
    ]
    for source, schedule_source, age, columns in tables:
        rows = [amounts(line) for line in read_text(source).splitlines()
                if re.match(r"\s*[1-5]\s+Kind|\s*5\s+und mehr Kinder", line) and amounts(line)]
        if source == "b23f241fdee3":
            assert len(rows) == 10 and all(len(row) == 1 for row in rows)
            rows = [first + second for first, second in zip(rows[:5], rows[5:], strict=True)]
        assert len(rows) == 5 and all(len(row) == len(columns) for row in rows), (source, rows)
        for index, (label, minutes, days) in enumerate(columns):
            if source == "cfe9dee5c692" and days == 5:
                # Same price and care as Egelsee. Preserve both official references.
                matching = [row for row in city["prices"] if row["offer_id"] == city["offers"][0]["id"]]
                assert [row["amount_cents"] for row in matching] == [row[index] for row in rows]
                for row in matching:
                    row["corroborating_evidence"] = [evidence(source, "PDF S. 1, Spalte 5 Tage")]
                continue
            schedule = evidence(schedule_source, "Kommunales Einrichtungsprofil und Wochentage laut Entgelttabelle")
            item = offer(city, label, age, (minutes * days / 60) if days else None,
                         source=source, daily=[minutes] * 5 if days == 5 else None,
                         locator="PDF S. 1, Entgelte ab April 2026",
                         schedule_evidence=schedule, nominal_daily_minutes=minutes,
                         **({"days_per_week": days} if days else {}))
            for family_count, row in enumerate(rows, 1):
                price(city, item, row[index], family_count, cents=True, minimum=False,
                      selectors={"family_count_is_minimum": True} if family_count == 5 else None)
    official_ue3_gt8 = [amounts(line)[0] for line in read_text("ebf4a741fccb").splitlines()
                       if re.match(r"\s*[1-4]\s+Kind|\s*5\s+und mehr Kinder", line) and amounts(line)]
    ue3_gt8 = next(item for item in city["offers"] if item["age_group"] == "o3" and item["original_label"] == "GT 8")
    rows = [row for row in city["prices"] if row["offer_id"] == ue3_gt8["id"]]
    assert [row["amount_cents"] for row in rows] == official_ue3_gt8
    for row in rows:
        row["corroborating_evidence"] = [evidence("ebf4a741fccb", "PDF S. 1, GT 8")]
    ue3_gt8["booking_source_details"] = [
        {"site": "Kinderhaus am Egelsee", "until": "2027-08-31", "evidence": evidence("dd3e952d070a", "Betreuungsmodelle")},
        {"site": "Kindergarten Alfred-Delp-Weg", "evidence": evidence("6fa342f5da83", "Ganztag 7 bis 15 Uhr")},
    ]
    for friday in [450, 540]:
        hours = (4 * 540 + friday) / 60
        item = offer(city, f"GT 9 · {hours:g} Wochenstunden", "o3", hours, source="dd3e952d070a",
                     daily=[540] * 4 + [friday], locator="Kinderhaus am Egelsee, Betreuungsmodelle mit Freitagswahl")
        for family_count in range(1, 6):
            price(city, item, None, family_count, status="not_published", minimum=False)
    for age, amount in [("u3", 4), ("o3", "5,20")]:
        gt = [item for item in city["offers"] if item["age_group"] == age and item["original_label"].startswith("GT")]
        component(city, f"Pflichtmittagessen {'Krippe' if age == 'u3' else 'Kindergarten'}", amount, age=age, unit="per_meal",
                  required=True, offers=gt, source="a3f277739333", locator="Verpflegung: Preise pro Essen")
    rule(city, "published_hourly_rates", {"regular_cents": 149, "extended_cents": 186, "full_day_cents": 223,
         "nursery_cents": 435, "monthly_factor": "4.3", "family_shares_percent": [100, 75, 50, 17, 0],
         "prefer_published_monthly_values": True}, locator="Kommunales Kita-Portal: Entgelte")
    city["issues"].extend([
        {"code": "gt9_monthly_amount_not_published", "detail": "Das Egelsee-Angebot GT 9 wird mit 43,5 oder 45 Wochenstunden geführt. Die Entgelttabelle nennt stattdessen GT 8 und GT 10. Die gerundeten Stundenbeträge reproduzieren die veröffentlichten Monatsentgelte nicht durchgängig."},
        {"code": "rohrspaetzle_hours_inconsistent_heading", "detail": "Entgelttabelle und konkrete Uhrzeit 7:45 bis 15:00 ergeben 7:15 Stunden täglich. Das Profil verwendet an anderer Stelle die Überschrift GT 8."},
    ])
    return city


def weinstadt(record, reference_date):
    source = record["sources"][0]["source_id"]
    portal = record["sources"][-1]["source_id"]
    city = catalog(record, reference_date, source, "2026-09-01", 11,
                   "§ 8 Ziff. 2–3 und Anlage S. 7", family_basis="child_benefit")
    city["scope"]["included"].extend(["clemens_kita", "rappelkiste", "sonnenblume"])
    pages = read_text(source).split("\f")
    rows = [amounts(line) for line in pages[6].splitlines() if re.match(r"^\s*\([1-4]\)", line)]
    assert len(rows) == 24 and all(len(row) == 2 for row in rows)
    labels = ["Regelgruppe", "Waldkindergarten", "VÖ 6", "VÖ 7", "GT 8", "GT 10"]
    schedules = {
        ("o3", "Regelgruppe"): ([480, 330, 330, 330, 330],
            "Badkindergarten: Ü3-Regelgruppe an fünf Tagen, täglich 7:30–13:00 plus Montag 14:00–16:30 Uhr"),
        ("o3", "Waldkindergarten"): ([300] * 5,
            "Waldkindergarten: fünf Tage Ü3, 8:00–13:00 Uhr"),
        ("o3", "VÖ 6"): ([360] * 5, "Badkindergarten: VÖ6 fünf Tage altersgemischt Ü3"),
        ("u3", "VÖ 6"): ([360] * 5, "Badkindergarten: VÖ6 fünf Tage altersgemischt U3 ab zwei Jahren"),
        **{(age, label): ([minutes] * 5, f"Kinderhaus Benzach: {label}, fünf Tage {age.upper()}")
           for age in ["u3", "o3"] for label, minutes in [("VÖ 7", 420), ("GT 8", 480)]},
    }
    for index, label in enumerate(labels):
        for column, age in enumerate(["o3", "u3"]):
            daily, locator = schedules.get((age, label), (None,
                f"Elternportal, kein aktuell bestätigter Fünf-Tage-Plan für {label} {age.upper()}"))
            hours = sum(daily) / 60 if daily else 50 if label == "GT 10" else None
            item = offer(city, label, age, hours, daily=daily, continuous=label != "Regelgruppe",
                         minimum=24 if age == "u3" and label == "VÖ 6" else None,
                         category="mixed_age" if age == "u3" and label == "VÖ 6" else "childcare",
                         locator=f"Satzungsanlage S. 7, {label}, {age.upper()}",
                         schedule_evidence=evidence(portal, locator))
            for count, row in enumerate(rows[index * 4:(index + 1) * 4], 1):
                price(city, item, row[column], count, cents=True)
    meal_amount = next(amounts(line)[0] for line in pages[7].splitlines() if "105 EUR" in line)
    meals = [item for item in city["offers"] if item["original_label"] in {"VÖ 7", "GT 8", "GT 10"}]
    component(city, "Pflichtmittagessen", meal_amount // 100, required=True, months=11, offers=meals,
              locator="§ 9 und Satzungsanlage S. 8, Pflicht bei Angeboten über sechs Stunden täglich")
    rule(city, "sibling_eligibility", {"normal_age_limit_months": 120, "primary_school_extension_requires_application": True,
         "outside_city_uses_first_tier": True, "model_children_are_under_age_limit": True}, locator="§ 8 Ziff. 3")
    rule(city, "optional_income_relief", {"income_basis": "housing_benefit_defined_gross", "income_period": "month",
         "threshold_cents": 350000, "reference_period": "previous_year", "application_required": True,
         "model_assumed_eligible": False}, locator="§ 8 Ziff. 5")
    city["issues"].append({"code": "booking_scope", "detail": "U3-VÖ6 ist ab zwei Jahren belegt. GT10 ist in der Preistabelle enthalten. Eine durchgehend für beide Altersgruppen bestätigte städtische Fünf-Tage-Buchung ist nicht hinterlegt."})
    return city


def main():
    register = json.loads((ROOT / REGISTER_PATH).read_text())
    source_manifest = {item["id"]: item for item in json.loads((ROOT / "data/source_manifest.json").read_text())}
    schema = json.loads((ROOT / "data/municipality.schema.json").read_text())
    registry = deepcopy(load_registry())
    catalogs = []
    normalizers = {"neuhausen-auf-den-fildern": neuhausen, "markgroeningen": markgroeningen,
                   "bietigheim-bissingen": bietigheim_bissingen, "weinstadt": weinstadt}
    for record in register["municipalities"]:
        for item in record["sources"]:
            meta = source_manifest[item["source_id"]]
            assert meta["http_status"] == 200 and meta["url"] == item["url"]
            assert sha256((ROOT / meta["local_path"]).read_bytes()).hexdigest() == meta["sha256"]
        city = normalizers[record["id"]](record, register["reference_date"])
        city = {key: value for key, value in city.items() if not key.startswith("_")}
        error_list = shape_errors(city, schema, schema, city["id"])
        if error_list:
            raise ValueError("\n".join(error_list))
        municipality_id, ags = record["id"], record["ags"]
        area_id = "municipality-" + ags
        registry["municipalities"].append({"id": municipality_id, "name": city["name"], "ags": ags,
            "active": False, "region_id": "stuttgart-region", "tariff_id": municipality_id, "area_id": area_id})
        registry["areas"].append({"id": area_id, "kind": "municipality", "municipality_id": municipality_id,
            "parent_id": None, "tariff_id": municipality_id, "geometry_key": ags})
        catalogs.append(city)
    error_list = validate_dataset([*load_cities(), *catalogs], registry=registry)
    if error_list:
        raise ValueError("\n".join(error_list))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for city, record in zip(catalogs, register["municipalities"], strict=True):
        path = OUTPUT / f"{city['id']}.json"
        payload = (json.dumps(city, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        path.write_bytes(payload)
        entries.append({"id": city["id"], "name": city["name"], "ags": record["ags"],
                        "path": path.relative_to(ROOT).as_posix(), "sha256": sha256(payload).hexdigest()})
        print(f"{city['name']}: {len(city['offers'])} offers, {len(city['prices'])} price cells")
    manifest = {"schema_version": "1.0", "reference_date": register["reference_date"], "municipalities": entries}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
