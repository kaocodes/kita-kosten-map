# Datenmodell und Vergleichsberechnung

**Stand:** 8. November 2026 · **Schema:** 1.0 · **Tarifstichtag beider Referenzprofile:** 4. November 2026

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

**Festlegungen für die Gebietserweiterung vom 10. November 2026:** Das [Recherche-JSON](../data/research/neighbor_expansion_2026-11-10.json) hält Nutzerentscheidungen mit Kennung, Datum, betroffener Kommune und Herkunft getrennt von Quellenbelegen fest. Steinenbronns zwölf Beitragsmonate sind eine Nutzerannahme; Möglingens zwölf Monate und Aichwalds U3-Essen mit 53 € über zwölf Monate sind Nutzerangaben. Diese Herkunft darf bei der späteren Normalisierung nicht als amtlicher Quellenbeleg umgeschrieben werden. Für Freiberg ist die U3-Gebührenordnung des Freiberger Zwergenstüble e.V. ausdrücklich zugelassen; der tatsächliche Vereinsträger bleibt erhalten. U3 hat laut dieser Quelle zwölf Beitragsmonate, kommunales Ü3 elf. Zahlungsmonate werden daher am jeweiligen Angebot und Kostenbaustein geführt. Die Erweiterung ist noch nicht in das kanonische Schema und den Rechner integriert.

Einkommensgrundlagen sind eigenständig: `taxable_income` in Ditzingen, `adjusted_taxable_income` in Korntal-Münchingen, `esslingen_gross_income`, `fellbach_gross_income` und `gerlingen_household_income`. Der Korntaler Begriff umfasst auch die satzungsgemäße Hinzurechnung von Vermietungsverlusten. Esslingen verwendet Einkommen des aktuellen Kalenderjahres mit eigenen Ein-/Ausschlüssen. Es gibt keine automatische Umrechnung von Brutto in steuerliches Einkommen. Monats- und Jahreswerte derselben Definition werden exakt durch zwölf geteilt bzw. multipliziert.

Die Familienstaffel wird anhand der Haushaltskinder nach der jeweiligen Kommune bestimmt. Die Eingabe führt Alter, Haushaltszugehörigkeit und Kindergeldberechtigung getrennt. Der Rang gleichzeitig betreuter Kinder ist ein weiterer Parameter und wird nicht aus der Familiengröße abgeleitet. Eine Spalte „4 Kinder“ wird nur dann als „4 oder mehr“ behandelt, wenn die Quelle das ausdrücklich ausweist.

**Schwieberdingen – Datenfestlegungen vom 10. November 2026:** Elf Betreuungs-Beitragsmonate (September bis Juli) gemäß Nutzerbestätigung. Für U3 ist die Zahl der Kinder unter 18 Jahren die Basis. Als ausdrücklich gewählte Modellannahme verschieben Alleinerziehung und mindestens zwei gleichzeitig U3-betreute Kinder die Familienstufe jeweils um eins. Beide Gründe kumulieren; die Berechnung endet an der niedrigsten veröffentlichten Stufe, ohne weitere erfundene Rabattstufen. Beispiel: zwei Haushaltskinder, zwei gleichzeitig U3-betreute Kinder und Alleinerziehung ergeben Stufe vier. Diese Annahme bleibt von der amtlich nicht geklärten Kumulationsauslegung getrennt.

Für Ü3 gilt bei einem betreuten Kind der erste veröffentlichte Satz; bei zwei gleichzeitig betreuten Kindern werden erster und zweiter Satz verwendet. Alleinerziehung verschiebt die Familienstufe um eins. Ab Stufe vier entfällt die Rangaufteilung. Maßgeblich sind die aktuellen Tabellenzellen ab September 2026, keine freie Halbierung und keine älteren Beispielbeträge. Eine preiswirksame Rangzuordnung bei unterschiedlichen Betreuungszeiten ist nicht belegt; solche Konfigurationen bleiben `unavailable`. Ebenso wird keine dritte Rangzelle für die Drei-Kinder-Stufe erfunden. Bei gleicher Betreuung beziehungsweise identischem Gesamtbetrag ist eine Rangfestlegung für die Familiensumme entbehrlich; auch dann dürfen keine erfundenen individuellen Rangzuordnungen angezeigt werden.

