# Konfigurierbare Modellfamilien

**Stand:** 8. November 2026 · **Tarifstichtag:** 4. November 2026

Die öffentliche Website bietet einen Modellvergleich mit einfachen Auswahlen. Persönliche Steuerdaten, Geburtsdaten und Pässe werden nicht abgefragt. Der bisherige Einzelkindvergleich bleibt als Standard erhalten. Das frühere persönliche Formular und die Höchsttarifreferenz bleiben im Code bzw. Datenbestand; beide haben keinen öffentlichen Reiter.

## Bedienung und Konfiguration

Die zentrale Datei `data/models/configuration.json` definiert Standardauswahl, Kinderkategorien, Modellalter, Betreuungszeiten, Einkommensszenarien und Annahmen. Der Browser erhält sie zusammen mit den Tarifdaten. Zod prüft Definitionen und Auswahlen; bei unvollständiger oder widersprüchlicher Konfiguration werden keine Ersatzwerte eingesetzt.

- Haushalt: zwei zusammenlebende Eltern oder alleinerziehend.
- Anzahl der Kinder: 1 bis 12; große Familien können wegen begrenzter veröffentlichter Tarifspalten unberechenbare Ergebnisse erhalten.
- Je Kind: Krippenkind (Modellalter 24 Monate), Kindergartenkind (48 Monate), Schulkind (96 Monate) oder zu Hause betreut (24 Monate).
- Nur Krippen- und Kindergartenkinder: 360 oder 480 Minuten durchgehend pro Tag, Montag bis Freitag.
- Alle Kinder gelten als minderjährig, im Haushalt lebend und kindergeldberechtigt. Schulkinder besuchen im Modell keine kostenpflichtige Schul- oder Hortbetreuung. Sie und zu Hause betreute Kinder zählen nach örtlicher Familienregel als Geschwister mit.
- Keine zusätzlichen Pässe oder antragsabhängigen Sozialermäßigungen. Reguläre Familienstaffeln bleiben wirksam.

Der Standard ist: zwei zusammenlebende Eltern, ein Krippenkind, Szenario 80.000 €, acht Stunden täglich. „Standard wiederherstellen“ setzt alle Auswahlen gemeinsam zurück. Neu ergänzte Kinder sind zunächst zu Hause betreut. Die Auswahlen bleiben nur im Arbeitsspeicher des Browserfensters; weder URL noch Local Storage noch Backend speichern sie.

## Einkommensszenarien und Aussagegrenze

Die folgende Tabelle enthält die ausdrücklich gesetzten jährlichen Rechenwerte in Euro. Sie sind Vergleichsannahmen, keine aus persönlichen Daten ermittelten oder statistisch belegten steuerlichen Werte. Das bestehende Modell 80.000/60.000 € bleibt unverändert; die steuerlich bezeichneten Werte der weiteren Szenarien führen dessen Verhältnis proportional fort. Dieser Modellabschlag von 25 % ist **keine allgemeingültige Umrechnung von Bruttoeinkommen in steuerliches Einkommen**. Das Brutto-Szenario allein bestimmt daher keinen verlässlichen persönlichen Gebührenbescheid. Für Alleinerziehende und Paare werden dieselben Einkommenswerte angenommen; dies ist ebenfalls keine steuerliche Gleichsetzung beider Haushalte.

| Haushaltsbrutto | Ditzingen: örtlicher Bemessungswert | Esslingen: örtliches Brutto | Korntal: bereinigter Wert |
|---:|---:|---:|---:|
| 40.000 | 30.000 | 40.000 | 30.000 |
| 60.000 | 45.000 | 60.000 | 45.000 |
| **80.000** | **60.000** | **80.000** | **60.000** |
| 100.000 | 75.000 | 100.000 | 75.000 |
| 140.000 | 105.000 | 140.000 | 105.000 |
| 180.000 | 135.000 | 180.000 | 135.000 |

