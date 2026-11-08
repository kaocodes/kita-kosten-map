# Website: Architektur, Karte und Bedienung

**Stand:** 8. November 2026  
**Status:** Pakete 1 bis 4 umgesetzt: Register, Profile, TypeScript-Rechenkern und lokal aufrufbare React-/Leaflet-Website. Pages-Veröffentlichung ist automatisiert. Das individuelle Formular bleibt im Code erhalten, ist aber vorerst ausgeblendet; leicht konfigurierbare Modellfamilien sollen die Hauptbedienung bilden.

Dieses Dokument bündelt die technische Beratung, die gezeigten Entwürfe und die daraus getroffenen Entscheidungen. Die fachlichen Anforderungen stehen in [PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md), die verbindliche Berechnung in [DATENMODELL.md](DATENMODELL.md) und das Referenzprofil in [STANDARDVERGLEICH.md](STANDARDVERGLEICH.md).

## 1. Entscheidungen und Verbindlichkeit

| Thema | Stand |
|---|---|
| Hauptdarstellung der Gebühren | **Beschlossen am 8. November 2026:** eingefärbte Gemeinde- bzw. Stadtflächen. Die Entscheidung fiel nach dem direkten Vergleich mit proportionalen Kreisen. |
| Hosting und Betrieb | **Umgesetzt:** statische Website auf GitHub Pages unter https://kaocodes.github.io/kita-kosten-map/. Das öffentliche Repository ist `kaocodes/kita-kosten-map`; GitHub Actions prüft, baut und veröffentlicht erfolgreiche Änderungen von `main`. |
| Backend | Für die vorgeschlagene erste Website nicht erforderlich. Ein Backend bleibt eine spätere Option bei tatsächlichem Bedarf, beispielsweise einer Redaktionsoberfläche. |
| Datenbasis und Standardprofil | Kommunenregister und AGS-Zuordnung sind umgesetzt. Die Modellfamilie ist der Standard in Python und den aktuellen Exporten; die Höchsttarifreferenz bleibt separat erhalten. Das Browserformular folgt. |
| Frontend und Kartenbibliothek | React 19.3.1, Vite 8.3.6, CSS Modules und Leaflet 1.9.4 sind in Paket 3 umgesetzt; der unabhängige TypeScript-Rechenkern und Zod bleiben die Berechnungsgrundlage. |
| Grenzdaten | BKG VG250 mit Grenzstand 01.01.2025 sind für die regionale Webkarte übernommen. Quelle, Abruf, Lizenz und Hashwerte sind unter `data/geodata/` gesichert; die Verarbeitung ist reproduzierbar. |
| Gestaltung und weitere Bedienfunktionen | Die unten beschriebenen Funktionen und Farben sind Vorschläge. Die Auswahl der Gemeindeflächen bestätigt nicht automatisch sämtliche Einzelheiten der Entwürfe. |

Die früheren konkreten Technikvorgaben in `PROJECT_REQUIREMENTS_LEGACY.md` bleiben historische Planung und werden durch diese Beratung nicht nachträglich verbindlich.

## 2. Empfohlener Stack

| Baustein | Empfehlung und Zweck |
|---|---|
| Oberfläche | **React + TypeScript:** gemeinsame Zustände für Karte, Filter, Liste und Gemeindedetails. |
| Entwicklung und Build | **Vite:** erzeugt die statisch auslieferbaren Dateien. |
| Gestaltung | **CSS Modules:** überschaubare komponentenbezogene Styles für Desktop und Mobilgeräte. |
| Karte | **Leaflet:** interaktive Polygone, Zoomen, Verschieben, Auswahl und Gebührenfarben. |
| Kartengeometrie | Zunächst **GeoJSON**; **TopoJSON** als mögliche zusätzliche Größenoptimierung. |
| Gebühren | Vorhandene kanonische JSON-Daten und daraus erzeugte Exporte in `data/exports/`. |
| Zusätzliche Frontend-Prüfung | **Zod** für Benutzereingaben. Das kanonische JSON-Schema bleibt Grundlage der Tarifdaten; dessen Definitionen werden nicht unabhängig und widersprüchlich in einem zweiten Schema gepflegt. |
| Quellen und Berechnung | Bestehende Python-Werkzeuge einschließlich `scripts/fetch_sources.py` und `kita_costs` weiterverwenden. |
| Hosting | **GitHub Pages**, ohne eigenen Anwendungs- oder Kartenserver. |

