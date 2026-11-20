# Schlanke Tarifpipeline mit gezielten Stichproben

## Ziel

Für neue Prüfungen gelten die Vorgaben im [Regelwerk für die Kita-Gebührenanalyse](REGELWERK_DATENANALYSE.md).

Ein gemeinsamer JSON-Katalog je Kommune dient als Eingabe für die Berechnung und die Website. Die Pipeline liest bekannte Gebührenformate automatisch aus, wertet wiederkehrende Tarifregeln aus und meldet konkrete Lücken. Die 33 vorhandenen Kataloge bilden den Ausgangspunkt. **Pro geänderter Kommune werden höchstens zwölf Familienkonfigurationen stichprobenartig geprüft.**

## Daten und Import

- Das vorhandene Kommunenschema für Angebote, Preiszeilen, Einkommensstufen, Zusatzkosten und Regeln weiterverwenden. Beträge werden in Cent, Zeiten in Minuten erfasst. Tarifwerte und Bedingungen behalten ihre Quellenfundstelle und Gültigkeit.
- Textbasierte PDFs und HTML-Tabellen über wiederverwendbare Importprofile auslesen. Vorhandene Transkriptionen bildbasierter Tabellen übernehmen. Bei einem unbekannten Layout oder widersprüchlichen Angaben meldet die Pipeline die betroffene Tabelle und den offenen Punkt.
- Den Quellabgleich zunächst manuell auslösen. Neue Fassungen anhand ihrer Prüfsumme erkennen und archivieren. Der Bericht zeigt Änderungen an Preisen, Bedingungen und Gültigkeit. Nur Änderungen mit Auswirkungen auf den Tarif lösen die erneute Stichprobenprüfung der Kommune aus.

## Berechnung und Freigabe

- Tabellenpreise, Wochenstundensätze und einkommensabhängige Beiträge über gemeinsame Regeltypen auswerten. Geschwisterrang, Familienstufen und die Behandlung enthaltener Verpflegung als Tarifdaten hinterlegen. Für Schwieberdingen gelten die dokumentierten Fallgrenzen.
- Den Kartenwert weiterhin aus der Summe der Jahresbeiträge aller betreuten Kinder geteilt durch zwölf bilden. Jeder Jahresbeitrag ergibt sich aus dem örtlichen Monatsbeitrag und den Beitragsmonaten des gewählten Angebots.
- **Den geprüften Tarifstand freigeben und die jeweilige Familienauswahl beim Aufruf prüfen.** Der Rechner zeigt einen Betrag, wenn er für alle betreuten Kinder ein eindeutiges Angebot mit vollständigen Tarifangaben und unterstützten Regeln bestimmen kann. Unbelegte Tageszeiten, fehlende örtliche Einkommenswerte oder eine preiswirksame ungeklärte Rangfolge ergeben „Nicht berechenbar“ mit Grund. Karte, Liste und Details verwenden dasselbe Ergebnis.
- Die Freigabe an Tarifstand, Quellen, Stichtag und Rechenlogik binden. Der Build prüft diese Zuordnung. Die Stichproben prüfen die Umsetzung am Tarifstand. Für die Anzeige weiterer Familienauswahlen gelten die Prüfung der Tarifvoraussetzungen und die Regeln zur eindeutigen Berechnung beim Aufruf.

## Stichproben und Einführung

- **Acht feste Stichproben** verwenden. Bei zwei zusammenlebenden Eltern und 80.000 € Haushaltsbrutto werden je ein Krippen- und Kindergartenkind mit sechs und acht Stunden geprüft. Dazu kommen eine Familie mit zwei betreuten Kindern, eine mit einem betreuten Kind und Schulgeschwister sowie eine mit vier Kindern und gemischter Betreuung. Als achter Fall wird das Kindergartenkind mit acht Stunden bei Alleinerziehung geprüft.
- **Bis zu vier Zusatzfälle** nach den preiswirksamen Änderungen auswählen, etwa an einer Einkommensgrenze, bei abweichenden Beitragsmonaten oder einer geänderten Geschwisterregel. Erwartete Beträge oder Ablehnungsgründe aus den Quellen festhalten. Gemeinsame Rechenregeln und ihre Grenzfälle einmal zentral in Python und TypeScript prüfen.
- Alle 33 Kataloge strukturell validieren. Die Stichproben dienen der fachlichen Abnahme je Tarifstand. Bei einer gemeinsamen Regeländerung werden die betroffenen Kommunen erneut anhand derselben begrenzten Auswahl geprüft.
- In der lokalen Vorschau Stichproben der 20 veröffentlichten Kommunen mit dem bisherigen Stand vergleichen. Zusätzlich eine teilweise berechenbare Kommune prüfen, die je nach Familienauswahl einen belegten Betrag oder einen konkreten Ablehnungsgrund zeigt. Der Bericht listet die geprüften Fälle und offenen Quellenfragen je Kommune für die nächste Veröffentlichung auf.

