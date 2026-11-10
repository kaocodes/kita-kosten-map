# Lokale Webanwendung und Geodaten

**Stand:** 8. November 2026 · **Umsetzungspaket:** Modellfamilien

Es gibt eine eigenständige React-Anwendung mit Leaflet-Karte. Sie stellt die zwölf Vergleichskommunen als Gebührenflächen dar und verwendet den geprüften TypeScript-Rechenkern. Die Anwendung läuft vollständig mit statischen Dateien; ein Backend wird nicht benötigt. Die Veröffentlichung auf GitHub Pages erfolgt über den Workflow `.github/workflows/pages.yml`.

## Familienatlas: lokaler Stand zur Durchsicht

Auf `codex/ui-redesign` ist das Familienatlas-Layout lokal umgesetzt: große Gemeindekarte mit dauerhaft sichtbaren Namen aller zwölf Vergleichskommunen, verschiebbarer und zentrierbarer Leaflet-Ansicht, Punktemuster im Hintergrund und Auswahlkontur über den Gebieten. Vollständige Kommuneninformationen stehen unter der Karte und nach Auswahl direkt in der absteigenden Liste. Kinderdetails sind aufklappbar und enthalten Verpflegung und Zusatzkosten direkt. Familienkarten öffnen den echten Konfigurator mit 1–4 Kindern oder setzen auf die Modellfamilie zurück. Die Überschrift wechselt aktive Kommunennamen auf einem lila Balken; der Wechsel ist pausierbar und berücksichtigt reduzierte Bewegung. Die Familienkarten tragen plakative Schriftbalken, die Methodik steht kompakt ohne Verpflegungsblock oder Bilder direkt auf dem Hintergrund. Familienillustrationen, Kopfsymbol und Schrift werden lokal mitgeliefert. Details und Prüfstand: [UI_REDESIGN.md](UI_REDESIGN.md). Dieser Stand wurde noch nicht auf GitHub Pages veröffentlicht.

## 1. Lokal starten

Benötigt werden Node.js **ab 22.12**, npm und Python **ab 3.11** für Datenprüfung und Vorbereitung. Nach der Installation der npm-Pakete werden beim Start keine externen Geodienste oder Gebührenquellen abgerufen.

```bash
npm ci
npm run dev
```

Die lokale Website erscheint unter **http://127.0.0.1:5173/**. Der Start prüft zuerst die kanonischen Daten und Quellenprüfsummen und erzeugt die Browserdaten. Port 5173 ist fest eingestellt; ein bereits belegter Port wird ausdrücklich gemeldet.

Für den fertigen statischen Build:

```bash
npm run build
npm run preview
```

Die Build-Vorschau läuft unter **http://127.0.0.1:4173/**. `dist/` enthält die veröffentlichbaren Dateien. Die Server können im jeweiligen Terminal mit `Ctrl+C` beendet werden. Python und Node.js sind Werkzeuge für Vorbereitung, Entwicklung und Build; die ausgelieferte Anwendung benötigt sie nicht.

## 2. Sichtbare Funktionen

- Gemeindekarte mit zwölf auswählbaren Gebührenflächen und 128 umliegenden Gemeindegebieten als räumlichem Kontext.
- Modellfamilien-Konfigurator mit Haushaltskonstellation, Kinderkategorien, sechs Einkommensszenarien und 6/8 Stunden täglich je Kita-Kind. Karte, Liste und Details verwenden dieselbe Familiensumme. „Eigene Familie“ und der separate Höchsttarif-Reiter sind ausgeblendet.
- Monatsäquivalent, ursprünglicher Monatsbeitrag, Beitragsmonate, gebuchte Wochenstunden, zusätzliche Buchungszeit und Tarifbeginn je Kommune.
- Verpflegung und Zusatzkosten als gesonderte Varianten; fehlende Beitragsmonate bleiben ausdrücklich unbekannt.
- Direkte Links zu offiziellen Gebührenquellen und aufklappbare Fundstellen.
- Feste Gebührenlegende, Zoom, Verschieben und Zurücksetzen auf die gesamte Vergleichsregion.
- Gemeindewahl per Maus, Tastatur oder Liste; auf schmalen Bildschirmen stehen Karte und Details untereinander. Die Detailansicht wird bei der Auswahl erreicht.