Diese Regeln und betroffenen Konfigurationen stehen zunächst im Recherchebestand. Gemäß Nutzeranweisung erfolgen **keine Änderungen an der Berechnungsengine für Schwieberdingen**. Änderungen der gemeinsamen Rechenlogik zur Aufnahme einzelner Kommunen werden vorab besprochen. Ein in den Quellen lösbarer Fall ist erst dann produktiv berechenbar, wenn der bestehende Rechner ihn korrekt aus den Daten abbilden kann; andernfalls bleibt auch er bis zu einer vereinbarten Lösung nicht berechenbar.

### 2.1 Kommunenregister und geografische Zuordnung

`data/municipality_registry.json` führt die geografischen Metadaten getrennt von den Tarifen. Das zugehörige Schema ist `data/municipality_registry.schema.json`.

- `municipalities`: stabile `id`, amtlicher `name`, achtstelliger `ags` als Zeichenkette einschließlich führender Null, `active`, `region_id`, `tariff_id` und primäre `area_id`.
- `areas`: eigene Flächenkennung, `kind` (`municipality` oder `district`), `municipality_id`, `parent_id`, `tariff_id` und `geometry_key`. Ein Bezirk verweist auf die übergeordnete Gemeindefläche und denselben kommunalen Tarif; zusätzliche Tarifkopien sind dafür nicht erforderlich.
- `geometry_reference`: Pfad, SHA-256-Prüfsumme, Schlüssel-/Namensfelder, Abrufdatum, Quelle und Lizenz der archivierten Geodaten. Die vorhandene BKG-Datei dient als Zuordnungsbeleg; die produktive Geodatenaufbereitung folgt in Paket 3.

Die Validierung verlangt die Tarifkataloge aller aktiven Kommunen und meldet nicht registrierte Kataloge. Registrierte inaktive Kommunen dürfen ihre Daten behalten oder noch keinen Katalog haben; sie erscheinen nicht im Vergleich. Doppelte Kennungen oder AGS, falsche Verweise, fehlende Geometrien und widersprüchliche amtliche Namen werden beanstandet. Es gibt keine feste Sollanzahl von Kommunen mehr. Die zwölf aktuellen Zuordnungen werden gegen die archivierten BKG-Attribute geprüft; Namensgleichheit allein wird nicht als laufende Verknüpfung verwendet.

`load_cities()` liest absichtlich alle kanonischen Tarifdateien, damit unregistrierte Daten bei der Prüfung auffallen. `compare_municipalities(cities, profile, registry)` wählt anschließend die aktiven Registereinträge aus. Es liefert geografische Kennung, AGS, Fläche und Tarifkennung getrennt und übernimmt lokale Profilabweichungen für die jeweilige Kommune. Mehrere Gebiete können denselben Katalog referenzieren. Ein Bezirksvergleich braucht zusätzlich die entsprechenden belegten Bezirksgeometrien; im Register sind derzeit ausschließlich Gemeindeflächen enthalten.

Eine weitere Kommune wird durch Register-/Flächeneintrag, belegte Tarifdaten, passende Geometrie und Referenzfälle ergänzt. Eine neue Abrechnungsregel kann weiterhin zusätzliche Berechnungslogik erfordern. Ein synthetisches dreizehntes Testgebiet prüft die Erweiterung, ohne reale Gebühren einer weiteren Stadt zu behaupten.

## 3. Profil und Berechnungsschnittstelle

`load_cities()`, `load_registry()`, `load_default_profile()` und `load_highest_band_profile()` lesen die JSON-Daten. `evaluate_city(city, profile)` wertet einen Tarifkatalog aus; `compare_municipalities()` ordnet ihn den aktiven Kommunen zu. Beide Berechnungen verändern weder Daten noch Profil und liefern reproduzierbare Ergebnisse.

