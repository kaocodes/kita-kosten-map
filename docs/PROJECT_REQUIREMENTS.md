# Projektanforderungen für den Kita-Gebührenvergleich

**Stand:** 20. November 2026

## 1. Projektziel

Die Anwendung sammelt, dokumentiert und vergleicht öffentlich verfügbare Gebühren für Krippen und Kindergärten in der Region Stuttgart. Sie richtet sich an Eltern und politische Entscheidungsträger. Die Höhe der Gebühren und ihre nachvollziehbare Berechnungsgrundlage stehen im Mittelpunkt.

## 2. Projektstatus und Leitlinien

Der reguläre Build enthält 20 Kommunen. Die lokale Erweiterungsvorschau umfasst 49 Kommunen. [Datenpipeline](DATENPIPELINE.md) und [Erweiterungsintegration](ERWEITERUNGSINTEGRATION.md) dokumentieren Datensätze, Prüfung und Freigabe.

Der Projektchat kann auf Deutsch oder Englisch geführt werden. Projektdokumentation wird auf Deutsch geschrieben. Bezeichner und Kommentare im Code werden auf Englisch geschrieben.

## 3. Geografischer Umfang

Der erste Erhebungsumfang umfasste Leonberg, Gerlingen, Ditzingen, Stuttgart, Korntal-Münchingen, Kornwestheim, Ludwigsburg, Leinfelden-Echterdingen, Böblingen, Sindelfingen, Esslingen am Neckar und Fellbach. Die erste Erweiterung betrachtet ihre 33 direkten Nachbarn. Vier weitere Kommunen wurden am 20. November separat erhoben. Die Ausweitung erfolgt schrittweise. [Nachbarliste](DATENERWEITERUNG.md) · [Zweite Erhebung](DATENERHEBUNG_2026-11-20.md)

### 3.1 Geografische Einheiten für die Karte

Die Karte bildet Gemeinde- und Stadtgebiete als Flächen ab. Einrichtungen dienen als Quelle für Buchbarkeit und Geltung. Die Karte enthält keine Einrichtungspunkte. Stuttgart wird als eine Kommune dargestellt. Eine Untereinheit ist möglich, wenn dort abweichende Tarife belegt sind. Der amtliche Gemeindeschlüssel verbindet die Tarifgebiete mit den BKG-Grenzen.

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

Für neue oder geänderte Kommunen gelten acht feste und bis zu vier zusätzliche Stichproben. Der Ablauf und die erwarteten Nachweise stehen in der [Datenpipeline](DATENPIPELINE.md).

## 7. Kartenanwendung und Vergleich

### 7.1 Oberfläche

Der Familienatlas verbindet die verschiebbare, zoombare Karte mit den Details der ausgewählten Kommune. Die Vergleichsliste ist von teuer bis günstig sortiert und zeigt die Details direkt beim ausgewählten Eintrag. Aufklappbare Kinderdetails zeigen Einzelbeiträge, tatsächliche Wochenstunden, Verpflegung, Zusatzkosten und Quellen. Kartennamen werden nach verfügbarem Platz eingeblendet. Die ausgewählte Kommune erhält Vorrang bei der Platzierung. Die Farblegende reicht von „günstig“ bis „teuer“. Fehlende Ergebnisse haben eine eigene graue Darstellung.

### 7.2 Modellfamilie und Eingaben

Die Ausgangskonfiguration **Modellfamilie** besteht aus zwei zusammenlebenden Eltern, einem zweijährigen Krippenkind mit acht Stunden Betreuungsbedarf und 80.000 € Haushaltsjahresbrutto. Das Profil ist eine vereinbarte Modellannahme. Der Vergleichsstichtag steht im [Kartenprofil](../data/profiles/default.json). Die Oberfläche kennzeichnet die Datenerhebung separat.

Die **Vergleichsfamilie** bietet zusammenlebende Eltern oder Alleinerziehung, ein bis vier Kinder, die Kategorien Krippe, Kindergarten, Schulkind und zu Hause betreut, sechs Bruttoszenarien von 40.000 bis 180.000 € und sechs oder acht Stunden Bedarf je Kita-Kind. Steuer- und Nettowerte werden für die jeweiligen kommunalen Regeln modelliert. Das frühere persönliche Formular und die Höchsttarifreferenz bleiben im Projekt als interne Referenzen erhalten. [Modellfamilien](MODELLFAMILIEN.md)

### 7.3 Angebotsauswahl und Monatswert