Ein Framework mit Serverbetrieb oder eine Datenbank sind für die erste Version nicht notwendig. Paketversionen und Entwicklungsabhängigkeiten sind im npm-Lockfile festgehalten. Die laufende Architektur und Startbefehle stehen in [WEBANWENDUNG.md](WEBANWENDUNG.md).

## 3. Datenfluss und Betrieb ohne Backend

```text
Offizielle Gebührenquellen
  → lokale Quellenkopien und strukturierte Tarife
  → Python-Validierung und Vergleichsberechnung
  → geprüfte JSON-Exporte
  → statischer Website-Build
  → GitHub Pages

Offizielle Grenzdaten
  → räumliche Auswahl, Vereinfachung und Attributreduktion
  → lokale Geometriedatei
  → statischer Website-Build
```

Der Browser lädt nur die für die Darstellung benötigten Exporte und Geometrien. Das Quellenarchiv und der vollständige Ausgangsdatensatz müssen nicht Teil der Website sein. Die großen Grenzdaten werden vor der Veröffentlichung verarbeitet, nicht bei jedem Seitenaufruf.

Der bestehende Höchsttarifvergleich lässt sich vollständig vorberechnen. Die frei einstellbaren Familienprofile benötigen zusätzlich eine Auswertung der Tarifregeln im Browser. Dafür ist seit Paket 2 eine von React und Leaflet unabhängige TypeScript-Berechnung mit Zod-Eingabeprüfung umgesetzt. 104 gemeinsame Szenarien stimmen mit Python überein; der Vergleich umfasst vollständige Ergebnisse einschließlich Quellen, Zusatzkosten und Fehlerzuständen. Python bleibt die Referenz für Datenprüfung und Export. Schnittstelle und Grenzen stehen in [BROWSERBERECHNUNG.md](BROWSERBERECHNUNG.md). Vorberechnete Ergebnisse können den Start der Website ergänzen; sie ersetzen die Auswertung individueller Eingaben nicht.

Geplante Gebührenaktualisierung: neue Quellenkopie sichern, JSON-Tarife prüfen und ergänzen, bestehende Validierung und Tests ausführen, Exporte erzeugen, Website neu bauen und veröffentlichen. Die automatische Veröffentlichung über GitHub Actions ist eingerichtet. Fachlicher Aktualisierungsrhythmus und Zuständigkeiten bleiben festzulegen.

### 3.1 Erweiterbarkeit auf weitere Kommunen und Bezirke

Die Stackbewertung vom 8. November 2026 bestätigt React, TypeScript, Vite, CSS Modules, Leaflet und statische JSON-Daten als passende Arbeitsgrundlage auch für weitere Kommunen. Mehr Vergleichsgebiete allein erfordern kein Backend. Für die Umsetzung gelten folgende Architekturregeln:

1. **Kommunenregister:** Aktive Kommunen, stabile Kennungen, amtliche Namen, AGS, Geometrie- und Tarifverweise werden zentral als Daten geführt. `data/municipality_registry.json` ist umgesetzt; Vergleich, Export und Vollständigkeitsprüfung lesen dieses Register. Die feste Prüfung auf zwölf Kommunen wurde durch den Abgleich mit registrierten aktiven Kommunen ersetzt. Auch die spätere Oberfläche liest das Register.
2. **Gebiet und Gebührenordnung:** Eine Kartenfläche bekommt eine eigene stabile Gebietskennung. Für Gemeinden wird der AGS gepflegt; Stadtbezirke erhalten eigene Kennungen und eine Referenz auf die übergeordnete Kommune. Mehrere Flächen können dieselbe Gebührenordnung verwenden. Eine neue Bezirksgeometrie begründet keinen neuen Tarif und keine Tarifkopie.
3. **Eigenständige Tarifberechnung:** Datenzugriff, lokale Tarifregeln und Berechnung bleiben unabhängig von Karte und Formular. Neue Kommunen mit bereits unterstützten Regeln werden über Daten, Geometriezuordnung und Referenzfälle ergänzt. Neue Abrechnungsregeln erfordern gegebenenfalls eine Erweiterung und Prüfung beider Berechnungen; die bestehende Python-Logik enthält noch kommunenspezifische Sonderfälle.
4. **Bedarfsgerechtes Laden:** Zunächst werden die benötigten Daten der zwölf Kommunen ausgeliefert. Bei wachsendem Umfang können Tarif- und Geometriedateien nach Region aufgeteilt und bei Bedarf nachgeladen werden. Das vollständige Quellenarchiv gehört nicht in den initialen Website-Download. Dateigrößen, Grenzpunkte, Ladezeit und Bedienung auf Mobilgeräten werden gemessen.
5. **Austauschbare Kartenansicht:** React erhält Kommune und Ergebnis aus dem gemeinsamen Zustand; Leaflet übernimmt die Darstellung und Auswahl. Eine spätere andere Darstellungstechnik soll Tarifdaten und Rechenlogik weiterverwenden können. Canvas, andere Geometriedateien oder ein anderer Renderer werden erst bei gemessenen Engpässen bewertet.

