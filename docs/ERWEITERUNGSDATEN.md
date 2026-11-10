# Aufbereitung der 33 Erweiterungskataloge

**Stand:** 2026-11-10. **Schritt 1 abgeschlossen:** Übertragung der aktuellen und bereits veröffentlichten künftigen Krippen-/Kindergartentarife in ein einheitliches Datenformat.

Erfasst sind **33 Kommunen**, **553 Angebote**, **4433 Preiszellen**, **51 Einkommensstufen** und **141 Zusatzkostenbausteine**. Formeltarife werden zusätzlich mit ihren Parametern gespeichert; eine fehlende Anzahl diskreter Preiszellen ist dort keine fehlende Tarifquelle.

## Ablage und Status

- Je Kommune eine JSON unter [`data/expansion/municipalities/`](../data/expansion/municipalities/), nach dem bestehenden [`municipality.schema.json`](../data/municipality.schema.json).
- [`data/expansion/manifest.json`](../data/expansion/manifest.json): vollständige Zuordnung, AGS, Dateipfade, Prüfsummen, Mengen und Umsetzungsgrenzen.
- [`Erweiterungsrecherche`](ERWEITERUNGSRECHERCHE.md): Quellenbewertungen, vereinbarte Annahmen und offene fachliche Fälle.
- `data/municipalities/` bleibt der produktive Bestand der zwölf bisherigen Kommunen. Der Importbereich wird weder von der laufenden Website noch vom normalen Export geladen.

Die Importdateien sind strukturiert und technisch geprüft. **Sie sind noch nicht pauschal für die Berechnung oder Veröffentlichung freigegeben.** Welche Modellkonfigurationen die bestehende Engine abbildet, ist inzwischen in der [Kompatibilitätsprüfung aus Schritt 2](ERWEITERUNGSBERECHNUNG.md) und ihrem eigenen Prüfindex dokumentiert. Manifest und Importstatus beschreiben den reproduzierbaren Normalisierungsstand; die zusätzliche Freigabe ist konfigurationsabhängig. Die gemeinsame Python-/TypeScript-Berechnungsengine und das produktive Register wurden nicht verändert. Für Schwieberdingen erfolgen keine Engineänderungen; Änderungen an der gemeinsamen Logik für einzelne Kommunen werden vorher mit dem Nutzer besprochen.

## Inhalt je Katalog

- `offers`: Originalmodell, Altersgruppe und gegebenenfalls Altersmischung, Anbieter-/Zeitvariante, Gültigkeit, Originalpreisstand, Beitragsmonate und belegte Tages-/Wochenzeiten. Unbelegte Tagesverteilungen bleiben `null`; Tarifobergrenzen sind als Obergrenzen gekennzeichnet.
- `prices`: veröffentlichte Monatsbeträge mit Familien-, Einkommens-, Pass- oder Rangzuordnung und Quellenfundstelle. Aus belegten Tarifbausteinen zusammengesetzte Beträge haben einen Rechenweg. Teilbeträge, etwa tageweise Rutesheimer GT-Gebühren ohne übrige Regelgruppentage, werden ausdrücklich als Teilbetrag gekennzeichnet.
- `income_bands`: Einkommensbegriff, Monats-/Jahresbezug, zeitlicher Bezug und wörtliche Grenzen. Keine erfundene Brutto-Netto-Umrechnung und kein Auffüllen unbekannter Grenzfälle.
- `components`: Verpflegung und weitere Kosten mit eigener Einheit, Pflichtstatus, Zuordnung und Beitragsmonaten. Unbekannt ist `null`, belegte Gebührenfreiheit `0`; enthaltenes Essen wird nicht als kostenlos ausgegeben oder nochmals addiert.
- `rules`: typisierte Parameter für Formeln, Ermäßigungen, Rundung, Alterswechsel und Nutzerentscheidungen sowie Verweise auf erhaltene Gebührenklauseln. `documented_not_implemented` beschreibt den Importstatus und behauptet keine Unterstützung durch die bestehende Engine.
- `original_research`: erhaltene Originalklauseln mit Fundstellen und Forschungsnotizen. Die vorhandene Browserprojektion entfernt dieses Feld; die dokumentarischen Texte müssen nicht in den Browser übertragen werden.
- `issues` / `coverage`: Quellenprobleme, nicht berechenbare Konfigurationen, Erfassungsumfang und noch ausstehende Rechenfreigabe.

Alle Geldbeträge sind ganzzahlige Centwerte, Zeiten Minuten. Beitragsmonate bleiben je Angebot/Kostenbaustein gespeichert. Bei Freiberg sind es U3 zwölf und Ü3 elf. Amtlicher Nachweis, Ableitung und ausdrückliche Nutzerangabe bleiben unterscheidbar.

