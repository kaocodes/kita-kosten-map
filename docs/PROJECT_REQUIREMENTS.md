# Projektanforderungen: Kita- und Kindergartengebühren in der Region Stuttgart

**Status:** Datenmodell, Kommunenregister, Rechenkern und lokale Webkarte umgesetzt; Pages-Veröffentlichung automatisiert; individuelles Familienformular erhalten, vorerst ausgeblendet
**Stand:** 8. November 2026

**Aktueller Modellvergleich:** Die vereinbarte Konfiguration ist umgesetzt. Haushaltskonstellation, Kinderzahl, vier Kinderkategorien, sechs Einkommensszenarien und 6/8 Stunden je Kita-Kind bestimmen die Familiengesamtkosten. Feste Einkommensannahmen und Einschränkungen stehen in [MODELLFAMILIEN.md](MODELLFAMILIEN.md). Die bisherigen persönlichen Eingaben und der Höchsttarif-Reiter bleiben öffentlich ausgeblendet.


## 1. Projektziel

Das Projekt sammelt, dokumentiert und vergleicht öffentlich verfügbare Gebühren für Krippen- und Kindergartenbetreuung in ausgewählten Städten und Gemeinden der Region Stuttgart. Die Ergebnisse sollen Eltern und politischen Entscheidungsträgern einen nachvollziehbaren Vergleich der Gebühren ermöglichen.

Die Gebühren werden von den Städten bzw. Gemeinden festgelegt. Nach bisherigem Kenntnisstand gelten die kommunalen Gebührenordnungen häufig auch für kirchliche und weitere Träger. Erfasst werden daher zunächst die kommunalen Gebührenregelungen und nicht einzelne Einrichtungen. Die tatsächliche Gültigkeit und mögliche Ausnahmen sind je Kommune anhand der Quellen zu prüfen und zu dokumentieren.

Die spätere Anwendung soll Gebühren auf einer interaktiven, flächigen Karte der Städte und Gemeinden darstellen. Sie soll möglichst leichtgewichtig und einfach zu betreiben sein. Bevorzugt wird eine statische Website auf GitHub Pages. Architekturvorschlag, Bedienkonzept und die Darstellungsentscheidung sind in [WEBSITE_KONZEPT.md](WEBSITE_KONZEPT.md) dokumentiert.

## 2. Projektstatus und Leitlinien

- Aktuelle Gebührenquellen sind recherchiert und als lokale Quellenkopien gesichert. Das strukturierte JSON-Datenmodell und die Vergleichsberechnung sind umgesetzt; Dokumentation: `DATENMODELL.md`, Ergebnis: `STANDARDVERGLEICH.md`.
- Die Datenerhebung umfasst zuerst eine Quellenübersicht und danach die Sammlung der verfügbaren Tarifinformationen.
- Es werden alle auffindbaren relevanten Informationen erfasst. Der Standardvergleich und seine Berechnungsregeln sind inzwischen festgelegt; zusätzliche Ansichten bleiben zu bestimmen.
- Der bisherige Requirement-Entwurf enthielt konkrete Vorgaben zu Frameworks, Bibliotheken und UI-Verhalten. Diese Vorgaben gelten nicht als beschlossen. Aktuelle Empfehlungen und ausdrücklich bestätigte Entscheidungen werden im Websitekonzept getrennt dokumentiert.
- Projektkommunikation kann auf Deutsch oder Englisch erfolgen. Projektdokumentation wird auf Deutsch geschrieben; Bezeichner und Kommentare im Code werden auf Englisch geschrieben.

## 3. Geografischer Umfang

Der erste Erhebungsumfang umfasst die zwölf Gebiete aus dem bisherigen Requirement-Dokument:

1. Leonberg
2. Gerlingen
3. Ditzingen
4. Stuttgart
5. Korntal-Münchingen
6. Kornwestheim
7. Ludwigsburg
8. Leinfelden-Echterdingen
9. Böblingen
10. Sindelfingen
11. Esslingen am Neckar
12. Fellbach

Diese Liste ist für den ersten Umfang maßgeblich. Sie ist keine Zusage, sämtliche Kommunen des Landkreises Ludwigsburg oder der gesamten Region Stuttgart abzudecken.

### 3.1 Geografische Einheiten für die Karte

