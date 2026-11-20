# Datenpipeline für kommunale Kita-Tarife

**Stand:** 20. November 2026

Diese Anleitung beschreibt den Arbeitsablauf für neue Kommunen und geänderte Tarife. Fachliche Entscheidungen stehen im [Regelwerk für die Kita-Gebührenanalyse](REGELWERK_DATENANALYSE.md). Amtliche Quellen und ausdrücklich vereinbarte Modellannahmen bleiben im Katalog unterscheidbar.

## Datenstände und Speicherorte

| Stufe | Pfade | Zweck |
|---|---|---|
| Quellen | [Quellenmanifest](../data/source_manifest.json), [Originaldateien](../data/sources/), [Recherche-Register](../data/research/) | URL, Abrufdatum, Prüfsumme, Original und Fundstellen. Recherche-Register halten außerdem ausgewählte Quellen und lokale Festlegungen fest. |
| Erste Erweiterung | [Manifest für 33 Kommunen](../data/expansion/manifest.json), [Kommunenkataloge](../data/expansion/municipalities/) | Erster Erweiterungsbestand, einschließlich der acht bereits für den regulären Build aktivierten Kommunen. |
| Zweite Erweiterung | [Manifest vom 20. November](../data/expansion/batches/2026-11-20/manifest.json), [Erhebungsbericht](DATENERHEBUNG_2026-11-20.md) | Neuhausen auf den Fildern, Markgröningen, Bietigheim-Bissingen und Weinstadt. |
| Regulärer Build | [Kommunenregister](../data/municipality_registry.json), [aktive Auswahl der Erweiterung](../data/expansion/activation.json), [kanonische Kataloge](../data/municipalities/) | 20 aktive Kommunen. Das Register ordnet die Tarife und Kartenflächen über den amtlichen Gemeindeschlüssel (AGS) einander zu. |
| GitHub Pages | [Veröffentlichungsauswahl](../data/expansion/pages_release.json) | 49 freigegebene Kommunen. Die Auswahl bindet die beiden Erweiterungsmanifeste per Prüfsumme. |
| Lokale Vorschau | `build/expansion-preview/` | 49 Kommunen aus dem regulären Bestand und den übrigen Einträgen der beiden Erweiterungsmanifeste. Die Vorschau verändert das reguläre Register auf der Festplatte nicht. |

## 1. Quellen finden und archivieren

1. Gemeinde und AGS bestimmen. Offizielle U3-/Ü3-Gebührenordnungen, Tabellen und Gültigkeitsdaten erfassen. Einen Trägertarif nur bei belegter Geltung oder ausdrücklicher Freigabe übernehmen. Die Gebührenordnung ist die erste Quelle für Stunden und Angebote. Öffnungszeiten ergänzen sie, wenn die Tarifunterlagen keine Stundenzahl nennen.
2. Das Recherche-Register mit Kommune, Titel und direkter URL anlegen. Als Vorlage dient das [Register der zweiten Erhebung](../data/research/municipal_tariff_collection_2026-11-20.json). Der Sammler archiviert darin verzeichnete URLs und ergänzt Quellenkennungen. Der Pfad im folgenden Befehl ist das bestehende Beispiel.

   ```bash
   python3 scripts/collect_expansion_sources.py data/research/municipal_tariff_collection_2026-11-20.json
   ```

3. Abrufstatus, Prüfsumme, Veröffentlichungs- und Gültigkeitsdatum sowie konkrete Fundstellen prüfen. Bildbasierte Tabellen visuell übertragen und die Abschrift mit dem Original verknüpfen. Bei einer neuen Fassung den bisherigen Beleg erhalten. Für einen gezielten erneuten Abruf einer festen URL kann `python3 scripts/fetch_sources.py --municipality <id> --url <url> --refresh` verwendet werden.

Die Auswahl und der fachliche Abgleich neuer Quellen erfolgen manuell. Es gibt keinen allgemeinen Import für beliebige neue Gebührenordnungen und keinen zeitgesteuerten Quellenabruf. GitHub Actions prüft und baut die Website nach Änderungen am Repository.

## 2. Einen Katalog pro Kommune normalisieren

Das [gemeinsame JSON-Schema](../data/municipality.schema.json) gilt für alle Kommunen. Preise in Cent, Zeiten in Minuten und die Zahl der monatlichen Beiträge erfassen. Angebotsdauer, belegte Buchbarkeit an fünf Tagen, Einkommensstufe, Familiengröße, Geburts- und Betreuungsrang sowie Verpflegung getrennt ablegen. Preiszellen und Bedingungen mit Gültigkeitsintervall und Quellenfundstelle verknüpfen. Unbekannte Pflichtkosten bleiben unbekannt. Eine belegte Gebührenbefreiung ist null Euro. Der Originalpreis bleibt auch bei belegter Trennung eines Essensanteils erhalten.