### Aichwald

Für Aichwald verwendet der Browserexport den bereits im Import gespeicherten Betreuungsanteil. Er prüft ihn gegen den Originalpreis und den für das Angebot hinterlegten Essensanteil. Die kanonischen Tarifzeilen bleiben erhalten. Bei gleicher Betreuungszeit und gleichem Betreuungsanteil bündelt der Export die Varianten mit und ohne Essen zu einem Angebot mit optionalem Mittagessen.

Der bisherige Browserexport verwendet das Paket mit fünf langen Tagen. In der Tarifprüfung gilt für U3 und Ü3 das Paket mit drei langen Tagen und 42 Std. 30 Min. Bei U3 sind zwei kurze Tage bis 14 Uhr eine Nutzerfestlegung. Für Ü3 ergibt sich derselbe Umfang aus dem veröffentlichten VÖ-Modell mit drei Ganztagsnachmittagen. Aichwald ist weiterhin im Erweiterungsbestand. [Zeitpaketprüfung](TARIFAUSWAHL.md#abschluss-der-zwölf-offenen-zeitprüfungen)

## Stichproben zur Übertragung der Regeln

Acht Varianten je Kommune prüfen die vier Kombinationen aus Alter und Betreuungsdauer sowie Geschwister, Schulkind und Alleinerziehung. Grundlage sind die Modellwerte zum 4. November 2026. Die geprüften Beträge und Fälle stehen in den [Webtests](../web/tests/model-family.test.mjs). Die Tarifstände liegen im Erweiterungsbestand.

| Kommune | Quellenabgleich und Ergebnis |
|---|---|
| Affalterbach | 40 Wochenstunden mit verkürztem Freitag. U3 und Ü3 jeweils für sechs und acht Stunden berechenbar. |
| Aichwald | Betreuungsanteil und beziffertes Essen separat. Das belegte Fünf-Tage-Paket deckt den Acht-Stunden-Bedarf. |
| Altbach | 30-Stunden-VÖ und 40-Stunden-Ganztag aus Tarif und [kommunaler Angebotsseite](https://www.altbach.de/leben-wohnen/kindergaerten/kommunale-kindergaerten) zusammengeführt. Elf Beiträge. Günstigere U3-Mischtarife bleiben mit eigener Angebotszuordnung im Archiv. |
| Baltmannsweiler | [Kindervilla Kunterbunt](https://www.baltmannsweiler.de/leben-wohnen/kinderbetreuung/kindervilla-kunterbunt) belegt HT/VÖ/VÖ XL. [Kinderhaus Arche Noah](https://www.baltmannsweiler.de/leben-wohnen/kinderbetreuung/kinderhaus-arche-noah) belegt Ü3-Ganztag mit drei oder vier langen Tagen. Der freitags verkürzte Vier-Tage-Tarif deckt Ü3 acht Stunden. U3 reicht bis 35 Wochenstunden und hat kein passendes Acht-Stunden-Angebot. |
| Benningen am Neckar | Die Aufnahmeanträge für [Kindergarten](https://www.benningen.de/fileadmin/Dateien/Dateien/Aufnahmeantrag_fuer_Kinder_in_Benninger_Kindergaerten-01-09-2025.pdf) und [Krippe](https://www.benningen.de/fileadmin/Dateien/Dateien/Aufnahmeantrag_-_Kinderkrippe-_Ver.2-Stand_2025.pdf) bestätigen 6,5 zusammenhängende VÖ-Stunden. Die Gebührentabelle 2026/2027 belegt Mo–Do 9,5 Stunden und Fr 7,5 Stunden für Ganztag. Elf Beitragsmonate. Essenspauschalen nach Tarifalter und Angebot getrennt. Die genaue Verteilung des Drei-Tage-Ganztags und eine Preisstufe ab fünf Haushaltskindern sind offen. |
| Denkendorf | Freitags sieben Stunden. Mittagessen nur bei den Ganztagsangeboten als Pflichtkosten ohne bezifferten Betrag erfasst. |
| Grafenau | Ü3 acht Stunden mit vier langen Tagen und Freitag VÖ, zusammen 44 Stunden. U3 höchstens drei lange Tage gemäß § 2 der Gebührensatzung. Mittagessen betrifft die Ganztagstarife und wird separat über den Caterer abgerechnet. |
| Plochingen | [Städtisches Angebot](https://www.plochingen.de/start/leben%20_%20wohnen/kinderbetreuungsangebote.html) belegt die VÖ für zwei- bis sechsjährige Kinder und den Freitag mit sechs Stunden bei Ganztag. Der Webexport filtert die ausdrücklich separat zugeordneten Tarife des katholischen Kinderhauses St. Johann. |
| Steinenbronn | Die [kommunale Angebotsübersicht](https://www.steinenbronn.de/leben-wohnen/kinder/kindertageseinrichtungen) belegt sieben Stunden in der Krippe und die Satzung das kürzere Ü3-Angebot mit 6,5 Stunden. Bis zu drei lange Nachmittage reichen für die Freitagsregel in beiden Altersgruppen nicht aus. Zwölf Beiträge nach Nutzerfestlegung. |
| Weissach | Das [verlinkte Modellblatt](https://www.kitas-weissach.de/fileadmin/KiTas_Weissach/Dateien/Betreuungsmodelle_Webseite.pdf) und die [kommunale Ferry-Porsche-Kita](https://www.kitas-weissach.de/kindergaerten/ferry-porsche-kita) bestätigen die Zeitmodelle. Die Tarifzellen bis vier Kinder und die getrennten Verpflegungspauschalen wurden überprüft. Ab fünf Haushaltskindern fehlt eine Tarifstufe. |

Separat verlangte Essensbeträge können offen sein, wenn die Betreuungskosten vollständig belegt sind. Ein fehlendes Acht-Stunden-Angebot wird in den Stichproben als nicht berechenbar behandelt.

## Teilprüfung Erdmannhausen, Filderstadt und Freiberg am Neckar

- **Erdmannhausen.** Der Scan der [Voranmeldeunterlagen](https://www.erdmannhausen.de/fileadmin/media/dokumente/Formulare/Unterlagen_Voranmeldung_Kindertageseinrichtung_ab_01.09.2026.pdf), Anlage 4, bestätigt für zwei Haushaltskinder 372,00 € Krippen-Grundbeitrag und bei Ermäßigung 260,40 €. Die Transkription wurde berichtigt. Für ein Kita-Kind ohne Einkommensrabatt setzt sich der Fünf-Tage-Ganztag aus 650,60 € U3 bzw. 357,70 € Ü3 Betreuung und 84,00 € Essen zusammen. Alleinerziehung verschiebt die Haushaltsstufe. Die einkommensabhängige Ermäßigung von 30 % betrifft den Grundbeitrag, die Geschwisterermäßigung von 50 % den Zuschlag bei gleichzeitiger Ganztagsbetreuung. Für mehrere gleichzeitig betreute Kinder fehlt ein amtliches Rechenbeispiel zur Zuordnung des halben Zuschlags.
- **Filderstadt.** Die 30-Stunden-Grundbuchung ist für beide Altersgruppen mit Mo–Fr 08:00–14:00 Uhr anhand der städtischen Broschüre belegt. Als Ganztagsreferenz hat Jahnareal Mo–Do acht und Fr sieben Stunden geöffnet. Ob für den Bedarf mit verkürztem Freitag die günstigere 38-Stunden-Kombination tatsächlich buchbar ist, geht aus den Unterlagen nicht eindeutig hervor.
- **Freiberg am Neckar.** Die [städtischen Angebotsseiten](https://www.freiberg-an.de/de/bildung-betreuung-soziales/kinderbetreuung/kindergaerten) bestätigen Ü3-Ganztag Mo–Fr 07:00–15:00 Uhr bzw. 07:00–16:00 Uhr. Die VÖ-Lebensmittelpauschale und das GT-Mittagessen sind den jeweiligen Angeboten zugeordnet. Für U3 und Ü3 bestimmt das [Nettomodell](MODELLFAMILIEN.md#monatliches-lohnnetto-für-nettotarife) die örtliche Stufe aus modelliertem Lohnnetto und Kindergeld. Stufe 2 ohne Nachweis ist in der Satzung belegt. Die Geschwisterrangfolge berücksichtigt auch Kinder in der Freiberger Schulkindbetreuung. Die derzeitige Modellkategorie Schulkind unterscheidet die Teilnahme daran nicht.

## Prüfung der übrigen offenen Kommunen

Geprüft wurden Tarifstand, belegte Tageszeiten und preiswirksame Sonderregeln. Wenn eine Rechenvoraussetzung offen bleibt, gilt die Stichprobe nur für die ausdrücklich belegte Konfiguration im Erweiterungsbestand. Die veröffentlichten 20 Kommunen bilden weiterhin den Ausgangsstand.

Die Zeitangaben dieses Abschnitts beziehen sich auf den damaligen Prüfstand. Für die aktuelle Auswahl gelten die [Nachprüfung nach Wochenzielen](TARIFAUSWAHL.md#nachprüfung-nach-wochenzielen) und der [Abschluss der zwölf offenen Zeitprüfungen](TARIFAUSWAHL.md#abschluss-der-zwölf-offenen-zeitprüfungen).

Der Modellvergleich ist auf ein bis vier Haushaltskinder begrenzt. Tarifzeilen und Ermäßigungen ab fünf Kindern bleiben Quellenmaterial. Sie sind damit für die Modellfreigabe keine Voraussetzung. Für Ostfildern ist die Wahl des Vorjahreseinkommens durch den Ansatz des ausgewählten Haushaltsjahresbruttos geklärt. Die örtlichen Reihenfolgen nach dem jüngsten betreuten Kind in Eberdingen und Freiberg gelten weiterhin für die fachliche Rangprüfung. [Regelwerk](REGELWERK_DATENANALYSE.md)

| Kommune | Bestätigt oder ergänzt | Vor einer Freigabe offen |
|---|---|---|
| Eberdingen | Der Masterplan, S. 10, ordnet Platzzusagen ab 01.07.2023 dem neuen System zu. Das ältere System gilt übergangsweise. Im neuen System gibt es VÖ mit sechs und Ganztag mit 7,5 Stunden täglich. | Den Vergleich ausdrücklich auf das neue System beziehen und die Reihenfolge nach dem jüngsten gleichzeitig betreuten Kind bei unterschiedlichen Betreuungszeiten abbilden. Die Acht-Stunden-Auswahl hat im neuen System kein passendes Angebot. |
| Hemmingen | Die [Einrichtungsübersicht](https://nhkita.hemmingen.de/uebersicht.html) nennt konkrete VÖ- und Ganztagszeiten. Die Beitragssatzung hat eigene Zeilen für Alleinerziehende mit einem Kind. | Zuordnung der Zeitfenster zu den Tarifvarianten einschließlich Spielgruppe/VÖ, Auswertung der besonderen Ein-Kind-Zeile und aktueller Essensbetrag. |
| Kernen im Remstal | Die Satzung nennt VÖ und Krippenangebote mit bis zu sechs Stunden täglich. Für Ganztag sieht sie Buchungsmodelle zwischen 40 und 48 Wochenstunden vor. | Die täglichen Zeiten und die Tarifzuordnung der konkreten Ganztagsplätze sowie ein Modellwert für das örtliche Monatsbrutto. Die zusätzlichen Rabatte sind typisiert und noch auszuführen. |
| Magstadt | Die Tariftabelle belegt GT8 für U3 und Ü3. Die VÖ-Befreiung betrifft jeweils das vierte und jedes weitere Haushaltskind unter 18. Die vorangehenden Kinder zahlen in solchen Haushalten den Beitrag der Drei-Kinder-Stufe. | Den Familienrang einschließlich älterer Geschwister abbilden, bevor VÖ-Fälle mit vier oder mehr Haushaltskindern freigegeben werden. |
| Ostfildern | § 8 belegt die Ü3-Grundbuchung mit fünfmal sechs Stunden. Sie ist im Datensatz hinterlegt. Ganztag hat 40 Wochenstunden als Grundbuchung; weitere fünf können zugebucht werden. | Für Ganztag die konkrete Wochentagsverteilung bestätigen und das örtliche Vorjahreseinkommen der Modellfamilien bestimmen. Die 50-Stunden-Tabellenspalte allein belegt keine Buchbarkeit. |
| Remseck am Neckar | Elf Beiträge für Betreuung und zehn für Essen. Die Essenspflicht ist den Ganztagsangeboten zugeordnet. Der 6-Stunden-Tarif der Altersmischung gilt ab zwei Jahren. Die Fußnote ab dem fünften Kind ist als Regel erfasst. | Klären, wie die Befreiung auf die Kinder einer Familie angewendet wird. Bei U3 bleiben die beiden altersabhängigen Essensbeträge als Varianten erhalten. Pattonville hat eigene Entgelte. |
| Renningen | VÖ6 und U3-GT40 sind mit Festpreisen berechenbar. Die [städtische Übersicht](https://www.renningen.de/renninger-in/familienportal/kinderbetreuung/kindergaerten/) belegt die Ü3-Zeiten für VÖ6, GT40 und GT46. | Ein amtliches Monatsbeispiel oder eine bestätigte Umrechnungsregel für den Ü3-Stundensockel und den Zuschlag ab Stunde 31. Bis dahin fehlt ein berechenbarer Ü3-Ganztagsbetrag. |
| Rutesheim | Die [städtische Öffnungszeitenübersicht](https://www.rutesheim.de/site/Rutesheim-Internet-2021/get/params_E-1082970528/19086738/Geb%C3%BChren.pdf) schließt die Zeitlücke für die Fünf-Tage-Pakete. Für das zweijährige U3-Modell sind die belegten Tarife im altersgemischten Kindergarten Richard-Wagner enthalten. | Den 50-€-Abzug bei gleichzeitig betreuten Geschwistern über Krippe, Ganztag und Hort richtig zuordnen. Die Familienpass-Ermäßigung hat eine separate Einkommensgrundlage. |
| Schönaich | Die Gemeinde belegt 51,5 Wochenstunden im [Ü3-Ganztag](https://kitas.schoenaich.de/kommunale-einrichtungen/kinderhaus-schoenaich/kontakt-oeffnungszeiten) und 37,5 in der [Ganztagskrippe Seestraße](https://kitas.schoenaich.de/kommunale-einrichtungen/kindertagesstaette-seestrasse/kontakt-oeffnungszeiten). | Für den günstigsten VÖ-Preis die konkret buchbare Wochenzeit und den anteiligen Mehrstundenbeitrag bestätigen. 37,5 Wochenstunden erfüllen das Acht-Stunden-Modell auch mit Freitagsregel nicht. |
| Schwieberdingen | Die [aktuelle Tabelle 2026](https://www.schwieberdingen.de/site/Schwieberdingen-2025/get/params_E415005327/25529925/Elternbeitraege%20in%20den%20gemeindli_2.pdf) bestätigt die dokumentierten Staffelpreise. | Ü3-Rang bei unterschiedlicher Betreuung, drittes gleichzeitig betreutes Ü3-Kind und fachliche Abbildung der vereinbarten Stufenverschiebungen. Betroffene Konfigurationen bleiben in der Freigabeprüfung gesperrt. |
| Waiblingen | § 5 knüpft die Kinderermäßigung an die Geburtenfolge der kindergeldberechtigten Kinder. Diese Bezugsgröße ist im Import berichtigt. Für die Karte gilt der veröffentlichte Preis inklusive Essen. | Modellannahme für das örtliche Jahresbrutto, Zuordnung konkreter Stundenpakete und Ausführung der Prozent- und Geburtsrangregeln. |
| Waldenbuch | Die [Stadt](https://www.waldenbuch.de/zielgruppen/start/kindergartengebuehren.html) bestätigt die Zeitfenster und das exakt passende 44-Stunden-Paket. | Die Buchungsverteilung der fünf Nachmittagsstunden im preiswerteren 40-Stunden-Tarif. Das [Vormerkportal](https://nhkita.waldenbuch.de/uebersicht.html) nennt teilweise noch 42,5 Stunden, die aktuelle Gebührentabelle nennt 40 Stunden. Eine täglich gleichmäßige Zubuchung ist nicht ausdrücklich veröffentlicht. |
| Weissach | Die [aktuelle Satzung](https://www.kitas-weissach.de/fileadmin/Dateien/Dateien/Kinderbetreuung/Satzung_Kitas_Schulkind_2026_2027.pdf) bestätigt die vorhandenen Tarife für ein bis vier Kinder. | Welcher Betrag für Familien ab fünf Haushaltskindern gilt. Die Zuordnung bleibt offen. |

## Erdmannhausen und Freiberg nach der Wochenstundenregel

Für den erneuten Einzelkind-Abgleich gelten fünf Betreuungstage und die Mindestumfänge von 30 bzw. 36 Wochenstunden sowie die Auswahl nach dem geringsten Abstand zu 30 bzw. 40 Stunden aus dem [Regelwerk](REGELWERK_DATENANALYSE.md). Beträge in der Tabelle sind monatliche Vergleichswerte für ein Kind ohne Sonderermäßigungen. Verpflegung ist separat erfasst.

| Kommune | Auswahl | Belegtes Paket am nächsten zur Zielgröße | Betreuung pro Monat |
|---|---|---|---:|
| Erdmannhausen | U3 · 6 Std. | 34 Std. 10 Min., VÖ an fünf Tagen | 500,60 € |
| Erdmannhausen | U3 · 8 Std. | 40 Std. 30 Min., drei Tage VÖ und zwei Ganztage | 600,60 € |
| Erdmannhausen | Ü3 · 6 Std. | 35 Std., VÖ an fünf Tagen | 207,70 € |
| Erdmannhausen | Ü3 · 8 Std. | 41 Std., drei Tage VÖ und zwei Ganztage | 307,70 € |
| Freiberg am Neckar | U3 · 6 Std. | 30 Std., Murmel halbtag | 345,00 € / 397,00 € |
| Freiberg am Neckar | U3 · 8 Std. | 40 Std., Flattichstraße GT40 | 452,00 € / 520,00 € |
| Freiberg am Neckar | Ü3 · 6 Std. | 30 Std., städtische Vormittagsgruppe | 209,92 € / 241,54 € |
| Freiberg am Neckar | Ü3 · 8 Std. | 40 Std., städtisches GT40 | 325,42 € / 374,00 € |

In Erdmannhausen sieht die [Voranmeldung](https://www.erdmannhausen.de/fileadmin/media/dokumente/Formulare/Unterlagen_Voranmeldung_Kindertageseinrichtung_ab_01.09.2026.pdf) Ganztag an einzeln wählbaren Tagen und VÖ an den übrigen Tagen vor. Zwei Ganztage pro Woche kosten 100 € Zuschlag zuzüglich 33,60 € verpflichtendem Essen pro Monat. Zwölf Betreuungsbeiträge sind aus der Benutzungsordnung abgeleitet. Die Tabellenwerte oben verwenden den Grundtarif bei 80.000 € Jahresbrutto. Die Zuordnung des halben GT-Zuschlags bei mehreren gleichzeitig betreuten Geschwistern bleibt gesondert zu klären.

Für U3 trifft das [GT40-Angebot in der Flattichstraße](https://www.zwergenstueble-freiberg.de/flattichstrasse/) die Zielgröße von 40 Wochenstunden genau. Die Halbtag-Plus-Pakete im Murmel umfassen 36 bzw. 37 Std. 30 Min. und liegen weiter vom Ziel entfernt. Die Freiberg-Werte stehen in der Reihenfolge Stufe 1 / Stufe 2 des monatlichen Haushaltsnettos. Das Paarmodell mit 80.000 € Jahresbrutto und einem Kind hat 4.769,67 € örtliches monatliches Haushaltsnetto und fällt in Stufe 1. U3 wird zwölfmal, Ü3 elfmal bezahlt. [Zwergenstüble-Gebührenordnung](https://www.zwergenstueble-freiberg.de/downloads/) · [Städtische Gebührenanlage](../data/sources/5f09f91f5eb1/text.txt)

Dieser Quellenabgleich beschreibt die Auswahl nach dem Regelwerk. Der Webrechner verwendet die Wochenziele. Die Nachprüfung und der Stand der Kartenfreigabe sind in der [Erweiterungsprüfung](ERWEITERUNGSBERECHNUNG.md#freigabeprüfung-der-13-kandidaten-nach-wochenzielen) dokumentiert.
