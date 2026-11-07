# Datenmodell und Vergleichsberechnung

**Stand:** 7. November 2026 · **Schema:** 1.0 · **Tarifstichtag des Defaultprofils:** 4. November 2026

## 1. Fachliche Trennung

Die zwölf Kommunen bleiben geografische Vergleichseinheiten. Es werden keine einzelnen Einrichtungen auf der Karte benötigt. Einrichtungsbezogene Veröffentlichungen dienen dort als Beleg, wo die kommunale Gebührenformel von den angebotenen Öffnungsstunden abhängt. Unterschiedliche Zeitverteilungen sind als Angebotsvarianten einer Kommune gespeichert; abweichende Essenspreise bleiben gesonderte Kostenvarianten.

Der Datenbestand besteht aus drei nachvollziehbaren Ebenen:

1. **Originalquellen:** PDFs und HTML-Antworten, Abrufdatum, URL, Antwortstatus, Prüfsumme sowie Textauszug. Auch Fußnoten, Bedingungen und bisher nicht ausführbare Regeln bleiben dadurch erhalten.
2. **Strukturierte Originaltarife:** Versionierte Angebote, Preiszellen, Einkommensstufen, Kostenbausteine und Regeln. Normalisierte Angaben ergänzen Originalbezeichnungen und Quellenfundstellen.
3. **Vergleichsergebnisse:** Ein Profil wird auf die lokalen Regeln angewendet. Das Ergebnis enthält den ausgewählten Tarif, Buchungsumfang, Originalbeitrag, Beitragsmonate, Vergleichsbetrag und Rechenweg.

Die kanonischen Daten stehen in `data/municipalities/`. Quellenkennungen werden über `data/source_manifest.json` aufgelöst. Die frühere Markdown-Recherche ist unter `data/imported/` eingefroren; sie wird nicht als aktuelle Gebühren-API gelesen. CSV-Dateien und der gemeinsame Katalog in `data/exports/` entstehen aus den kanonischen JSON-Dateien.

## 2. Vertrag des Datenformats

Das formale Schema ist `data/municipality.schema.json`. Die ausführbare Prüfung kontrolliert zusätzlich Referenzen, doppelte Selektoren, Datumsintervalle, Geldwerte, Tages-/Wochensummen und Quellenprüfsummen.

| Sammlung / Feld | Bedeutung |
|---|---|
| `id`, `name`, `scope` | Stabile Kommune und Geltungsbereich; die Berechnung verwendet städtische Tarife. Andere Träger werden nur nach gesondertem Nachweis einbezogen. |
| `offers` | Originalname, Altersgrenzen, Gültigkeit, expliziter ursprünglicher Preisstand, Wochenminuten, Dauer an Montag bis Freitag, durchgehende Betreuung, Zahlungsmonate und Quellenbelege. |
| `prices` | Eine veröffentlichte Preiszelle mit `amount_cents`, `value_status`, `offer_id`, Selektoren und Originalfundstelle. Eingeschlossene Zuschläge sind gesondert ausgewiesen und werden nicht erneut addiert. |
| `income_bands` | Lokale Einkommensdefinition, Monats-/Jahresbezug, Einkommenszeitraum, Grenzen einschließlich Grenzwertbehandlung, Sonderfall Alleinerziehende und Kennzeichnung der höchsten Stufe. |
| `components` | Essen, Snacks, Betreuungserweiterungen und sonstige Gebühren; eigene Einheit, Gültigkeit, betroffene Angebote, Beitragsmonate, Voraussetzungen und Pflichtstatus. |
| `rules` | Nachgewiesene Rechen- oder Anspruchsregel mit Ausführbarkeitsstatus, Voraussetzungen und Fundstelle. Tabellenbeträge haben Vorrang vor nachgerechneten Prozentwerten. |
| `issues`, `coverage` | Bekannte Quelleneinschränkungen und Umfang der strukturierten Übertragung. |
| `evidence` | `source_id`, genaue `locator`-Fundstelle und gegebenenfalls Originalzelle bzw. ursprüngliche Tabellenzeile. |

Alle Geldwerte sind ganzzahlige Eurocent. Zeitangaben sind Minuten. Unbekannte Beträge sind `null`; nur belegte Gebührenfreiheit ist `0`. Statuswerte unterscheiden `known`, `unknown`, `not_published`, `not_offered` und `conflicting`. Ein nicht anwendbarer Tarif wird durch seine Selektoren bzw. Angebotszuordnung ausgeschlossen und nicht mit null Euro dargestellt.