- Die Karte bildet Stadt- bzw. Gemeindegebiete als Flächen ab.
- Einzelne Kitas werden nicht als Kartenpunkte erfasst oder dargestellt.
- Stuttgart wird als ein Gebiet behandelt; die geprüfte kommunale Tarifquelle weist keine Bezirksstaffel aus.
- Korntal-Münchingen und Esslingen am Neckar sind die amtlichen Vergleichseinheiten. Das Register ordnet alle zwölf Kommunen anhand ihres AGS den archivierten BKG-Grenzen zu; die produktive Aufbereitung folgt.
- Für die lokale Webkarte werden vereinfachte BKG-VG250-Gemeindegrenzen mit Stand 01.01.2025 verwendet. Quelle, Lizenz, Abruf und Hashwerte sind gesichert; die Verarbeitung ist reproduzierbar. Zoom- und Größenbudgets stehen in `WEBANWENDUNG.md`. Ein im alten Dokument genannter OpenStreetMap-Polygon-Endpunkt ist lediglich ein historischer Recherchehinweis.

## 4. Umfang der Gebührenerhebung

### 4.1 Betreuungsangebote

Für jede Kommune sollen die verfügbaren kommunalen Tarife für folgende Bereiche erfasst werden:

- Krippenbetreuung
- Kindergartenbetreuung
- alle in den Quellen aufgeführten Betreuungszeitmodelle, insbesondere Halbtag und Ganztag sowie abweichende Stunden- oder Zeitmodelle

Weitere Betreuungsarten werden nur aufgenommen, wenn sie in den für diese Untersuchung relevanten kommunalen Gebührenunterlagen enthalten sind. Die Abgrenzung von Altersgruppen und Angebotsarten folgt zunächst der jeweiligen kommunalen Quelle und wird zusätzlich in normalisierter Form dokumentiert.

### 4.2 Gebühren und Einflussfaktoren

Erfasst werden alle veröffentlichten gebührenbezogenen Angaben, soweit sie aus offiziellen Quellen verfügbar sind. Dazu gehören insbesondere:

- Betreuungskosten
- Essensgeld bzw. Verpflegungskosten, getrennt von den Betreuungskosten, falls separat ausgewiesen
- weitere verpflichtende oder regelmäßig anfallende Kosten, sofern sie in den Gebührenunterlagen genannt werden
- Alters- bzw. Angebotsgruppen und Betreuungsumfang
- Einkommensstufen oder sonstige einkommensabhängige Berechnungsregeln
- Ermäßigungen oder Zuschläge, zum Beispiel aufgrund der Zahl der Kinder bzw. Geschwister
- Anspruchsvoraussetzungen, Ausnahmen, Befreiungen und Berechnungsbedingungen
- Abrechnungsweise und Zahlungsrhythmus, soweit angegeben

Die Erhebung soll die veröffentlichten Tarifstaffeln und Bedingungen vollständig abbilden, nicht nur einen daraus abgeleiteten Einzelbetrag. Originalbezeichnungen und Originalwerte der Quelle bleiben nachvollziehbar erhalten. Normalisierte Felder dürfen ergänzend verwendet werden, müssen aber auf die jeweilige Quelle zurückführbar sein.

### 4.3 Geltung nach Träger

- Primäre Quellen sind Gebührenordnungen und Tarifinformationen der jeweiligen Stadt bzw. Gemeinde.
- Erfasst wird, für welche Träger und Einrichtungen die kommunale Regelung laut Quelle gilt.
- Wenn die Kommune angibt, dass der Tarif auch für kirchliche oder freie Träger gilt, wird diese Aussage mit Quelle dokumentiert.
- Abweichende Gebührenregeln einzelner nicht-städtischer Träger sind nicht Teil des anfänglichen Erhebungsumfangs, sofern sie nicht nötig sind, um den Geltungsbereich der kommunalen Regelung zu beschreiben.

**Vereinbarte Ausnahme für die Erweiterung (10. November 2026):** Für U3 in Freiberg am Neckar wird die veröffentlichte Gebührenordnung des Freiberger Zwergenstüble e.V. übernommen. Der Verein bleibt als tatsächlicher Träger erfasst; die Freigabe gilt nicht pauschal für andere freie Träger. Für Ü3 bleibt die kommunale Gebührenordnung maßgeblich. Beide Tarifbereiche gehören zur selben Gemeindefläche und behalten ihre eigenen Gültigkeitsdaten und Beitragsmonate.