### Persönliches Profil (Paket 4, vorerst deaktiviert)

**Aktuelle Entscheidung vom 8. November 2026:** „Eigene Familie“ wird nicht mehr angeboten. Die frühere Oberfläche liegt in `web/src/LegacyProfileApp.tsx` mit `FEATURES.personalProfiles: false`; sie wird von der aktiven Anwendung nicht importiert. Formular, Integration, Rechenkern und alle Tests bleiben erhalten. Die folgende Beschreibung dokumentiert das deaktivierte Verhalten. Eine spätere Reaktivierung benötigt eine fachliche Prüfung der örtlichen Einkommensdefinitionen und bekannten Sonderregeln; der Schalter allein ist keine fachliche Freigabe.

Die vereinbarte Modellkonfiguration ist umgesetzt; verbindliche Beschreibung und Einschränkungen stehen in [MODELLFAMILIEN.md](MODELLFAMILIEN.md): Haushaltskonstellation, Kinderzahl, je Kind Krippe/Kindergarten/Schulkind/zu Hause betreut, sechs Haushaltseinkommen (40.000/60.000/80.000/100.000/140.000/180.000 € jährlich) und je betreutem Kind 6 oder 8 Stunden täglich. Die Karte soll die vollständigen Betreuungskosten aller betreuten Kinder zeigen. Örtliche Einkommensannahmen sind offengelegt; ungeklärte Geschwisterzuordnungen ergeben keine geschätzte Gesamtsumme. Der bisherige Standard bleibt vorbelegt.

Der separate Höchsttarif-Reiter ist ebenfalls über `FEATURES.highestBandReference: false` ausgeblendet. Ist keine zusätzliche Profilansicht aktiv, entfällt der gesamte Profilumschalter. Referenzdatei, Browserkatalog, Exporte, Berechnung und Tests des Höchsttarifs bleiben erhalten. Ein hohes Bruttoszenario entspricht nicht zwangsläufig in jeder Gemeinde dem Höchsttarif; die tatsächliche Abdeckung muss anhand der örtlichen Modellwerte geprüft werden.

„Eigene Familie“ übernimmt zunächst Familienstruktur und Betreuungszeiten der Modellfamilie. Einkommen, Betreuungsrang, Pässe, Ermäßigungen und deren Bestätigungen bleiben leer. Ein Wechsel zu einer Referenz und zurück erhält die persönlichen Eingaben innerhalb dieses Browserfensters. „Modellfamilie wiederherstellen“ setzt den persönlichen Entwurf zurück und aktiviert die Referenz. Neuladen verwirft persönliche Eingaben; es gibt keine Speicherung in URL, Local Storage oder Backend.

Erfasst werden alle Haushaltskinder mit Alter in Jahren/Monaten, Haushaltszugehörigkeit und Kindergeldberechtigung, das Vergleichskind, Einschulung, Haushaltskonstellation, täglicher durchgehender Betreuungsbedarf und der gesonderte Sindelfinger Betreuungsrang. Bei genau 36 Monaten wird für Städte mit Tarifwechsel im Folgemonat der Geburtstagsmonat abgefragt. Die drei Haushaltsoptionen unterscheiden zusammenlebende Eltern, Alleinerziehende und getrennt lebende, nicht alleinerziehende Eltern. Relevante Einkünfte und Haushaltszugehörigkeit müssen nach örtlicher Regel selbst angegeben werden. Beim Wechsel des Vergleichskindes werden Betreuungsrang und Einschulungsangabe zurückgesetzt.