Einkommensgrundlagen sind eigenständig: `taxable_income` in Ditzingen, `adjusted_taxable_income` in Korntal-Münchingen, `esslingen_gross_income`, `fellbach_gross_income` und `gerlingen_household_income`. Der Korntaler Begriff umfasst auch die satzungsgemäße Hinzurechnung von Vermietungsverlusten. Esslingen verwendet Einkommen des aktuellen Kalenderjahres mit eigenen Ein-/Ausschlüssen. Es gibt keine automatische Umrechnung von Brutto in steuerliches Einkommen. Monats- und Jahreswerte derselben Definition werden exakt durch zwölf geteilt bzw. multipliziert.

Die Familienstaffel wird anhand der Haushaltskinder nach der jeweiligen Kommune bestimmt. Die Eingabe führt Alter, Haushaltszugehörigkeit und Kindergeldberechtigung getrennt. Der Rang gleichzeitig betreuter Kinder ist ein weiterer Parameter und wird nicht aus der Familiengröße abgeleitet. Eine Spalte „4 Kinder“ wird nur dann als „4 oder mehr“ behandelt, wenn die Quelle das ausdrücklich ausweist.

## 3. Profil und Berechnungsschnittstelle

`load_cities()` und `load_default_profile()` lesen die JSON-Daten. `evaluate_city(city, profile)` verändert weder Quelle noch Profil und liefert ein reproduzierbares Ergebnis.

Wesentliche Profileingaben:

- `as_of`: Tarifstichtag; `children`: Haushaltskinder mit `age_months`, `resident`, `child_benefit`; `target_child`: Index des zu vergleichenden Kindes.
- `weekday_minutes`: fünf gewünschte Tagesdauern von Montag bis Freitag. Es wird durchgehende Betreuung verlangt.
- `care_rank`: ausdrücklich angegebener Rang im betreffenden städtischen Betreuungssystem, falls benötigt.
- `meal_days_per_week`: ausdrücklich gewählte Essenstage, falls abweichend vom gebuchten Zeitpaket; ein Mahlzeitenpreis wird ohne tatsächliche Zahl der Essenstage nicht auf ein Jahr hochgerechnet.
- `income_mode`: `highest_band` oder `specified`; `incomes`: Einträge mit lokaler `basis`, `period` und `amount_cents`.
- `pass_id`, `approved_rules`, `eligibility`: nachgewiesener Pass und ausdrücklich bestätigte Anspruchsvoraussetzungen. Einkommen allein löst keine antragsabhängige Sozialermäßigung aus.
- `municipality_overrides`: lokale Abweichungen für Einkommenswerte, Pass, bewilligte Regeln, Voraussetzungen und Betreuungsrang; Kindesalter und Betreuungsbedarf bleiben gemeinsam.
- `allow_published_future`: ausdrücklich gewählte Nutzung veröffentlichter künftiger Tarife. Ohne diese Auswahl wird kein Datum nach dem Prüfstand bewertet.

Bei einem gerade drei Jahre alten Kind verlangen Kommunen mit Wechsel im Folgemonat zusätzlich `birthday_in_reference_month`. Ohne diese Angabe wird der Grenzmonat nicht geraten. Persönliche Angaben zur Haushaltszugehörigkeit, Kindergeldberechtigung und Anerkennung volljähriger Kinder müssen die für den Tarif genehmigte Konstellation wiedergeben.

Die Berechnung wählt gültige Tarife für Alter und Geltungsbereich, wendet lokale Familien- und Einkommensmerkmale an und prüft die Zeitdeckung **für jeden einzelnen Tag**. Unter den belegten passenden Angeboten wird zuerst der geringste Buchungsumfang und danach der günstigste anwendbare Betreuungspreis gewählt. Nicht veröffentlichte Preise für ein kleineres passendes Paket dürfen nicht stillschweigend durch einen größeren Tarif ersetzt werden. Ungeklärte gleichwertige Varianten ergeben `ambiguous`.

Reguläre Ergebnisse verwenden `status: comparable`. Bei fehlenden Angaben wird `status: unavailable` mit konkreten `reasons` geliefert. Ein Ergebnis kann den bekannten Originalmonatsbeitrag enthalten, während das Monatsäquivalent wegen unbekannter Beitragsmonate leer bleibt.

Wesentliche Ergebnisfelder sind `monthly_care_cents`, `payment_months`, `annual_care_cents`, `monthly_equivalent_cents`, `booked_weekly_minutes`, `extra_weekly_minutes`, `selected_price_id`, `components`, `evidence` und `calculation`. Zusatzkosten ändern die Hauptkennzahl nicht. Eine zusätzliche Pflichtkostensumme wird nur bei ausreichend bekannten und eindeutigen ausgewählten Komponenten gebildet; `total_status` nennt deren Umfang.

## 4. Vergleichsregeln und Default