**Denkendorf (10. November 2026):** Die Gemeinde veröffentlicht gemeinsame U3-/Ü3-Tabellen für die evangelischen und katholischen Einrichtungen; getrennte Betreuungstarife nach Träger sind dort nicht ausgewiesen. Diese Tabellen werden als gemeinsame Grundlage verwendet. Für die Modellberechnung wird das gemeinsame Jahresbrutto direkt genutzt, ohne weitere Einkommensabfragen. Pflichtessen bei Ganztag bleibt mit unbekanntem Betrag als Zusatzinformation erfasst.

## 5. Quellen, Erfassungsdatum und Gebührenhistorie

### 5.1 Quellenanforderungen

Bevorzugt werden offizielle und möglichst aktuelle Quellen der Stadt bzw. Gemeinde, darunter:

- Gebührenordnungen und Satzungen
- offizielle Gebührentabellen und Elterninformationen
- Rats- oder Gemeinderatsunterlagen, sofern sie Gebührenänderungen oder historische Tarife belegen
- offizielle PDF-Dokumente und Webseiten

PDF-Dokumente sind ausdrücklich als mögliche Primärquellen vorgesehen. Wenn eine Angabe aus einer PDF-Datei stammt, soll die konkrete Seite oder der relevante Abschnitt festgehalten werden, sofern er bestimmbar ist.

### 5.2 Herkunftsnachweis

Für jede Quelle und jeden daraus übernommenen Tarifstand sind nach Möglichkeit folgende Angaben zu erfassen:

- Kommune
- Titel des Dokuments oder der Webseite
- herausgebende Stelle
- direkte URL
- Dokument- oder Veröffentlichungsdatum, falls angegeben
- Gültig-ab- und Gültig-bis-Datum des Tarifs, soweit ermittelbar
- Datum des Abrufs bzw. der Erfassung
- Seite, Abschnitt, Tabellenzeile oder sonstige Fundstelle
- Hinweise zu Extraktion, Mehrdeutigkeit oder manueller Prüfung

### 5.3 Historische Preisentwicklung

**Zurückgestellt:** Historische Preisreihen werden auf Nutzerwunsch derzeit nicht weiter recherchiert. Bereits erhobene Angaben bleiben erhalten; die folgenden Anforderungen gelten für eine spätere Erweiterung.

- Zusätzlich zu aktuellen Tarifen sollen Gebührenstände der vergangenen fünf Jahre gesammelt werden, soweit sie in offiziellen Quellen auffindbar und ausreichend belegbar sind.
- Änderungen sollen mit ihrem Gültigkeitszeitraum und ihrer Quelle getrennt erfasst werden, damit spätere Preisvergleiche möglich sind.
- Historische Werte dürfen nicht aus einer späteren Tabelle zurückgerechnet oder geschätzt werden. Nicht auffindbare Zeiträume werden als fehlende Daten gekennzeichnet.
- Ob und wie Preissteigerungen oder Zeitreihen in der Anwendung visualisiert werden, wird nach der Erhebung entschieden.

## 6. Datenqualität und Aufbereitung

- Unklare oder fehlende Werte werden als unbekannt bzw. nicht verfügbar gekennzeichnet und nicht als Nullbetrag interpretiert.
- Originalangaben aus der Quelle und aufbereitete Vergleichswerte sind unterscheidbar zu halten.
- Ein aufbereiteter Betrag muss seine Berechnungsgrundlage erkennen lassen, etwa Monatsbetrag, Zahlungsmonate, Betreuungsumfang, Altersgruppe und anwendbare Ermäßigungen.
- Unterschiedliche Gebührenmodelle dürfen nicht ohne dokumentierte Regel zu einem scheinbar vergleichbaren Einzelwert zusammengezogen werden.
- Extraktionen aus PDFs, insbesondere Tabellen, sind auf Vollständigkeit und korrekte Zuordnung zu Tarifmerkmalen zu prüfen.
- Bei widersprüchlichen Quellen werden die Quellen und der Umgang mit dem Widerspruch dokumentiert.