Seit Paket 2 bestehen dieselben Fachfunktionen zusätzlich als TypeScript-Modul für die spätere Browseranwendung. Schnittstelle, exakte Bruchrechnung und Gegenprüfung stehen in [BROWSERBERECHNUNG.md](BROWSERBERECHNUNG.md). Beide Laufzeiten prüfen dieselben 104 Szenarien. Die kanonischen Tarife und Python bleiben für Datenpflege und Export maßgeblich.

Seit Paket 3 ist der Rechenkern in die lokale React-/Leaflet-Website eingebunden. Dafür wird ein abgeleiteter Browserkatalog erzeugt; Originaldaten und Quellenarchive bleiben unverändert. Datenprojektion, Geodatenaufbereitung und Startbefehle sind in [WEBANWENDUNG.md](WEBANWENDUNG.md) beschrieben.

`normalize_profile()` prüft Eingaben und ergänzt ausschließlich fehlende optionale Listen. `create_personal_profile()` übernimmt Familie und Betreuungsbedarf, entfernt aber alle Einkommen, Modellannahmen, Modell-Quellenhinweise und lokalen Profilabweichungen. Damit werden persönliche Angaben nicht mit alten steuerlichen Modellwerten vermischt. In TypeScript heißen diese Funktionen `normalizeProfile()` und `createPersonalProfile()`.

Wesentliche Profileingaben:

- `as_of`: Tarifstichtag; `children`: Haushaltskinder mit `age_months`, `resident`, `child_benefit`; `target_child`: Index des zu vergleichenden Kindes.
- `weekday_minutes`: fünf gewünschte Tagesdauern von Montag bis Freitag. Es wird durchgehende Betreuung verlangt.
- `care_rank`: ausdrücklich angegebener Rang im betreffenden städtischen Betreuungssystem, falls benötigt.
- `meal_days_per_week`: ausdrücklich gewählte Essenstage, falls abweichend vom gebuchten Zeitpaket; ein Mahlzeitenpreis wird ohne tatsächliche Zahl der Essenstage nicht auf ein Jahr hochgerechnet.
- `income_mode`: `highest_band` oder `specified`; `incomes`: Einträge mit lokaler `basis`, `period` und `amount_cents`.
- `single_parent`: ausdrücklich angegebener Status. Das Modell ergänzt `household.parent_count` und `household.parents_living_together`; zusammenlebende Eltern dürfen nicht gleichzeitig als alleinerziehend angegeben sein.
- `pass_id`, `approved_rules`, `eligibility`: nachgewiesener Pass und ausdrücklich bestätigte Anspruchsvoraussetzungen. Einkommen allein löst keine antragsabhängige Sozialermäßigung aus.
- `municipality_overrides`: lokale Abweichungen für Einkommenswerte, Pass, bewilligte Regeln, Voraussetzungen und Betreuungsrang; Kindesalter und Betreuungsbedarf bleiben gemeinsam.
- `allow_published_future`: ausdrücklich gewählte Nutzung veröffentlichter künftiger Tarife. Ohne diese Auswahl wird kein Datum nach dem Prüfstand bewertet.

Bei einem gerade drei Jahre alten Kind verlangen Kommunen mit Wechsel im Folgemonat zusätzlich `birthday_in_reference_month`. Ohne diese Angabe wird der Grenzmonat nicht geraten. Persönliche Angaben zur Haushaltszugehörigkeit, Kindergeldberechtigung und Anerkennung volljähriger Kinder müssen die für den Tarif genehmigte Konstellation wiedergeben.

Die Berechnung wählt gültige Tarife für Alter und Geltungsbereich, wendet lokale Familien- und Einkommensmerkmale an und prüft die Zeitdeckung **für jeden einzelnen Tag**. Unter den belegten passenden Angeboten wird zuerst der geringste Buchungsumfang und danach der günstigste anwendbare Betreuungspreis gewählt. Nicht veröffentlichte Preise für ein kleineres passendes Paket dürfen nicht stillschweigend durch einen größeren Tarif ersetzt werden. Ungeklärte gleichwertige Varianten ergeben `ambiguous`.

