# Integration der ersten acht Erweiterungskommunen

**Stand:** 10. November 2026 · **Branch:** `Datensatz-Erweiterung` · **Veröffentlichung:** nach lokaler Durchsicht freigegeben; Deployment über `main`.

Der ursprüngliche Aufbereitungs- und Kompatibilitätsstand wurde vor der Integration als `1d69bad` auf `main` committed. Die folgende Erweiterung liegt auf dem anschließend angelegten Branch.

## Aufgenommene Kommunen

Ausgewählt sind ausschließlich die acht Kommunen, die sämtliche 2.508 geprüften Modellkonfigurationen unterstützen. Das umfasst bis zu vier Haushaltskinder, beide Haushaltskonstellationen, sechs Einkommensszenarien, sechs beziehungsweise acht Stunden täglich für Krippen- und Kindergartenkinder sowie Schul- und zu Hause betreute Geschwister. Sonderpässe, persönliche Eingaben und künftige Tarifstichtage gehören nicht zu dieser Freigabe.

| Kommune | Bisherige Modellfamilie, Monatsäquivalent | Monatsbeitrag laut Tarif | Beitragsmonate | Gebuchter Wochenumfang |
|---|---:|---:|---:|---:|
| Aidlingen | 700,00 € | 700,00 € | 12 | 40 Std. |
| Asperg | 473,00 € | 473,00 € | 12 | 47,5 Std. |
| Deizisau | 766,33 € | 836,00 € | 11 | 50 Std. |
| Ehningen | 910,25 € | 993,00 € | 11 | 50 Std. |
| Holzgerlingen | 670,00 € | 670,00 € | 12 | 42,5 Std. |
| Marbach am Neckar | 655,42 € | 715,00 € | 11 | 40 Std. |
| Möglingen | 432,00 € | 432,00 € | 12 | 40 Std. |
| Tamm | 628,00 € | 628,00 € | 12 | 40 Std. |

Der Bedarf der Modellfamilie bleibt acht Stunden an jedem Wochentag. Größere gebuchte Umfänge ergeben sich aus den verfügbaren, ausreichend belegten örtlichen Paketen. Es werden keine fiktiven 40-Stunden-Preise interpoliert. Essen und Zusatzkosten bleiben separat; unbekannte Preise werden nicht geschätzt.

Die zwölf bisherigen Kataloge, Profile und Rechenfunktionen bleiben unverändert. Die restlichen 25 Erweiterungskommunen, einschließlich Schwieberdingen, sind weiterhin nicht aktiviert. Der [Kompatibilitätsbericht](ERWEITERUNGSBERECHNUNG.md) dokumentiert den ursprünglichen Prüfstand aller 33 Kandidaten; er wird durch diese Auswahl nicht rückwirkend verändert.

## Übernahme und Schutz vor ungeprüften Änderungen

`data/expansion/activation.json` hält die ausdrückliche Auswahl und die Prüfsumme des zugrunde liegenden Prüfindexes fest. `scripts/activate_expansion_catalogs.py` kopiert ausschließlich diese Kataloge bytegleich nach `data/municipalities/` und ergänzt Register und AGS-Flächenzuordnung. Importdaten und Prüfsnapshots bleiben erhalten; ihre damaligen Angaben wie `not_active` sind Archivmetadaten. Für die laufende Aktivierung ist das Kommunenregister maßgeblich.

`npm run prepare:web`, damit auch Entwicklung, Tests und Build, führt zuerst `--check` aus. Dabei müssen alle Eingabe- und Codeprüfsummen des Prüfindexes, sämtliche Freigabebits der ausgewählten Kommunen, die acht aktiven Katalogkopien und die Registerverweise übereinstimmen. Teilfreigaben werden von dieser ersten Übernahmestufe abgelehnt. Änderungen an Modelloptionen oder Rechenkern erfordern eine erneute Prüfung. Eine kommunale Sonderberechnung wurde nicht eingeführt.