Der erste Import verwendet kommunenspezifische Normalisierer in `scripts/normalize_expansion_tariffs.py`. Deren unveränderte Ausgabe lässt sich mit `--check` prüfen. Die zweite Erhebung hat eigene Normalisierer in `scripts/normalize_municipal_tariff_collection.py`. Das Skript prüft Schema, Quellprüfsummen und Zuordnung und erzeugt Kataloge und Manifest aus den archivierten Eingaben. Der Befehl schreibt die abgeleiteten Dateien erneut.

```bash
python3 scripts/normalize_expansion_tariffs.py --check
python3 scripts/validate_expansion_catalogs.py
python3 scripts/normalize_municipal_tariff_collection.py
```

Für weitere Kommunen den passenden Parser wiederverwenden oder eine gezielte Übertragung ergänzen. Die Vorschau liest derzeit zwei explizit eingebundene Manifeste. Ein zusätzlicher Importordner allein genügt für die Kartenvorschau nicht. Änderungen an der gemeinsamen Engine wegen eines einzelnen Ortsfalls vorab abstimmen. Für Schwieberdingen gilt die ausdrückliche Vorgabe, dafür keine Engineänderung vorzunehmen.

## 3. Mit gezielten Stichproben prüfen

Je geänderter Kommune acht feste Modellfälle prüfen. Das Grundprofil verwendet zwei zusammenlebende Eltern und 80.000 € Jahresbrutto.

1. Einzelkind U3 mit sechs Stunden.
2. Einzelkind U3 mit acht Stunden.
3. Einzelkind Ü3 mit sechs Stunden.
4. Einzelkind Ü3 mit acht Stunden.
5. Zwei betreute Kita-Kinder mit unterschiedlichen Zeitmodellen.
6. Ein betreutes Kita-Kind und ein Schulgeschwister.
7. Vier Haushaltskinder mit gemischter Betreuung.
8. Ein Ü3-Kind mit acht Stunden bei Alleinerziehung.

Pro Kommune sind bis zu vier zusätzliche Fälle für preiswirksame Besonderheiten möglich. Dazu zählen Einkommensgrenzen, abweichende Beitragsmonate oder eine besondere Geschwisterregel. Erwarteten Beitrag, tatsächliche Wochenstunden und Quellenfundstelle oder den belegten Grund der Nichtverfügbarkeit dokumentieren. Vollständige Kombinationstests gehören zur früheren Freigabe der ersten acht Kommunen. Für neue fachliche Prüfungen gilt die begrenzte Stichprobe.

Der Browser wählt das belegte Fünf-Tage-Paket am nächsten zu 30 bzw. 40 Wochenstunden. Die Untergrenzen liegen bei 30 bzw. 36 Stunden. Bei gleichem Abstand gewinnt der größere Umfang, bei gleicher Wochenzeit der günstigere belegte Tarif. Die Karte zeigt die Summe der Jahresbeiträge aller betreuten Kita-Kinder geteilt durch zwölf. Fehlt ein Beitrag, bleibt die Familiensumme nicht berechenbar. Belegte Einzelwerte bleiben sichtbar. Die Regeln zu enthaltenem Essen und örtlichen Sonderfällen stehen im [Regelwerk](REGELWERK_DATENANALYSE.md).

```bash
npm test
npm run test:expansion
npm run dev:expansion
```

Die Vorschau läuft auf [localhost:5174](http://127.0.0.1:5174/). Dort Modellfamilie, Quellen, tatsächliche Wochenzeit und die Darstellung eines nicht berechenbaren Falls kontrollieren. Der Vergleichsstichtag des Kartenprofils ist der 4. November 2026. Der Abruf und die Einzelprüfung der zweiten Erhebung am 20. November haben dieses Profil nicht umgestellt.

## 4. Regelbetrieb und Freigabe

Die Vorschau dient der fachlichen Sichtung. Der reguläre Build bezieht Tarife aus den aktiven Einträgen des kanonischen Registers. Für die bereits freigegebenen acht Erweiterungskommunen prüft `npm run prepare:web` die Auswahl, Quellkataloge und Prüfsummen über `scripts/activate_expansion_catalogs.py --check`. Diese Sperre basiert auf dem historischen Freigabeindex des ersten Imports. Der Pages-Build ergänzt die 29 weiteren Kommunen über die Freigabedatei. Sie legt die geprüften Manifeststände und die freigegebene Gebietsanzahl fest, ohne das kanonische Register zu ändern. Neue oder geänderte Manifeststände brauchen erneute Prüfung und eine aktualisierte Freigabedatei.

Nach einer Veröffentlichungsfreigabe bauen `npm run build:pages` und `npm run test:pages` den freigegebenen Stand und prüfen die erzeugten Daten. GitHub Actions veröffentlicht erfolgreiche Builds von `main`. Details zu Ports, Größenbudgets und Befehlen stehen in [WEBANWENDUNG.md](WEBANWENDUNG.md). Frühere Quellen- und Tarifprüfungen liegen im lokalen Archiv.