Ein Erweiterungsvorgang besteht damit aus Registereintrag, belegten Tarifdaten, passender Geometrie, Quellen- und Lizenzangaben, fachlichen Prüffällen und einem neuen statischen Build. Eine Grenze für die Anzahl unterstützter Kommunen wird nicht in Komponenten eingebaut. Neue Kommunen dürfen bestehende Tarife und regionale Vergleichsprofile nicht verändern.

## 4. Gemeindegrenzen und Zeichnung

Eine Gemeinde wird als **Polygon** gespeichert: Koordinaten beschreiben einen geschlossenen Außenring und gegebenenfalls Innenringe. Bei getrennten Gebietsteilen wird ein **MultiPolygon** verwendet. Die Daten repräsentieren Stadt- bzw. Gemeindegebiete, keine einzelnen Kita-Standorte.

Gebogene Grenzen werden durch ausreichend viele kurze Liniensegmente angenähert. Individuell gezeichnete Bézierkurven sind nicht erforderlich. Leaflet projiziert geografische Koordinaten auf Bildschirmpositionen und zeichnet daraus interaktive Flächen, beispielsweise mit SVG.

Für die produktive Verbindung zwischen Gebühren und Geometrie ist der **amtliche Gemeindeschlüssel (AGS)** vorgesehen. Stabile interne Kommune-IDs bleiben erhalten; ihre Zuordnung zu den AGS ist seit Paket 1 im Register gepflegt und gegen die archivierten BKG-Daten geprüft. Die alten visuellen Entwürfe verbinden ihre eingebetteten Daten weiterhin über die damals geprüften amtlichen Namen; die neue Website übernimmt die Registerzuordnung.

Die Karte kann aus zwei getrennten Ebenen bestehen:

- **Gemeindeflächen:** lokale Geometrien, Gebührenfarben und Auswahl.
- **Optionale Hintergrundkarte:** beispielsweise Straßen, Flüsse oder Ortsnamen zur Orientierung.

Die Gemeindeflächen funktionieren ohne externe Kartenkacheln. Bei Verwendung einer Hintergrundkarte sind Anbieter, Lizenz, Namensnennung und technische Abhängigkeit gesondert zu entscheiden. Der bisherige Vergleich verwendet umgebende Gemeindegeometrien als regionalen Kontext und keinen externen Kacheldienst.

## 5. Grenzdaten verkleinern

Für die vorgeschlagene Architektur wird eine kleine Webfassung der Grenzen vorbereitet. Die genaue Vereinfachungsstärke und ein verbindliches Größenbudget sind noch nicht beschlossen.

1. Nur die zwölf benötigten Kommunen und gegebenenfalls einen bewusst begrenzten Umgebungskontext auswählen.
2. Überflüssige Grenzpunkte entfernen, sodass die Form bei der erlaubten maximalen Zoomstufe ausreichend erhalten bleibt.
3. Gemeinsame Grenzen benachbarter Gemeinden **zusammen und topologiebewusst** vereinfachen, damit sie weiterhin zueinander passen.
4. Kleine Teilflächen, Exklaven und Innenringe gesondert kontrollieren. `keep-shapes` allein garantiert nicht den Erhalt jedes einzelnen Teils eines MultiPolygons.
5. Unnötige Attribute entfernen und die Koordinatengenauigkeit passend zur Darstellungsgröße begrenzen.
6. Ergebnis und Original bei der maximal vorgesehenen Zoomstufe vergleichen; Lücken, Überlappungen und verschwundene Gebiete prüfen.

