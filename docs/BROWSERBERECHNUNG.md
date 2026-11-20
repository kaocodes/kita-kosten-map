# Gebührenberechnung für den Browser

**Stand:** 8. November 2026 · **Umsetzungspaket:** 2

Die bestehende Tariflogik ist als eigenständiges TypeScript-Modul unter `web/src/domain/` umgesetzt. Es erhält Tarifkataloge, Kommunenregister und Profil als Daten. Es greift weder auf Dateien noch auf Netzwerk, React, Kartenbibliothek oder DOM zu. Die spätere Webanwendung übernimmt das Laden und die Darstellung. Python bleibt die Referenz für Datenprüfung und Export.

## 1. Aufbau und Ausführung

| Datei | Aufgabe |
|---|---|
| `web/src/domain/index.ts` | Öffentliche Schnittstelle für die spätere Anwendung |
| `web/src/domain/types.ts` | TypeScript-Verträge für kanonische JSON-Daten und Ergebnisse |
| `web/src/domain/profile.ts` | Zod-Eingabeprüfung, Normalisierung und Wechsel zum persönlichen Profil |
| `web/src/domain/engine.ts` | Tarifauswahl, Familien- und Einkommensstaffeln, Regeln, Zusatzkosten und Registerzuordnung |
| `web/src/domain/money.ts` | Exakte Bruchrechnung und kaufmännische Rundung |
| `tests/fixtures/comparison_cases.json` | Gemeinsame Szenarien für beide Implementierungen |
| `scripts/evaluate_reference_cases.py` | Auswertung derselben Szenarien mit Python |
| `web/tests/conformance.test.mjs` | Vollständiger Ergebnisabgleich und zusätzliche Modultests |

Für Entwicklung und Tests werden **Node.js ab 22.12**, npm und **Python ab 3.11** benötigt. Python wird im Browser nicht benötigt. Der Rechenkern verwendet zur Laufzeit nur Zod als Paketabhängigkeit. TypeScript ist eine Entwicklungsabhängigkeit. Festgehalten sind TypeScript **7.0.2**, Zod **4.6.7** und die aufgelösten Abhängigkeiten in `package-lock.json`.

Im Projektordner:

```bash
npm ci
npm run typecheck
npm test
python3 -m kita_costs validate
python3 -m unittest discover -s tests
```

`npm test` bereitet seit Paket 3 zuerst die Webdaten vor, kompiliert das Modul, ruft die Python-Referenz über `python3` auf und vergleicht die Ergebnisse mit dem kompilierten JavaScript. Zusätzlich laufen acht Prüfungen der Webdaten; zusammen mit dreizehn Formular-/Profilprüfungen und siebzehn Modellfamilienprüfungen sind es insgesamt 151 JavaScript-Tests. Die Referenzdatei `build/python-reference-results.json` wird dabei vor jedem Testlauf frisch erzeugt. Die Schritte laufen nacheinander; die direkt ausgeführte Testdatei verwendet `node:test` und benötigt keinen weiteren Unterprozess. Bei einem anders benannten Python-Befehl können Build, `python -m scripts.evaluate_reference_cases --output build/python-reference-results.json` und `node web/tests/conformance.test.mjs` separat ausgeführt werden. `npm run build:domain` erzeugt ES-Module und Typdeklarationen unter `build/domain/`. `build/` und `node_modules/` werden nicht versioniert.

Der reine Modul-Build bleibt vom Website-Build getrennt. Seit Paket 3 bündelt Vite den Rechenkern und Zod für die lokale Website. Desktop, schmale Ansicht, individuelle Profile, Ermäßigungen und Eingabefehler sind mit Paket 4 geprüft. Startbefehle und Architektur stehen in [WEBANWENDUNG.md](WEBANWENDUNG.md).

## 2. Öffentliche Schnittstelle