Ditzinger steuerliches Vorjahreseinkommen, Esslinger örtliches Familienbrutto des laufenden Jahres, Korntaler bereinigtes steuerliches Vorjahreseinkommen und allgemeines Haushaltsbrutto sind unabhängige Felder. Der Tarifstichtag bleibt der geprüfte 4. November 2026. Ein bestätigter Abzug in Esslingen ist vor Eingabe selbst zu berücksichtigen; die Anwendung schätzt weder Steuern noch Pauschbeträge. Deutsche Geldbeträge wie `80.000,01` werden exakt in Cent gelesen. Leer bedeutet unbekannt, `0` einen ausdrücklich angegebenen Nullbetrag.

Örtliche Pässe und ausführbare Ermäßigungen werden aus den aktiven Tarifkatalogen angeboten. Jede erforderliche Berechtigung muss ausdrücklich bestätigt werden. Fellbacher und Gerlinger Ermäßigungseinkommen werden separat erfasst. Änderungen an Pass oder Regelauswahl löschen bisherige Bestätigungen. Angaben gelten nur für die gewählte Kommune; Einkommensgrenzen begründen keine automatische Berechtigung.

Fehlende Einkommen lassen die übrigen Kommunen berechenbar. Ungültige Beträge, Altersangaben oder Zeiten entfernen dagegen alle vorherigen Preise, Pakete, Zusatzkosten und Rechenspuren. Inline-Fehler und eine Fehlerübersicht verweisen auf die Eingaben; Gemeindedetails bieten Links zu fehlenden Einkommen bzw. Betreuungsrang. Nicht berechenbare Ergebnisse bleiben grau. Quellen sind auch dann erreichbar. Formular und Ergebnisübersicht sind per Anker verbunden; das gesamte Formular lässt sich einklappen. Die Gemeindewahl bleibt bei Ergebnisänderungen stabil, und eine Auswahl aus Karte oder Liste setzt den Fokus auf die Detailüberschrift.

Die Referenzprofile bleiben unverändert. Historien, freie Tarifstichtage, Schulkinder und nicht im Rechenkern ausführbare Sonderregelungen sind weiterhin nicht Bestandteil der persönlichen Berechnung.

## 3. Dateien und Architektur

| Bereich | Zweck |
|---|---|
| `web/index.html`, `web/src/main.tsx` | Einstieg und React-Start |
| `web/src/App.tsx`, `web/src/App.module.css` | Gemeinsamer Profil-/Auswahlzustand, Oberfläche und responsives Layout |
| `web/src/components/MunicipalityMap.tsx` | Leaflet-Anbindung für Geometrie, Farben und Gemeindewahl |
| `web/src/components/MunicipalityDetails.tsx` | Originalbeitrag, Zusatzkosten und Quellen |
| `web/src/site/data.ts` | Laden der erzeugten lokalen JSON-Dateien und Prüfung ihrer geografischen Zuordnung |
| `web/src/components/ModelConfigurator.tsx`, `web/src/domain/model-family.ts`, `data/models/configuration.json` | Aktiver Modellkonfigurator, Familienberechnung und zentrale Szenarien |
| `web/src/components/FamilyForm.tsx`, `web/src/site/personal-profile.ts` | Formular, exakte Textauswertung und sichere persönliche Profile |
| `web/src/site/presentation.ts` | Deutsche Formatierung und Gebührenklassen |
| `web/src/domain/` | Unabhängiger Rechenkern aus Paket 2 |
| `scripts/prepare_web_data.mjs` | Reproduzierbare Vorbereitung von Browserkatalog, Geometrie, Quellenindex und Lizenztexten |
| `data/geodata/` | Archivierte BKG-Produktseite und dauerhaft belegte Herkunft der Geometrien |
| `web/public/data/`, `dist/` | Erzeugte Dateien; werden nicht versioniert |

