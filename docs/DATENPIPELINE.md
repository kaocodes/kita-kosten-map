# Schlanke Tarifpipeline mit gezielten Stichproben

## Ziel

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