Der Default ist ein 24 Monate altes Einzelkind ohne Geschwister, Montag bis Freitag mindestens acht Stunden durchgehend, städtischer Tarif, höchste reguläre Einkommensstufe ohne Sozial- oder Passermäßigung.

**Vergleichswert = ursprünglicher Monatsbeitrag × jährliche Beitragsmonate ÷ 12.**

Der Tarif wird für dieses Jahresäquivalent am Stichtag konstant gehalten. Unterjährige Änderungen werden nicht in eine vermeintliche tatsächliche Jahresrechnung eingemischt. Die Auswahl ist ein Vollzahler-Referenzprofil und keine Aussage über den Durchschnittshaushalt. Originalpreis, Beitragsmonate, Mehrstunden und Zusatzkosten bleiben sichtbar.

Es wird nicht zwischen Pauschalen interpoliert. Leonbergs bzw. Gerlingens 8,5 Stunden täglich bleiben zum veröffentlichten Preis erhalten. Ditzingens kleinstes passendes Paket umfasst 45 Wochenstunden. Bei Fellbach entscheidet die **angebotene Tagesverteilung**, nicht eine frei gewählte Wochenstundenzahl: Das geprüfte 40-Stunden-Modell endet donnerstags und freitags nach sieben Stunden. Der Default verwendet deshalb ein belegtes 45-Stunden-Modell mit acht Stunden am Freitag. Die U3-Gebühr beträgt dafür 45 × 15,60 € = 702 € je Monat. Die ganze Wochenstundenzahl wird mit dem Tarif oberhalb der 35-Stunden-Schwelle bewertet.

Leinfelden-Echterdingens Passpreise werden direkt aus den veröffentlichten Tabellen übernommen. Beispielsweise sind für U3/40 Stunden/ein Kind mit Stadtpass A **234,90 €** ausgewiesen; eine freie Prozentrechnung würde 234,88 € ergeben. Die Tabelle bleibt maßgeblich.

Die Berechnung verwendet exakte Dezimalrechnung und rundet das fertige Vergleichsergebnis kaufmännisch auf Cent. Fellbachs Gebühren und Ditzingens Familienpassregel verwenden die satzungsgemäße Rundung auf volle Euro. Bereits veröffentlichte gerundete Werte werden unverändert übernommen.

## 5. Prüfung, Pflege und verbleibende Einschränkungen

Der [Standardvergleich](STANDARDVERGLEICH.md) wird aus den Daten erzeugt. Die unabhängigen Sollwerte des Defaultprofils stehen in `data/reviews/default_review.json`, mit Fundstellen für alle zwölf Kommunen. Die ausgewählten PDF-Tarifzellen wurden zusätzlich visuell geprüft; Fellbachs Formel wurde mit den offiziellen Tageszeiten abgeglichen. Alle 800 Esslinger Zusatzzeitbeträge werden außerdem automatisiert gegen die archivierte Original-PDF-Tabelle geprüft.

Die Tests decken die zwölf Defaultwerte, Zahlungsmonate, Paketgrenzen, Tagesverteilung, Einkommensarten und Grenzwerte, Alleinerziehende, Familiengröße und Betreuungsrang, Passvoraussetzungen, Rundung, Zusatzzeiten, eingeschlossene Zuschläge, künftige Tarife und fehlende Angaben ab. Die Datenvalidierung kontrolliert auch die SHA-256-Prüfsummen aller archivierten Antworten.

Für Aktualisierungen wird zuerst eine neue Quellenkopie mit `scripts/fetch_sources.py --refresh` gesichert. Bestehende Quellenkennungen bleiben erhalten. Danach werden neue Tarifversionen ergänzt, alte Intervalle begrenzt, Quellen- und Prüfdaten aktualisiert sowie Tests, Validierung und Export ausgeführt. Quellen mit unterschiedlichen Abrufzeitpunkten werden nicht als identische historische Fassungen ausgegeben.

Die archivierten Dokumente bewahren auch Regeln, die noch nicht vollständig automatisiert sind: Aufnahme-/Austrittsmonate, Abwesenheit und Rückerstattung, Sonderentscheidungen, einzelne Randzeiten und die einmalige Zuschlagsverteilung für mehrere U3-Kinder mit FamilienCard. Unbelegte Tagesverteilungen alternativer Wochenpakete bleiben gesperrt. GT11 in Ludwigsburg und wörtlich mehrdeutige Einkommensgrenzen bleiben als Quellenlücken erhalten. Einrichtungsabhängige Essensvarianten und unbestätigte Essens-Beitragsmonate ergeben keine geschätzte Gesamtsumme.

Historische Daten bleiben archiviert; eine systematische historische Preisreihe und die Webkarte gehören nicht zu dieser Datenmodell-Umsetzung.
