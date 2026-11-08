"""Command-line validation and reproducible exports for the tariff dataset."""

import argparse
import csv
import json
from pathlib import Path

from .engine import (ROOT, compare_municipalities, load_cities, load_default_profile,
                     load_highest_band_profile)
from .registry import active_municipalities, load_registry
from .validation import validate_dataset


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_csv(path, records, columns):
    # This is a machine-readable export of canonical records, not a workbook.
    records = list(records)
    columns = columns + sorted({key for row in records for key in row} - set(columns))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for record in records:
            writer.writerow({key: json.dumps(record.get(key), ensure_ascii=False, sort_keys=True)
                             if isinstance(record.get(key), (dict, list)) else record.get(key) for key in columns})


def euro(cents):
    return "—" if cents is None else f"{cents / 100:,.2f}".replace(",", "x").replace(".", ",").replace("x", ".") + " €"


def write_report(path, cities, profile, results):
    sources = {s["id"]: s for s in json.loads((ROOT / "data/source_manifest.json").read_text())}
    if profile["income_mode"] == "highest_band":
        description = "Profil: 24 Monate altes Einzelkind, kommunale Betreuung, höchster regulärer Einkommenstarif, ohne Pass- oder Sozialermäßigung; Montag bis Freitag jeweils mindestens acht Stunden durchgehend."
        reference = "Zusätzliche Höchsttarifreferenz: `data/profiles/highest_band.json`, Sollwerte in `data/reviews/highest_band_review.json`. Die Modellfamilie ist der Standard; diese Referenz erhält die bisherigen Vollzahlerwerte."
    else:
        description = "Profil: zwei zusammenlebende Eltern, ein 24 Monate altes Kind ohne Geschwister; 80.000 € Haushaltsbrutto und unabhängig angenommene 60.000 € zu versteuerndes Jahreseinkommen, im Vorjahr und laufenden Jahr unverändert, keine weiteren Einkünfte oder Vermietungsverluste; kommunale Betreuung ohne Pass- oder Sozialermäßigung; Montag bis Freitag jeweils mindestens acht Stunden durchgehend."
        reference = "Modellannahmen: Esslingens gesonderte Einkommensgrundlage wird mit 80.000 € angesetzt; ein möglicher Arbeitnehmer-Pauschbetrag wird im Modell nicht abgezogen. Korntal-Münchingens bereinigte steuerliche Grundlage beträgt ohne Vermietungsverluste 60.000 € jährlich bzw. 5.000 € monatlich. Das ist keine Brutto-/Steuerumrechnung und kein statistischer Durchschnittshaushalt. Die lokalen Grundlagen sind ausdrücklich im Profil erfasst."
    title = "# Höchsttarifvergleich und Vollständigkeitsprüfung" if profile["income_mode"] == "highest_band" else "# Standardvergleich und Vollständigkeitsprüfung"
    lines = [title, "",
             f"**Tarifstichtag:** {profile['as_of']} · **Quellenprüfung:** 7. November 2026", "",
             description, "", reference, "",
             "Der Vergleichswert ist der am Stichtag geltende Monatsbeitrag × Beitragsmonate ÷ 12. Das Jahresäquivalent hält diesen Tarif konstant und bildet keine tatsächliche Jahresabrechnung mit unterjährigen Änderungen ab. Die Kennzahl enthält Betreuung; Zusatzkosten stehen separat im JSON-Export. Ein veröffentlichtes Angebot garantiert keinen freien Platz.", "",
             "| Kommune | Gewähltes Paket | Wochenstunden | Mehrstunden | Monatsbeitrag | Beitragsmonate | Monatsäquivalent | Status |",
             "|---|---|---:|---:|---:|---:|---:|---|"]
    for row in results:
        hours = "—" if row["booked_weekly_minutes"] is None else f"{row['booked_weekly_minutes'] / 60:g}".replace(".", ",")
        extra = "—" if row["extra_weekly_minutes"] is None else f"{row['extra_weekly_minutes'] / 60:g}".replace(".", ",")
        status = {"comparable": "vergleichbar", "unavailable": "nicht berechenbar", "ambiguous": "mehrdeutig"}[row["status"]]
        lines.append(f"| {row['municipality']} | {row['offer_label'] or '—'} | {hours} | {extra} | {euro(row['monthly_care_cents'])} | {row['payment_months'] or '—'} | {euro(row['monthly_equivalent_cents'])} | {status} |")
    lines += ["", "## Vollständigkeit der strukturierten Übertragung", "",
              "Die Zahlen beziehen sich auf gespeicherte Tarifzellen und Angebotsdefinitionen einschließlich ausdrücklich nicht angebotener oder nicht bepreister Varianten mit eigenem Status. Formelbasierte Angebote haben keine künstlich vervielfältigten Preiszeilen. Unklare Regeln bleiben mit Originalquelle dokumentiert. Vollständigkeit des Quellenarchivs bedeutet nicht, dass jede Sonderregel automatisch ausführbar ist.", "",
              "| Kommune | Angebote | Tarifzellen | Einkommensstufen | Kostenbausteine | Regelstatus |",
              "|---|---:|---:|---:|---:|---|"]
    for city in cities:
        lines.append(f"| {city['name']} | {len(city['offers'])} | {len(city['prices'])} | {len(city['income_bands'])} | {len(city['components'])} | Unterstützte Berechnung plus archivierter Satzungstext |")
    lines += ["", "## Einschränkungen und Quellenhinweise", "",
              "- Ein numerischer Wert von `0` bedeutet ausdrücklich gebührenfrei; fehlende oder unklare Werte sind `null` im JSON und haben einen eigenen Status.",
              "- Bruttoeinkommen, zu versteuerndes Einkommen und kommunale Einkommensdefinitionen bleiben getrennt. Es gibt keine geschätzte steuerliche Umrechnung.",
              "- Nicht belegte tägliche Verteilungen werden nicht aus Wochenstunden abgeleitet. Das betrifft weiterhin einzelne alternative Stundenmodelle.",
              "- Mahlzeitenpreise werden nur mit bekannten Beitragsmonaten bzw. ausdrücklich eingegebenen Essenstagen umgerechnet. Einrichtungsabhängige Preise bleiben Varianten.",
              "- Passbesitz und Bewilligungsvoraussetzungen müssen für ermäßigte Profile ausdrücklich bestätigt werden. Sonderfälle wie Eingewöhnung, Abwesenheit, Härtefallentscheidungen und anteilige Aufnahmemonate sind im Quellenarchiv erhalten und werden nicht in den regulären Referenzwert eingerechnet.",
              "- Bei FamilienCard-Profilen mit mehreren U3-Kindern bleibt die Verteilung des einmaligen Kleinkindzuschlags offen; die Berechnung verlangt dafür eine gesonderte Klärung.", ""]
    for city, row in zip(cities, results, strict=True):
        lines += [f"### {city['name']}", ""]
        if row["reasons"]:
            lines += ["Berechnung eingeschränkt: " + ", ".join(row["reasons"]), ""]
        descriptions = {
            "income_interval_gaps": "Die wörtlichen Einkommensgrenzen lassen einzelne Grenz-/Centwerte offen. Dafür wird keine Gebührenstufe geraten.",
            "unpriced_gt11": "GT11 ist definiert, aber in der Gebührenanlage nicht bepreist.",
            "unpriced_gt50_2027": "Die 2027-Anlagen führen keinen GT50-Preis auf. Daraus wird weder eine Abschaffung noch die gesicherte Fortgeltung des 2026-Betrags abgeleitet.",
            "older_u3_price_date": "Die aktuelle Gerlinger Satzung führt weiterhin die U3-Tabelle mit Preisstand September 2025.",
            "no_uniform_40h_daily_schedule": "Fellbachs belegtes 40-Stunden-Modell hat donnerstags/freitags nur sieben Stunden. Das kleinste geprüfte Paket für acht Stunden an jedem Tag umfasst 45 Stunden (9,25/9,25/9,25/9,25/8). Die Stadt rechnet mit den angebotenen Öffnungsstunden.",
            "adult_child_application": "Die Berücksichtigung kindergeldberechtigter volljähriger Kinder in Leinfelden-Echterdingen erfordert einen Antrag; das persönliche Profil muss die genehmigte Haushaltskonstellation wiedergeben.",
            "published_pass_rounding": "Die veröffentlichten Stadtpassbeträge haben Vorrang vor der Prozentrechnung; die Quelle weist gerundete Beträge aus.",
        }
        for issue in city["issues"]:
            lines.append(f"- `{issue['code']}`: {descriptions.get(issue['code'], 'Siehe Originalquelle und strukturierten Datensatz.')}")
        if row["evidence"]:
            for ref in row["evidence"]:
                source = sources[ref["source_id"]]
                lines.append(f"- [Originalquelle {ref['source_id']}]({source['url']}): {ref['locator']}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n")