## 7. Geplante Kartenanwendung

### 7.1 Zweck und Darstellung

- Die Anwendung stellt die erhobenen Gebühren auf einer interaktiven Karte mit Gemeinde- bzw. Stadtgebieten als Flächen dar.
- **Darstellungsentscheidung vom 8. November 2026:** Nach dem visuellen Vergleich mit proportionalen Kreisen sind eingefärbte Gemeindeflächen als Hauptdarstellung beschlossen. Die Gebühren werden über die Flächenfarbe vermittelt.
- Es gibt keine Darstellung einzelner Einrichtungspunkte.
- Zielgruppen sind Eltern und politische Entscheidungsträger.
- Der Schwerpunkt liegt auf der Höhe und Vergleichbarkeit der Gebühren.
- Öffnungszeiten und Kontaktdaten einzelner Kitas sind nicht erforderlich.

### 7.2 Startprofil und individuelle Einstellungen

**Aktuelle Bedienentscheidung (8. November 2026):** Die individuelle Eingabe „Eigene Familie“ ist vorerst ausgeblendet; Code und Tests bleiben erhalten. Die Hauptbedienung soll auf einfach auswählbaren Modellfamilien beruhen. Vereinbart sind Haushaltskonstellation, Anzahl der Kinder, Kategorien Krippe/Kindergarten/Schulkind/zu Hause betreut, Einkommen 40.000/60.000/80.000/100.000/140.000/180.000 € und je betreutem Kind 6 oder 8 Stunden täglich. Die künftige Karte zeigt die vollständigen Betreuungskosten der Familie. Diese Konfiguration ist umgesetzt; örtliche Werte sind ausdrücklich dokumentierte Modellannahmen. Der bisherige Standard bleibt unverändert. Der separate Höchsttarif-Reiter ist ausgeblendet; Referenzprofil und Tests bleiben erhalten. Die weiter unten beschriebenen persönlichen Eingaben sind eine zurückgestellte Funktion.

Die Website soll mit einer einstellbaren Modellfamilie starten:

- zwei zusammenlebende Eltern, ein 24 Monate altes Kind in Krippenbetreuung und keine Geschwister;
- Montag bis Freitag mindestens acht Stunden durchgehende Betreuung, jeweils das kleinste belegte ausreichende Paket;
- 80.000 € Bruttojahreseinkommen des Haushalts und unabhängig davon angenommene 60.000 € zu versteuerndes Jahreseinkommen;
- unverändertes Einkommen im Vorjahr und laufenden Jahr; keine weiteren Einkünfte;
- reguläre Einkommensstaffeln; zusätzliche Pass- und Sozialermäßigungen nur bei bestätigten Voraussetzungen;
- Betreuungskosten als Monatsäquivalent: ursprünglicher Monatsbeitrag × Beitragsmonate ÷ 12; Essen und andere Kosten separat.

**Vereinbarte Behandlung enthaltener Verpflegung (10. November 2026):** Bei Waiblingen wird für Angebote mit Mittagessen der veröffentlichte Gesamtbeitrag einschließlich Essen als Karten- und Listenwert verwendet. Die Details zeigen unter Verpflegung „Im Tarif enthalten“. Es wird kein geschätzter Essensanteil abgezogen und kein zweiter Essensbetrag addiert. Angebote ohne enthaltenes Essen erhalten diese Kennzeichnung nicht. Für Aichwald werden gemäß Nutzerangabe 53 € U3-Essen monatlich auf Zwölf-Monats-Basis erfasst; ausschließlich aus U3-Preisen mit bereits enthaltenem Essen wird dieser bekannte Anteil herausgerechnet. Unveränderte Originalpreise und die Herkunft dieser Festlegungen bleiben gespeichert. Diese Regeln sind für die Erweiterung vereinbart; die neuen Kommunen sind noch nicht aktiviert.

Das Profil ist eine transparente Referenzannahme und kein statistisch belegter Durchschnittshaushalt. Die beiden Einkommenswerte sind keine steuerliche Umrechnung. Kommunal abweichende Einkommensdefinitionen bleiben zu berücksichtigen.