## Erfassungsgrenzen

Aktuelle Krippen- und Kindergartentarife sowie in denselben Quellen bereits veröffentlichte künftige Fassungen sind übertragen. Überholte historische Tabellen, Schulkindbetreuung, TAKKI/Kindertagespflege und separate Spielgruppen gehören nicht zu den regulären Vergleichspreiszeilen. Ihre Originalunterlagen bleiben erhalten; ergänzende Klauseln sind dokumentiert. Es wird keine historische Preisreihe angelegt.

Eine Tabelle kann einen Tarif nennen, ohne die Buchbarkeit einer konkreten Tagesverteilung zu belegen. Dies bleibt beispielsweise bei einzelnen Ostfilderner Stundenklassen und bei der widersprüchlichen Benninger VÖ-Zeit offen. Der Schuljahresbeginn für die nur als 2026/2027 bezeichneten Tabellen in Altbach und Benningen ist ausdrücklich als Ableitung gekennzeichnet.

## Besonderheiten für Rechenprüfung und Integration

- **Denkendorf:** Jahresbrutto direkt verwenden; die genehmigte Ausnahme betrifft ausschließlich einen kürzeren Freitag bei ausreichender Betreuung Montag bis Donnerstag. Tatsächliche Zeiten und verpflichtendes GT-Essen mit unbekanntem Betrag bleiben sichtbar zu machen.
- **Schwieberdingen:** elf Monate gemäß Nutzerbestätigung; die vereinbarte kumulative U3-Stufenregel ist als Modellannahme dokumentiert. Preiswirksame ungeklärte Ü3-Ränge und fehlende dritte Rangzellen bleiben `unavailable` / „Nicht berechenbar“.
- **Aichwald:** Originalpreise einschließlich Verpflegung bleiben erhalten; die getrennten Betreuungsanteile stehen ergänzend daneben. Für U3 gelten die vereinbarten 53 Euro, für Ü3 die belegte Differenz zwischen den Tabellen mit und ohne Essen. Kein pauschaler 53-Euro-Abzug bei Ü3.
- **Waiblingen:** Prozentformeln mit Mindest-/Höchstbeitrag und Geburtsrang bleiben unverändert; enthaltenes Mittagessen bleibt Bestandteil des Kartenwerts und wird ohne weiteren Zuschlag als enthalten gekennzeichnet.
- **Renningen:** stündlicher Sockelbetrag und Zuschlag ab der 31. Stunde sind als Parameter erhalten. Die monatliche Umsetzung der Ü3-Stundenformel benötigt noch die folgende Rechenprüfung; der Stundenwert wird nicht als fertiger Monatsbeitrag gespeichert.
- **Asperg:** künftige Fassungen ab Januar und September 2027 getrennt. Die auffällige veröffentlichte Zelle für U3 GT9,5 an drei Tagen, vier Kinder, September 2027 bleibt unverändert; keine vermutete Korrektur.
- **Marbach:** kommunale Satzung als maßgeblicher Preis- und Pflichtessensbeleg; abweichender Essenshinweis der ergänzenden Trägerseite als Konflikt dokumentiert.

## Übersicht

