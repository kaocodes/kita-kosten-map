# Berechenbarkeit der 33 Erweiterungskataloge

**Prüfstand:** 2026-11-10. **Schritt 2 abgeschlossen:** Kompatibilitätsprüfung der bestehenden Engine und Kennzeichnung nicht berechenbarer Modellkonfigurationen.

Für die bisherige Modellfamilie sind **10 Kommunen berechenbar** und **23 nicht berechenbar**. Das ist keine Freischaltung. Die gemeinsame Engine und das produktive Kommunenregister bleiben unverändert.

## Prüfumfang

Geprüft wurden **2508 Konfigurationen je Kommune**, insgesamt **82764 Familienfälle**: ein bis vier Haushaltskinder, beide Haushaltskonstellationen, alle sechs Einkommensszenarien, Krippe/Kindergarten mit sechs oder acht Stunden sowie Schul- und zu Hause betreute Kinder. Kindreihenfolgen wurden als Multimengen abgedeckt und durch Umkehrung zusätzlich geprüft. Familien mit fünf bis zwölf Kindern, persönliche Eingaben, Pässe, außergewöhnliche Aufnahmefälle und künftige Tarifstichtage sind nicht freigegeben.

**15840 Einzelberechnungen** wurden zwischen unveränderter Python- und TypeScript-Engine abgeglichen; **80388 Reihenfolgeprüfungen** ergaben identische Familienbeträge/-status. Zusätzlich bestanden **61 ausdrücklich hinterlegte Quellen- und Ablehnungsfälle**. Diese technische Kompatibilitätsprüfung ersetzt die nachfolgende umfassende fachliche Quellenabnahme aus Schritt 3 nicht.

## Sicherheitsentscheidung

Die native Berechnung lieferte in **11280 geprüften Fällen** einen als vergleichbar bezeichneten Betrag, der wegen einer nicht berücksichtigten Bedingung oder ungeklärten Angebotsauswahl verworfen wurde. Die geprüften Ausgaben verwenden dann `status: unavailable`, konkrete Gründe und leere Geldfelder. Weder null Euro noch ein geratener Ersatzpreis wird ausgegeben. Ein separater Schutzschritt in der Offline-Prüfung erzeugt diese Freigabeentscheidung; die bestehende Engine selbst wurde nicht nachträglich umdefiniert.

Unbekannte separat zu erhebende Essenspreise sperren einen ansonsten belastbaren Betreuungskostenwert nicht automatisch. Ein falscher Essensabzug, Doppelansatz oder eine falsch zugeordnete Kostenvariante verhindert dagegen die Freigabe.

## Ergebnisse nach Kommune

| Kommune | Bisherige Modellfamilie | Berechenbare / geprüfte Konfigurationen mit Kita-Betreuung | Einschränkung |
|---|---|---:|---|
| Affalterbach | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt |
| Aichwald | Nicht berechenbar | 240 / 2340 | Enthaltenes Essen wird von der Ergebnisaufbereitung nicht als inklusive behandelt; Der native Kartenbetrag enthält einen bekannten abzutrennenden Essensanteil |
| Aidlingen | 700,00 € | 2340 / 2340 | Innerhalb des geprüften Modellumfangs unterstützt. |
| Altbach | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt |
| Asperg | 473,00 € | 2340 / 2340 | Innerhalb des geprüften Modellumfangs unterstützt. |
| Baltmannsweiler | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt |
| Benningen am Neckar | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt; Ein möglicherweise kleineres passendes Angebot ist nicht ausreichend zeitlich geklärt |
| Deizisau | 766,33 € | 2340 / 2340 | Innerhalb des geprüften Modellumfangs unterstützt. |
| Denkendorf | Nicht berechenbar | 660 / 2340 | Die genehmigte Freitagsausnahme ist nicht in die bestehende Auswahl integriert; Kein belegtes Angebot deckt den Bedarf an allen fünf Tagen |
| Eberdingen | Nicht berechenbar | 480 / 2340 | Die Rangverteilung erlaubt keinen eindeutigen Familienbetrag; Kein belegtes Angebot deckt den Bedarf an allen fünf Tagen |
| Ehningen | 910,25 € | 2340 / 2340 | Innerhalb des geprüften Modellumfangs unterstützt. |
| Erdmannhausen | Nicht berechenbar | 0 / 2340 | Passende Preiszelle oder örtliche Einkommensangabe fehlt; Das zusätzliche Haushaltskind bei Alleinerziehung wird nicht berücksichtigt |
| Filderstadt | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt |
| Freiberg am Neckar | Nicht berechenbar | 0 / 2340 | Für monatliches Haushaltsnetto liegt keine bestätigte Modellannahme vor; Die Rangverteilung erlaubt keinen eindeutigen Familienbetrag |
| Grafenau | Nicht berechenbar | 660 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt; Ein möglicherweise kleineres passendes Angebot ist nicht ausreichend zeitlich geklärt |
| Hemmingen | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt; Die zusätzliche Haushaltsbedingung an der Preiszelle wird nicht ausgewertet |
| Holzgerlingen | 670,00 € | 2340 / 2340 | Innerhalb des geprüften Modellumfangs unterstützt. |
| Kernen im Remstal | Nicht berechenbar | 0 / 2340 | Eine ausdrücklich bestätigte örtliche Einkommens-Modellannahme fehlt; Die zusätzliche Familienermäßigung wird nicht angewendet |
| Magstadt | 595,00 € | 1272 / 2340 | Der Familien-Geburtsrang wird nicht durch den Betreuungsrang abgebildet; Die Rangverteilung erlaubt keinen eindeutigen Familienbetrag |
| Marbach am Neckar | 655,42 € | 2340 / 2340 | Innerhalb des geprüften Modellumfangs unterstützt. |
| Möglingen | 432,00 € | 2340 / 2340 | Innerhalb des geprüften Modellumfangs unterstützt. |
| Ostfildern | Nicht berechenbar | 0 / 2340 | Eine ausdrücklich bestätigte örtliche Einkommens-Modellannahme fehlt; Eine benötigte Tagesverteilung ist nicht ausreichend belegt |
| Plochingen | Nicht berechenbar | 0 / 2340 | Ein möglicherweise kleineres passendes Angebot ist nicht ausreichend zeitlich geklärt; Der Geltungsbereich der ausgewählten Trägervariante ist noch zu bestätigen |
| Remseck am Neckar | Nicht berechenbar | 240 / 2340 | Eine Zusatzkostenvariante außerhalb der Alterszuordnung wird mit ausgegeben; Die Pflicht zur Verpflegung ist noch nicht passend nach Betreuungsumfang zugeordnet |
| Renningen | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt; Die gespeicherte Formelart wird von der bestehenden Engine nicht unterstützt |
| Rutesheim | Nicht berechenbar | 0 / 2340 | Die Rangverteilung erlaubt keinen eindeutigen Familienbetrag; Eine benötigte Tagesverteilung ist nicht ausreichend belegt |
| Schönaich | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt |
| Schwieberdingen | 512,42 € | 1632 / 2340 | Die erforderliche Alleinerziehenden-Stufenverschiebung wird nicht angewendet; Die Rangverteilung erlaubt keinen eindeutigen Familienbetrag |
| Steinenbronn | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt |
| Tamm | 628,00 € | 2340 / 2340 | Innerhalb des geprüften Modellumfangs unterstützt. |
| Waiblingen | Nicht berechenbar | 0 / 2340 | Die gespeicherte Formelart wird von der bestehenden Engine nicht unterstützt; Die vereinbarte Inklusivdarstellung ist noch nicht umgesetzt |
| Waldenbuch | Nicht berechenbar | 660 / 2340 | Ein möglicherweise kleineres passendes Angebot ist nicht ausreichend zeitlich geklärt |
| Weissach | Nicht berechenbar | 0 / 2340 | Eine benötigte Tagesverteilung ist nicht ausreichend belegt |