- `normalizeProfile(input: unknown): Profile` prüft ein eingehendes Profil und liefert eine unabhängige Kopie. Fehlende optionale Listen für Einkommen, bewilligte Regeln und Anspruchsvoraussetzungen werden als leere Listen ergänzt.
- `createPersonalProfile(input: unknown): Profile` übernimmt Familienkonstellation und Betreuungsbedarf, setzt `income_mode` auf `specified` und entfernt sämtliche Einkommen, Modellannahmen, Modell-Quellenhinweise und lokale Profilabweichungen. Neue persönliche Einkommensgrundlagen müssen ausdrücklich ergänzt werden.
- `evaluateCity(catalog, profile)` wertet einen kanonischen Tarifkatalog aus.
- `compareMunicipalities(catalogs, profile, registry, municipalityId?)` ordnet die aktiven Registereinträge zu und ergänzt AGS, Kartenfläche und Tarifkennung. Gemeinsam genutzte Tarife behalten getrennte geografische Identitäten und lokale Eingaben.

Zusätzlich sind die kleinen Fachfunktionen `familyCount`, `incomeValue`, `bandMatches` und `formulaPrice` verfügbar. Tarifkataloge und Register sind vorausgehend mit der Python-Datenvalidierung zu prüfen. Die TypeScript-Typen sind keine zweite unabhängige Laufzeitvalidierung des vollständigen Tarifarchivs.

Beispiel für die spätere Anwendung; alle Einkommenseinträge werden von außen ausdrücklich bestätigt übergeben:

```typescript
import {
  compareMunicipalities,
  createPersonalProfile,
  type Income,
  type MunicipalityCatalog,
  type Registry,
} from "../web/src/domain/index.js";

export function comparePersonalInputs(
  catalogs: MunicipalityCatalog[],
  registry: Registry,
  model: unknown,
  confirmedIncomes: Income[],
) {
  const profile = createPersonalProfile(model);
  profile.incomes = confirmedIncomes;
  return compareMunicipalities(catalogs, profile, registry);
}
```

Die Profileingaben entsprechen der [Python-Schnittstelle](DATENMODELL.md). Geldwerte stehen in Eurocent, Zeitwerte in Minuten. Zeichenketten wie `"8000000"`, als Zahlen getarnte Wahrheitswerte und Werte außerhalb des sicheren JavaScript-Ganzzahlbereichs werden abgewiesen. Es gibt keine automatische Brutto-/Steuerumrechnung, keine Gleichsetzung kommunaler Einkommensdefinitionen und keine automatische Bewilligung einkommensabhängiger Ermäßigungen.

Unverändert geladene Modellprofile bleiben durch `model_income_snapshot` geschützt. Eine persönliche Bruttoeingabe wird beim Wechsel zum persönlichen Profil nicht mit den alten steuerlichen Modellwerten kombiniert. Auch lokale Profilabweichungen werden dafür entfernt; bei Bedarf müssen sie neu ausdrücklich gesetzt werden. Der ursprüngliche Modell-Datensatz wird nicht verändert.

## 3. Zahlen, Ergebnisse und Fehler

Der TypeScript-Kern rechnet intern mit gekürzten Brüchen aus `bigint`. Monats-/Jahresumrechnung, Stundenformeln, Prozentsätze und einkommensabhängige Quotienten erzeugen dadurch keine binären Rundungsfehler. Erst die fachlich festgelegten Rundungsschritte liefern ganzzahlige Centbeträge zurück. `bigint` gelangt nicht in die JSON-Ergebnisse.

Die Ergebnisse enthalten dieselben Felder und Gründe wie Python: Betrag, Paket, Buchungsumfang, Mehrstunden, Beitragsmonate, Vergleichsbetrag, zusätzliche Kosten, Quellen und Rechenweg. Die Zustände bleiben getrennt:

- `comparable`: Vergleichsbetrag berechenbar, einschließlich belegter Gebührenfreiheit als `0`.
- `unavailable`: fehlende Eingaben, unbestätigte Bedingungen oder Quellenlücken; konkrete maschinenlesbare `reasons`, keine Ersatzbeträge.
- `ambiguous`: mehrere gleichwertige ungeklärte Tarifvarianten mit den entsprechenden Alternativen.

Ungültige Profile lösen in TypeScript einen `ProfileValidationError` mit `code: invalid_profile` aus. Python verwendet `ValueError`. Die technischen Fehlermeldungen sind englisch; die frühere persönliche Formularoberfläche hat eigene Feldmeldungen. Fehlende Pflichtangaben sind bei ansonsten gültigem Profil ein fachlicher Ergebniszustand und keine automatische Wahl des Höchsttarifs.

