# Kita-Gebührenvergleich Region Stuttgart

Strukturierte Gebühren für zwölf Kommunen, mit archivierten offiziellen Quellen und einer nachvollziehbaren Vergleichsberechnung. Tarifstichtag des Standardprofils: **4. November 2026**; ergänzende Quellenprüfung: **7. November 2026**.

Der Datenbestand enthält Krippen- und Kindergartentarife, Einkommens- und Familienstaffeln, Betreuungsmodelle, Ermäßigungen sowie gesonderte Kostenbausteine. Die Berechnung benötigt Python ab Version 3.11 und ausschließlich die Standardbibliothek.

## Einstieg

- [Standardvergleich und Vollständigkeitsprüfung](docs/STANDARDVERGLEICH.md): die zwölf Vergleichswerte und ihre Einschränkungen.
- [Datenmodell und Berechnung](docs/DATENMODELL.md): Struktur, Eingaben, Regeln und Pflegeablauf.
- [Aktuelle Projektanforderungen](docs/PROJECT_REQUIREMENTS.md): fachlicher Umfang des Gesamtprojekts.
- [Websitekonzept und Entscheidungen](docs/WEBSITE_KONZEPT.md): statische Architektur, Stackempfehlung, Gemeindeflächen, Geodatenaufbereitung, Bedienkonzept und Entwürfe.
- [Quellenübersicht](docs/QUELLENUEBERSICHT.md): kommunale Einstiegsseiten und Prüfhinweise.

Maßgeblicher Datenbestand: `data/municipalities/*.json`. Das JSON-Schema steht in `data/municipality.schema.json`. `data/source_manifest.json` verknüpft Quellenkennungen mit URLs, Abrufzeitpunkten, lokalen Kopien und SHA-256-Prüfsummen. Ursprüngliche PDFs, Webseiten und Textauszüge liegen in `data/sources/`. Die ursprüngliche Recherchefassung bleibt in `data/imported/` erhalten.

## Befehle

Im Projektordner ausführen:

```bash
python3 -m kita_costs validate
python3 -m kita_costs compare --municipality stuttgart
python3 -m kita_costs export
python3 -m unittest discover -s tests -v
```

`export` erzeugt `data/exports/default_comparison.json`, die zugehörige CSV-Datei, einen vollständigen JSON-Katalog sowie CSV-Tabellen für Tarife, Angebote, Einkommensstufen und Zusatzkosten. Außerdem aktualisiert der Befehl den deutschen Standardvergleichsbericht. Die CSV-Dateien sind abgeleitete Ansichten; ihre Geldbeträge stehen in **Cent**, Zeitangaben in **Minuten**. Verschachtelte Felder enthalten JSON.

Eigene Profile werden als JSON übergeben:

```bash
python3 -m kita_costs compare --profile data/profiles/default.json
```

Das Standardprofil vergleicht ein zweijähriges Einzelkind, Vollzahlertarif und mindestens acht Stunden durchgehende Betreuung an jedem Wochentag. Die Hauptkennzahl ist der Monatsbeitrag × Beitragsmonate ÷ 12. Essen und weitere Kosten stehen gesondert im Ergebnis. Das ist ein Jahresäquivalent bei konstantem Stichtagstarif, kein Durchschnittshaushalt und keine tatsächliche Kalenderjahresabrechnung.

## Pflege und Grenzen

Neue Quellenkopien werden ausdrücklich angefordert und überschreiben vorhandene Belege nicht:

```bash
python3 scripts/fetch_sources.py --municipality Stuttgart --url https://www.stuttgart.de/elternbeitraege-staedtische-kitas --refresh
```

Der Abruf benötigt Internetzugang; PDF-Texte werden mit `pdftotext` extrahiert. Anschließend müssen Änderungen an den kanonischen JSON-Dateien geprüft, mit Quellen belegt und mit den Befehlen oben validiert und exportiert werden. Der einmalige Import `scripts/import_snapshot.py` ist eine Migration der alten Recherchefassung. Er wird im Pflegeablauf nicht erneut ausgeführt; `--force` würde manuelle Datenänderungen ersetzen.

Alle zwölf Defaultwerte sind mit offiziellen Quellen abgeglichen. Einzelne andere Modelle und Sonderfälle bleiben eingeschränkt: etwa nicht veröffentlichte GT11-Preise, uneindeutige Einkommensgrenzen, unbestätigte Tagesverteilungen und die einmalige FamilienCard-Zuschlagsverteilung bei mehreren U3-Kindern. Solche Fälle liefern einen konkreten Grund statt eines geschätzten Betrags. Satzungsregeln zu Abwesenheit, Eingewöhnung und Einzelfallentscheidungen bleiben vollständig in den Quellen erhalten; die ausführbare Berechnung deckt reguläre Tarife und die dokumentierten unterstützten Ermäßigungen ab.

Historische Preisreihen sind zurückgestellt. Die Umsetzung der Webkarte folgt auf dieser Datengrundlage.

## Geplante Website

Als Hauptdarstellung sind seit 8. November 2026 **eingefärbte Gemeindeflächen** beschlossen. Eine statische Website auf **GitHub Pages** ist die bevorzugte Betriebsform. React, TypeScript, Vite und Leaflet sind die vorgeschlagenen Bibliotheken; ihre endgültige Auswahl steht noch aus.

Die Geodaten werden vor der Veröffentlichung ausgewählt und vereinfacht. Für den visuellen Vergleich wurden echte BKG-Gemeindegrenzen und die zwölf vorhandenen Standardvergleichswerte verwendet. Die vereinfachte regionale Geometrie einschließlich Umgebung umfasst rund 122 kB. Entwürfe in `output/` sind Gesprächsvorschauen; eine produktive Website oder ein Deployment bestehen noch nicht. Aufbereitung, Quellen, Prüfstand und offene Entscheidungen sind im [Websitekonzept](docs/WEBSITE_KONZEPT.md) dokumentiert.

Für die Website wurde anschließend eine einstellbare Modellfamilie als Startprofil besprochen: zwei zusammenlebende Eltern, ein zweijähriges Kind, fünfmal mindestens acht Stunden Betreuung, 80.000 € Bruttojahreseinkommen und separat angenommene 60.000 € zu versteuerndes Einkommen. Kinder, Haushalt, Einkommen, Betreuungsbedarf und nachgewiesene Vergünstigungen sollen einstellbar sein. Die genannten Einkommenswerte sind unabhängige Modellannahmen. Die Umstellung ist noch nicht implementiert; die derzeitigen Befehle und Exporte verwenden weiterhin die geprüfte Höchsttarifreferenz.

Die Erweiterungsstrategie ist im Websitekonzept festgehalten: ein zentrales Kommunenregister, getrennte Kartenflächen und Gebührenordnungen, eine eigenständige Tarifberechnung, bedarfsgerecht geladene regionale Daten und eine austauschbare Kartenansicht. Neue Kommunen benötigen Register-, Tarif- und Geometriedaten sowie Referenzfälle; neue Abrechnungsregeln können zusätzliche Berechnungslogik erfordern.

**Nächstes Arbeitspaket:** Kommunenregister und AGS-Zuordnung einführen, die feste Zwölferprüfung ablösen und Modellfamilie sowie Höchsttarifprofil getrennt prüfen. Darauf folgen die TypeScript-Berechnung, die eigenständige Website mit Formular/Karte/Liste/Details und die Vorbereitung der statischen Bereitstellung.