Vorjahr und laufendes Jahr werden als unverändert angenommen; weitere Einkünfte und Vermietungsverluste sind ausgeschlossen. In Esslingen wird kein Arbeitnehmer-Pauschbetrag abgezogen. Korntals örtlicher Jahreswert darf für dieselbe Einkommensdefinition durch zwölf geteilt werden. Eine automatische steuerliche Berechnung findet nicht statt. Die vollständige Tabelle und die Annahmen sind auf der Website aufklappbar.

Ditzingens interner Schlüssel `taxable_income` bleibt aus Kompatibilitätsgründen erhalten. Fachlich ist der örtliche Bemessungswert aus § 7 Abs. 4 gemeint: positive Einkünfte und die genannten Ersatz-/Sozialleistungen. Die Tabellenbezeichnung darf nicht ungeprüft mit dem zu versteuernden Betrag aus einem Steuerbescheid gleichgesetzt werden. Die Formularhilfe und Katalogmetadaten sind entsprechend präzisiert.

Mit dem bestehenden U3-/8-Stunden-Standard werden sechs der zehn Esslinger, alle vier Ditzinger und fünf der sechs Korntaler Einkommensbereiche erreicht. Der Korntaler Bereich 7.001–8.000 € monatlich liegt zwischen den hinterlegten Szenarien. Die Sondervariante für Alleinerziehende im untersten Bereich wird durch die Haushaltsauswahl geprüft. Eine Schätzung persönlicher Einkommensverhältnisse oder eine automatische Gewährung von Sozialermäßigungen ist nicht Gegenstand dieses Modells.

## Familiengesamtkosten

`web/src/domain/model-family.ts` erstellt aus den gewählten Kategorien ein normalisiertes Profil. Für jedes Kita-Kind werden die tägliche Betreuungsdauer und der Zielkindindex gesetzt und der bestehende Rechenkern verwendet. Alle Haushaltskinder bleiben bei jeder Berechnung für die örtliche Familienstaffel erhalten.

**Familienvergleichswert = Summe der jährlichen Betreuungsbeiträge aller Kita-Kinder ÷ 12.**

Gerundet wird einmal auf der Familienebene. Die sichtbaren, bereits auf Cent gerundeten Einzeläquivalente können sich deshalb um einen oder bei großen Familien mehrere Cent von der Familiensumme unterscheiden. Die tatsächlichen Monatsbeiträge, Beitragsmonate, gebuchten Stunden, Mehrstunden, Quellen und Zusatzkosten bleiben je Kind sichtbar. Essensvarianten werden nicht zu einer vermeintlich sicheren Gesamtsumme addiert.

Sind alle Beiträge bekannt, zeigen Karte und Liste die Familiensumme. Fehlt ein notwendiger Beitrag, bleibt die vollständige Familiensumme leer; bekannte Einzelbeträge sind weiterhin sichtbar. Eine Familie ausschließlich mit Schul- und zu Hause betreuten Kindern hat ausdrücklich 0 € Kita-Kosten. Daraus folgt keine Aussage über tatsächliche Schul-/Hortkosten.

Die Sortierung und feste Gebührenlegende verwenden denselben Familienwert wie die Karte. Die ausgewählte Gemeinde bleibt bei einer Modelländerung erhalten. Eine Auswahl aus Karte oder Liste fokussiert die Detailüberschrift; auf schmalen Bildschirmen wird sie zusätzlich in den sichtbaren Bereich gescrollt.

## Sindelfinger Geschwisterränge

Die Satzung vom 1. August 2026, § 11 Abs. 7 und Anlagen Seiten 12–13, unterscheidet Haushaltskinder und den Rang in städtischer Betreuung. Für den Modellvergleich gilt auf ausdrücklichen Nutzerwunsch folgende Festlegung:

1. Ausschließlich gleichzeitig in einer Kita betreute Kinder erhalten einen Betreuungsrang. Schul- und zu Hause betreute Kinder zählen weiterhin nach örtlicher Regel zur Familiengröße, erhalten aber keinen Betreuungsrang.
2. Das ältere betreute Kind erhält Rang 1, danach folgen die jüngeren. Entscheidend ist das festgelegte Modellalter der Kategorie: Kindergarten vor Krippe.
3. Innerhalb derselben Kategorie entscheidet die Eingabereihenfolge. Der Betreuungsumfang ändert diese Reihenfolge nicht.

Dies ist eine festgelegte Modellkonvention und keine neu belegte amtliche Altersregel. Auf der Website wird auf ausdrücklichen Nutzerwunsch kein zusätzlicher Vermerk dazu ergänzt. Die Festlegung bleibt ausschließlich hier und im Code dokumentiert. Tarifkatalog und allgemeiner Rechenkern mit explizitem `care_rank` bleiben unverändert; die Modellberechnung setzt den Rang vor der jeweiligen Sindelfinger Auswertung.

Beispiele aus den veröffentlichten Zwei-Kind-Spalten:

- Zwei Krippenkinder mit acht Stunden: 282,00 + 211,50 = **493,50 € monatlich**.
- Krippe und Kindergarten mit acht Stunden: Kindergarten Rang 1 **142,70 €**, Krippe Rang 2 **211,50 €**, zusammen **354,20 € monatlich**. Ein Vertauschen dieser beiden Kategorien im Formular ändert die Summe nicht.
- Zwei Krippenkinder, zuerst sechs und danach acht Stunden: **190,70 + 211,50 = 402,20 €**. Bei umgekehrter Eingabereihenfolge: **282,00 + 143,00 = 425,00 €**.

Fehlt eine für den zugewiesenen Rang benötigte Tarifzelle, bleibt die vollständige Familiensumme weiterhin leer; bekannte Einzelbeiträge bleiben sichtbar. Für andere künftige Tarife ohne festgelegte Rangkonvention bleibt die bisherige Prüfung möglicher Zuordnungen erhalten.

## Korrekturen und Prüfung

Ditzingens Familienpassregel (§ 8 Abs. 1) rundet den ermäßigten Beitrag auf volle Euro **auf** und setzt voraus, dass kein vorrangiger Leistungsanspruch besteht. Das ist im kanonischen Katalog, Importskript und beiden Rechenkernen berücksichtigt. Der gemeinsame Testfall 636 € × 70 % ergibt nun 446 € statt 445 €. Die Standard-Modellfamilie ohne Pass ändert sich dadurch nicht.

Die Tests prüfen die unveränderten zwölf Standardwerte, beide Haushalte, alle sechs Szenarien, beide Betreuungsdauern, Quellen, Kategorien ohne Betreuung, unabhängig abgelesene Zwei-Kind-Tarifzellen, fehlende Beiträge, einmalige Rundung, Geschwisterränge und Registererweiterungen. Konfiguration und Tarife werden bei einer Berechnung nicht verändert.

Die frühere Oberfläche liegt unter `web/src/LegacyProfileApp.tsx`; `FamilyForm`, `MunicipalityDetails` und `personal-profile.ts` bleiben einschließlich Tests erhalten. Die Legacy-Oberfläche wird von der öffentlichen Anwendung nicht importiert oder gebündelt. Die beiden alten Feature-Schalter betreffen nur diese erhaltene Oberfläche und sind keine Freigabe der persönlichen Berechnung.

## Geprüfte Ansichten

Die tatsächliche Anwendung wurde auf Desktop sowie bei 390 und 320 Pixeln Breite geprüft. Auch mit geöffneter Einkommenstabelle bleibt die Seite ohne horizontalen Überlauf; die Tabelle kann innerhalb ihres Bereichs horizontal gescrollt werden. Auswahl per Tastatur, Fokus auf Gemeindedetails, Zurücksetzen und der statische Build unter `/kita-kosten-map/` sind geprüft.

Gesicherte Ansichten mit synthetischen Prüfdaten: [Desktop](../output/website-model-config-desktop.jpg), [Mobil](../output/website-model-config-mobile.jpg).