Maßgeblich ist das [Regelwerk für die Kita-Gebührenanalyse](REGELWERK_DATENANALYSE.md). Die Auswahl setzt ein belegtes Fünf-Tage-Angebot voraus. Das 6-Stunden-Modell sucht den Wochenumfang am nächsten zu 30 Stunden bei mindestens 30 Stunden. Das 8-Stunden-Modell sucht den Umfang am nächsten zu 40 Stunden bei mindestens 36 Stunden. Bei gleichem Abstand gewinnt der größere Umfang. Die tatsächlichen Wochenstunden werden angegeben.

Karte und Liste zeigen die Summe der Jahresbeiträge aller betreuten Kita-Kinder geteilt durch zwölf. Der Tarifstand bleibt für die Umrechnung konstant. Fehlt für ein Kind ein belegter Beitrag, bleibt die Familiensumme nicht berechenbar. Verpflegung und Zusatzkosten werden grundsätzlich separat ausgewiesen. Bei enthaltenem Essen ohne belegbaren Abzugsbetrag bleibt der veröffentlichte Gesamtpreis maßgeblich. Die Details kennzeichnen die enthaltene Essenspauschale. Dokumentierte örtliche Entscheidungen, etwa zu Waiblingen, Aichwald und Schwieberdingen, folgen dem Regelwerk und den jeweiligen Katalogen.

## 8. Technische Leitplanken

- Statischer Betrieb auf GitHub Pages mit React, Vite, Leaflet, TypeScript und Zod. Tarifprüfung und Datenaufbereitung laufen vor der Auslieferung. Die Berechnung der Modellfamilien läuft im Browser.
- Ein gemeinsames JSON-Schema, ein Tarifkatalog pro Kommune und ein Register für aktive Gebiete, AGS, Tarife und Geometrien. Die Website hält keine eigene feste Kommunenliste.
- BKG-Gemeindegrenzen in vereinfachtem GeoJSON. Der Build prüft Zuordnung, Quelle und Größenbudgets. Die Anwendung unterstützt Desktop, Mobilgeräte und Tastaturbedienung.
- Ein Backend oder regionales Nachladen bleibt eine spätere Option, wenn Datenmenge oder Pflegeaufwand es erfordern. [Webanwendung](WEBANWENDUNG.md) · [Datenmodell](DATENMODELL.md)

## 9. Aufnahme und Veröffentlichung

Für neue Gebiete zuerst offizielle Quellen sichern und die Kataloge normalisieren. Danach die erwarteten Beträge, tatsächlichen Wochenstunden und belegten Datenlücken anhand begrenzter Stichproben prüfen. Die lokale Vorschau dient der Sichtung. Für die Veröffentlichung ist eine eigene Freigabe erforderlich. Die bestehende Freigabesicherung und der Ablauf für weitere Importe stehen in der [Datenpipeline](DATENPIPELINE.md).

## 10. Abnahmekriterien für Datensätze

- Quellenregister, Tarifgeltung und Gebietszuordnung sind vollständig nachvollziehbar.
- Veröffentlichte U3- und Ü3-Tarife und ihre Zeitmodelle sind quellenbezogen hinterlegt. Beiträge, Essensgeld, Gültigkeit und Ermäßigungen bleiben unterscheidbar.
- Fehlende oder mehrdeutige Angaben sind als solche dokumentiert. Die betroffenen Modellfälle liefern einen konkreten Grund statt eines geschätzten Tarifs.
- Schema und Quellprüfsummen sind geprüft. Die Stichproben belegen Preise, Wochenstunden und gegebenenfalls die erwartete Nichtverfügbarkeit.
- Karte, Liste und Details verwenden denselben Vergleichswert. Änderungen an der gemeinsamen Rechenlogik für einzelne Kommunen werden vorab abgestimmt. Für Schwieberdingen gilt die ausdrückliche Vorgabe, dafür keine Engineänderung vorzunehmen.

## 11. Offene Aufgaben und Entscheidungen

- Weitere Freigaben für die Erweiterungsvorschau nach fachlicher Prüfung.
- Rhythmus und mögliche Automatisierung des Quellenabgleichs und der Übernahme neuer Tarifstände.
- Historische Preisreihen, zusätzliche Sprachversionen und gegebenenfalls detailliertere Grenzdaten bleiben spätere Entscheidungen.
- Die Prüfung der Webseitentexte auf SEO bleibt vorgemerkt. [Offene Aufgabe](NAECHSTE_SESSION.md)