**Zugelassene lokale Zeitabweichung für Denkendorf (10. November 2026):** Für die Einordnung dürfen die belegten Betreuungszeiten von Montag bis Donnerstag verwendet werden, wenn ausschließlich der Freitag den gewünschten Tagesumfang unterschreitet. Die tatsächliche Freitagszeit, Wochenstunden und der Originalbeitrag bleiben erhalten; die Details müssen die Abweichung anzeigen. Es wird keine fiktive Betreuung am Freitag ergänzt und kein Preis auf eine erfundene Acht-Stunden-Woche umgerechnet. Für andere Kommunen ändert diese Freigabe die Auswahlregeln nicht.

**Vorgabe zur Umsetzung kommunaler Sonderfälle (10. November 2026):** Für Schwieberdingen keine Änderungen an der Berechnungsengine vornehmen. Änderungen an der gemeinsamen Berechnungslogik für einzelne Kommunen müssen generell zuerst mit dem Nutzer besprochen werden. Eindeutig darstellbare Regeln gehören in die Daten. Ergibt eine bestimmte Familienkonfiguration keinen eindeutigen, belegten oder ausdrücklich vereinbarten Wert, wird sie als „Nicht berechenbar“ (`unavailable`) ausgewiesen. Keine willkürliche Rangfolge, Preiszelle oder Ersatzberechnung einsetzen.

Nutzer sollen Kinderzahl und Alter, Haushaltszugehörigkeit und -konstellation, gleichzeitig betreute Geschwister, Brutto- und steuerliches Einkommen, Betreuungstage und Tagesstunden sowie vorhandene Pässe oder bewilligte Vergünstigungen einstellen können. Karte, Liste und Details verwenden dasselbe Profil. Eine Aktion stellt die Modellfamilie wieder her. Fehlende lokale Pflichtangaben ergeben eine eigene Kennzeichnung statt einer Schätzung. Eine geänderte persönliche Einkommenseingabe darf nicht unbemerkt mit einer alten steuerlichen Modellannahme kombiniert werden.

**Implementierungsstand nach Paket 4:** `data/profiles/default.json`, Standardexporte und Website verwenden die Modellfamilie. `data/profiles/highest_band.json` erhält die Höchsttarifreferenz, deren separater Reiter inzwischen ausgeblendet ist; Profil und Tests bleiben erhalten. Beide Profile sind für alle zwölf Kommunen gegen belegte Sollwerte geprüft. Lokale Einkommensgrundlagen sind ausdrücklich erfasst; ein Snapshot schützt gegen unbemerkt veränderte Modellannahmen. Esslingen wird im Modell ohne den optionalen Arbeitnehmer-Pauschbetrag berechnet. Die persönliche Eingabeoberfläche ist als drittes Profil „Eigene Familie“ umgesetzt. Sie entfernt Modell-Einkommen und Berechtigungen, hält Einkommensdefinitionen getrennt und aktualisiert Karte, Liste und Details. Fehlerhafte Eingaben entfernen alle bisherigen Gebühren; fehlende Angaben sperren nur die betroffenen Berechnungen. Persönliche Angaben werden nicht gespeichert oder übertragen. Details und Abnahme stehen in [WEBANWENDUNG.md](WEBANWENDUNG.md).

Originalbeiträge, tatsächlicher Buchungsumfang, Mehrstunden und Beitragsmonate bleiben sichtbar. Das Jahresäquivalent hält den Tarif am Stichtag konstant und bildet keine tatsächliche Jahresabrechnung mit unterjährigen Änderungen ab.

### 7.3 Vergleichbarkeit und Karteneinfärbung

- Die Karte soll Gebühren zwischen den erfassten Gebieten vergleichbar machen.
- Eine Kartenfarbe basiert standardmäßig auf dem beschlossenen monatlichen Betreuungsäquivalent. Tarifstichtag und Profil müssen sichtbar sein.
- Farbschema und Legende sind noch zu gestalten. Fehlende und mehrdeutige Ergebnisse bekommen keine aus null Euro abgeleitete Kartenfarbe.
- Die konfigurierbare Modellfamilie bildet die künftige Hauptbedienung. Ein separater Höchsttarif-Reiter entfällt. Weitere Komfortprofile bleiben optional.

## 8. Technische Leitplanken