Als Werkzeug wurde **Mapshaper** empfohlen und für den Vergleich verwendet. Zunächst genügt vereinfachtes GeoJSON. TopoJSON speichert gemeinsame Grenzabschnitte nur einmal; für Leaflet wäre eine Konvertierung in GeoJSON im Browser nötig. Dies ist eine Option, keine Voraussetzung.

Für Paket 3 ist das Budget der Webgeometrie auf höchstens 200 kB festgelegt. Die erzeugte Fassung umfasst 132.114 Byte einschließlich Zuordnung und Kontext. Die maximale Zoomstufe ist 11. Verarbeitung, weitere Datenbudgets und aktuelle Prüfungen stehen in [WEBANWENDUNG.md](WEBANWENDUNG.md).

## 6. Erprobte Datenquelle und Aufbereitung

Die folgenden Angaben beschreiben den früheren visuellen Entwurf. Die seit Paket 3 verwendete Website verarbeitet denselben archivierten Ausgangsabruf mit Mapshaper 0.7.101 über ein festes Skript. Grenzstand 01.01.2025 und BKG-Produktseite sind inzwischen archiviert; die aktuelle Webfassung und deren Maße stehen in [WEBANWENDUNG.md](WEBANWENDUNG.md).

Für den visuellen Vergleich wurden die Verwaltungsgebiete **VG250 des Bundesamts für Kartographie und Geodäsie (BKG)** verwendet. Der Dienst bietet Gemeindegrenzen und amtliche Schlüssel. Er ist für eine regionale Übersicht ein Kandidat; die Eignung für eine detaillierte Nahansicht bleibt zu prüfen.

