"""Verify archived expansion evidence and render its German research report.

This checks provenance and consistency; it does not verify municipal legal rules
or convert the research into production tariffs.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "data/research/neighbor_expansion_2026-11-10.json"
REPORT = ROOT / "docs/ERWEITERUNGSRECHERCHE.md"

STATUS_LABELS = {
    "available": "Tarifbasis vorhanden",
    "clarification_required": "Klärung erforderlich",
}
SCHEDULE_LABELS = {
    "available": "Passendes Zeitmodell belegt*",
    "schedule_to_verify": "Tagesverteilung noch prüfen",
    "not_in_published_u3_catalog": "Nicht im U3-Katalog",
    "friday_too_short": "Freitag kürzer als 8 Std.",
    "municipal_u3_not_established": "Kommunale U3-Basis offen",
}


def activated_candidates(register):
    """Read current activation separately from the archived research assessment."""
    candidate_ids = {item["id"] for item in register["municipalities"]}
    registry = json.loads((ROOT / "data/municipality_registry.json").read_text())
    return sorted(item["id"] for item in registry["municipalities"] if item["active"] and item["id"] in candidate_ids)


def verify_decisions(municipality, decisions, source_ids):
    """Keep project assumptions distinct from source-backed tariff facts."""
    decision_ids = set(municipality.get("decision_ids", []))
    for decision_id in decision_ids:
        decision = decisions.get(decision_id)
        if not decision or decision["municipality_id"] != municipality["id"]:
            raise ValueError("Decision does not belong to this municipality")

    def check_months(months):
        if months["verification"] == "open":
            if months["count"] is not None:
                raise ValueError("Unverified payment months must remain null")
            return
        if months["verification"] == "age_group_specific":
            if months["count"] is not None or not months.get("by_age_group"):
                raise ValueError("Age-specific payment months require separate counts")
            for age_months in months["by_age_group"].values():
                check_months(age_months)
            return
        if type(months["count"]) is not int or not 1 <= months["count"] <= 12:
            raise ValueError("Payment months must be an integer between one and twelve")
        if months["verification"] in {"user_assumption", "user_confirmed"}:
            if months.get("decision_id") not in decision_ids:
                raise ValueError("User-specified payment months need a recorded decision")
        if "source_id" in months and months["source_id"] not in source_ids:
            raise ValueError("Unregistered payment-month evidence")

    check_months(municipality["payment_months"])
    policy = municipality.get("comparison_policy", {})
    if policy and policy.get("decision_id") not in decision_ids:
        raise ValueError("Comparison policy needs a recorded decision")
    meals = municipality.get("meals", {})
    if "decision_id" in meals and meals["decision_id"] not in decision_ids:
        raise ValueError("Meal parameters need a recorded decision")
    if policy.get("schedule_matching") == "allow_friday_shortfall_when_monday_to_thursday_meet_daily_need":
        if (municipality["id"] != "denkendorf" or policy.get("allowed_shortfall_days") != ["friday"]
                or not policy.get("requires_documented_daily_schedule")
                or not policy.get("retain_original_weekly_minutes")
                or not policy.get("retain_original_price") or not policy.get("show_schedule_shortfall")):
            raise ValueError("Approved Friday exception must preserve actual offers and remain local")
    for rule in municipality.get("family_rules", {}).values():
        if isinstance(rule, dict) and rule.get("decision_id") not in decision_ids:
            raise ValueError("Family-rule assumptions need a recorded decision")
    for configuration in municipality.get("unavailable_configurations", []):
        if configuration.get("result_status") != "unavailable" or not configuration.get("reasons"):
            raise ValueError("Unresolved configurations must explicitly remain unavailable")
    if policy.get("meal_handling") == "keep_included":
        if (policy.get("subtract_meal_costs") is not False
                or meals.get("status") != "included"
                or meals.get("additional_charge") is not False
                or not policy.get("derive_inclusion_from_offer")):
            raise ValueError("Included meals must remain included without a second charge")
    if policy.get("meal_handling") == "subtract_known_included_amount":
        if (not policy.get("requires_meal_inclusion") or policy.get("age_group") != meals.get("age_group")
                or policy.get("monthly_deduction_cents") != meals.get("amount_cents")):
            raise ValueError("Meal deduction requires a matching amount and offer inclusion")
        reference = municipality["comparison_reference_price"]
        if (reference["published_amount_cents"] != municipality["reference_price"]["amount_cents"]
                or reference["deduction_cents"] != meals["amount_cents"]
                or reference["amount_cents"] != reference["published_amount_cents"] - reference["deduction_cents"]
                or reference["annual_care_cents"] != reference["amount_cents"] * reference["payment_months"]
                or reference["annual_meal_cents"] != meals["amount_cents"] * meals["payment_months"]
                or reference.get("decision_id") not in decision_ids
                or reference["source_id"] not in source_ids
                or reference["is_default_comparison"]):
            raise ValueError("Meal-adjusted reference does not reconcile with its original")


def verify(register):
    candidates = {
        (name.strip(), ags)
        for name, ags in re.findall(
            r"^\| \d+ \| ([^|]+) \| (\d{8}) \|",
            (ROOT / "docs/DATENERWEITERUNG.md").read_text(),
            re.MULTILINE,
        )
    }
    municipalities = register["municipalities"]
    actual = {(item["name"], item["ags"]) for item in municipalities}
    if len(municipalities) != len(actual) or actual != candidates:
        raise ValueError("Research municipalities do not match the documented candidates")
    if activated_candidates(register):
        subprocess.run([sys.executable, str(ROOT / "scripts/activate_expansion_catalogs.py"), "--check"],
                       check=True, capture_output=True, text=True)
    transcriptions = json.loads((ROOT / register["transcriptions_path"]).read_text())
    manual_sources = {item["source_id"] for item in transcriptions["sources"]}
    decisions = {item["id"]: item for item in register.get("decisions", [])}
    municipality_ids = {item["id"] for item in municipalities}
    if len(decisions) != len(register.get("decisions", [])):
        raise ValueError("Duplicate decision IDs")
    for decision in decisions.values():
        if decision["provenance"] != "user_instruction" or decision["municipality_id"] not in municipality_ids:
            raise ValueError("Invalid user-decision provenance")
    all_sources = {}
    for municipality in municipalities:
        if municipality["status"] not in STATUS_LABELS:
            raise ValueError(f"Unreviewed municipality: {municipality['name']}")
        if municipality["status"] == "clarification_required" and not municipality["gaps"]:
            raise ValueError("A conditional assessment must identify its gaps")
        source_ids = {source["source_id"] for source in municipality["sources"]}
        verify_decisions(municipality, decisions, source_ids)
        if not set(municipality["key_source_ids"]) <= source_ids:
            raise ValueError(f"Unregistered key evidence for {municipality['name']}")
        reference = municipality["reference_price"]
        if reference["source_id"] not in source_ids or reference["is_default_comparison"]:
            raise ValueError("A source reference must not be presented as a default comparison")
        for additional in municipality.get("additional_reference_prices", []):
            if additional["source_id"] not in source_ids or additional["is_default_comparison"]:
                raise ValueError("An additional reference needs registered source evidence")
        for source in municipality["sources"]:
            metadata_path = ROOT / "data/sources" / source["source_id"] / "metadata.json"
            metadata = json.loads(metadata_path.read_text())
            if metadata["url"] != source["url"]:
                raise ValueError(f"Source URL mismatch: {source['source_id']}")
            if "local_path" in metadata:
                path = (ROOT / metadata["local_path"]).resolve()
                if not path.is_relative_to(ROOT / "data/sources"):
                    raise ValueError("Evidence path outside the archive")
                if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
                    raise ValueError(f"Evidence checksum mismatch: {source['source_id']}")
            if source["source_id"] in municipality["key_source_ids"]:
                if metadata["http_status"] != 200:
                    raise ValueError("Failed downloads cannot be key tariff evidence")
                text_path = metadata_path.with_name("text.txt")
                if not text_path.exists() or len(text_path.read_text().strip()) < 50:
                    if source["source_id"] not in manual_sources:
                        raise ValueError(f"Missing text or visual transcription: {source['source_id']}")
            all_sources[source["source_id"]] = metadata
    for source in transcriptions["sources"]:
        if source["source_id"] not in all_sources:
            raise ValueError("Unregistered visual transcription")
        if source["review_method"] != "visual_transcription" or not source["pages"]:
            raise ValueError("A visual transcription must identify reviewed pages")
        pdf_path = ROOT / all_sources[source["source_id"]]["local_path"]
        info = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True, check=True)
        page_count = int(re.search(r"^Pages:\s+(\d+)", info.stdout, re.MULTILINE).group(1))
        if any(not 1 <= page <= page_count for page in source["pages"]):
            raise ValueError("A visual transcription refers to a nonexistent PDF page")
    return all_sources


def render(register, sources):
    municipalities = register["municipalities"]
    counts = Counter(item["status"] for item in municipalities)
    date = register["review_date"]
    lines = [
        "# Recherche und Bewertung der 33 Nachbarkommunen",
        "",
        f"**Prüfstand:** {date}. Aktuelle veröffentlichte Tarife; keine historische Preisrecherche.",
        "",
        f"**Ergebnis:** Für alle 33 Orte wurden offizielle kommunale Einstiegs- oder Gebührenquellen gesichert. "
        f"Bei **{counts['available']} Kommunen** ist eine auswertbare U3-/Ü3-Tarifbasis vorhanden; "
        f"bei **{counts['clarification_required']} Kommunen** bestehen konkrete Klärungspunkte für den bisherigen Vergleich. "
        "Damit liegt noch **kein uneingeschränkt vergleichbarer Produktionsdatensatz für alle 33 Orte** vor.",
        "",
        "Die Prüfung bewertet die gefundenen Quellen. Sie ist weder eine vollständige Umsetzung der Tarifregeln "
        "im Rechner noch eine Freigabe sämtlicher Familientypen. Die zwölf bisherigen Kommunen bleiben unverändert. "
        "Die Recherche wurde am 10. November auf ausdrücklichen Nutzerwunsch vorgezogen. "
        "Der anschließende Integrations- und Veröffentlichungsstand ist getrennt in der [Erweiterungsintegration](ERWEITERUNGSINTEGRATION.md) dokumentiert.",
        "",
        "## Ablage und Prüfmethode",
        "",
        "- [Recherche-JSON](../data/research/neighbor_expansion_2026-11-10.json): einheitliche Bewertungen aller 33 Orte, Quellenkennungen, Gültigkeit, Beitragsmonate, Einschränkungen und belegte Preisbeispiele.",
        "- [Manuelle Tabellenübertragungen](../data/research/scanned_tariff_transcriptions_2026-11-10.json): bildbasierte Tabellen aus Aidlingen, Ehningen, Eberdingen, Erdmannhausen, Freiberg und Renningen; Geldbeträge in Cent.",
        "- [Quellenmanifest](../data/source_manifest.json) und `data/sources/<source_id>/`: Originale, Abrufzeitpunkt, endgültige URL, HTTP-Status und SHA-256. PDF-Textauszüge behalten Tabellenlayout; Originale bleiben erhalten.",
        "- [Technische Integritätsprüfung](../data/research/neighbor_expansion_integrity_2026-11-10.json): Abdeckung der Kandidaten, Quellenverweise und unveränderte Originaldateien. Diese Prüfung beweist keine fachliche Fehlerfreiheit der Satzungen.",
        "",
        "Suchtreffer wurden als Wegweiser genutzt. Maßgeblich sind heruntergeladene amtliche Tabellen und Satzungen. "
        "Künftig gültige Fassungen wurden vom geltenden Tarif getrennt; ältere Einstiegsfunde und fehlgeschlagene Links bleiben als Rechercheweg erkennbar. "
        "Ein HTTP-200-Status allein genügt nicht als Tarifnachweis. Quellen freier Träger erweitern den vereinbarten Geltungsbereich nicht automatisch. "
        "Ausdrücklich vereinbarte Ausnahme: Die U3-Gebührenordnung des Freiberger Zwergenstüble e.V. wird für Freiberg übernommen; der tatsächliche Vereinsträger bleibt dokumentiert.",
        "",
        f"Gesichert sind **{sum(source['http_status'] == 200 for source in sources.values())} erfolgreiche Abrufe** "
        f"aus **{len(sources)} registrierten Quellen/Versuchen**, einschließlich Einstiegsseiten, ergänzender Regeln und ausgeschiedener älterer Kandidaten. "
        "Die drei fehlgeschlagenen Ausgangslinks wurden durch erreichbare aktuelle Quellen ersetzt und werden nicht als Tarifbeleg verwendet. "
        "Die Zahl der Abrufe ist keine Zahl vollständig normalisierter Gebührentabellen.",
        "",
        "## Überblick aller Orte",
        "",
        "„Tarifbasis vorhanden“ bedeutet: auswertbare Tarifquelle unter Berücksichtigung der ausdrücklich dokumentierten Nutzerfestlegungen. "
        "Eine Nutzerannahme wird dadurch nicht zur amtlichen Bestätigung. Offene Zusatzkosten, Tagesverteilungen "
        "oder Sonderfallregeln stehen zusätzlich in den Detailnotizen. Ein fehlendes 8-Stunden-Angebot ist kein fehlender Tarifdatensatz.",
        "",
        "| Kommune | Quellenbewertung | Preisstand | Beitragsmonate Betreuung | U3: mindestens 8 Std. an allen 5 Tagen | Hauptquelle |",
        "|---|---|---|---|---|---|",
    ]
    for item in municipalities:
        months = item["payment_months"]
        month_label = str(months["count"]) if months["count"] is not None else "offen"
        if months["verification"] == "derived":
            month_label += " (abgeleitet)"
        elif months["verification"] == "age_group_specific":
            month_label = " / ".join(
                f"{'U3' if age == 'u3' else 'Ü3'}: {value['count']}"
                for age, value in months["by_age_group"].items()
            )
        elif months["verification"] == "user_assumption":
            month_label += " (Nutzerannahme)"
        elif months["verification"] == "user_confirmed":
            month_label += " (Nutzerangabe)"
        schedule_label = SCHEDULE_LABELS[item["model_8h_schedule_status"]]
        if item.get("comparison_policy", {}).get("show_schedule_shortfall"):
            schedule_label += " (lokale Ausnahme zugelassen; Hinweis erforderlich)"
        valid = item["current_tariff_valid_from"] or item["current_tariff_period"]
        url = sources[item["reference_price"]["source_id"]]["url"]
        lines.append(
            f"| {item['name']} | {STATUS_LABELS[item['status']]} | {valid} | {month_label} | "
            f"{schedule_label} | [Original]({url}) |"
        )
    lines += [
        "",
        "*Die Zeitmodellbewertung betrifft die veröffentlichte Angebotsstruktur, keine Platzgarantie und noch keine automatische Angebotsauswahl. "
        "Bei Wochenpaketen und Mischwochen ist die Tagesverteilung zusätzlich zu belegen. Zwölf abgeleitete Beitragsmonate beruhen "
        "auf der durchgehenden Kalendermonatspflicht einschließlich Ferien; Quellenbelege, abgeleitete Werte und Nutzerangaben bleiben unterscheidbar.",
        "",
        "## Festlegungen vom 10. November 2026",
        "",
        f"Die {len(register.get('decisions', []))} Nutzerentscheidungen sind im Recherche-JSON mit Datum und Herkunft hinterlegt. "
        "Sie legen den Umgang mit Quellenlücken fest, ersetzen aber keine vollständige Normalisierung oder Prüfung aller Familienkonfigurationen.",
        "",
        "- **Freiberg am Neckar:** U3 nach der Gebührenordnung des Freiberger Zwergenstüble e.V. ab 1. Juni 2026. Alle fünf PDF-Seiten wurden visuell geprüft und übertragen. "
        "U3 hat zwölf Beitragsmonate, der städtische Ü3-Tarif elf. Mittagessen und weitere U3-Verpflegung werden getrennt erfasst. Eine Brutto-Netto-Umrechnung ist damit nicht festgelegt.",
        "- **Steinenbronn:** zwölf Beitragsmonate als ausdrücklich gewählte Nutzerannahme; keine zusätzliche amtliche Bestätigung behauptet.",
        "- **Aichwald:** Krippe als U3 und Kindergarten als Ü3 einordnen; abweichende Altersmischungstarife erhalten. U3-Essen mit 53 € monatlich auf Zwölf-Monats-Basis erfassen. "
        "Nur bei U3-Preisen mit bereits enthaltenem Essen diesen bekannten Betrag abziehen: Kontrollzelle 753,50 € veröffentlicht = 700,50 € Betreuung + 53 € Essen. "
        "Originalpreise bleiben unverändert; kein Abzug bei Ü3 oder bereits essensfreien U3-Angeboten.",
        "- **Waiblingen:** veröffentlichte Beiträge einschließlich Mittagessen unverändert als Karten- und Listenwert verwenden. "
        "Bei Angeboten mit enthaltenem Essen unter Verpflegung „Im Tarif enthalten“ anzeigen. Weder einen geschätzten Anteil abziehen noch Essen ein zweites Mal addieren. "
        "Eine unbekannte separate Monatssumme bedeutet hier keine fehlende Gebühr; Angebote ohne Essen erhalten keine Inklusivkennzeichnung.",
        "- **Möglingen:** zwölf Beitragsmonate gemäß Nutzerangabe verwenden; Herkunft von einem ausdrücklichen Quellenbeleg unterscheidbar halten.",
        "- **Denkendorf:** gemeinsame kommunal veröffentlichte Tabellen der evangelischen und katholischen Einrichtungen verwenden. "
        "Keine unterschiedlichen Betreuungstarife nach Träger ausgewiesen. Das gemeinsame Jahresbrutto direkt verwenden, keine weiteren Einkommensabfragen. "
        "Bei belegtem ausreichendem Umfang von Montag bis Donnerstag darf eine ausschließlich freitags kürzere Betreuung eingeordnet werden; die tatsächlichen Tageszeiten, Wochenstunden und der Originalpreis bleiben erhalten. "
        "Die Details müssen auf die Freitagsabweichung und verpflichtendes GT-Mittagessen mit unbekanntem Preis hinweisen. Keine pauschale Ausnahme für andere Kommunen.",
        "- **Schwieberdingen:** elf Beitragsmonate September bis Juli gemäß Nutzerbestätigung verwenden. Der Verweis auf die Ordnung ist als Nutzerangabe erfasst; "
        "die gesicherte aktuelle Beitragstabelle enthält selbst keine entsprechende Passage. Für Ü3 werden die aktuellen ersten/zweiten Tabellensätze und die Alleinerziehenden-Stufenverschiebung verwendet; "
        "ältere Beträge aus 2025/2026 sind keine aktuellen Preisbelege. Bei U3 wird ausdrücklich als Modell angenommen, dass pro Ermäßigungsgrund eine zusätzliche Stufe gilt. "
        "Bei zwei Haushaltskindern, gleichzeitiger U3-Betreuung und Alleinerziehung ist das Stufe vier. Über die niedrigste veröffentlichte Stufe wird nicht hinausgerechnet. "
        "Ungeklärte Ü3-Rangfolgen mit preisabhängigem Ergebnis und fehlende Rangzellen bleiben für die betroffenen Konfigurationen nicht berechenbar.",
        "",
        "Diese Anzeige- und Berechnungsregeln gelten für die anschließende Integration. Die laufende Website verwendet weiterhin nur die zwölf bisherigen Kommunen. "
        "Die Berechnungsengine wird in dieser Recherche nicht geändert. Änderungen der gemeinsamen Rechenlogik für einzelne Kommunen werden vorher mit dem Nutzer besprochen; "
        "für Schwieberdingen ist keine Engineänderung beauftragt. Fehlende Lösungen erhalten `unavailable` / „nicht berechenbar“, keinen geratenen Ersatzpreis.",
        "",
        "## Verbleibende Klärungsfälle",
        "",
    ]
    for item in municipalities:
        if item["status"] != "clarification_required":
            continue
        lines.append(f"- **{item['name']}:** " + " ".join(item["gaps"]))
    lines += [
        "",
        "## Konsequenzen für Datenmodell und Vergleich",
        "",
        "1. **Tarifvollständigkeit und Vergleichbarkeit getrennt halten.** Ein verlässlich belegtes VÖ-/7,5-Stunden-Angebot darf gespeichert werden, ohne einen Preis für fünfmal acht Stunden zu erfinden. "
        "Denkendorfs ausdrücklich zugelassene Freitagsausnahme ändert weder die tatsächlichen Stunden noch die allgemeinen Auswahlregeln anderer Kommunen.",
        "2. **Haushaltsgröße, betreute Geschwister und Geburtsrang getrennt speichern.** Eberdingen berechnet nach gleichzeitig betreuten Kindern, das jüngste zuerst. Remseck und Waiblingen unterscheiden auch noch das fünfte Kind. Die heutige UI-Auswahl bis vier reicht für eine vollständige Darstellung dieser Regeln nicht aus.",
        "3. **Gemeinsame Eingabe und Quellenbegriff nachvollziehbar halten.** Denkendorf verwendet nach Nutzerfestlegung direkt das gemeinsame Jahresbrutto ohne weitere Abfragen. "
        "Freiberg verwendet monatliches Haushaltsnetto; Waiblingen rechnet unter anderem Kindergeld hinzu; Ostfildern berücksichtigt das Vorjahr und Abzüge. "
        "Quellenregeln und ausdrücklich gewählte Modellannahmen bleiben getrennt dokumentiert.",
        "4. **Essen und Abrechnungsmonate separat führen.** Remseck: Betreuung elf, Essen zehn Monate. Tamm: Betreuung zwölf, Essen elf Monate. "
        "Aichwald: bekannten U3-Essensanteil nur aus einschließenden Preisen herausrechnen. Waiblingen: veröffentlichte Beiträge einschließlich Essen behalten und den enthaltenen Bestandteil kennzeichnen. "
        "Ein unbekannter separat ausgewiesener Betrag bleibt `null`, belegte Gebührenfreiheit ist `0`; enthaltene Verpflegung ist ein eigener Sachverhalt.",
        "5. **Angebotsarten und Träger nicht zusammenwerfen.** Krippe, U3-Altersmischung, TAKKI und Schulkindbetreuung bleiben unterscheidbar. Pattonville besitzt eigene Entgelte; ein einziges Stadtgebiet beweist keine einheitliche Gebührenordnung aller Träger.",
        "6. **Originale und zeitliche Gültigkeit erhalten.** Aspergs prominent verlinkte neue Fassung gilt erst 2027. In Schönaich und Filderstadt ist die Linkbeschriftung teils älter als der verlinkte Dokumentinhalt. Maßgeblich ist das Dokument, nicht URL-Dateiname oder Suchsnippet.",
        "",
        "## Details je Kommune",
        "",
        "Die folgenden Preiszellen dienen als nachvollziehbare Erfassungsbelege. Sie haben unterschiedliche Zeit-, Familien- "
        "und Einkommensbedingungen und sind **keine Rangliste und keine neuen Defaultwerte**.",
        "",
    ]
    for item in municipalities:
        reference = item["reference_price"]
        url = sources[reference["source_id"]]["url"]
        lines += [
            f"### {item['name']} ({item['ags']})",
            "",
            f"**Bewertung:** {STATUS_LABELS[item['status']]}. **Erfasste Struktur:** {item['care_models']}",
            "",
            " ".join(item["findings"]),
            "",
            f"**Kontrollzelle:** {reference['description']}. [Originalquelle]({url}); {reference['locator']}.",
            "",
            "**Grenzen / nächste fachliche Prüfung:** " + " ".join(item["gaps"]),
            "",
        ]
    lines += [
        "## Nächster Umsetzungsschritt",
        "",
        "Die Tarifbasen wurden inzwischen in 33 getrennte Kommunen-JSONs im vorhandenen Schema übertragen; "
        "sie liegen isoliert unter `data/expansion/municipalities/`. Mengen, Umfang und technische Prüfung stehen in der "
        "[Aufbereitungsübersicht](ERWEITERUNGSDATEN.md). Die [Kompatibilitätsprüfung der bestehenden Engine](ERWEITERUNGSBERECHNUNG.md) "
        "ist inzwischen abgeschlossen und weist unterstützte sowie nicht berechenbare Konfigurationen aus. Die vertiefte fachliche Quellenabnahme bleibt ein weiterer Schritt. "
        f"Die {counts['clarification_required']} verbleibenden Klärungsfälle bleiben für ihre betroffenen Konfigurationen eingeschränkt. "
        "Neue Einkommens-/Geschwisterregeln, Verpflegung und belegte Tagesverteilungen werden vor einer Aktivierung berücksichtigt. "
        f"Die gemeinsame Engine bleibt unverändert. Inzwischen sind **{len(activated_candidates(register))} vollständig unterstützte Kandidaten** "
        "über eine gesonderte, gegen den Prüfindex abgesicherte Auswahl in die lokale Website übernommen. "
        "Die Veröffentlichung auf GitHub Pages erfolgt nach ausdrücklicher Freigabe über den Workflow auf `main`; historische Preisreihen bleiben zurückgestellt.",
        "",
        "Erneut prüfen und Bericht aus den Bewertungen erzeugen:",
        "",
        "```bash",
        "python3 scripts/report_expansion_research.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify evidence without rewriting the report")
    args = parser.parse_args()
    register = json.loads(REGISTER.read_text())
    sources = verify(register)
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "municipalities": len(register["municipalities"]),
        "status_counts": dict(Counter(item["status"] for item in register["municipalities"])),
        "recorded_user_decisions": len(register.get("decisions", [])),
        "registered_unique_sources": len(sources),
        "http_200_sources": sum(source["http_status"] == 200 for source in sources.values()),
        "failed_attempts": sum(source["http_status"] != 200 for source in sources.values()),
        "checksum_verification": "passed",
        "canonical_tariff_normalization": register["tariff_normalization_status"],
        "production_activation": json.loads((ROOT / "data/expansion/activation.json").read_text())["status"] if activated_candidates(register) else "not_performed",
        "activated_municipality_ids": activated_candidates(register),
    }
    if not args.check:
        REPORT.write_text(render(register, sources))
        target = ROOT / "data/research/neighbor_expansion_integrity_2026-11-10.json"
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