Für die spätere Integration ist ausschließlich für **Denkendorf** eine Nutzerfreigabe zur kürzeren Freitagsbetreuung dokumentiert: Montag bis Donnerstag müssen den gewünschten Tagesumfang belegt erreichen, der Freitag darf kürzer sein. Die tatsächliche Tagesverteilung und der veröffentlichte Preis bleiben unverändert. Das Recherchefeld `model_8h_schedule_status: friday_too_short` bleibt deshalb korrekt; die zusätzliche lokale Vergleichsfreigabe steht in `comparison_policy`. Sie darf nicht zu `available` im Sinn von fünfmal acht Stunden umgedeutet werden. Für Denkendorfs Einkommen wird unmittelbar das gemeinsame Jahresbrutto verwendet; GT-Mittagessen bleibt verpflichtend mit unbekanntem Preis. Dies ist eine Integrationsvorgabe und noch keine Änderung der bestehenden Engine.

Reguläre Ergebnisse verwenden `status: comparable`. Bei fehlenden Angaben wird `status: unavailable` mit konkreten `reasons` geliefert. Ein Ergebnis kann den bekannten Originalmonatsbeitrag enthalten, während das Monatsäquivalent wegen unbekannter Beitragsmonate leer bleibt.

Wesentliche Ergebnisfelder sind `monthly_care_cents`, `payment_months`, `annual_care_cents`, `monthly_equivalent_cents`, `booked_weekly_minutes`, `extra_weekly_minutes`, `selected_price_id`, `components`, `evidence` und `calculation`. Der registergestützte Vergleich ergänzt `ags`, `area_id` und `tariff_id`. Zusatzkosten ändern die Hauptkennzahl nicht. Eine zusätzliche Pflichtkostensumme wird nur bei ausreichend bekannten und eindeutigen ausgewählten Komponenten gebildet; `total_status` nennt deren Umfang.

Für die Erweiterung ist eine Ausnahme für **bereits enthaltene Verpflegung in Waiblingen** vereinbart: Der veröffentlichte Gesamtbeitrag bleibt die Hauptkennzahl und wird mit seinen Beitragsmonaten auf zwölf Monate umgelegt. Die Angebotszuordnung bestimmt, ob Essen enthalten ist. Der Essensbaustein erhält eine Inklusivkennzeichnung und erzeugt keinen weiteren Zuschlag. Eine nicht getrennt veröffentlichte Monatssumme bleibt `null`, verhindert aber weder den bekannten Vergleichswert noch eine bekannte Gesamtsumme; sie darf auch nicht als belegte kostenlose Verpflegung ausgegeben werden. Die UI zeigt „Im Tarif enthalten“. Ein veröffentlichter Einzelpreis je Mahlzeit dient nicht dazu, einen geschätzten Monatsanteil abzuziehen.

Bei **Aichwald** ist der U3-Essensanteil dagegen mit 5.300 Cent monatlich über zwölf Monate gemäß Nutzerangabe festgelegt. Der Abzug setzt sowohl U3 als auch nachgewiesene Einbeziehung des Essens im veröffentlichten Preis voraus. Die Kontrollzelle bleibt ursprünglich 75.350 Cent; abgeleitet werden 70.050 Cent Betreuung und 5.300 Cent Essen. Ü3, bereits essensfreie U3-Angebote und Original-Ausnahmen für altersgemischte Gruppen bleiben davon unberührt. Originalbetrag, Abzug, Nutzerentscheidung und Quellenfundstelle werden gemeinsam erhalten. Diese Ergebnisbehandlung muss bei der anschließenden Integration im Python- und TypeScript-Rechner sowie in der Anzeige umgesetzt und geprüft werden.

## 4. Vergleichsregeln und Default