- Produktseite: [WFS Verwaltungsgebiete 1:250 000](https://gdz.bkg.bund.de/index.php/default/open-data/wfs-verwaltungsgebiete-1-250-000-stand-01-01-wfs-vg250.html)
- Dienst: `https://sgx.geodatenzentrum.de/wfs_vg250`
- Abruf für die Vorschau am 7. November 2026; das Abrufdatum ist keine Aussage über den fachlichen Grenzstand.

Verwendete WFS-Parameter:

```text
service=WFS
version=2.0.0
request=GetFeature
typeNames=vg250:vg250_gem
outputFormat=application/json
srsName=urn:ogc:def:crs:OGC:1.3:CRS84
bbox=8.8,48.6,9.5,49.0,urn:ogc:def:crs:OGC:1.3:CRS84
```

Der Abruf lieferte **140 Gemeindegeometrien**, also die zwölf Vergleichskommunen und weiteren Umgebungskontext. Für die Vorschau wurde **Mapshaper 0.6.113** mit folgender Verarbeitung verwendet:

```bash
mapshaper output/municipalities-original.geojson \
  -simplify 30% keep-shapes \
  -filter-fields gen,ags \
  -o output/municipalities-preview.geojson precision=0.00001
```

`30%` bezeichnet die angestrebte Beibehaltung von Grenzpunkten, nicht die verbleibende Dateigröße. Die Koordinatenpräzision ist hier in geografischen Grad angegeben; sie ist keine festgelegte Vereinfachungstoleranz in Metern. Das Werkzeug wurde für die Vorschau temporär installiert; ein dauerhaftes Vorverarbeitungsskript und eine Projektabhängigkeit sind noch nicht eingerichtet.

Gemessene Dateigrößen:

| Datei | Inhalt | Größe |
|---|---|---:|
| `output/municipalities-original.geojson` | ursprünglicher regionaler WFS-Abruf mit Attributen, 140 Geometrien | 391.188 Byte |
| `output/municipalities-preview.geojson` | vereinfachte regionale Geometrie mit Name und AGS, 140 Geometrien | 121.956 Byte |
| `output/kita-map-comparison.html` | gesamter interaktiver Vergleich einschließlich eingebetteter Geometrie und Gebührenauszug | 132.868 Byte |

Die GeoJSON-Webfassung ist damit rund **69 % kleiner** als der regionale Abruf. Der HTML-Wert enthält keine separat geladenen Bibliotheken oder den Gesprächsrenderer und ist daher kein vollständiges Netzwerkbudget einer Website. Eine Beschränkung auf zwölf Geometrien wurde in diesem Vergleich bewusst noch nicht vorgenommen.

Die Quelle verlangt Namensnennung nach **Datenlizenz Deutschland – Namensnennung 2.0**. Im Vergleich werden `BKG` und `dl-de/by-2-0` verlinkt sowie die Vereinfachung kenntlich gemacht. Vor der produktiven Übernahme sind der konkrete Datenstand, vollständige Quellenangaben und die Lizenzinformationen dauerhaft mit den Geodaten zu sichern.

## 7. Vorgeschlagene Oberfläche

**Desktop:** Die Gemeindekarte steht im Mittelpunkt. Kompakte Profilfilter stehen darüber. Ein Klick auf eine Fläche öffnet die Gebührenaufschlüsselung, beispielsweise in einem seitlichen Detailbereich. Eine sortierbare Liste ergänzt die räumliche Ansicht; ein direkter Vergleich ausgewählter Kommunen wurde ebenfalls vorgeschlagen.

**Mobil:** Karte und Liste können über einen Umschalter erreichbar sein; Gemeindedetails stehen darunter. Alle wesentlichen Informationen sollen per Tastatur und ohne Hover erreichbar bleiben. Die Liste bietet Zugang zu den Werten unabhängig von der Kartenbedienung. Das genaue Layout und die Abnahmekriterien zur Barrierefreiheit sind noch zu bestimmen.

**Aktuelle Bedienentscheidung (8. November 2026):** „Eigene Familie“ ist über `FEATURES.personalProfiles` deaktiviert. Auch der separate Höchsttarif-Reiter ist über `FEATURES.highestBandReference` ausgeblendet. Die bisherige Standard-Modellfamilie bleibt sichtbar. Die vereinbarte Konfiguration mit Kinderkategorien, 6/8 Stunden Betreuung und sechs Einkommensszenarien ist noch nicht eingebaut; Einzelheiten stehen in `WEBANWENDUNG.md`.

Das bereits implementierte, vorerst deaktivierte Familienformular kann ein einstellbares Familienprofil bieten. Nutzer können Kinder mit Alter und Haushaltszugehörigkeit, das zu vergleichende Kind, gleichzeitig betreute Geschwister, Haushaltskonstellation, Bruttojahreseinkommen, zu versteuerndes Einkommen, Betreuungstage und Tagesstunden sowie vorhandene Pässe oder bewilligte Vergünstigungen angeben. Karte, Liste und Gemeindedetails verwenden dasselbe Profil. Die genaue Anordnung der Eingaben bleibt Teil der Oberflächengestaltung.

Dabei gelten folgende Verhaltensregeln:

- Die Modellfamilie kann mit einer Aktion wiederhergestellt werden. Die Höchsttarifreferenz bleibt für Datenprüfung und Exporte erhalten; ihr separater Reiter entfällt.
- Zusammenleben und Alleinerziehen werden als Haushaltsmerkmale erfasst. Bei getrennten Haushalten sind die Zugehörigkeit der Kinder und die nach der jeweiligen Quelle relevanten Einkünfte ausdrücklich zu klären; der Familienstand allein legt keinen Tarif fest.
- Familiengröße, Kindergeldberechtigung und Rang in gleichzeitiger Betreuung bleiben getrennte Merkmale.
- Bruttoeinkommen, steuerliches Einkommen und davon abweichende kommunale Einkommensbegriffe werden nicht stillschweigend gleichgesetzt. Weitere Angaben werden dort abgefragt, wo sie für die lokale Einkommensdefinition erforderlich sind.
- Fehlt eine benötigte Einkommensangabe, erscheint für die betroffenen Kommunen „Weitere Angabe erforderlich“. Die betreffende Fläche erhält keine aus einem alten oder geschätzten Betrag abgeleitete Gebührenfarbe.
- Die steuerliche Einkommensannahme der Modellfamilie wird als solche gekennzeichnet. Bei einer Änderung des Bruttoeinkommens darf sie nicht unbemerkt als persönlicher Wert weitergelten; sie muss ausdrücklich bestätigt oder ersetzt werden.
- Antrags- und passabhängige Vergünstigungen werden nur bei bestätigten Voraussetzungen angewendet. Individuelle Berechnungsangaben können vollständig im Browser bleiben.

Gemeindedetails sollen den Vergleichswert, den ursprünglichen Beitrag, Beitragsmonate, gebuchte Stunden und Mehrstunden, Essen und weitere Kosten, Gültigkeit, Geltungsbereich sowie Quelle und Berechnungsgrundlage nachvollziehbar darstellen. Fehlende oder mehrdeutige Ergebnisse erhalten eine eigene Kennzeichnung und keine Null-Euro-Farbe.

Vorgeschlagene Gestaltung: ruhige Flächen, gut lesbare Schrift und Beträge, eine abgestufte Farbskala mit Euro-Legende und leicht erreichbare Quellen. Dezente Grüntöne wurden zunächst angeregt; die gezeigte Karte verwendet eine vom Gesprächsdesign abhängige Serienfarbe. Eine endgültige Palette oder feste Klassen wurden nicht beschlossen.

## 8. Kennzahl und Vergleichbarkeit

Beide gezeigten Karten enthalten einen eingebetteten Auszug der bisherigen Höchsttarifwerte. Diese werden jetzt unter `data/exports/highest_band_comparison.json` erhalten; `default_comparison.json` verwendet seit Paket 1 die Modellfamilie. Das Profil der alten Vorschauen lautet:

- 24 Monate altes Einzelkind, kommunale Betreuung;
- Montag bis Freitag mindestens acht Stunden durchgehende Betreuung;
- höchste reguläre Einkommensstufe ohne Pass- oder Sozialermäßigung;
- **Monatsäquivalent = ursprünglicher Monatsbeitrag × Beitragsmonate ÷ 12**;
- Betreuung ohne Essen und weitere Zusatzkosten; Tarifstichtag 4. November 2026.

Die verfügbaren Buchungspakete umfassen je nach Kommune 40, 42,5 oder 45 Wochenstunden. Diese Unterschiede bleiben in der Auswahl sichtbar. Es wird weder auf einen fiktiven einheitlichen Stundenpreis umgerechnet noch eine tatsächliche Jahresabrechnung mit unterjährigen Tarifwechseln behauptet. Künftige Tarife und fehlende Angaben müssen ausdrücklich behandelt werden. Einzelheiten und Quellen stehen im Standardvergleich und im Datenmodell.

### 8.1 Geplantes Startprofil und bestehende Referenz

Nach der Diskussion über Esslingens höchste Einkommensstufe soll die Website mit einer anpassbaren Modellfamilie starten:

| Merkmal | Startannahme |
|---|---|
| Haushalt | Zwei zusammenlebende Eltern, ein Kind, keine Geschwister |
| Kind | 24 Monate, Krippenbetreuung |
| Betreuung | Montag bis Freitag jeweils mindestens acht Stunden durchgehend |
| Bruttojahreseinkommen des Haushalts | 80.000 € |
| Zu versteuerndes Jahreseinkommen | 60.000 €, eigenständige ausdrücklich gekennzeichnete Modellannahme |
| Zeitlicher Einkommensbezug | Unverändert im Vorjahr und laufenden Jahr |
| Weitere Einkünfte | Keine Vermietung, Selbstständigkeit oder sonstigen Einkünfte |
| Vergünstigungen | Reguläre Einkommensstaffeln anwenden; zusätzliche Pass- und Sozialermäßigungen nur bei bestätigten Voraussetzungen |
| Kennzahl | Monatliches Betreuungsäquivalent; Essen separat |

Die beiden Einkommenswerte sind keine behauptete steuerliche Umrechnung und kein statistisch belegter Durchschnittshaushalt. Besondere kommunale Einkommensdefinitionen bleiben zu berücksichtigen.

**Umsetzungsstand nach Paket 1:** `data/profiles/default.json` und `data/exports/default_comparison.json` verwenden die Modellfamilie. Das unveränderte alte Profil liegt unter `data/profiles/highest_band.json`, sein Ergebnis unter `data/exports/highest_band_comparison.json`. Beide Profile haben unabhängige Sollwerte für alle zwölf Kommunen und eigene Berichte. Die alten HTML-/Bildvorschauen werden nicht automatisch aktualisiert und zeigen weiterhin die Höchsttarifreferenz.

Die lokalen Einkommensannahmen sind ausdrücklich erfasst: für Esslingen 80.000 € nach örtlicher Definition, ohne den möglichen Arbeitnehmer-Pauschbetrag abzuziehen; für Korntal-Münchingen 60.000 € bereinigtes steuerliches Jahreseinkommen ohne Vermietungsverluste. Der Modell-Snapshot verhindert, dass geändertes Brutto oder veränderte Bedingungen unbemerkt mit unveränderten steuerlichen bzw. lokalen Modellwerten weiterberechnet werden. Die persönliche Eingabe im Browser muss später ein eigenes Profil mit bestätigten Grundlagen bilden. Details stehen im [Datenmodell](DATENMODELL.md).

## 9. Besprochene Darstellungsalternativen

| Variante | Zweck und Ergebnis der Beratung |
|---|---|
| Eingefärbte Gemeindeflächen | Zeigen das Tarifgebiet und die räumliche Verteilung der Gebühren; **als Hauptdarstellung ausgewählt**. |
| Proportionale Kreise | Stellen Beträge über die Kreisfläche dar; wurden visualisiert und zugunsten der Gemeindeflächen zurückgestellt. Keine zusätzliche Umschaltansicht beauftragt. |
| Gleich große, eingefärbte Kreise | Mögliche Darstellung ohne Grenzgeometrie; nicht ausgewählt. |
| Preislabels an einem Ortspunkt | Direkt lesbare Beträge ohne Grenzgeometrie; als Alternative besprochen. Labels können künftig auch Gemeindeflächen ergänzen. |
| Ring um ein Stadtgebiet | Technisch möglich, bildet aber keine genaue Gemeindegrenze ab; nicht weiterverfolgt. |

Bei proportionalen Kreisen müsste die Fläche dem Betrag entsprechen, also der Radius mit der Quadratwurzel des Betrags wachsen. Solche Marker könnten mit je einer repräsentativen Standortkoordinate auskommen. Bildschirmradien in Pixeln und geografische Radien in Metern sind unterschiedliche Darstellungen. Diese Überlegungen bleiben als Kontext erhalten und sind kein Auftrag für weitere Kartenmodi.

## 10. Entwürfe und bisherige Prüfung

| Datei | Einordnung |
|---|---|
| [Detailentwurf](../output/kita-detail-concept.html) | Frühe isolierte Ditzinger Detailansicht mit interaktiven Tarifauswahlen; verwendet einen eingebetteten Auszug der damals erfassten Tabellen. Kein kanonischer Datenbestand und kein vollständiger Gebührenrechner. |
| [Kartenvergleich](../output/kita-map-comparison.html) | Zwei synchron auswählbare Karten mit den bisherigen Höchsttarifwerten für zwölf Kommunen und regionalen Gemeindegrenzen. |
| [Vorschau bei 500 Pixel Kartenbreite](../output/kita-maps-preview-500.png) | Statische Kontrollansicht beider Karten. |
| [Vorschau bei 320 Pixel Kartenbreite](../output/kita-maps-preview-320.png) | Statische Kontrollansicht mit angepassten Beschriftungspositionen. |

Die HTML-Dateien sind Fragmente für die Gesprächsdarstellung. Sie sind keine fertigen GitHub-Pages-Einstiegsseiten. Der Kartenvergleich nutzt **D3 7.9.0** zur geografischen Projektion und SVG-Zeichnung; daraus folgt keine Änderung der Leaflet-Empfehlung für die spätere Website. Er enthält die Geometrie und einen Gebührenauszug direkt. Eine dauerhafte automatische Erzeugung und Aktualisierung dieser Vorschau ist noch nicht eingerichtet.

Geprüft wurden die Datenzuordnung für alle zwölf Kommunen, die geografische Ringorientierung für D3, zwölf Kreismarker und zwölf Gebührenflächen sowie die gemeinsame Auswahl und deren Ergebnisanzeige. Statische SVG-Renderings wurden bei 500 und 320 Pixel Kartenbreite visuell kontrolliert; Beschriftungen wurden für die schmale Darstellung angepasst. Dies war keine vollständige Geometrie-, Barrierefreiheits- oder Browserabnahme. Eine Browserprüfung war in dieser Sitzung wegen deaktivierter lokaler Browsernutzung nicht verfügbar.

Die statischen PNGs stellen die Karten nebeneinander dar; die interaktive Darstellung ordnet sie bei schmaler Breite untereinander an. Der 500-Pixel-Kontrollstand wurde vor der letzten kleinen Text- und Mobilanpassung erzeugt und dient als Layoutreferenz.

## 11. Nächste Umsetzungspakete und Abnahme

1. **Register und Profile vorbereiten — umgesetzt:** Aktive Kommunen und AGS sind zentral erfasst, die feste Zwölferprüfung ist abgelöst und die Modellfamilie neben dem Höchsttarifprofil eingeführt. Abnahme in Daten und Python: Register-/Tarif-/Geometrieverweise werden geprüft; ein synthetisches dreizehntes Gebiet funktioniert allein mit weiteren Daten; beide Profile liefern für die zwölf Bestandskommunen belegte Werte. Die späteren Kartenkomponenten dürfen ebenfalls keine feste Gebietsliste enthalten; eine solche Oberfläche existiert noch nicht.
2. **Browserberechnung aufbauen — umgesetzt:** Profileingaben normalisieren, Tarifregeln im unabhängigen TypeScript-Modul auswerten und gemeinsame Referenzfälle gegen Python prüfen. Abnahme: 104 gemeinsame Szenarien mit gleichen vollständigen Ergebnissen, beide Referenzprofile zusätzlich gegen Quellen-Sollwerte geprüft; keine stillschweigende Brutto-/Steuerumrechnung. TypeScript 7.0.2 und Zod 4.6.7 sind im Lockfile festgehalten. Website-Bündelung und tatsächliche Browserintegration folgen in Paket 3.
3. **Frontend und Geodaten integrieren — umgesetzt:** React/Vite, CSS Modules und Leaflet mit festgelegten Paketversionen und Lockfile eingerichtet. BKG-Grenzstand, Lizenz und Quellen sind gesichert; Geometrien werden gemeinsam vereinfacht und anhand von AGS/Flächen-ID zugeordnet. Abnahme: eigenständige lokale Anwendung mit zwölf Vergleichsflächen, beiden Profilen, Quellen und acht zusätzlichen Webdaten-Prüfungen. Desktop, 390/320 Pixel und der statische Projekt-Unterpfad wurden im Browser geprüft. Größenbudget und Zoomgrenzen sind dokumentiert.
4. **Bedienbare erste Version fertigstellen — umgesetzt:** Familienformular, Gebührenfarben, Legende, Liste und Gemeindedetails zusammenführen. Farbpalette und Klassengrenzen im Rahmen dieses Pakets festlegen; die bisherigen Vorschauklassen sind keine verbindliche Vorgabe. Abnahme: Eingaben aktualisieren alle Ansichten konsistent; fehlende Werte, Essen, Mehrstunden und Modellannahmen bleiben sichtbar; Desktop, Mobilgeräte und Tastaturbedienung sind geprüft.
5. **Bereitstellung vorgezogen:** GitHub-Pages-Ziel und Actions-Workflow sind eingerichtet. Python- und JavaScript-Tests sowie Build laufen automatisch; ausschließlich erfolgreiche Builds von `main` werden veröffentlicht. Pull Requests erhalten dieselben Prüfungen ohne Deployment. Fachliche Zuständigkeiten und Aktualisierungsrhythmus bleiben offen.

Paket 4 ist umgesetzt und mit 132 JavaScript-Tests, 70 Python-Tests sowie Browserprüfungen auf Desktop, bei 390 und 320 Pixeln Breite abgesichert. Das Formular ist einklappbar; Karte, Liste und Details bleiben gleichzeitig verfügbar. Ein gesonderter mobiler Karte/Liste-Umschalter ist für diese erste Version nicht erforderlich. Als Nächstes folgen die fachliche Nutzerabnahme weiterer persönlicher Konstellationen und ein wiederholbarer Aktualisierungsablauf für neue Tarife. Die automatische Veröffentlichung ist eingerichtet.

Historische Preisreihen bleiben zurückgestellt. Eine englische Oberfläche, eine Redaktionsoberfläche und zusätzliche Kartenmodi sind nicht beschlossen.

## 12. Technische Referenzen

- [Vite: statische Bereitstellung](https://vite.dev/guide/static-deploy)
- [Leaflet: GeoJSON](https://leafletjs.com/examples/geojson/) und [API-Referenz](https://leafletjs.com/reference)
- [GeoJSON-Spezifikation RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946)
- [Zod](https://zod.dev/)
- [Mapshaper: Vereinfachung](https://mapshaper.org/docs/guides/simplification.html), [Topologie](https://mapshaper.org/docs/guides/topology.html) und [Dateiformate](https://mapshaper.org/docs/formats/overview.html)
- [Datenlizenz Deutschland – Namensnennung 2.0](https://www.govdata.de/dl-de/by-2-0)
