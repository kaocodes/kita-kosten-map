# Kita-Gebührenvergleich Region Stuttgart

**Website:** [kaocodes.github.io/kita-kosten-map](https://kaocodes.github.io/kita-kosten-map/)

Strukturierte Gebühren für zwölf Kommunen, mit archivierten offiziellen Quellen und einer nachvollziehbaren Vergleichsberechnung. Tarifstichtag des Standardprofils: **4. November 2026**; ergänzende Quellenprüfung: **7. November 2026**.

Der Datenbestand enthält Krippen- und Kindergartentarife, Einkommens- und Familienstaffeln, Betreuungsmodelle, Ermäßigungen sowie gesonderte Kostenbausteine. Die Python-Datenpipeline benötigt Python ab Version 3.11 und ausschließlich die Standardbibliothek. Die lokale React-/Leaflet-Website verwendet den TypeScript-Rechenkern direkt im Browser.

## Einstieg

- [Standardvergleich und Vollständigkeitsprüfung](docs/STANDARDVERGLEICH.md): die zwölf Vergleichswerte und ihre Einschränkungen.
- [Höchsttarifvergleich](docs/HOECHSTTARIFVERGLEICH.md): die erhaltene Vollzahlerreferenz.
- [Datenmodell und Berechnung](docs/DATENMODELL.md): Struktur, Eingaben, Regeln und Pflegeablauf.
- [TypeScript-Berechnung](docs/BROWSERBERECHNUNG.md): Schnittstelle, Entwicklung und Python-Gegenprüfung für den Browser-Rechenkern.
- [Lokale Webanwendung](docs/WEBANWENDUNG.md): Startbefehle, Bedienung, Geodaten, Größenbudget und statischer Build.
- [Aktuelle Projektanforderungen](docs/PROJECT_REQUIREMENTS.md): fachlicher Umfang des Gesamtprojekts.
- [Websitekonzept und Entscheidungen](docs/WEBSITE_KONZEPT.md): statische Architektur, Stackempfehlung, Gemeindeflächen, Geodatenaufbereitung, Bedienkonzept und Entwürfe.
- [Quellenübersicht](docs/QUELLENUEBERSICHT.md): kommunale Einstiegsseiten und Prüfhinweise.

Maßgeblicher Tarifbestand: `data/municipalities/*.json`. Das JSON-Schema steht in `data/municipality.schema.json`. Das neue `data/municipality_registry.json` bestimmt aktive Kommunen, amtliche Gemeindeschlüssel (AGS), Kartenflächen, Regionen und Tarifverweise. Es ersetzt die feste Prüfung auf zwölf Kommunen. `data/source_manifest.json` verknüpft Quellenkennungen mit URLs, Abrufzeitpunkten, lokalen Kopien und SHA-256-Prüfsummen. Ursprüngliche PDFs, Webseiten und Textauszüge liegen in `data/sources/`. Die ursprüngliche Recherchefassung bleibt in `data/imported/` erhalten.

## Befehle

Im Projektordner ausführen:

```bash
python3 -m kita_costs validate
python3 -m kita_costs compare --municipality stuttgart
python3 -m kita_costs export
python3 -m unittest discover -s tests -v
```

Website und TypeScript-Rechenkern benötigen für Entwicklung und Gegenprüfung Node.js ab 22.12 sowie Python ab 3.11:

```bash
npm ci
npm run dev
```

Danach **http://127.0.0.1:5173/** öffnen. Die Website zeigt Gemeindeflächen, beide Vergleichsprofile, eine Gebührenliste und Gemeindedetails mit Quellen. Die persönlichen Familien-/Einkommensfelder folgen in Paket 4.

Prüfen und statisch bauen:

```bash
npm run typecheck
npm test
npm run build
npm run preview
```

`npm test` prüft Rechenkern und Webdaten mit 119 JavaScript-Tests, einschließlich der gemeinsamen Szenarien gegen Python. `build` erzeugt die statische Website unter `dist/`; `preview` zeigt diesen Build unter **http://127.0.0.1:4173/**. Der Workflow unter `.github/workflows/pages.yml` prüft Änderungen und veröffentlicht erfolgreiche Builds von `main` auf GitHub Pages. Die Python-Datenpipeline benötigt weiterhin keine externen Python-Pakete.

`export` erzeugt `data/exports/default_comparison.json` für die Modellfamilie und `highest_band_comparison.json` für die Höchsttarifreferenz, jeweils mit CSV-Datei. Dazu kommen Register, Katalog der aktiven Tarife sowie CSV-Tabellen für Tarife, Angebote, Einkommensstufen und Zusatzkosten. Beide deutschen Vergleichsberichte werden aktualisiert. Die CSV-Dateien sind abgeleitete Ansichten; ihre Geldbeträge stehen in **Cent**, Zeitangaben in **Minuten**. Verschachtelte Felder enthalten JSON. Das vollständige Quellenarchiv wird nicht in diese Exporte kopiert.

Das zusätzliche Höchsttarifprofil oder eigene Profile werden als JSON übergeben:

```bash
python3 -m kita_costs compare --profile data/profiles/highest_band.json
python3 -m kita_costs compare --profile /path/to/personal-profile.json
```

Das Standardprofil ist die Modellfamilie: zwei zusammenlebende Eltern, ein zweijähriges Kind, 80.000 € Haushaltsbrutto und unabhängig angenommene 60.000 € zu versteuerndes Jahreseinkommen, mindestens acht Stunden durchgehende Betreuung an jedem Wochentag. Die Hauptkennzahl ist der Monatsbeitrag × Beitragsmonate ÷ 12. Essen und weitere Kosten stehen gesondert im Ergebnis. Das ist ein Jahresäquivalent bei konstantem Stichtagstarif, kein Durchschnittshaushalt und keine tatsächliche Kalenderjahresabrechnung. Lokale Einkommensdefinitionen und der Schutz gegen unbemerkt veraltete Modellannahmen sind im [Datenmodell](docs/DATENMODELL.md) beschrieben.

## Pflege und Grenzen

Neue Quellenkopien werden ausdrücklich angefordert und überschreiben vorhandene Belege nicht:

```bash
python3 scripts/fetch_sources.py --municipality Stuttgart --url https://www.stuttgart.de/elternbeitraege-staedtische-kitas --refresh
```

Der Abruf benötigt Internetzugang; PDF-Texte werden mit `pdftotext` extrahiert. Anschließend müssen Änderungen an den kanonischen JSON-Dateien geprüft, mit Quellen belegt und mit den Befehlen oben validiert und exportiert werden. Der einmalige Import `scripts/import_snapshot.py` ist eine Migration der alten Recherchefassung. Er wird im Pflegeablauf nicht erneut ausgeführt; `--force` würde manuelle Datenänderungen ersetzen.

Alle zwölf Werte beider Referenzprofile sind mit offiziellen Quellen abgeglichen. Einzelne andere Modelle und Sonderfälle bleiben eingeschränkt: etwa nicht veröffentlichte GT11-Preise, uneindeutige Einkommensgrenzen, unbestätigte Tagesverteilungen und die einmalige FamilienCard-Zuschlagsverteilung bei mehreren U3-Kindern. Solche Fälle liefern einen konkreten Grund statt eines geschätzten Betrags. Satzungsregeln zu Abwesenheit, Eingewöhnung und Einzelfallentscheidungen bleiben vollständig in den Quellen erhalten; die ausführbare Berechnung deckt reguläre Tarife und die dokumentierten unterstützten Ermäßigungen ab.

Historische Preisreihen sind zurückgestellt. Die Webkarte verwendet diese Datengrundlage seit Paket 3.

## Website und weitere Umsetzung

Als Hauptdarstellung sind seit 8. November 2026 **eingefärbte Gemeindeflächen** beschlossen und mit React, Vite, CSS Modules und Leaflet umgesetzt. TypeScript und Zod bilden den Rechenkern und die Eingabeprüfung. Eine statische Website auf **GitHub Pages** ist die bevorzugte Betriebsform; Tests, Build und Veröffentlichung werden durch GitHub Actions automatisiert.

Die Webgeometrie wird reproduzierbar aus den archivierten BKG-Grenzen aufbereitet. Sie enthält die zwölf Vergleichskommunen und 128 Umgebungsgebiete und umfasst rund 132 kB. Grenzstand 1. Januar 2025, Quellen, Lizenz und Prüfsummen sind gesichert; die aktuelle Verarbeitung steht in [WEBANWENDUNG.md](docs/WEBANWENDUNG.md). Die älteren HTML-Entwürfe in `output/` bleiben Gesprächsvorschauen mit Höchsttarifwerten.

Die Modellfamilie ist das Standardprofil in Python, Exporten und der Website. Die Höchsttarifreferenz ist als zweite Ansicht auswählbar. Kinder, Haushalt, Einkommen, Betreuungsbedarf und nachgewiesene Vergünstigungen sollen in Paket 4 über das individuelle Formular einstellbar werden.

Die Erweiterungsstrategie ist im Websitekonzept festgehalten: ein zentrales Kommunenregister, getrennte Kartenflächen und Gebührenordnungen, eine eigenständige Tarifberechnung, bedarfsgerecht geladene regionale Daten und eine austauschbare Kartenansicht. Neue Kommunen benötigen Register-, Tarif- und Geometriedaten sowie Referenzfälle; neue Abrechnungsregeln können zusätzliche Berechnungslogik erfordern.

**Pakete 1 bis 3 umgesetzt:** Register, beide Referenzprofile, unabhängige TypeScript-Berechnung sowie die lokal aufrufbare Website mit Gemeindekarte und reproduzierbarer Geodatenaufbereitung. Die Gegenprüfung umfasst 104 gemeinsame Szenarien; zusätzliche Webtests sichern Geometriezuordnung, Gebührenwerte und Datenbudgets. **Nächstes Arbeitspaket:** individuelles Familienformular und vollständige Bedienung fertigstellen. Danach folgt die Einrichtung der statischen Veröffentlichung.

## Veröffentlichung und Aktualisierung

Der [Pages-Workflow](.github/workflows/pages.yml) installiert die festgelegten npm-Abhängigkeiten, führt die Python- und JavaScript-Tests aus und baut die Website. Auf `main` wird anschließend ausschließlich `dist/` veröffentlicht. Pull Requests durchlaufen dieselben Prüfungen ohne Deployment. Der Workflow kann auch manuell über GitHub Actions gestartet werden. Schlägt ein Schritt fehl, wird der neue Stand nicht veröffentlicht.

Gebührenänderungen werden weiterhin anhand neuer Quellen geprüft und in den kanonischen Daten gepflegt. Ein Push nach `main` baut die Browserdaten neu und aktualisiert die Website. Es gibt keinen automatischen Abruf kommunaler Quellen beim Seitenbesuch oder Deployment.