Das Standardprofil `data/profiles/default.json` ist die Modellfamilie: zwei zusammenlebende Eltern, ein 24 Monate altes Kind ohne Geschwister, Montag bis Freitag mindestens acht Stunden durchgehend, städtischer Tarif. Das Haushaltsbrutto beträgt 80.000 € jährlich; das zu versteuernde Einkommen wird unabhängig davon mit 60.000 € angenommen. Einkommen bleibt im Vorjahr und laufenden Jahr gleich; andere Einkünfte und Vermietungsverluste werden ausgeschlossen. Pass- und zusätzliche Sozialermäßigungen sind nicht bestätigt und werden nicht automatisch angewendet.

Die Einkommensgrundlagen stehen ausdrücklich im Profil: `gross_income` 80.000 €, `taxable_income` 60.000 €, `esslingen_gross_income` 80.000 € und `adjusted_taxable_income` 60.000 € jährlich. Esslingen schließt insbesondere Kindergeld aus und erlaubt einen Arbeitnehmer-Pauschbetrag. Das Modell nimmt keinen solchen Abzug vor. Korntals lokale Grundlage entspricht nur wegen der Modellannahme ohne Vermietungsverluste den 60.000 €; für die Monatstabelle werden daraus 5.000 €. Diese Werte sind gesonderte Modellannahmen, keine allgemeine Gleichsetzung verschiedener Einkommensdefinitionen. `income_assumption_evidence` verknüpft die lokalen Definitionen mit den archivierten Quellen.

`model_income_snapshot` hält Einkommen und zugehörige Bedingungen fest. Wird ein Einkommen oder eine dieser Bedingungen geändert, meldet die Validierung einen Fehler, statt alte steuerliche oder lokale Modellwerte weiterzuverwenden. Für persönliche Angaben wird ein eigenes Profil mit unabhängig bestätigten Einkommensgrundlagen erstellt; Modell-Snapshot und unbestätigte Modellwerte werden nicht übernommen. Die geplante Browseroberfläche muss diesen Wechsel ausdrücklich umsetzen. Lokale `municipality_overrides.incomes` ersetzen bewusst nur die Eingaben der betreffenden Kommune; dabei wird der Snapshot nur für diese lokale Berechnung aufgehoben. Fehlende örtliche Grundlagen bleiben fehlend.

Das bisherige Profil bleibt unter `data/profiles/highest_band.json` unverändert als zusätzliche Höchsttarifreferenz erhalten. Beide Profile haben eigene Sollwerte, JSON-/CSV-Ergebnisse und deutsche Berichte. Die vorhandenen Vorschauen in `output/` enthalten weiterhin die alten Höchsttarifwerte und werden durch den Export nicht aktualisiert.

**Vergleichswert = ursprünglicher Monatsbeitrag × jährliche Beitragsmonate ÷ 12.**

Der Tarif wird für dieses Jahresäquivalent am Stichtag konstant gehalten. Unterjährige Änderungen werden nicht in eine vermeintliche tatsächliche Jahresrechnung eingemischt. Beide Profile sind Referenzannahmen und keine Aussage über den Durchschnittshaushalt. Originalpreis, Beitragsmonate, Mehrstunden und Zusatzkosten bleiben sichtbar.

Es wird nicht zwischen Pauschalen interpoliert. Leonbergs bzw. Gerlingens 8,5 Stunden täglich bleiben zum veröffentlichten Preis erhalten. Ditzingens kleinstes passendes Paket umfasst 45 Wochenstunden. Bei Fellbach entscheidet die **angebotene Tagesverteilung**, nicht eine frei gewählte Wochenstundenzahl: Das geprüfte 40-Stunden-Modell endet donnerstags und freitags nach sieben Stunden. Der Default verwendet deshalb ein belegtes 45-Stunden-Modell mit acht Stunden am Freitag. Die U3-Gebühr beträgt dafür 45 × 15,60 € = 702 € je Monat. Die ganze Wochenstundenzahl wird mit dem Tarif oberhalb der 35-Stunden-Schwelle bewertet.

Leinfelden-Echterdingens Passpreise werden direkt aus den veröffentlichten Tabellen übernommen. Beispielsweise sind für U3/40 Stunden/ein Kind mit Stadtpass A **234,90 €** ausgewiesen; eine freie Prozentrechnung würde 234,88 € ergeben. Die Tabelle bleibt maßgeblich.