Verwendete Pakete sind React und React DOM **19.3.1**, Vite **8.3.6**, Leaflet **1.9.4**, Mapshaper **0.7.101**, TypeScript **7.0.2** und Zod **4.6.7**. CSS Modules sind in den Build integriert. Exakte Versionen und Abhängigkeiten stehen im Lockfile. Mapshaper und Vite sind Entwicklungswerkzeuge und werden nicht als Bibliotheken in den Browser geladen.

Die Oberfläche erhält weder eine eigene feste Kommunenliste noch eine zweite Berechnungsimplementierung. Das Register bestimmt die aktiven Kommunen; AGS und `area_id` verbinden sie mit den Geometrien, `tariff_id` mit den Gebühren. Die Map-Komponente erhält nur Geometrie, Ergebnisse und Auswahl. Sie kann später ausgetauscht werden, ohne die Tariflogik zu ändern.

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

`web/public/data/region-stuttgart.json` enthält die benötigten aktiven Tarifkataloge, Register, beide Profile, örtliche Regeln und einen Quellenindex. Verbatim-Recherchetexte (`original_research`) sowie Kopien der Originalzellen innerhalb von Quellenbelegen (`evidence.original`) werden ausschließlich in diesem abgeleiteten Browserexport weggelassen. Originaldaten und Quellenarchive bleiben vollständig erhalten. Quellenkennung, URL, Fundstelle, Tarifdaten und Rechenregeln bleiben verfügbar. Prüfungen vergleichen die Beträge, Pakete, Zusatzkosten und Quellenfundstellen beider Profile mit den kanonischen Katalogen.

Messstand dieser Umsetzung:

| Bestandteil | Unkomprimiert | Mit gzip |
|---|---:|---:|
| Ursprünglicher regionaler Geometrieabruf | 391.188 Byte | – |
| Vereinfachte Webgeometrie mit Zuordnung | 132.114 Byte | 28.358 Byte |
| Browserkatalog, Profile und Quellenindex | rund 1,12 MB | rund 48 kB |
| JavaScript-Bundle | rund 510 kB | rund 154 kB |
| CSS-Bundle | rund 37 kB | rund 11 kB |

Die frühere Oberfläche einschließlich des persönlichen Formulars wird von der aktiven Anwendung nicht importiert und nicht in deren Produktionsbundle aufgenommen. Der Haupt-Build liegt knapp über der Vite-Hinweisschwelle von 500 kB unkomprimiert; die Datenbudgets bleiben erfüllt.

Die rechnerische gzip-Summe aus HTML, CSS, JavaScript, Geometrie und Browserkatalog liegt bei ungefähr **240 kB**. Tatsächlicher Transfer und Ladezeit hängen von Serverkomprimierung, Verbindung und Cache ab. Die lokale einfache HTTP-Vorschau liefert Dateien unkomprimiert aus. Quellen-PDFs und das vollständige Forschungsarchiv gehören nicht zum Website-Build.

Das Vorverarbeitungsskript prüft feste Ausgangsbudgets: höchstens **200 kB** Webgeometrie, **1,5 MB** Browserkatalog und zusammen höchstens **150 kB gzip** für die beiden Datenressourcen. Die aktuellen Werte und Hashes werden unter `web/public/data/build-metrics.json` neu erzeugt. Größere Erweiterungen können eine regionale Aufteilung erfordern; die Grenzen werden dann bewusst überprüft.

## 6. Prüfung und statische Bereitstellung

```bash
npm test
npm run typecheck
npm run build
python3 -m unittest discover -s tests
```

`npm test` bereitet die Webdaten vor und führt **151 JavaScript-Prüfungen** aus: die bisherigen 113 Rechenkern-/Paritätsprüfungen sowie acht Prüfungen für die Website-Daten und Darstellungskonventionen und dreizehn für persönliche Profile, exakte Eingaben, Fehlerzustände und örtliche Ermäßigungen sowie siebzehn für Modellfamilien und Familiengesamtkosten. Die Python-Suite umfasst 70 Tests. Die acht zusätzlichen Prüfungen decken Register-/Geometriezuordnung, Umgebungskontext, Polygone, gemeinsame Grenzen, unveränderte Vergleichswerte, Herkunft, Datenbudgets und die Unterscheidung von null Euro gegenüber fehlenden Werten ab. Sie lassen sich auch eigenständig mit `npm run test:web` ausführen.