- Die Anwendung soll leichtgewichtig, einfach zu bedienen und wartbar sein.
- Eine statische Website auf GitHub Pages ohne Backend ist die bevorzugte Betriebsform. Datenprüfung und Export können vor dem Website-Build erfolgen.
- Ein kleines Backend bleibt möglich, falls es für Datenpflege, Datenprüfung oder Bereitstellung tatsächlich erforderlich ist.
- TypeScript und Zod sind für das Rechenmodul umgesetzt; React, Vite, CSS Modules und Leaflet für die lokale Website. Konkrete Versionen stehen im Lockfile. Python-Berechnung und kanonische JSON-Daten bleiben Grundlage der Datenpflege.
- Eine interaktive Karte mit Gemeindegrenzen ist vorgesehen; die konkrete Quelle für Grenzdaten und deren Lizenz müssen vor der Umsetzung geklärt werden.
- Grenzdaten werden vor der Veröffentlichung räumlich ausgewählt und topologiebewusst vereinfacht. Nur die benötigte Webfassung wird ausgeliefert. GeoJSON ist die vorgeschlagene Ausgangslösung; TopoJSON bleibt eine Optimierungsoption.
- Die Anwendung soll auf üblichen Desktop- und Mobilbildschirmen nutzbar sein. Weitere Anforderungen an Barrierefreiheit und Sprachunterstützung sind noch zu konkretisieren.
- Technischer Datenfluss, vorgeschlagene Oberfläche, geprüfte Entwürfe und offene Umsetzungsfragen stehen in [WEBSITE_KONZEPT.md](WEBSITE_KONZEPT.md).
- Die Zahl der aktiven Kommunen wird über `data/municipality_registry.json` bestimmt. Die feste Prüfung auf zwölf Kommunen ist abgelöst; Oberflächenkomponenten dürfen keine eigene feste Gebietsliste pflegen.
- Kartenflächen und Gebührenordnungen bleiben getrennt. Zusätzliche Stadtbezirke können dieselbe kommunale Gebührenordnung referenzieren. AGS, interne Gebietskennung und gegebenenfalls übergeordnete Kommune werden ausdrücklich zugeordnet.
- Die Browserberechnung ist unabhängig von React und Leaflet als TypeScript-Modul umgesetzt und anhand von 104 gemeinsamen Szenarien gegen Python geprüft. Zod prüft Profileingaben; exakte Bruchrechnung sichert Beträge und Grenzen. Die Browserintegration folgt. Eine Erweiterung der Datenmenge allein erfordert kein Backend.
- Bei wachsendem Umfang können Daten nach Region nachgeladen werden. Dateigröße, Geometriekomplexität und tatsächliche Lade- und Bedienzeiten bestimmen die Optimierung; die Kartenansicht bleibt von den fachlichen Daten unabhängig.

## 9. Geplante Arbeitsschritte

**Priorität vor zusätzlichen Kommunen:** Zuerst muss die Website mit den bestehenden zwölf Vergleichskommunen stabil laufen und die vollständige UI/UX-Prüfung abgeschlossen und dokumentiert sein. Anschließend können die 33 direkt angrenzenden Kommunen aus [DATENERWEITERUNG.md](DATENERWEITERUNG.md) schrittweise aufgenommen werden. Sie sind vorgemerkte Kandidaten; Quellenrecherche, Tarifübertragung und Aktivierung sind bis zum Abschluss dieser Voraussetzungen zurückgestellt.

**Geplante UI-Neugestaltung, Entscheidung vom 9. November 2026:** Maßgeblich ist der Familienatlas-Entwurf aus [UI_REDESIGN.md](UI_REDESIGN.md): große Karte mit vollständigen Kommunendetails darunter, auswählbare Modellfamilienkarten und eine Kommunenliste von teuer bis günstig mit denselben vollständigen Details direkt am Auswahlort. Kinderdetails sind aufklappbar; darin sind Verpflegung und Zusatzkosten direkt sichtbar. Die Ausgangsfamilie heißt Modellfamilie und ist kein Durchschnitts-/Medianhaushalt. Die Gestaltung verwendet helles Flieder, warme weiße Inhaltsbereiche, pastellhellblauen Kartenhintergrund und neutrale graue Umgebungsflächen. Diese Anforderungen sind auf `codex/ui-redesign` lokal umgesetzt und unter `http://127.0.0.1:5173/` zur Durchsicht bereitgestellt; eine Veröffentlichung ist noch nicht erfolgt.