def export_comparison(output, name, profile, results):
    dump(output / (name + ".json"), {"schema_version": "1.0", "profile": profile, "results": results})
    write_csv(output / (name + ".csv"), results, [
        "municipality_id", "municipality", "ags", "area_id", "tariff_id", "status", "as_of", "offer_label",
        "booked_weekly_minutes", "extra_weekly_minutes", "monthly_care_cents", "payment_months",
        "annual_care_cents", "monthly_equivalent_cents", "reasons", "evidence", "components"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "compare", "export"])
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--municipality")
    parser.add_argument("--output", type=Path, default=ROOT / "data/exports")
    args = parser.parse_args()
    if args.command == "export" and (args.profile or args.municipality):
        parser.error("Export publishes the complete default catalog. Use compare for personal profiles or a single municipality.")
    cities = load_cities()
    registry = load_registry()
    errors = validate_dataset(cities)
    if errors:
        parser.exit(1, "\n".join(errors) + "\n")
    entries = active_municipalities(registry)
    if args.command == "validate":
        print(f"Valid: {len(entries)} active municipalities; {len(cities)} tariff catalogs; {sum(len(c['offers']) for c in cities)} offers; {sum(len(c['prices']) for c in cities)} prices; registry, profiles and archived hashes verified.")
        return
    try:
        profile = json.loads(args.profile.read_text()) if args.profile else load_default_profile()
        results = compare_municipalities(cities, profile, registry, args.municipality)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    if args.command == "compare":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    active_tariffs = {entry["tariff_id"] for entry in entries}
    cities = [city for city in cities if city["id"] in active_tariffs]
    by_id = {city["id"]: city for city in cities}
    report_cities = [dict(by_id[entry["tariff_id"]], name=entry["name"]) for entry in entries]
    args.output.mkdir(parents=True, exist_ok=True)
    export_comparison(args.output, "default_comparison", profile, results)
    highest_profile = load_highest_band_profile()
    highest_results = compare_municipalities(cities, highest_profile, registry)
    export_comparison(args.output, "highest_band_comparison", highest_profile, highest_results)
    prices = [dict(row, municipality_id=city["id"]) for city in cities for row in city["prices"]]
    write_csv(args.output / "tariffs.csv", prices, ["municipality_id", "id", "offer_id", "amount_cents", "unit", "value_status", "selectors", "included_components", "evidence"])
    for collection, columns in [
        ("offers", ["municipality_id", "id", "original_label", "age_group", "valid_from", "valid_to", "original_price_valid_from", "weekly_minutes", "weekday_minutes", "schedule_status", "payment_months", "formula", "evidence", "schedule_evidence", "payment_evidence"]),
        ("components", ["municipality_id", "id", "kind", "original_label", "amount_cents", "unit", "age_group", "offer_ids", "required", "payment_months", "selectors", "evidence"]),
        ("income_bands", ["municipality_id", "id", "basis", "period", "reference_period", "lower_cents", "upper_cents", "lower_inclusive", "upper_inclusive", "is_highest", "single_parent", "original_label", "evidence"]),
    ]:
        records = [dict(row, municipality_id=city["id"]) for city in cities for row in city[collection]]
        write_csv(args.output / (collection + ".csv"), records, columns)
    dump(args.output / "municipality_registry.json", registry)
    dump(args.output / "catalog.json", {"schema_version": "1.0", "registry": registry, "municipalities": cities})
    write_report(ROOT / "docs/STANDARDVERGLEICH.md", report_cities, profile, results)
    write_report(ROOT / "docs/HOECHSTTARIFVERGLEICH.md", report_cities, highest_profile, highest_results)
    print(f"Exported {len(results)} default results ({sum(r['status'] == 'comparable' for r in results)} comparable) and {len(highest_results)} highest-band results to {args.output}.")


if __name__ == "__main__":
    main()