Im Browser wurden Desktop sowie 390 und 320 Pixel Breite geprüft. Profilwechsel, Flächenwahl, Tastaturwahl, Zusatzkosten und die schmale Darstellung funktionieren. Ein bei 320 Pixeln beobachteter horizontaler Überlauf wurde behoben. Der fertige Build wurde zusätzlich durch einen einfachen statischen HTTP-Server unter `/kita-costs-map/` geladen; Karte, Daten, Profile und lokale Lizenzverweise funktionieren auch dort. Paket 4 ergänzt Browserprüfungen für leere und fehlerhafte Einkommen, bestätigte und unbestätigte Pässe/Sozialermäßigungen, Kindergartenkinder mit Geschwistern, abweichende Tageszeiten, Profilwechsel, Zurücksetzen, Einklappen und Auswahl per Tastatur. Bei 390 und 320 Pixeln bleibt auch das Formular ohne horizontalen Überlauf. Die Prüfung ist keine formale WCAG-Zertifizierung.

Gesicherte Formularansichten aus Paket 4: [Desktop](../output/website-family-form-desktop.jpg) und [Mobil](../output/website-family-form-mobile.jpg). Die Eingaben in den Bildern sind synthetische Prüfdaten.

Gesicherte Ansichten der tatsächlichen Anwendung aus Paket 3: [Desktop](../output/website-preview-desktop.jpg) und [Mobil](../output/website-preview-mobile.jpg). Die Bilder zeigen das Modellfamilienprofil; die älteren Entwürfe in `output/` bleiben separat erhalten.

`vite.config.ts` verwendet `base: "./"`. Die Anwendung hat keine serverseitigen Routen; interne Verweise sind Seitenanker. Dadurch funktionieren die gebauten Dateien im Stammverzeichnis und in einem GitHub-Pages-Projektverzeichnis. Der Pages-Workflow ist eingerichtet; die Zieladresse lautet https://kaocodes.github.io/kita-kosten-map/.

Technische Referenzen: [Vite und GitHub Pages](https://vite.dev/guide/static-deploy.html), [Leaflet und GeoJSON](https://leafletjs.com/examples/geojson/), [Mapshaper-Schnittstelle](https://mapshaper.org/docs/guides/programmatic.html), [Mapshaper-Vereinfachung](https://mapshaper.org/docs/guides/simplification.html).

## 7. Veröffentlichung über GitHub Actions

Der Workflow unter `.github/workflows/pages.yml` läuft bei Pushes nach `main`, Pull Requests gegen `main` und auf manuellen Aufruf. Unter Ubuntu 24.04 mit Node.js 22 und Python 3.11 werden `npm ci`, die Python-Tests, `npm test` und `npm run build` ausgeführt. Nur erfolgreiche Builds von `main` werden als Pages-Artefakt hochgeladen und veröffentlicht. Der Deployment-Schritt hat ausschließlich die erforderlichen Pages-/OIDC-Schreibrechte; der Build erhält nur Lesezugriff auf das Repository. Action-Versionen sind auf geprüfte Commit-SHAs festgelegt.

GitHub Pages verwendet den Build-Typ `workflow`. Die relative Vite-Basis bleibt erhalten und ist für das Projektverzeichnis geprüft. Der aktuelle Veröffentlichungsstand und mögliche Fehler stehen in den GitHub-Actions-Läufen. Nach einem erfolgreichen neuen Push aktualisiert sich die Website automatisch; die fachliche Pflege und Freigabe neuer Tarife bleibt erforderlich.