Bei der Gegenprüfung wurde ein bestehender Python-Rundungsfehler korrigiert: Bei Fellbach, 45 Wochenstunden, vier berücksichtigten Kindern und bestätigter Sozialermäßigung mit 1.212,50 € maßgeblichem Monatseinkommen gilt `702 € × 40 % × (1.212,50 / 5.820) = 58,50 €`. Auf volle Euro gerundet sind das **59 €**. Die Division vor der Multiplikation konnte zuvor knapp unterhalb der Hälfte landen und 58 € ergeben. Python multipliziert jetzt zuerst; ein gemeinsamer Regressionstest sichert die korrekte Rundung. Beide bestehenden Standardvergleiche bleiben unverändert.

## 4. Prüfung und Pflege

Der gemeinsame Referenztest berechnet die Python-Ergebnisse bei jedem Lauf neu und prüft die TypeScript-API im Referenzmodus. Ausgewählte Fälle enthalten unabhängige Sollwerte aus den Quellen. Die öffentliche Wochenzielauswahl wird separat mit Modellfamilien und den Webdaten geprüft.

Der vollständige Vergleich schließt Quellen, Rechenweg, Zusatzkosten, Buchungspakete, Beitragsmonate, Nullwerte und Fehlerzustände ein. Abgedeckt sind unter anderem Einkommens- und Centgrenzen, unterschiedliche Einkommensdefinitionen, Kinderstaffeln und Betreuungsrang, Passbestätigung, nicht kombinierbare Ermäßigungen, Stundenformeln, Zusatzzeiten, Altersübergänge, veröffentlichte künftige Tarife, fehlende Preise, unbestätigte Tagesmodelle und veraltete Modellannahmen. Weitere Tests prüfen unabhängigen Zustand, zusätzliche Registereinträge, geteilte Tarife und persönliche Eingaben.

Neue gemeinsame Regeln mit gezielten fachlichen Grenzfällen prüfen. Bereits unterstützte örtliche Regeln über Tarifdaten ergänzen. Änderungen der gemeinsamen Berechnung für einen einzelnen Ortsfall vorab abstimmen. [Regelwerk](REGELWERK_DATENANALYSE.md)

## 5. Aufruf durch die Webanwendung

`web/src/App.tsx` ruft `compareModelFamily` mit `weeklyComparison` auf. Die Wochenoption prüft belegte Fünf-Tage-Angebote und verwendet die Ziele 30 bzw. 40 Stunden mit Untergrenzen von 30 bzw. 36 Stunden. Lokale Anpassungen aus dem Tarifkatalog werden bei Bedarf über `model-tariff.ts` angewandt. Die allgemeine API ohne Wochenoption und die Python-Referenz behalten ihre Tagesprüfung.

Das frühere persönliche Formular ist im Quellcode erhalten. Die aktive Anwendung verwendet die Auswahl der [Modellfamilien](MODELLFAMILIEN.md). Die Befehle für regulären Build und Erweiterungsvorschau stehen unter [Webanwendung](WEBANWENDUNG.md).

## Modellfamilien und Familiensummen

`domain/model-family.ts` ergänzt den unabhängigen Rechenkern um validierte Modellauswahlen, explizite Einkommensszenarien und eine Auswertung je Kita-Kind. Die Jahressummen werden vor der abschließenden Rundung addiert. Sindelfingen verwendet im Modell die Altersreihenfolge betreuter Kinder und bei gleicher Kategorie die Eingabereihenfolge. Fehlende zugewiesene Tarifzellen ergeben keine Teilsumme als Gesamtbetrag. Für andere Tarife ohne festgelegte Rangkonvention bleibt die dynamische Zuordnungsprüfung erhalten. Die Modelltests prüfen Quellen-Sollwerte, Einkommen, Haushalte, Kategorien, fehlende Beiträge und Rundung. Fachliche Annahmen und Grenzen stehen in [MODELLFAMILIEN.md](MODELLFAMILIEN.md). Die Ditzinger Familienpassregel verwendet nun `whole_euro_up` und verlangt `no_priority_benefit`.