1. **Quelleninventar:** Für die zwölf Gebiete vorhanden; Pflege bei neuen Quellen fortführen.
2. **Datenverfügbarkeit prüfen:** Aktuelle Tarife und bekannte Einschränkungen sind dokumentiert; historische Preisreihen bleiben zurückgestellt.
3. **Datenmodell festlegen:** Strukturiertes JSON-Schema und ausführbare Validierung sind umgesetzt.
4. **Datenerhebung:** Aktuelle Tarife sind strukturiert übertragen und geprüft; Änderungen künftig versioniert ergänzen.
5. **Vergleichsregeln bestimmen:** Höchsttarifreferenz, Modellfamilie und registergestützter Vergleich sind in Python und TypeScript umgesetzt und geprüft. Der Wechsel zum persönlichen Profil verwirft unbestätigte Modell-Einkommen. Browserintegration und Formular folgen.
6. **Technische Umsetzung planen:** Gemeindeflächen sind beschlossen, statisches Hosting ist bevorzugt und Entwürfe sind vorhanden. Die verbleibenden Entscheidungen stehen im Websitekonzept.
7. **Anwendung umsetzen:** Lokale Website, Gemeindekarte, Referenzprofilwahl und Grunddetails sind umgesetzt und im Browser geprüft. Pages-Deployment und automatische Prüfungen sind eingerichtet. Individuelles Formular und vollständige Bedienabnahme stehen aus.

## 10. Erste Abnahmekriterien für den Datensatz

Der Erhebungsdatensatz gilt als fachlich prüfbar, wenn:

- alle zwölf Gebiete im Quelleninventar enthalten sind;
- für jede Kommune dokumentiert ist, welche offiziellen Tarifquellen gefunden wurden;
- verfügbare Gebühren für Krippe, Kindergarten und die jeweils veröffentlichten Betreuungszeitmodelle erfasst sind;
- Essensgeld und weitere ausgewiesene Kosten getrennt erfasst oder als nicht veröffentlicht gekennzeichnet sind;
- Bedingungen wie Einkommensstaffeln und Ermäßigungen aus den Quellen nachvollziehbar übernommen sind;
- jede erfasste Tarifangabe auf eine Quelle und möglichst eine konkrete Fundstelle zurückgeführt werden kann;
- bei einer später beauftragten historischen Erweiterung verfügbare Tarifstände der vergangenen fünf Jahre dokumentiert sind und Lücken als solche kenntlich bleiben;
- offene Mehrdeutigkeiten und notwendige manuelle Prüfungen sichtbar dokumentiert sind.

## 11. Noch offene Entscheidungen

- Werden für spätere zusätzliche Gebiete oder andere Zoomansichten detailliertere Grenzdaten benötigt? Die jetzige regionale Karte verwendet dokumentierte BKG-VG250-Daten.
- Wie werden die vorgesehenen persönlichen Eingaben, die Modellfamilie, der Höchsttarifvergleich und die Zusatzkostenansicht im endgültigen Layout angeordnet?
- Welche Farbpalette, Klassengrenzen und Legende erhalten die beschlossenen Gemeindeflächen? Wie werden Mehrstunden und fehlende oder mehrdeutige Ergebnisse gekennzeichnet?
- Welche Sprachversionen benötigt die Anwendung? Deutsch ist die Projektsprache; eine englische UI ist noch nicht beschlossen.
- Wie wird der dokumentierte Pflegeprozess aus Quellenkopie, JSON-Aktualisierung, Prüfung und Export künftig organisatorisch betrieben?
- Welche konkreten Paketversionen und Details der empfohlenen Frontend-Bibliotheken werden bei der Umsetzung verwendet? Individuelle Profile sind für die Berechnung im Browser vorgesehen.
- In welchem Rhythmus werden fachlich geprüfte Tarifänderungen veröffentlicht? Ziel und technischer Prozess stehen fest: https://kaocodes.github.io/kita-kosten-map/ über GitHub Actions.
- Wie oft sollen die Gebühren nach dem ersten Erhebungsstand überprüft und aktualisiert werden?