| Kommune | Angebote | Preiszellen | Einkommensstufen | Zusatzkosten | Status |
|---|---:|---:|---:|---:|---|
| [Affalterbach](../data/expansion/municipalities/affalterbach.json) | 3 | 12 | 0 | 1 | Kompatibilität separat bewertet |
| [Aichwald](../data/expansion/municipalities/aichwald.json) | 13 | 52 | 0 | 2 | Kompatibilität separat bewertet |
| [Aidlingen](../data/expansion/municipalities/aidlingen.json) | 12 | 48 | 0 | 1 | Kompatibilität separat bewertet |
| [Altbach](../data/expansion/municipalities/altbach.json) | 6 | 24 | 0 | 5 | Kompatibilität separat bewertet |
| [Asperg](../data/expansion/municipalities/asperg.json) | 37 | 148 | 0 | 7 | Kompatibilität separat bewertet |
| [Baltmannsweiler](../data/expansion/municipalities/baltmannsweiler.json) | 16 | 64 | 0 | 10 | Kompatibilität separat bewertet |
| [Benningen am Neckar](../data/expansion/municipalities/benningen.json) | 9 | 36 | 0 | 11 | Kompatibilität separat bewertet |
| [Deizisau](../data/expansion/municipalities/deizisau.json) | 12 | 48 | 0 | 1 | Kompatibilität separat bewertet |
| [Denkendorf](../data/expansion/municipalities/denkendorf.json) | 5 | 120 | 6 | 1 | Kompatibilität separat bewertet |
| [Eberdingen](../data/expansion/municipalities/eberdingen.json) | 4 | 12 | 2 | 1 | Kompatibilität separat bewertet |
| [Ehningen](../data/expansion/municipalities/ehningen.json) | 30 | 120 | 0 | 1 | Kompatibilität separat bewertet |
| [Erdmannhausen](../data/expansion/municipalities/erdmannhausen.json) | 36 | 144 | 3 | 5 | Kompatibilität separat bewertet |
| [Filderstadt](../data/expansion/municipalities/filderstadt.json) | 44 | 176 | 0 | 12 | Kompatibilität separat bewertet |
| [Freiberg am Neckar](../data/expansion/municipalities/freiberg.json) | 27 | 312 | 8 | 14 | Kompatibilität separat bewertet |
| [Grafenau](../data/expansion/municipalities/grafenau.json) | 20 | 80 | 0 | 1 | Kompatibilität separat bewertet |
| [Hemmingen](../data/expansion/municipalities/hemmingen.json) | 8 | 40 | 0 | 0 | Kompatibilität separat bewertet |
| [Holzgerlingen](../data/expansion/municipalities/holzgerlingen.json) | 8 | 32 | 0 | 5 | Kompatibilität separat bewertet |
| [Kernen im Remstal](../data/expansion/municipalities/kernen.json) | 36 | 432 | 20 | 4 | Kompatibilität separat bewertet |
| [Magstadt](../data/expansion/municipalities/magstadt.json) | 6 | 30 | 0 | 1 | Kompatibilität separat bewertet |
| [Marbach am Neckar](../data/expansion/municipalities/marbach.json) | 16 | 64 | 0 | 3 | Kompatibilität separat bewertet |
| [Möglingen](../data/expansion/municipalities/moeglingen.json) | 10 | 80 | 0 | 3 | Kompatibilität separat bewertet |
| [Ostfildern](../data/expansion/municipalities/ostfildern.json) | 40 | 1920 | 12 | 1 | Kompatibilität separat bewertet |
| [Plochingen](../data/expansion/municipalities/plochingen.json) | 13 | 52 | 0 | 10 | Kompatibilität separat bewertet |
| [Remseck am Neckar](../data/expansion/municipalities/remseck.json) | 7 | 35 | 0 | 2 | Kompatibilität separat bewertet |
| [Renningen](../data/expansion/municipalities/renningen.json) | 10 | 24 | 0 | 1 | Kompatibilität separat bewertet |
| [Rutesheim](../data/expansion/municipalities/rutesheim.json) | 44 | 66 | 0 | 7 | Kompatibilität separat bewertet |
| [Schönaich](../data/expansion/municipalities/schoenaich.json) | 4 | 16 | 0 | 4 | Kompatibilität separat bewertet |
| [Schwieberdingen](../data/expansion/municipalities/schwieberdingen.json) | 10 | 50 | 0 | 5 | Kompatibilität separat bewertet |
| [Steinenbronn](../data/expansion/municipalities/steinenbronn.json) | 15 | 60 | 0 | 1 | Kompatibilität separat bewertet |
| [Tamm](../data/expansion/municipalities/tamm.json) | 5 | 20 | 0 | 5 | Kompatibilität separat bewertet |
| [Waiblingen](../data/expansion/municipalities/waiblingen.json) | 15 | 0 | 0 | 12 | Kompatibilität separat bewertet |
| [Waldenbuch](../data/expansion/municipalities/waldenbuch.json) | 12 | 36 | 0 | 1 | Kompatibilität separat bewertet |
| [Weissach](../data/expansion/municipalities/weissach.json) | 20 | 80 | 0 | 3 | Kompatibilität separat bewertet |

## Reproduzierbare Prüfung

```bash
python3 scripts/normalize_expansion_tariffs.py --check
python3 scripts/validate_expansion_catalogs.py
python3 -m unittest discover -s tests -v
```

Ohne `--check` erzeugt der Normalisierer die 33 Importdateien, das Manifest und diesen Bericht neu. Alle Kataloge werden vor dem Schreiben gemeinsam geprüft. Die Validierung verwendet ein ausschließlich im Speicher ergänztes inaktives Register für die geografische Zuordnung; die produktive Registerdatei bleibt unverändert.

Die Prüfungen sichern Format, IDs, Selektoren, Geld-/Zeitwerte, Quellenfundstellen, archivierte Prüfsummen und reproduzierbare Ausgabe. Die Importtests gleichen außerdem alle 1.920 Ostfilderner U3-/Ü3-Preiszellen gegen den archivierten PDF-Text und die bisherigen Kontrollzellen aller 33 Kommunen gegen die Kataloge ab. Dies ersetzt weder die vollständige fachliche Rechenprüfung noch die Website-Abnahme.
