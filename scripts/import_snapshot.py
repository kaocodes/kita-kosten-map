"""One-time, reproducible migration of the reviewed research into canonical JSON.

Normal exports read JSON directly; this migration never runs during evaluation.
Official supplemental tables are parsed from archived source text, not inferred.
"""

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/imported/research_2026-11-04.md"
CONFIG = {
    "ditzingen": ("Ditzingen", "e3a01305341e", "2026-01-01", 12, "child_benefit"),
    "kornwestheim": ("Kornwestheim", "ecb1d09b1939", "2026-09-01", 11, "resident_children"),
    "stuttgart": ("Stuttgart", "535c7b4c86f8", "2026-08-01", 11, "under_18"),
    "gerlingen": ("Gerlingen", "f9eb066f5901", "2026-09-01", 12, "child_benefit"),
    "leonberg": ("Leonberg", "ca8ce11d0b8f", "2026-10-01", 12, "under_18"),
    "korntal-muenchingen": ("Korntal-Münchingen", "e534e1399550", "2024-01-01", 11, "under_18"),
    "fellbach": ("Fellbach", "772cfcc5d07d", "2026-09-01", 12, "under_18"),
    "esslingen": ("Esslingen am Neckar", "55d9e28a62d7", "2026-03-01", 12, "under_18_or_child_benefit"),
    "sindelfingen": ("Sindelfingen", "8552e155f7fe", "2026-08-01", 12, "under_18"),
    "ludwigsburg": ("Ludwigsburg", "29969ba83249", "2026-09-01", 11, "under_18"),
    "leinfelden-echterdingen": ("Leinfelden-Echterdingen", "3edbd30ca2f4", "2026-09-01", 11, "child_benefit"),
    "boeblingen": ("Böblingen", "d1f83ab397ca", "2026-09-01", 12, "under_18_or_child_benefit"),
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def cents(value):
    value = value.replace("€", "").replace("*", "").strip()
    if value in {"–", "-", "kein Angebot"}:
        return None
    if value == "gebührenfrei":
        return 0
    return int(Decimal(value.replace(".", "").replace(",", ".")) * 100)


def numbers(value):
    return [cents(n) for n in re.findall(r"\d[\d.]*(?:,\d+)?", value)]


def source_text(source_id):
    return (ROOT / "data/sources" / source_id / "text.txt").read_text()


def evidence(source_id, locator, original=None):
    return {"source_id": source_id, "locator": locator, "original": original}


def parse_tables(text):
    tables = []
    current = None
    city = heading = ""
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            city = line[3:]
        if line.startswith("### "):
            heading = line[4:]
        if line.startswith("|"):
            if current is None:
                current = {"municipality": city, "heading": heading, "line": line_no, "rows": []}
                tables.append(current)
            if not re.match(r"^\|[\s:|\-]+$", line):
                current["rows"].append([cell.strip() for cell in line.strip("|").split("|")])
        else:
            current = None
    return tables


def create_city(city_id, config, text):
    name, source_id, valid_from, months, family_basis = config
    section = re.search(r"^## " + re.escape(name) + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return {
        "schema_version": "1.0", "id": city_id, "name": name,
        "reviewed_at": "2026-11-07", "reference_date": "2026-11-04",
        "scope": {"included": ["municipal"], "other_providers": "only_with_explicit_source_evidence"},
        "family_basis": family_basis,
        "family_evidence": evidence(source_id, "Gebührenmaßstab / Familienbegriff"),
        "payment_months": months,
        "payment_evidence": evidence(source_id, "Entstehung/Fälligkeit; monatliche Erhebung und Ferienregelung"),
        "original_research": {"path": str(ARCHIVE.relative_to(ROOT)), "section": name,
                              "text": section.group(1) if section else ""},
        "income_bands": [], "offers": [], "prices": [], "components": [], "rules": [], "issues": [],
        "_source": source_id, "_from": valid_from,
    }


def offer(city, label, age, weekly_hours, *, start=None, end=None, daily=True,
          continuous=True, schedule_source=None, schedule_status="published",
          original_price_from=None, source_id=None, locator="Gebührentabelle"):
    source_id = source_id or city["_source"]
    start = start or city["_from"]
    key = f"{label}:{age}:{start}"
    offer_id = city["id"] + "-" + hashlib.sha256(key.encode()).hexdigest()[:10]
    existing = next((o for o in city["offers"] if o["id"] == offer_id), None)
    if existing:
        return existing
    minutes = int(Decimal(str(weekly_hours)) * 60) if weekly_hours is not None else None
    item = {
        "id": offer_id, "original_label": label, "age_group": age,
        "age_min_months": 12 if age == "u3" else 36,
        "age_max_months_exclusive": 36 if age == "u3" else None,
        "until_school_entry": age == "o3", "valid_from": start, "valid_to": end,
        "original_price_valid_from": original_price_from or start,
        "scope": "municipal", "weekly_minutes": minutes,
        "weekday_minutes": [minutes // 5] * 5 if daily and minutes is not None else None,
        "continuous": continuous, "schedule_status": schedule_status,
        "schedule_evidence": evidence(schedule_source or source_id, locator),
        "payment_months": city["payment_months"], "payment_evidence": city["payment_evidence"],
        "evidence": evidence(source_id, locator), "formula": None,
    }
    if city["id"] == "stuttgart":
        item["valid_to"] = "2027-07-31"
        item["age_min_months"] = 0 if age == "u3" else 36
    if city["id"] == "leonberg":
        item["age_min_months"] = 0 if age == "u3" else 36
    city["offers"].append(item)
    return item


def price(city, item, amount, family, original, *, band=None, pass_id="none", rank=None,
          family_max=4, source_id=None, locator=None, status=None, included=None):
    row = {
        "id": f"{city['id']}-price-{len(city['prices']) + 1:04}", "offer_id": item["id"],
        "amount_cents": amount, "unit": "per_month",
        "value_status": status or ("not_offered" if amount is None else "known"),
        "selectors": {"family_count": family, "family_count_is_minimum": family == 4 and family_max is None,
                      "income_band_id": band, "pass_id": pass_id, "care_rank": rank},
        "included_components": included or [],
        "evidence": evidence(source_id or item["evidence"]["source_id"],
                             locator or item["evidence"]["locator"], original),
    }
    city["prices"].append(row)
    return row


def component(city, label, amount, *, age=None, offers=None, required=None, months=None,
              source_id=None, locator="Verpflegung", unit="per_month", **extra):
    item = {"id": f"{city['id']}-component-{len(city['components']) + 1:03}",
            "kind": "meal", "original_label": label, "amount_cents": amount,
            "unit": unit, "age_group": age, "offer_ids": offers,
            "required": required, "payment_months": months,
            "valid_from": city["_from"], "valid_to": None,
            "value_status": "known" if amount is not None else "unknown",
            "evidence": evidence(source_id or city["_source"], locator), **extra}
    city["components"].append(item)
    return item


def income_band(city, band_id, low, high, *, basis, period="year", lower_inclusive=True,
                highest=False, single_parent=None, literal=None):
    existing = next((b for b in city["income_bands"] if b["id"] == band_id), None)
    if existing:
        return band_id
    city["income_bands"].append({"id": band_id, "basis": basis, "period": period,
        "reference_period": "previous_year", "lower_cents": low, "upper_cents": high,
        "lower_inclusive": lower_inclusive, "upper_inclusive": True,
        "is_highest": highest, "single_parent": single_parent,
        "original_label": literal, "evidence": evidence(city["_source"], "Einkommensstaffel", literal)})
    return band_id


def table_ref(table, row):
    return {"research_line": table["line"], "heading": table["heading"], "row": row}


def migrate_tables(cities, tables):
    by_name = {c["name"]: c for c in cities.values()}
    for index, table in enumerate(tables, 1):
        city = by_name.get(table["municipality"])
        if not city:
            continue
        header, *rows = table["rows"]
        if index in {12, 13, 14}:  # History is preserved; official supplements replace partial tables.
            continue
        for row in rows:
            ref = table_ref(table, row)
            if index in {1, 2, 3, 4}:
                age = "o3" if index in {1, 3} else "u3"
                start = "2027-01-01" if index in {3, 4} else city["_from"]
                end = "2026-12-31" if index in {1, 2} else None
                hours = int(re.search(r"(30|35|45|50) Std", row[0]).group(1))
                label = row[0].split(", zvE")[0].split(", wörtlich")[0]
                if "Ganztag" in label or "GT," in label:
                    label = f"GT {hours} Std./Woche"
                item = offer(city, label, age, hours, start=start, end=end,
                             source_id="55caf2cb4eb8" if start == "2027-01-01" else None,
                             continuous=not row[0].startswith(("Regel", "RG")))
                band = None
                values = row[2:6] if index in {1, 2} else row[1:5]
                if hours >= 45:
                    income_text = row[1] if index in {1, 2} else row[0]
                    n = 0 if "bis 35" in income_text else 1 if "35.001" in income_text else 2 if "50.001" in income_text else 3
                    low = [None, 3500100, 5000100, 7000100][n]
                    high = [3500000, 5000000, 7000000, None][n]
                    band = income_band(city, f"tax-{n}", low, high, basis="taxable_income",
                                       lower_inclusive=n != 3, highest=n == 3, literal=income_text)
                for family, value in enumerate(values, 1):
                    price(city, item, cents(value), family, ref, band=band, family_max=None)
            elif index == 5:
                age = "u3" if "U3" in row[0] else "o3"
                match = re.search(r"(\d+(?:,\d+)?) Std", row[0])
                hours = float(match.group(1).replace(",", ".")) * 5 if match else None
                item = offer(city, row[0], age, hours, schedule_status="published" if match else "unknown")
                for family, value in enumerate(row[1:], 1):
                    price(city, item, cents(value), family, ref)
            elif index in {6, 7}:
                age = "u3" if index == 6 else "o3"
                hours = 10 if "bis 2 Std" in row[0] else 9 if "bis 1 Std" in row[0] else int(re.search(r"(\d+) Std", row[0]).group(1))
                item = offer(city, row[0], age, hours * 5)
                family = int(row[1][0])
                for column, pass_id in [(2, "family_card"), (3, "none")]:
                    included = [{"kind": "infant_surcharge", "amount_cents": numbers(row[4])[column - 2]}] if index == 6 else []
                    price(city, item, cents(row[column]), family, ref, pass_id=pass_id,
                          family_max=None, included=included)
            elif index in {8, 9}:
                age = "u3" if index == 8 else "o3"
                hours = 6.5 if "VÖ" in row[0] else 8.5
                item = offer(city, row[0], age, hours * 5,
                             original_price_from="2025-09-01" if age == "u3" else None)
                for family, value in enumerate(row[1:], 1):
                    price(city, item, cents(value), family, ref, family_max=None)
            elif index in {10, 11}:
                age = "u3" if index == 10 else "o3"
                for column, value in enumerate(row[1:], 1):
                    label = header[column]
                    hours = float(re.search(r"(\d+(?:,\d+)?) Std", label).group(1).replace(",", "."))
                    item = offer(city, label, age, hours * 5, continuous=not label.startswith("Regel"), end="2027-08-31")
                    price(city, item, cents(value), int(row[0][0]), ref)
            elif index == 15:
                band_index = rows.index(row)
                upper = [50000, 60000, 70000, 80000, 90000, 100000, 120000, 140000, 160000, None][band_index]
                lower = [0, 50000, 60000, 70000, 80000, 90000, 100000, 120000, 140000, 160000][band_index]
                band = income_band(city, f"gross-{band_index}", lower * 100 if band_index else None, upper * 100 if upper else None,
                                   basis="esslingen_gross_income", lower_inclusive=band_index == 0,
                                   highest=upper is None, literal=row[0])
                for column, age in [(1, "u3"), (2, "o3")]:
                    item = offer(city, "Ganztag 40 Std./Woche", age, 40)
                    for family, value in enumerate(numbers(row[column]), 1):
                        price(city, item, value, family, ref, band=band, family_max=None)
            elif index in {16, 17}:
                age = "o3" if index == 16 else "u3"
                band = f"gross-{rows.index(row)}"
                base = offer(city, "Ganztag 40 Std./Woche", age, 40)
                for column, minutes in [(1, 30), (2, 60)]:
                    for days, group in zip([5, 4, 3, 2, 1], row[column].split(";"), strict=True):
                        for family, value in enumerate(numbers(group), 1):
                            component(city, f"Zusatzbetreuung +{minutes} Minuten an {days} Tagen", value,
                                      age=age, offers=[base["id"]], required=False, months=12,
                                      kind="care_extension", extension_minutes=minutes, days_per_week=days,
                                      selectors={"family_count": family, "family_count_is_minimum": family == 4,
                                                 "income_band_id": band, "pass_id": "none", "care_rank": None},
                                      evidence=evidence(city["_source"], f"PDF Zusatzbetreuung {age}", ref))
            elif index in {18, 19}:
                age = "o3" if index == 18 else "u3"
                family = int(row[0][0])
                rank = 1 if family == 1 else int(re.search(r": (\d)\.", row[0]).group(1))
                for column, value in enumerate(row[1:], 1):
                    hours = int(re.search(r"\d+", header[column]).group())
                    item = offer(city, header[column], age, hours * 5)
                    for pass_id, amount in zip(["none", "social_card"], [0, 0] if value == "gebührenfrei" else numbers(value), strict=True):
                        price(city, item, amount, family, ref, rank=rank, pass_id=pass_id, family_max=None)
            elif index == 22:
                age = "u3" if "unter" in row[1] else "o3"
                hours = int(re.search(r"(\d+) Std", row[0]).group(1))
                item = offer(city, row[0], age, hours * 5)
                for family, value in enumerate(row[2:6], 1):
                    price(city, item, cents(value), family, ref, family_max=None)
            elif index == 23:
                age = "u3" if row[0] == "U3" else "o3"
                for hours, value in zip([25, 30, 35, 40, 45], row[3:], strict=True):
                    item = offer(city, header[[25, 30, 35, 40, 45].index(hours) + 3], age, hours)
                    price(city, item, cents(value), int(row[1][0]), ref)
                component(city, "Früh-/Spätdienst je angefangene halbe Stunde", cents(row[2]),
                          age=age, months=11, required=False, kind="care_extension",
                          extension_minutes=30, days_per_week=None,
                          selectors={"family_count": int(row[1][0]), "income_band_id": None},
                          execution_status="blocked_schedule_details", evidence=evidence(city["_source"], "Entgelttabelle", ref))
            elif index == 24:
                age = "u3" if "unter" in row[0] else "o3"
                for hours, value in zip([25, 30, 35, 40, 45, 50, 55], row[2:], strict=True):
                    item = offer(city, f"bis {hours} Std./Woche", age, hours, daily=False,
                                 schedule_status="weekly_only")
                    price(city, item, cents(value), int(row[1][0]), ref, family_max=None)


def supplement_korntal(city):
    source_id = city["_source"]
    page_rows = source_text(source_id).split("\f")
    band_specs = [(None, 300000, True), (None, 300000, True), (300000, 450000, True),
                  (450100, 600000, True), (600100, 700000, True), (700100, 800000, True),
                  (800000, None, False)]
    for n, (lower, upper, inclusive) in enumerate(band_specs):
        income_band(city, f"tax-month-{n}", lower, upper, basis="adjusted_taxable_income", period="month",
                    lower_inclusive=inclusive, highest=n == 6, single_parent=True if n == 0 else False if n == 1 else None,
                    literal=["alleinerziehend unter 3.000 €", "unter 3.000 €", "3.000–4.500 €", "4.501–6.000 €",
                             "6.001–7.000 €", "7.001–8.000 €", "über 8.000 €"][n])
        if n in {0, 1}:
            city["income_bands"][-1]["upper_inclusive"] = False
    for page_index, age, prefix in [(7, "u3", "Krippe"), (8, "o3", "Ganztag"), (9, "o3", "VÖ")]:
        hours = None
        for line in page_rows[page_index].splitlines():
            match = re.match(r"(\d+(?:[,.]\d+)?) Wochenstunden", line.strip())
            if match:
                hours = float(match.group(1).replace(",", "."))
            if "für ein Kind aus einer Familie mit" not in line:
                continue
            family = int(re.search(r"mit (\d)", line).group(1))
            values = re.findall(r"\d[\d.]*,\d{2}\s*€", line)
            if hours is None or len(values) != 7:
                raise ValueError(f"Unexpected Korntal row: {line}")
            item = offer(city, f"{prefix} {hours:g} Std./Woche", age, hours, daily=False,
                         schedule_status="weekly_only", locator=f"PDF Seite {page_index + 1}, Anlage 1, 2.7")
            for n, value in enumerate(values):
                price(city, item, cents(value), family, line.strip(), band=f"tax-month-{n}")
    component(city, "Mittagessen bei mehr als 7 Stunden Betreuung", 8500, required=None, months=None,
              minimum_daily_minutes_exclusive=420, locator="PDF Seite 11, Anlage 1 Ziff. 5")
    component(city, "Mittagessen im VÖ-Bereich", 8000, required=None, months=None,
              offer_ids=[o["id"] for o in city["offers"] if o["original_label"].startswith("VÖ")],
              locator="PDF Seite 11, Anlage 1 Ziff. 5")
    city["issues"].append({"code": "income_interval_gaps", "detail": "Literal boundaries leave cent values between 4500/4501, 6000/6001 and 7000/7001 unresolved."})
    city["rules"].append({"id": "income_definition", "execution_status": "documented",
        "detail": "Previous-year taxable income plus any losses from letting; income changes above EUR 400/month must be reported.",
        "evidence": evidence(source_id, "Anlage 1 Ziff. 2.1–2.6")})


def supplement_esslingen(city):
    source_id = "62c98dd6879d"
    text = source_text(source_id)
    starts = [m.start() for m in re.finditer(r"Entgelte ab 01\.03\.2026 für", text)]
    for n, start in enumerate(starts):
        chunk = text[start:starts[n + 1] if n + 1 < len(starts) else text.index("Wird in der Einrichtung", start)]
        rows = re.findall(r"(\d) Kind(?:er)?(?: und mehr)?\s*\|\s*([\d.,]+) € / ([\d.,]+) €\*\s*\|\s*([\d.,]+) € / ([\d.,]+) €\*", chunk)
        if len(rows) != 4:
            raise ValueError(f"Unexpected Esslingen RO table: {chunk}")
        for family, u3, u3_pass, o3, o3_pass in rows:
            for age, full, reduced in [("u3", u3, u3_pass), ("o3", o3, o3_pass)]:
                label = ["Regelöffnungszeiten", "VÖ6", "VÖ7"][n]
                item = offer(city, label, age, [None, 30, 35][n], source_id=source_id,
                             continuous=n != 0, schedule_status="unknown" if n == 0 else "published",
                             locator=f"HTML: Entgelte ab 01.03.2026 für {label}")
                for value, pass_id in [(full, "none"), (reduced, "city_pass")]:
                    price(city, item, cents(value), int(family), chunk, source_id=source_id,
                          pass_id=pass_id, family_max=None)
    city["rules"].append({"id": "city_pass_ro", "execution_status": "table_lookup",
        "requires": ["city_pass", "priority_benefits_denied"],
        "evidence": evidence(source_id, "IV. Höhe der Entgelte")})


def supplement_components(cities):
    for city_id, city in cities.items():
        offers = city["offers"]
        gt_ids = [o["id"] for o in offers if o["weekly_minutes"] and o["weekly_minutes"] >= 2250]
        if city_id == "ditzingen":
            for item in offers:
                hours = item["weekly_minutes"] / 60
                amount = 8800 if hours >= 45 else 0 if item["original_label"].startswith(("Regel", "RG")) else 5800
                component(city, "Verpflegung", amount, offers=[item["id"]], required=amount != 0, months=12,
                          valid_from=item["valid_from"], valid_to=item["valid_to"])
        elif city_id == "kornwestheim":
            component(city, "Mittagessen Standard", 7600, required=True, offers=gt_ids, months=None,
                      exception_group="standard")
            component(city, "Vollverpflegung Bebelstraße/Karlstraße/Neckarstraße", 9000,
                      required=True, offers=gt_ids, months=None, exception_group="full_board")
        elif city_id == "stuttgart":
            component(city, "Essensgeld", 7700, required=True, offers=gt_ids, months=None)
        elif city_id == "gerlingen":
            component(city, "Verpflegungspauschale", 6900, required=None, months=12)
            component(city, "Verpflegung Tagessatz", 375, required=None, unit="per_meal",
                      alternative_to="monthly_meal")
        elif city_id == "leonberg":
            for age, amount in [("u3", 9680), ("o3", 11480)]:
                component(city, "Pflichtverpflegung KK/KG", amount, age=age,
                          offers=[o["id"] for o in offers if o["age_group"] == age and o["weekly_minutes"] >= 1950 and not o["original_label"].startswith("VÖ")],
                          required=True, months=12, source_id="14d95ae93ac8", locator="§ 5 ff. und Gebührentabelle")
        elif city_id == "fellbach":
            component(city, "Mahlzeiten inkl. Getränke", 13400, required=None, months=11,
                      required_condition="when_meals_are_offered_and_booked")
        elif city_id == "esslingen":
            component(city, "Mittagessen GT", 7900, offers=[o["id"] for o in offers if "Ganztag" in o["original_label"]],
                      required=True, months=12)
            component(city, "Mittagessen VÖ bei Teilnahme", 7900, required=False, months=12,
                      offers=[o["id"] for o in offers if o["original_label"].startswith("VÖ")], source_id="62c98dd6879d")
        elif city_id == "sindelfingen":
            component(city, "Mittagessen", 9500, required=None, months=12, pass_id="none")
            component(city, "Mittagessen Sozialtarif", 2000, required=None, months=12, pass_id="social_card")
        elif city_id == "ludwigsburg":
            component(city, "Ganztagsverpflegung", 8000, required=True, offers=gt_ids, months=None)
            component(city, "Mittagessen RG/VÖ nach Teilnahme", 400, required=False, unit="per_meal",
                      offers=[o["id"] for o in offers if o["id"] not in gt_ids])
        elif city_id == "leinfelden-echterdingen":
            for age, amounts in [("u3", [1640, 3280, 4920, 6560, 8200]), ("o3", [1720, 3440, 5160, 6880, 8600])]:
                for days, amount in enumerate(amounts, 1):
                    component(city, "Mittagessen", amount, age=age, days_per_week=days, required=None,
                              months=11, source_id="d14c375c9897", valid_from="2025-09-01", pass_id="none",
                              required_condition="care_until_14_or_later")
                    component(city, "Mittagessen Stadtpass A/B/C", days * 1200, age=age,
                              days_per_week=days, required=None, months=11, source_id="d14c375c9897",
                              valid_from="2025-09-01", pass_id="city_pass_abc")
            for amount, group in [(1000, "half_day"), (1600, "voe_or_gt")]:
                component(city, "Zwischenmahlzeit/Snack", amount, age="o3", required=True, months=11,
                          kind="snack", source_id="d14c375c9897", valid_from="2025-09-01", offer_group=group)
        elif city_id == "boeblingen":
            for age, amount in [("u3", 9000), ("o3", 10000)]:
                component(city, "Verpflegung", amount, age=age, required=None, months=11)


def supplement_rules(cities):
    policies = {
        "ditzingen": [("family_pass", "percent_discount", {"percent": 30, "rounding": "whole_euro_half_up", "components": ["care"]}, ["family_pass"])],
        "kornwestheim": [("social_reduction", "percent_discount", {"percent": 50, "income_below_cents": 400000, "income_basis": "gross_income", "income_period": "month", "components": ["care", "meal"]}, ["priority_benefits_denied"])],
        "gerlingen": [("income_reduction", "income_discount", {"bands": [{"below_cents": 5000000, "percent": 20}, {"below_cents": 6000000, "percent": 10}], "income_basis": "gerlingen_household_income", "income_period": "year", "components": ["care"], "offer_groups": ["u3", "gt"]}, ["priority_benefits_denied"])],
        "leinfelden-echterdingen": [("city_pass_a", "percent_discount", {"percent": 60, "components": ["care"]}, ["city_pass_a"]), ("city_pass_b", "percent_discount", {"percent": 35, "components": ["care"]}, ["city_pass_b"]), ("city_pass_c", "percent_discount", {"percent": 25, "components": ["care"]}, ["city_pass_c"])],
    }
    for city_id, entries in policies.items():
        city = cities[city_id]
        for rule_id, kind, parameters, requires in entries:
            city["rules"].append({"id": rule_id, "kind": kind, "parameters": parameters,
                                  "requires": requires, "stackable": False, "execution_status": "supported",
                                  "evidence": evidence(city["_source"], "Gebührenermäßigung")})
    for city in cities.values():
        source_id = city["_source"]
        if (ROOT / "data/sources" / source_id / "text.txt").exists():
            city["source_text_archive"] = str((Path("data/sources") / source_id / "text.txt"))
        city["coverage"] = {"care_tables": "transferred", "income_tables": "transferred_or_not_applicable",
                            "family_tables": "transferred", "rules": "source_text_preserved_with_supported_subset",
                            "exceptions": "source_text_preserved", "reviewed_at": "2026-11-07"}
    cities["leonberg"]["payment_evidence"] = evidence("adc2c4902240", "§ 5 Ziff. 2: monatlich, auch während der Ferien")
    cities["ditzingen"]["issues"].append({"code": "income_interval_gaps", "detail": "Published boundaries include 'mehr als 70.001 €'; do not fill uncovered boundary values."})
    cities["ditzingen"]["issues"].append({"code": "unpriced_gt50_2027", "detail": "The 2027 appendices do not list GT50. Do not infer abolition or continue the 2026 fee as a confirmed 2027 amount."})
    cities["ludwigsburg"]["issues"].append({"code": "unpriced_gt11", "detail": "GT11 is defined without a price in Anlage A."})
    unpriced = offer(cities["ludwigsburg"], "GT11", "u3", 55)
    price(cities["ludwigsburg"], unpriced, None, 1, "GT11 defined in §2, no price in Anlage A", status="not_published")
    unpriced = offer(cities["ludwigsburg"], "GT11", "o3", 55)
    price(cities["ludwigsburg"], unpriced, None, 1, "GT11 defined in §2, no price in Anlage A", status="not_published")
    cities["gerlingen"]["issues"].append({"code": "older_u3_price_date", "detail": "Current consolidated ordinance preserves the explicitly dated September 2025 U3 table."})
    for item in cities["gerlingen"]["offers"]:
        if item["age_group"] == "o3":
            item["valid_to"] = "2027-08-31"
    for label, hours, values in [("VÖ, 7:30–14:00 Uhr", 32.5, [203, 154, 103, 53]), ("Ganztag, 7:30–16:00 Uhr", 42.5, [394, 291, 216, 116])]:
        item = offer(cities["gerlingen"], label, "o3", hours, start="2027-09-01")
        for family, amount in enumerate(values, 1):
            price(cities["gerlingen"], item, amount * 100, family, "Gebührenverzeichnis, Seite 6: ab 1. September 2027", family_max=None)


def supplement_fellbach(city):
    for age, low_rate, high_rate in [("u3", 1300, 1560), ("o3", 650, 780)]:
        item = offer(city, "Gebühr je angebotener Wochenstunde", age, None,
                     daily=False, schedule_status="offered_hours_required")
        item["formula"] = {"kind": "weekly_hour_rate", "threshold_minutes": 2100,
                           "below_or_equal_rate_cents": low_rate, "above_rate_cents": high_rate,
                           "rate_applies_to": "entire_weekly_hours", "rounding": "whole_euro_half_up",
                           "minimum_cents": 1000, "family_discount_percent": [0, 20, 40, 60]}
    city["rules"].append({"id": "social_income_ratio", "kind": "income_ratio",
        "execution_status": "supported", "parameters": {"income_basis": "fellbach_gross_income", "income_period": "month", "threshold_cents": 582000},
        "requires": ["approved_social_reduction", "resident", "no_priority_benefit"],
        "evidence": evidence(city["_source"], "§§ 2–4, whole-euro rounding and minimum EUR 10")})
    city["issues"].append({"code": "offered_hours_required", "detail": "The rate multiplies the opening hours actually offered by the institution, not freely selected hours. A schedule must be verified before the default can use 40 hours."})


def supplement_schedules(cities):
    city = cities["boeblingen"]
    for item in city["offers"]:
        if item["weekly_minutes"] in {1500, 1800, 2100, 2400}:
            item["weekday_minutes"] = [item["weekly_minutes"] // 5] * 5
            item["schedule_status"] = "verified"
            item["schedule_evidence"] = evidence("6d67ccd75002", "PDF Seite 1: Betreuungsformen; Seite 2: städtische Angebote")
    city["payment_evidence"] = evidence("4b99e2929828", "§§ 14,16: ganzjährig monatlich, auch Ferien; nur Essen im August ausgenommen")
    city = cities["korntal-muenchingen"]
    for item in city["offers"]:
        if item["weekly_minutes"] in {1800, 2400}:
            item["weekday_minutes"] = [item["weekly_minutes"] // 5] * 5
            item["schedule_status"] = "verified"
            item["schedule_evidence"] = evidence("d9080549f5ae", "Öffnungszeiten: Montag bis Freitag 7:30–13:30 oder 7:00–15:00 Uhr")
    city["coverage"]["meal_fees"] = "transferred_monthly_85_or_80_payment_months_unconfirmed"
    city = cities["fellbach"]
    formulas = {o["age_group"]: o["formula"] for o in city["offers"]}
    # Equal schedules shared by multiple sites are one municipal offer variant.
    variants = [
        ("GT 45 Std., Mo–Do 9,25 Std./Fr 8 Std.", [555, 555, 555, 555, 480], "e0f7ae696e98", ["u3", "o3"]),
        ("GT 42,5 Std., Mo–Do 9 Std./Fr 6,5 Std.", [540, 540, 540, 540, 390], "cc8785e12412", ["u3", "o3"]),
        ("GT 40 Std., Mo/Di 9 Std., Mi 8 Std., Do/Fr 7 Std.", [540, 540, 480, 420, 420], "17735adc2ed8", ["u3", "o3"]),
        ("VÖ 34,5 Std., Mo–Do 7 Std./Fr 6,5 Std.", [420, 420, 420, 420, 390], "17735adc2ed8", ["u3", "o3"]),
        ("VÖ 34,25 Std., Mo–Mi 7 Std., Do 8,5 Std., Fr 4,75 Std.", [420, 420, 420, 510, 285], "923b8e4514fb", ["u3"]),
        ("VÖ 30 Std., Mo–Fr 6 Std.", [360] * 5, "22e722be0364", ["u3", "o3"]),
        ("HT 25 Std., Mo–Fr 5 Std.", [300] * 5, "fd3ce01c91ee", ["u3"]),
    ]
    for label, schedule, source_id, ages in variants:
        for age in ages:
            item = offer(city, label, age, sum(schedule) / 60, daily=False,
                         schedule_status="verified", schedule_source=source_id,
                         locator="Öffnungszeiten und Altersgruppen auf der städtischen Angebotsseite")
            item["weekday_minutes"] = schedule
            item["formula"] = formulas[age]
            if source_id == "22e722be0364" and age == "u3":
                item["age_min_months"] = 24
    city["issues"] = [{"code": "no_uniform_40h_daily_schedule", "detail": "The published 40-hour package has only seven hours on Thursday/Friday. The smallest verified schedule covering eight hours every weekday is 45 hours (9.25/9.25/9.25/9.25/8)."}]
    cities["leinfelden-echterdingen"]["family_basis"] = "under_18_or_child_benefit"
    cities["leinfelden-echterdingen"]["issues"].append({"code": "adult_child_application", "detail": "Counting child-benefit-eligible adults requires a parental application; eligibility input must reflect the approved household."})
    cities["leonberg"]["family_evidence"] = evidence("ca8ce11d0b8f", "Tabellenfußnote: Kinder unter 18 im selben Haushalt; Satzung §7")
    # The four-child family column and fourth-or-later care rank are distinct selectors.
    for row in cities["sindelfingen"]["prices"]:
        row["selectors"]["care_rank_is_minimum"] = row["selectors"]["care_rank"] == 4
    for band in cities["esslingen"]["income_bands"]:
        band["reference_period"] = "current_calendar_year"
        band["definition_evidence"] = evidence("4d33c02682ef", "IV. Höhe der Entgelte: Bruttojahreseinkommen; Kindergeld ausgeschlossen; Arbeitnehmerpauschbetrag berücksichtigt")
    for item in cities["kornwestheim"]["offers"]:
        if item["weekly_minutes"] is None and item["original_label"].startswith("VÖ"):
            item["weekly_minutes"] = 1800
            item["weekday_minutes"] = [360] * 5
            item["schedule_status"] = "verified"
            item["schedule_evidence"] = evidence("ecb1d09b1939", "§1b: VÖ durchgehend sechs Stunden pro Tag")


def supplement_leinfelden(city):
    page = source_text("03bd8c4fc8b1").split("\f")[5].split("Rückerstattung Klein-")[0]
    for age, chunk in [("o3", page.split("U3 Kleinkind")[0]), ("u3", page.split("U3 Kleinkind")[1])]:
        lines = [line for line in chunk.splitlines() if re.search(r"(?:[1-4]) Kind(?:er)?\s+(?:100,0|75,0|50,0|25,0)%", line)]
        if len(lines) != 16:
            raise ValueError("Expected sixteen Leinfelden family/pass rows")
        hours_options = [25, 30, 35, 40, 45] if age == "o3" else [30, 35, 40, 45]
        for index, line in enumerate(lines):
            family = index % 4 + 1
            pass_id = ["none", "city_pass_a", "city_pass_b", "city_pass_c"][index // 4]
            amounts = re.findall(r"\d[\d.]*,\d{2}\s*€", line)
            if len(amounts) != len(hours_options) + 1:
                raise ValueError(f"Unexpected Leinfelden row: {line}")
            for hours, value in zip(hours_options, amounts[1:], strict=True):
                item = next(o for o in city["offers"] if o["age_group"] == age and o["weekly_minutes"] == hours * 60)
                item["schedule_evidence"] = evidence("03bd8c4fc8b1", "PDF Seite 6: Wochenpakete mit Endzeiten 13/14/15/16/17 Uhr, Frühdienst vor 8 Uhr")
                if pass_id == "none":
                    row = next(r for r in city["prices"] if r["offer_id"] == item["id"] and r["selectors"]["family_count"] == family)
                    if row["amount_cents"] != cents(value):
                        raise ValueError("Leinfelden original transfer differs from the current official table")
                    row["selectors"]["family_count_is_minimum"] = "ab 4" in line
                else:
                    price(city, item, cents(value), family, line.strip(), pass_id=pass_id,
                          source_id="03bd8c4fc8b1", locator="PDF Seite 6: veröffentlichte Stadtpass-Tabelle")
            if pass_id != "none":
                component(city, "Früh-/Spätdienst Stadtpass", cents(amounts[0]), age=age, required=False,
                          months=11, source_id="03bd8c4fc8b1", kind="care_extension", extension_minutes=30,
                          selectors={"family_count": family, "pass_id": pass_id}, execution_status="blocked_schedule_details")
    city["rules"] = [{"id": "published_city_pass_prices", "kind": "table_lookup", "execution_status": "table_lookup",
                       "requires": ["valid_city_pass", "no_priority_benefit"],
                       "evidence": evidence("03bd8c4fc8b1", "PDF Seite 6: veröffentlichte Stadtpassbeträge haben Vorrang vor Prozentrechnung") }]
    city["issues"].append({"code": "published_pass_rounding", "detail": "Use the published A/B/C price cells. Applying 60/35/25 percent to regular fees can differ from the rounded published tariffs."})


def refine_evidence(cities):
    payment_refs = {
        "ditzingen": ("e3a01305341e", "§3 Abs. 3 und §5: monatliche Erhebung auch ohne tatsächlichen Besuch, keine Ferienausnahme"),
        "kornwestheim": ("ecb1d09b1939", "PDF Seite 2, §3 Abs. 2: elf Monate, August gebührenfrei"),
        "stuttgart": ("535c7b4c86f8", "PDF Seite 1: elf Monatsbeiträge, August beitragsfrei"),
        "gerlingen": ("f9eb066f5901", "PDF Seite 6, Gebührenverzeichnis: zwölf Monate pro Jahr"),
        "korntal-muenchingen": ("e534e1399550", "PDF Seite 7, Anlage 1 Ziff. 1: elf Monatsbeiträge, August frei"),
        "fellbach": ("772cfcc5d07d", "§2 Abs. 1, §6 Abs. 1 und §7 Abs. 3: monatliche Betreuung auch in Ferien; elf Monate gelten separat nur fürs Essen nach §5"),
        "esslingen": ("4d33c02682ef", "III. Entstehen und Fälligkeit: zwölf Monate"),
        "sindelfingen": ("8552e155f7fe", "PDF Seite 10, §11: zwölf Monatsgebühren"),
        "ludwigsburg": ("29969ba83249", "PDF Seite 2, §4 Abs. 1: elf Monate, August gebührenfrei"),
        "leinfelden-echterdingen": ("3edbd30ca2f4", "PDF Seite 2, Ziff. 3.4: September bis Juli, elf Monate"),
    }
    for city in cities.values():
        if city["id"] in payment_refs:
            city["payment_evidence"] = evidence(*payment_refs[city["id"]])
        city["age_transition"] = "following_month" if city["id"] in {"esslingen", "fellbach", "leinfelden-echterdingen"} else "age_group_at_reference_date"
        city["supporting_source_ids"] = [json.loads(p.read_text())["id"] for p in sorted((ROOT / "data/sources").glob("*/metadata.json"))
                                          if json.loads(p.read_text())["municipality"] == city["name"] and json.loads(p.read_text())["http_status"] == 200]
        city["scope"]["also_included"] = []
        if city["id"] == "ludwigsburg":
            city["scope"]["also_included"] = ["evangelische Kirche", "katholische Kirche", "Charlottenkrippe", "AWO Ludwigsburg gGmbH", "MAHALE gGmbH", "ausdrücklich vereinbarte städtisch belegte Betriebsplätze"]
            city["scope"]["evidence"] = evidence("29969ba83249", "§1, PDF Seite 1")
        if city["id"] == "leinfelden-echterdingen":
            city["scope"]["also_included"] = ["konfessionelle und freie Träger, die am städtischen Vergabeverfahren teilnehmen"]
            city["scope"]["evidence"] = evidence("3edbd30ca2f4", "Ziff. 0 Öffentliche Einrichtung")
        if city["id"] == "fellbach":
            city["scope"]["partial_rule_scope"] = {"rule": "social_income_ratio", "also_applies_to": "freie Träger mit vertraglicher Beziehung zur städtischen Bedarfsplanung", "evidence": evidence("772cfcc5d07d", "§4 Abs. 7")}
        if city["id"] == "stuttgart":
            city["family_evidence"] = evidence("95bc452daed1", "Welche Regelungen gibt es für den Elternbeitrag? Kinder im Haushalt bis zum vollendeten 18. Lebensjahr")
        if city["id"] == "esslingen":
            city["family_evidence"] = evidence("4d33c02682ef", "IV. Höhe der Entgelte: unter 18 bzw. kindergeldberechtigte ältere Haushaltskinder")
        if city["id"] == "boeblingen":
            city["family_evidence"] = evidence("4b99e2929828", "§14 Abs. 2c: Haushaltskinder unter 18 und kindergeldberechtigte ältere Kinder")
        for item in city["offers"]:
            if city["id"] in {"kornwestheim", "ludwigsburg", "fellbach"} and item["age_group"] == "u3" and item["age_min_months"] == 12:
                item["age_min_months"] = 0
            if city["id"] == "fellbach" and item["formula"]:
                item["evidence"]["locator"] = "PDF Seite 3, §§2–4: Tarif je angebotener Wochenstunde, Familienstaffel und Mindestgebühr"
            source_id = item["evidence"]["source_id"]
            if item["evidence"]["locator"] != "Gebührentabelle":
                continue
            age = item["age_group"]
            pages = {"stuttgart": 1 if age == "u3" else 2, "gerlingen": 6, "leonberg": 1,
                     "kornwestheim": 6, "ludwigsburg": 6 if (item["weekly_minutes"] or 0) <= 2400 else 7,
                     "sindelfingen": 13 if age == "u3" else 12, "leinfelden-echterdingen": 6,
                     "boeblingen": 1, "ditzingen": 11 if age == "u3" else 10, "esslingen": 1}
            locator = f"PDF Seite {pages.get(city['id'], 1)}, {item['original_label']}, {age}"
            if city["id"] == "ditzingen" and item["valid_from"] == "2027-01-01":
                locator = f"PDF Seite {3 if age == 'u3' else 2}, Anlage {'2' if age == 'u3' else '1'} ab 01.01.2027, visuell geprüft"
                item["evidence"]["source_id"] = "ad138a5bccc4"
            item["evidence"]["locator"] = locator
            for row in city["prices"]:
                if row["offer_id"] == item["id"] and row["evidence"]["source_id"] == source_id:
                    row["evidence"]["locator"] = locator
                    row["evidence"]["source_id"] = item["evidence"]["source_id"]
                    if source_id != item["evidence"]["source_id"]:
                        row["corroborating_evidence"] = [evidence(source_id, "HTML-Tabelle ab 01.01.2027")]


def supplement_missing_categories(cities):
    city = cities["boeblingen"]
    for age in ["u3", "o3"]:
        item = offer(city, "15 Std./Woche: kein Angebot", age, 15, daily=False,
                     schedule_status="not_offered", locator="PDF Seite 1: Spalte 15 Stunden, kein Angebot")
        for family in range(1, 5):
            price(city, item, None, family, "kein Angebot", family_max=None, status="not_offered")
    for city_id, age, label, hours, continuous, locator in [
        ("ludwigsburg", "u3", "Regelgruppe RG: definiert, kein Preis in Anlage A", 30, False, "§2 Ziff. 1; Anlage A"),
        ("ludwigsburg", "o3", "Regelgruppe RG: definiert, kein Preis in Anlage A", 30, False, "§2 Ziff. 1; Anlage A"),
        ("kornwestheim", "u3", "HT3: definiert, kein Preis in Anlage 1", 15, True, "§1c; Anlage 1"),
        ("kornwestheim", "o3", "Regelgruppe RG: definiert, kein Preis in Anlage 1", None, False, "§1a; Anlage 1"),
    ]:
        city = cities[city_id]
        item = offer(city, label, age, hours, continuous=continuous,
                     schedule_status="defined_only", locator=locator)
        row = price(city, item, None, 1, "Definition ohne separat ausgewiesenen Tarif", status="not_published")
        row["selectors"]["family_count_is_minimum"] = True


def supplement_leonberg(city):
    future = {
        "u3": {10.5: [722, 672, 622, 572], 9: [608, 558, 508, 458], 8.5: [558, 508, 458, 408],
               6.5: [469, 419, 369, 319], 6: [432, 335, 226, 75], 5.5: [345, 268, 182, 61]},
        "o3": {10.5: [512, 462, 412, 362], 9: [425, 375, 325, 275], 8.5: [390, 340, 290, 240],
               7: [277, 213, 142, 48], 6: [216, 169, 112, 38], 5.5: [173, 134, 92, 30]},
    }
    for old in list(city["offers"]):
        hours = old["weekly_minutes"] / 300
        item = offer(city, old["original_label"], old["age_group"], old["weekly_minutes"] / 60,
                     start="2027-09-01", continuous=old["continuous"], source_id="adc2c4902240",
                     locator="Satzung §6/7: ab 01.09.2027")
        for family, amount in enumerate(future[old["age_group"]][hours], 1):
            price(city, item, amount * 100, family, "Satzung §6: 2027-Grundtarif und §7: Familienstaffel")
    # Preserve supplemental day prices and penalty rules without estimating monthly attendance.
    for age, amount in [("u3", 1076), ("o3", 784)]:
        component(city, "Zusatzbetreuung bis 17 Uhr an einzelnen Tagen", amount, age=age,
                  required=False, unit="per_day", kind="care_extension", source_id="adc2c4902240",
                  locator="§6 Ziff. 1e/2d", execution_status="attendance_days_required")
    component(city, "Verspätete Abholung nach Öffnungsende", 600, required=False, unit="per_started_quarter_hour",
              kind="penalty", source_id="adc2c4902240", locator="§6 Ziff. 5a")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    target = ROOT / "data/municipalities"
    if target.exists() and any(target.glob("*.json")) and not args.force:
        parser.error("Canonical data already exists. Use --force only to repeat the initial migration.")
    if not ARCHIVE.exists():
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "docs/ERFASSTE_GEBUEHREN.md", ARCHIVE)
    text = ARCHIVE.read_text()
    tables = parse_tables(text)
    write_json(ROOT / "data/imported/original_tables.json", tables)
    cities = {key: create_city(key, config, text) for key, config in CONFIG.items()}
    migrate_tables(cities, tables)
    supplement_korntal(cities["korntal-muenchingen"])
    supplement_esslingen(cities["esslingen"])
    supplement_fellbach(cities["fellbach"])
    supplement_components(cities)
    supplement_rules(cities)
    supplement_schedules(cities)
    supplement_leonberg(cities["leonberg"])
    supplement_leinfelden(cities["leinfelden-echterdingen"])
    supplement_missing_categories(cities)
    refine_evidence(cities)
    for city_id, city in cities.items():
        for item in city["offers"]:
            item["payment_evidence"] = city["payment_evidence"]
        for key in ["_source", "_from"]:
            del city[key]
        write_json(target / f"{city_id}.json", city)
    write_json(ROOT / "data/profiles/default.json", {
        "id": "u3-single-child-full-payer-40h", "label": "Krippe · Einzelkind · mindestens 8 Stunden täglich · Vollzahler",
        "as_of": "2026-11-04", "children": [{"age_months": 24, "resident": True, "child_benefit": True}],
        "target_child": 0, "school_entry": False, "care_rank": 1,
        "weekday_minutes": [480, 480, 480, 480, 480], "income_mode": "highest_band",
        "incomes": [], "pass_id": "none", "approved_rules": [], "eligibility": [], "single_parent": False,
        "scope": "municipal", "metric": "care_annual_equivalent_divided_by_12"})
    print(f"Imported {len(cities)} municipalities, {sum(len(c['offers']) for c in cities.values())} offers and {sum(len(c['prices']) for c in cities.values())} prices.")


if __name__ == "__main__":
    main()