Die Zahlen schließen Familien ohne Kita-Kind aus; deren belegter Betreuungskostenwert null wird separat mitgeprüft. Ein berechenbarer Teilbereich bedeutet keine pauschale Freigabe der Kommune für alle Einstellungen.

## Konkrete Einschränkungen und nächste Arbeit

- **Schwieberdingen:** reguläre Tabellen können nur dort verwendet werden, wo die native Rechnung stimmt. Nicht ausgeführte Alleinerziehenden-/U3-Stufenverschiebungen, eine falsche Rangpopulation und ungeklärte Ü3-Ränge bleiben nicht berechenbar. Keine Sonderlogik wurde in die Engine eingebaut.
- **Denkendorf:** die genehmigte Freitagsausnahme ist dokumentiert; die unveränderte tägliche Bedarfsprüfung berücksichtigt diese noch nicht. Sechs-Stunden-Fälle werden davon getrennt geprüft.
- **Aichwald / Erdmannhausen:** die Originalpreise einschließlich Essen sind erhalten. Die laufende Engine liest ergänzende reine Betreuungsanteile nicht automatisch; solche Beträge werden nicht ungeprüft als Kartenwert freigegeben.
- **Freiberg / Kernen / Ostfildern / Waiblingen:** fehlende örtliche Modellannahmen werden nicht durch eine Brutto-Konvertierung ersetzt. Waiblingens Prozentformel und Inklusivdarstellung sowie Renningens Ü3-Stundenformel benötigen eine abgestimmte Lösung.
- **Weitere Datenarbeit:** fehlende Tagesverteilungen, unterschiedliche Kostenvarianten und besondere Preis-Selektoren werden mit konkretem Grund im Freigabeindex geführt. Datenkorrekturen sind von Änderungen der gemeinsamen Rechenlogik zu unterscheiden.

Änderungen der gemeinsamen Berechnungslogik für einzelne Kommunen werden vorab mit dem Nutzer besprochen. Für Schwieberdingen ist keine Engineänderung beauftragt. Schritt 3 bleibt die vertiefte Quellenabnahme der freizugebenden Ergebnisse, Schritt 4 die kontrollierte Integration.

## Ablage und Wiederholung

- [Maschinenlesbarer Freigabeindex](../data/expansion/calculation_review.json): geprüfter Umfang, Fallgruppen, Ablehnungsgründe und Standardergebnisse. Nicht berechenbare Standardergebnisse haben ausschließlich leere Geldfelder.
- [Prüfbedingungen](../data/reviews/expansion_compatibility_policy.json) und [Referenzfälle](../data/reviews/expansion_calculation_cases.json): Quellenbelege und ausdrückliche Entscheidungen.
- Rohproben und Profile bleiben unter `build/expansion-review/` und werden nicht veröffentlicht. Der produktive Export liest weiterhin nur die bisherigen zwölf Kommunen.

Der Freigabeindex ist ein Offline-Prüfergebnis, noch keine angeschlossene Laufzeitsperre. Eine spätere Veröffentlichung muss ihn wirksam beachten; die Importkataloge dürfen nicht ungeprüft aktiviert werden. Änderungen an Quellen, Katalogen, Modellprofilen, Engine oder Prüflogik machen die jeweilige Freigabe anhand gespeicherter Prüfsummen ungültig.

```bash
python3 scripts/review_expansion_compatibility.py
# Bereits vorhandene, unveränderte Rohproben erneut auswerten:
python3 scripts/review_expansion_compatibility.py --reuse-probes --check
```