Die Berechnung verwendet exakte Dezimalrechnung und rundet das fertige Vergleichsergebnis kaufmännisch auf Cent. Fellbachs Gebühren und Ditzingens Familienpassregel verwenden die satzungsgemäße Rundung auf volle Euro. Bereits veröffentlichte gerundete Werte werden unverändert übernommen.

Der TypeScript-Kern verwendet dafür exakte Bruchrechnung mit `bigint` und gibt ausschließlich ganzzahlige Centbeträge zurück. Die Python-Quotientenberechnung einer Fellbacher Sozialermäßigung wurde im Rahmen der Gegenprüfung so umgeordnet, dass eine exakte Halb-Euro-Grenze nicht durch vorzeitige Division unterschritten wird. Die Referenzprofile ändern sich dadurch nicht; der Grenzfall ist gemeinsam abgesichert.

## 5. Prüfung, Pflege und verbleibende Einschränkungen

Der [Standardvergleich](STANDARDVERGLEICH.md) und der [Höchsttarifvergleich](HOECHSTTARIFVERGLEICH.md) werden aus den Daten erzeugt. Die unabhängigen Sollwerte stehen in `data/reviews/model_family_review.json` und `data/reviews/highest_band_review.json`, mit Fundstellen für alle zwölf Kommunen. Die bisherige `default_review.json` wurde in `highest_band_review.json` umbenannt. Für die Modellfamilie ändern sich Ditzingen, Esslingen und Korntal-Münchingen; deren neue Zellen wurden gegen die archivierten Originaltabellen geprüft. Die zuvor ausgewählten Höchsttarifzellen wurden auch visuell geprüft; Fellbachs Formel wurde mit den offiziellen Tageszeiten abgeglichen. Alle 800 Esslinger Zusatzzeitbeträge werden außerdem automatisiert gegen die archivierte Original-PDF-Tabelle geprüft.

Die Tests decken beide Referenzprofile, Registererweiterung, inaktive Kommunen, AGS-Zuordnung, geteilte Tarifverweise, Schutz der Modellannahmen, Zahlungsmonate, Paketgrenzen, Tagesverteilung, Einkommensarten und Grenzwerte, Alleinerziehende, Familiengröße und Betreuungsrang, Passvoraussetzungen, Rundung, Zusatzzeiten, eingeschlossene Zuschläge, künftige Tarife und fehlende Angaben ab. Die Datenvalidierung kontrolliert außerdem die kanonischen Profile, deren Quellenverweise und die SHA-256-Prüfsummen aller archivierten Antworten und der Geometrie-Referenzdatei.

Für Aktualisierungen wird zuerst eine neue Quellenkopie mit `scripts/fetch_sources.py --refresh` gesichert. Bestehende Quellenkennungen bleiben erhalten. Danach werden neue Tarifversionen ergänzt, alte Intervalle begrenzt, Quellen- und Prüfdaten aktualisiert sowie Tests, Validierung und Export ausgeführt. Quellen mit unterschiedlichen Abrufzeitpunkten werden nicht als identische historische Fassungen ausgegeben.

Die archivierten Dokumente bewahren auch Regeln, die noch nicht vollständig automatisiert sind: Aufnahme-/Austrittsmonate, Abwesenheit und Rückerstattung, Sonderentscheidungen, einzelne Randzeiten und die einmalige Zuschlagsverteilung für mehrere U3-Kinder mit FamilienCard. Unbelegte Tagesverteilungen alternativer Wochenpakete bleiben gesperrt. GT11 in Ludwigsburg und wörtlich mehrdeutige Einkommensgrenzen bleiben als Quellenlücken erhalten. Einrichtungsabhängige Essensvarianten und unbestätigte Essens-Beitragsmonate ergeben keine geschätzte Gesamtsumme.

Historische Daten bleiben archiviert; eine systematische historische Preisreihe und die Webkarte gehören nicht zu dieser Datenmodell-Umsetzung.
