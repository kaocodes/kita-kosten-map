# Berechenbarkeit der 33 Erweiterungskataloge

## Nachprüfung der letzten zwölf Kommunen

Die Stichprobe verwendet den Tarifstand der Website vom 4. November 2026 und prüft je Kommune acht Modellfamilien mit 80.000 € Haushaltsjahresbrutto. Die Fälle decken beide Altersgruppen mit je zwei Zeitmodellen, Geschwister in und außerhalb der Kita, vier Kinder und Alleinerziehung ab. Zusätzliche Prüffälle kontrollieren gezielt einzelne Rabatte und Einkommensgrenzen. Von 96 Basisfällen liefern 91 einen Monatsbetrag. Die fünf Fälle mit Ü3-Ganztag in Renningen geben wegen der offenen Preisumrechnung korrekt „Nicht berechenbar“ aus. Die Prüfung läuft über `npm test`.

| Kommune | Übernommene Regel und verbleibende Lücke |
|---|---|
| Eberdingen | Bei gleichzeitig betreuten Kita-Kindern zählt das jüngste zuerst. Beide Altersgruppen haben im neuen Beitragssystem 37 Std. 30 Min. als nächstes Ganztagspaket. |
| Erdmannhausen | Das Wochenziel berücksichtigt buchbare GT-Nachmittage. Der Zuschlag halbiert sich für gleichzeitig im Ganztag betreute Geschwister. Das Essensgeld wird separat gezeigt. Bei Alleinerziehung zählt für die Beitragsstufe ein zusätzliches Kind. |
| Freiberg am Neckar | Die Modell-Netto-Einkommensstufe gilt für die Gebührentabellen, bei der städtischen Ü3-Staffel zählt das jüngste betreute Kind zuerst. Schulkinder im Modell werden ohne gebuchten Hort, Ganztagsschule oder Kernzeit angesetzt. Für das ältere von zwei gleichzeitig betreuten Krippenkindern bleibt der Beitrag offen, weil die Krippenordnung auf Ermäßigungen verweist, aber keinen eindeutigen ermäßigten Betragsansatz nennt. [Städtische Gebührenordnung](https://www.freiberg-an.de/de/bildung-betreuung-soziales/kinderbetreuung/gebuehren) |
| Hemmingen | Die Regelgruppe mit 30 Stunden und die Ganztagsgruppe mit 42 Std. 30 Min. sind für beide Altersgruppen belegt. Bei Alleinerziehung mit einem Kind gelten die eigenen Tabellenzeilen. [Kommunales Vormerkportal](https://nhkita.hemmingen.de/uebersicht.html) |
| Kernen im Remstal | Die bestätigte Tarifstufe 40–43 Stunden wird für 40 Stunden verwendet. Das gewählte Jahresbrutto steht für das Vorjahr und wird für die Staffel durch zwölf geteilt. Ab zwei kindergeldberechtigten Kindern reduziert sich der Beitrag um 20 Prozent. Bei Alleinerziehung folgen weitere 10 Prozent auf den bereits ermäßigten Betrag. |
| Magstadt | Bei vier Kindern zahlen die drei älteren für VÖ den Betrag der Dreikindstufe. Das vierte Kind ist im VÖ-Modell beitragsfrei. |
| Remseck am Neckar | Die Verpflegung wird getrennt nach Betreuungsmodell und modelliertem Alter gezeigt. Für das Krippenkind am Modellalter von genau zwei Jahren werden 45 € pro Beitragsmonat angesetzt. Essen wird über zehn Monate bezahlt. |
| Renningen | U3 und Ü3-VÖ sind über die veröffentlichten Monatsbeiträge abgedeckt. Ü3-Ganztag ist mit 40 Stunden buchbar. Anlage und Änderungssatzung liefern den Stundensockel und den Zuschlag ab der 31. Wochenstunde. Der genaue Monatsfaktor und die Rundungsregel bleiben unbelegt. [Änderungssatzung](https://www.renningen.de/dokumente/oeffentliche-bekanntmachungen/2026/5.-aenderung-der-benutzungs-und-gebuehrensatzung-kitas-2026-2028-sig.pdf?cid=1s2p) |
| Rutesheim | In gleichzeitig belegten zuschussfähigen Angeboten erhält jedes weitere Kind 50 € Rabatt. Das städtische Verzeichnis klassifiziert die altersgemischte Betreuung bis 15 Uhr als Ganztag. Der Modellrang beginnt beim ältesten berechtigten Kind. [Städtische Angebotsübersicht](https://www.rutesheim.de/site/Rutesheim-Internet-2021/get/params_E2133346668/18996882/240819_Infoblatt%20%C3%9Cbersicht%20alle%20Kitas-2024.pdf) |
| Schönaich | VÖ ist auf 31 Std. 30 Min. für U3 und 31 Std. 45 Min. für Ü3 umgerechnet. Im Ganztag gelten 37 Std. 30 Min. für U3 und 51 Std. 30 Min. für Ü3. |
| Schwieberdingen | Elf Beitragsmonate. Die U3-Beitragsstufe sinkt bei Alleinerziehung und bei gleichzeitiger U3-Betreuung um je eine Stufe bis zur niedrigsten veröffentlichten Stufe. Bei Ü3-Geschwistern mit unterschiedlichen Zeitpaketen und bei drei Ü3-Kindern in der Dreikindstufe fehlen eindeutige Tabellenangaben. Diese Fälle erhalten keinen Gesamtpreis. |
| Waiblingen | Für die Einkommensformel zählt das gewählte Haushaltsjahresbrutto plus Kindergeld. Die veröffentlichten Grenzen und die Abschläge nach Geburtsrang werden angewandt. Bei einem Tarif mit Mittagsverpflegung bleibt der Gesamtbetrag auf der Karte und die Details zeigen „Essenspauschale enthalten“. [Städtisches Einrichtungsverzeichnis](https://www.waiblingen.de/de/Die-Stadt/Leben-in-Waiblingen/Kindertageseinrichtungen/Kindertageseinrichtungen) |

Bei identischem Modellalter bestimmt die Reihenfolge der Eingabe den Rang. Bei Freiberg und Rutesheim nimmt das Modell keine zusätzliche Betreuung für Schulkinder an. Die örtlichen Regeln werden in der Webprojektion für die Modellfamilie angewandt. Die gemeinsame Angebotsauswahl und Jahresumrechnung verwenden weiterhin denselben Rechner. Diese Nachprüfung ist von der Aktivierung für die Website unabhängig.

## Freigabeprüfung der 13 Kandidaten nach Wochenzielen

Die Nachprüfung vom 20. November 2026 nach Anpassung der Webauswahl ergab **104 von 104 übereinstimmende Modellfälle**. Die zwei nicht verfügbaren U3-Fälle in Baltmannsweiler stimmen mit den Quellen überein. Der laufende Tarifstichtag bleibt der 4. November. Die folgenden 41 Abweichungen dokumentieren den Stand vor der Korrektur. Der Nachtest ist in `web/tests/model-family.test.mjs` reproduzierbar.

### Vor der Korrektur am 20. November

Stand 18. November 2026, mit dem laufenden Tarifstichtag der Website vom 4. November 2026. Diese Prüfung vergleicht die dokumentierten Sollwerte aus Satzungen, Angeboten und Tarifzeilen mit der Browserberechnung nach der Webprojektion der Erweiterungskataloge. Die Prüfumgebung stellt jede Kommune isoliert im Register bereit. Die Aktivierungsliste führt weiterhin acht bereits freigegebene Erweiterungskommunen.

Je Kommune wurden acht Fälle bei 80.000 € Haushaltsjahresbrutto geprüft: U3 und Ü3 jeweils mit sechs und acht Stunden, zwei unterschiedlich betreute Kita-Kinder, ein Ü3-Kind mit Schulkind, vier Haushaltskinder mit zwei Kita-Kindern und ein Ü3-Ganztagskind bei Alleinerziehung. Maßstab sind das passende Zeitpaket nach Wochenzielen, der monatliche Betreuungsvergleichswert und die korrekte Nichtverfügbarkeit. Für die fünf bestandenen Kommunen wurden auch Beitragsmonate und die Zuordnung der separat ausgewiesenen Zusatzkosten stichprobenartig geprüft.

| Kommune | Bestanden | Befund |
|---|---:|---|
| Affalterbach | 8/8 | 40 Stunden im Ganztag. Belegte Beitragsfreiheit bei vier Kindern im Prüffall. |
| Aichwald | 1/8 | Der Rechner nutzt für den Ganztag 47 Std. 30 Min. statt 42 Std. 30 Min. Der Ü3-Regelkindergarten kommt mit 30 Stunden über fünf Tage dem Ziel des Sechs-Stunden-Modells näher als die verwendete 35-Stunden-VÖ. |
| Altbach | 8/8 | Die belegten 30- und 40-Stunden-Angebote werden gewählt. |
| Baltmannsweiler | 5/8 | U3 mit acht Stunden wird korrekt als nicht berechenbar ausgegeben. Für Ü3 gewinnt nach Wochenziel das belegte 40-Std.-30-Min.-Paket mit drei langen Tagen. Der Rechner verwendet 44 Std. 30 Min. |
| Benningen am Neckar | 8/8 | Der Rechner verwendet das belegte 45-Std.-30-Min.-Paket. Das Drei-Ganztage-Modell bleibt bei der Auswahl außen vor, da für seine übrigen Wochentage der Buchungsnachweis fehlt. |
| Denkendorf | 8/8 | Der Ganztag mit 45 Stunden und das separat berechnete Pflichtessen sind den richtigen Angeboten zugeordnet. Der Essensbetrag ist unbekannt. |
| Filderstadt | 3/8 | Der Rechner liefert für die dokumentierten 40-Stunden-Modelle keinen Ganztagsbetrag. |
| Grafenau | 3/8 | 40 Std. 30 Min. mit drei langen Tagen sind für U3 und Ü3 belegt. Der Rechner lässt U3 ohne Ergebnis und verwendet bei Ü3 44 Stunden. |
| Ostfildern | 2/8 | Die Bruttoannahme für das Vorjahr liefert den erwarteten Ü3-VÖ-Betrag. Die Buchung von 35 Stunden für U3 und die 40-Stunden-Angebote für U3 und Ü3 wirken in der Webauswahl noch nicht. |
| Plochingen | 3/8 | Die kommunale Gebührenordnung führt drei Ganztagstage plus zwei Regelgruppentage. Bei neun und sechs Stunden je Tag ergibt das 39 Stunden. Der Rechner verwendet das 42-Stunden-Paket mit vier langen Tagen. |
| Steinenbronn | 3/8 | Bei Gleichstand zwischen 39 und 41 Stunden gewinnt das 41-Stunden-Paket. Der Rechner liefert für beide Altersgruppen keinen Ganztagsbetrag. |
| Waldenbuch | 3/8 | Der Rechner verwendet das 39-Stunden-Paket. Die maßgebliche Gebührenordnung belegt 40 Stunden mit Frühbetreuung für beide Altersgruppen. |
| Weissach | 8/8 | Die 30- und 40-Stunden-Modelle für bis zu vier Kinder sowie Getränke- und Essenspauschalen stimmen in den Stichproben. |

Von **104 Fällen stimmen 63 mit dem Soll überein**, darunter zwei korrekte Nichtverfügbarkeiten in Baltmannsweiler. **41 weichen ab.** Die fünf Kommunen mit 8/8 können für die Übernahme vorgeschlagen werden. Die acht übrigen brauchen einen erneuten Test nach Umsetzung der Wochenstundenregel in der Webauswahl und Übernahme der dokumentierten Pakete in die Vergleichsdaten.

[Regelwerk](REGELWERK_DATENANALYSE.md) · [Aktuelle Tarifauswahl und Quellen](TARIFAUSWAHL.md)

## Historische Kompatibilitätsprüfung

**Prüfstand:** 2026-11-10. Die folgenden Zahlen, Freigabehinweise und Befehle dokumentieren den damaligen Lauf. Für neue Kommunen gilt die [Stichprobenprüfung](DATENPIPELINE.md#3-mit-gezielten-stichproben-prüfen). **Schritt 2 abgeschlossen:** Kompatibilitätsprüfung der bestehenden Engine und Kennzeichnung nicht berechenbarer Modellkonfigurationen.

Für die bisherige Modellfamilie sind **10 Kommunen berechenbar** und **23 nicht berechenbar**. Das ist keine Freischaltung. Die gemeinsame Engine und das produktive Kommunenregister bleiben unverändert.

### Prüfumfang

Geprüft wurden **2508 Konfigurationen je Kommune**, insgesamt **82764 Familienfälle**: ein bis vier Haushaltskinder, beide Haushaltskonstellationen, alle sechs Einkommensszenarien, Krippe/Kindergarten mit sechs oder acht Stunden sowie Schul- und zu Hause betreute Kinder. Kindreihenfolgen wurden als Multimengen abgedeckt und durch Umkehrung zusätzlich geprüft. Familien mit fünf bis zwölf Kindern, persönliche Eingaben, Pässe, außergewöhnliche Aufnahmefälle und künftige Tarifstichtage sind nicht freigegeben.

**15840 Einzelberechnungen** wurden zwischen unveränderter Python- und TypeScript-Engine abgeglichen; **80388 Reihenfolgeprüfungen** ergaben identische Familienbeträge/-status. Zusätzlich bestanden **61 ausdrücklich hinterlegte Quellen- und Ablehnungsfälle**. Diese technische Kompatibilitätsprüfung ersetzt die nachfolgende umfassende fachliche Quellenabnahme aus Schritt 3 nicht.

### Sicherheitsentscheidung

Die native Berechnung lieferte in **11280 geprüften Fällen** einen als vergleichbar bezeichneten Betrag, der wegen einer nicht berücksichtigten Bedingung oder ungeklärten Angebotsauswahl verworfen wurde. Die geprüften Ausgaben verwenden dann `status: unavailable`, konkrete Gründe und leere Geldfelder. Weder null Euro noch ein geratener Ersatzpreis wird ausgegeben. Ein separater Schutzschritt in der Offline-Prüfung erzeugt diese Freigabeentscheidung; die bestehende Engine selbst wurde nicht nachträglich umdefiniert.

Unbekannte separat zu erhebende Essenspreise sperren einen ansonsten belastbaren Betreuungskostenwert nicht automatisch. Ein falscher Essensabzug, Doppelansatz oder eine falsch zugeordnete Kostenvariante verhindert dagegen die Freigabe.

### Ergebnisse nach Kommune

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

### Konkrete Einschränkungen und nächste Arbeit

- **Schwieberdingen:** reguläre Tabellen können nur dort verwendet werden, wo die native Rechnung stimmt. Nicht ausgeführte Alleinerziehenden-/U3-Stufenverschiebungen, eine falsche Rangpopulation und ungeklärte Ü3-Ränge bleiben nicht berechenbar. Keine Sonderlogik wurde in die Engine eingebaut.
- **Denkendorf:** die genehmigte Freitagsausnahme ist dokumentiert; die unveränderte tägliche Bedarfsprüfung berücksichtigt diese noch nicht. Sechs-Stunden-Fälle werden davon getrennt geprüft.
- **Aichwald / Erdmannhausen:** die Originalpreise einschließlich Essen sind erhalten. Die laufende Engine liest ergänzende reine Betreuungsanteile nicht automatisch; solche Beträge werden nicht ungeprüft als Kartenwert freigegeben.
- **Freiberg / Kernen / Ostfildern / Waiblingen:** fehlende örtliche Modellannahmen werden nicht durch eine Brutto-Konvertierung ersetzt. Waiblingens Prozentformel und Inklusivdarstellung sowie Renningens Ü3-Stundenformel benötigen eine abgestimmte Lösung.
- **Weitere Datenarbeit:** fehlende Tagesverteilungen, unterschiedliche Kostenvarianten und besondere Preis-Selektoren werden mit konkretem Grund im Freigabeindex geführt. Datenkorrekturen sind von Änderungen der gemeinsamen Rechenlogik zu unterscheiden.

Änderungen der gemeinsamen Berechnungslogik für einzelne Kommunen werden vorab mit dem Nutzer besprochen. Für Schwieberdingen ist keine Engineänderung beauftragt. Schritt 3 bleibt die vertiefte Quellenabnahme der freizugebenden Ergebnisse, Schritt 4 die kontrollierte Integration.

### Ablage und Wiederholung

- [Maschinenlesbarer Freigabeindex](../data/expansion/calculation_review.json): geprüfter Umfang, Fallgruppen, Ablehnungsgründe und Standardergebnisse. Nicht berechenbare Standardergebnisse haben ausschließlich leere Geldfelder.
- [Prüfbedingungen](../data/reviews/expansion_compatibility_policy.json) und [Referenzfälle](../data/reviews/expansion_calculation_cases.json): Quellenbelege und ausdrückliche Entscheidungen.
- Rohproben und Profile bleiben unter `build/expansion-review/` und werden nicht veröffentlicht. Der produktive Export liest weiterhin nur die bisherigen zwölf Kommunen.

Der Freigabeindex ist ein Offline-Prüfergebnis, noch keine angeschlossene Laufzeitsperre. Eine spätere Veröffentlichung muss ihn wirksam beachten; die Importkataloge dürfen nicht ungeprüft aktiviert werden. Änderungen an Quellen, Katalogen, Modellprofilen, Engine oder Prüflogik machen die jeweilige Freigabe anhand gespeicherter Prüfsummen ungültig.

Das Skript `scripts/review_expansion_compatibility.py` gehört zu diesem historischen Stand. Die Reproduktion setzt die damaligen Daten und Rechenstände voraus. Ein neuer Lauf im aktuellen Arbeitsstand würde den gespeicherten Freigabeindex und dieses Dokument überschreiben. Für die heutige Prüfung gelten die [gezielten Stichproben der Datenpipeline](DATENPIPELINE.md#3-mit-gezielten-stichproben-prüfen).
