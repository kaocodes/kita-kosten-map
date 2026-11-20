# Webanwendung und Geodaten

**Stand:** 20. November 2026

Die Anwendung besteht aus statischen Dateien. React und Leaflet stellen die Oberfläche dar. Der TypeScript-Rechenkern wertet die Tarifdaten im Browser aus. Python und Node.js werden zur Entwicklung, Prüfung und Aufbereitung benötigt.

## 1. Lokal starten

Voraussetzungen sind Node.js ab 22.12 und Python ab 3.11. Im Projektverzeichnis einmal `npm ci` ausführen.

| Befehl | Adresse | Umfang |
|---|---|---|
| `npm run dev` | [localhost:5173](http://127.0.0.1:5173/) | Regulärer Stand mit 20 Vergleichskommunen und 120 Kontextflächen. |
| `npm run dev:expansion` | [localhost:5174](http://127.0.0.1:5174/) | Lokale Vorschau mit 49 Vergleichskommunen und 91 Kontextflächen. |
| `npm run build:pages`, danach `npm run preview` | [localhost:4173](http://127.0.0.1:4173/) | Vorschau des GitHub-Pages-Builds mit 49 freigegebenen Kommunen in `dist/`. |

Die Server lassen sich mit `Ctrl+C` beenden. Der reguläre Start prüft Freigabe, Kataloge und Quellenprüfsummen und schreibt die Webdaten in `web/public/data/`. Die Erweiterungsvorschau lädt eigene Daten aus `build/expansion-preview/` über Vite. Sie ist unabhängig vom statischen Build.

## 2. Bedienung und Anzeige

- Die Karte lässt sich zoomen, verschieben und über „Region anzeigen“ zentrieren. Namen werden anhand des Platzes bei der jeweiligen Zoomstufe positioniert und bei Überlagerung ausgeblendet. Die gewählte Kommune erhält Vorrang. Gemeindegrenzen bleiben fokussierbar und auswählbar.
- Kommunendetails stehen direkt unter der Karte oder unter dem gewählten Listeneintrag. Kinderdetails sind aufklappbar. Sie zeigen unter anderem den Beitrag, die Beitragsmonate, die tatsächlichen Wochenstunden und Verpflegung. Quellen sind verlinkt.
- Eine klare graue Darstellung kennzeichnet fehlende Vergleichswerte. Im voreingestellten Modell liefert die Vorschau 48 Preise. Baltmannsweiler hat für U3 mit acht Stunden kein passendes Stundenpaket.
- Familienkarte und Vergleichsfamilie steuern dieselben Werte auf Karte, Liste und in den Details. „Eigene Familie“ und der Höchsttarif-Reiter sind als frühere Ansichten im Code bzw. als internes Referenzprofil erhalten. [Modellfamilien](MODELLFAMILIEN.md)

## 3. Aufbau und Datenfluss

| Datei | Aufgabe |
|---|---|
| `data/municipality_registry.json` | Aktive Kommunen, amtliche Gemeindeschlüssel (AGS), Zuordnung zu Tarifen und Flächen. |
| `scripts/prepare_web_data.mjs` | Aufbereitung von Geometrie, Tarifen, Profilen und Quellenindex für den jeweiligen Modus. |
| `web/src/App.tsx` | Gemeinsame Modellauswahl und Berechnung für Karte, Liste und Details. |
| `web/src/components/MunicipalityMap.tsx` | Leaflet-Karte, Flächenauswahl und Beschriftung. |
| `web/src/domain/` | Datenprüfung, Angebotsauswahl nach Wochenzielen und Vergleichsberechnung. |

Das kanonische Register liefert 20 Tarife für den Basisbuild `npm run build`. Vorschau und Pages-Build ergänzen die Einträge aus beiden Erweiterungsmanifesten und prüfen die Katalogprüfsummen. Der Pages-Build prüft zusätzlich die freigegebenen Manifeststände. Abrufe von Gebührenquellen finden im Erhebungsprozess statt. Der Browser erhält aufbereitete Daten und Quellenlinks. [Datenpipeline](DATENPIPELINE.md)

## 4. Geodaten und Herkunft

Ausgangspunkt ist der archivierte regionale WFS-Abruf unter `output/municipalities-original.geojson` mit 140 Geometrien. Seine Prüfsumme bleibt über das Kommunenregister gesichert. Die [BKG-Produktseite](https://gdz.bkg.bund.de/index.php/default/open-data/wfs-verwaltungsgebiete-1-250-000-stand-01-01-wfs-vg250.html) nennt den **Grenzstand 1. Januar 2025**; sie wurde am 8. November 2026 unter `data/geodata/bkg-product-page.html` archiviert. `data/geodata/source.json` hält Quelle, Fundstelle, Grenzstand, Abrufdaten, Hashwerte, ursprüngliche WFS-Parameter, Lizenz und Verarbeitung fest. Der Geometrieabruf am 7. November 2026 und der fachliche Grenzstand sind getrennte Angaben.

Die Verarbeitung läuft mit `npm run prepare:web` vollständig lokal:

1. Kanonische Tarife, Register und Quellenarchive prüfen.
2. Hashwerte der originalen Geometrie und der BKG-Produktseite kontrollieren.
3. Alle 140 Nachbargemeinden gemeinsam mit Mapshaper vereinfachen: gewichtetes Visvalingam-Verfahren, 30 % Punktbeibehaltung, `keep-shapes`, Koordinatenpräzision `0.00001` Grad.
4. Attribute reduzieren und aktive Vergleichsgebiete anhand des AGS zuordnen. Namensgleichheit wird nicht zur Verknüpfung verwendet.
5. Interne Flächen- und Kommune-IDs ergänzen; Beschriftungspunkte innerhalb der größten Polygonteile bestimmen.
6. Browserdaten, Größen-/Hashbericht und verwendete Laufzeit-Lizenztexte schreiben.

Gemeinsame Grenzen werden zusammen verarbeitet. Prüfungen sichern insbesondere die erhaltenen Gemeindefeatures, geschlossenen Ringe und gemeinsam genutzten Grenzen zwischen bekannten Nachbarn. Die ursprünglichen 18.350 Koordinatenpunkte werden auf 6.240 reduziert. Die Karte dient der regionalen Übersicht; die maximale Zoomstufe ist **11**, die minimale **8**. Die Beschriftung vermeidet Überlagerungen; jede Kommune bleibt zusätzlich in der Liste und als fokussierbare Fläche erreichbar.

Quellenvermerk und Änderungshinweis stehen direkt in der Karte und ausführlich im Fußbereich: **© BKG 2026, dl-de/by-2-0, Grenzen vereinfacht**. BKG, Lizenz, Datenprodukt und die Aufstellung der Datenquellen sind verlinkt. Die Lizenztexte von React, React DOM, Leaflet und Zod werden unter `THIRD_PARTY_NOTICES.txt` mit ausgeliefert. Die Anwendung verwendet lokale Schriftarten und keine externen Kartenkacheln.

## 5. Browserdaten und Größenbudget

Die zwei Browserdateien heißen `region-stuttgart.json` und `municipalities.geojson`. Der Katalog erhält ausführbare Angebote, Preise, Modellprofile und Quellenfundstellen. Umfangreiche Originaltranskriptionen und nicht ausführbare Regelparameter bleiben im Archiv. Die Vorschau beschränkt Angebote und Preise zusätzlich auf den Vergleichsstichtag. Erhebungsdaten sowie Datenblatt und Kartenprofil können unterschiedliche Zeitpunkte festhalten.

| Modus | Katalog unkomprimiert | Geometrie unkomprimiert | Beide Dateien gzip | Höchstwerte für Katalog und gzip-Summe |
|---|---:|---:|---:|---:|
| Regulärer Build | rund 1,52 MB | rund 133 kB | rund 105 kB | 2 MB und 150 kB |
| Erweiterungsvorschau und Pages | rund 2,27 MB | rund 134 kB | rund 180 kB | 2,3 MB und 185 kB |

Die Geometrie hat in beiden Modi ein Limit von 200 kB. Die Werte betreffen die Datenressourcen. Messwerte und Prüfsummen stehen in der jeweils erzeugten `build-metrics.json`.

## 6. Prüfen und veröffentlichen

```bash
python3 -m unittest discover -s tests
npm test
npm run test:expansion
npm run build:pages
npm run test:pages
```

`npm test` prüft Rechenkern, Python-Referenzfälle und reguläre Webdaten. `npm run test:expansion` prüft die Vorschaugeometrie und die Zuordnung der Kataloge, Modellwerte und erwartete Lücken. Bei UI-Änderungen auf Desktop und schmalen Ansichten zusätzlich Kartenauswahl, Familienwechsel, Listen- und Kinderdetails sowie Tastaturbedienung prüfen.

Vite baut mit relativer Basis `./` und legt die statischen Dateien in `dist/` ab. Der [Pages-Workflow](../.github/workflows/pages.yml) prüft Pull Requests gegen `main` und veröffentlicht erfolgreiche Builds von `main`. Der manuelle Workflow-Aufruf verwendet dieselben Prüfungen. Der Build für GitHub Pages ergänzt das kanonische Register aus der [Freigabedatei](../data/expansion/pages_release.json). Vor dem Upload prüft `npm run test:pages` die veröffentlichten Dateien unter `dist/data/`.

Frühere Bildschirmaufnahmen dienen als Referenz für [Paket 3](../output/website-preview-desktop.jpg) und [Paket 4 mit dem persönlichen Formular](../output/website-family-form-desktop.jpg).