Der bestehende Berechnungsstichtag bleibt der 4. November 2026; die Kompatibilitätsprüfung verwendete den 10. November. Die Übernahme prüft für jedes datierte Tarifobjekt, dass dessen Gültigkeit an beiden Tagen identisch ist. Diese Prüfung ersetzt keine Freigabe für spätere Preisstände.

Karte, Namenwechsel, Liste und Quellen arbeiten bereits registergesteuert. Sie zeigen nun 20 Vergleichskommunen und 120 Umgebungsgebiete. Die Geometrien werden weiterhin gemeinsam vereinfacht; alle 20 aktiven Gebiete erhalten eine dauerhafte Beschriftung und bleiben auswählbar.

## Datenmenge

Der Browserexport entfernt reine Importmetadaten und Parameter ausdrücklich nicht ausführbarer Regeln; Regelkennung, Ablehnungsstatus und Quellenbelege bleiben erhalten. Vollständige Originale liegen weiterhin in den kanonischen JSONs und Archiven. Die Projektion ändert keine ausführbare Berechnungsregel.

- Browserkatalog: **1.514.199 Byte**, mit gzip **76.557 Byte**.
- Gemeindegrenzen: **132.635 Byte**, mit gzip **28.518 Byte**.
- Gemeinsame gzip-Datenmenge: **105.075 Byte**; das bisherige Budget von 150 kB bleibt eingehalten.
- Unkomprimiertes Katalogbudget für die größere Gebietszahl: **2 MB**; Geometriebudget weiterhin 200 kB.

Der Webbuild enthält weiterhin weder Quellen-PDFs noch das Forschungsarchiv oder den vollständigen Prüfindex. Ein Backend wird nicht benötigt. Die CSV-/JSON-Exporte und beide Vergleichsberichte wurden ebenfalls auf 20 Kommunen aktualisiert.

## Prüfungen und Veröffentlichungsfreigabe

Die bestehenden Quellenreferenzen der zwölf Ausgangskommunen bleiben als Regressionstests erhalten. Separate Integrationstests prüfen die acht neuen Referenzwerte, veröffentlichte Einzel- und Geschwisterzellen, beide Referenzprofile, Quellenverweise, zusätzliche Familienkonfigurationen und die Ablehnung geänderter oder nur teilweise unterstützter Kataloge.

```bash
python3 scripts/activate_expansion_catalogs.py --check
python3 scripts/validate_expansion_catalogs.py
python3 -m unittest discover -s tests -q
npm test
npm run build
npm run dev
```

Prüfergebnis: **91 Python-Tests**, **157 JavaScript-Tests** und Produktionsbuild erfolgreich. Zusätzlich wurden sämtliche **2.508 Familienkonfigurationen** mit den tatsächlich projizierten Browserdaten am Website-Stichtag durchlaufen: **20.064 berechenbare Kommunenergebnisse** für die acht neuen Kommunen. Desktop und 390-Pixel-Ansicht wurden im Browser geprüft, einschließlich Karten-/Listenauswahl, Kinderdetails, Familienänderung, Tastaturauswahl, Zoom und Zurücksetzen. Alle 20 Namen sind in der geprüften mobilen Regionsansicht ohne gegenseitige Überdeckung oder Verdeckung durch Kartensteuerungen sichtbar. Die Platzierung berücksichtigt dafür die Steuerflächen und sucht bei dichten Beschriftungen zusätzliche freie Positionen.

Die aktuelle lokale Vorschau läuft unter **http://127.0.0.1:5174/** (`npm run dev -- --port 5174`), weil Port 5173 bereits durch eine ältere Vorschau belegt war. Der reguläre Start ohne Portargument verwendet weiterhin 5173. Nach der lokalen Durchsicht wurde ausdrücklich beauftragt, die Änderungen auf dem Erweiterungsbranch zu committen, nach `main` zu mergen und auf GitHub Pages zu veröffentlichen. Der bestehende Pages-Workflow prüft und veröffentlicht den Merge.
