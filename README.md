# Kita-Gebührenvergleich Region Stuttgart

Die interaktive Karte vergleicht kommunale Gebühren für Krippe und Kindergarten. Der reguläre Build enthält **20 Kommunen**. Auf dem Branch `datapipeline` sind **49 Kommunen** in der lokalen Erweiterungsvorschau verfügbar. Der Vergleichsstichtag des Kartenprofils ist der **4. November 2026**. Vier zusätzliche Gemeinden wurden am 20. November separat erhoben und geprüft. [GitHub Pages](https://kaocodes.github.io/kita-kosten-map/) · [Erweiterungsstand](docs/ERWEITERUNGSINTEGRATION.md) · [Zweite Erhebung](docs/DATENERHEBUNG_2026-11-20.md)

Die voreingestellte **Modellfamilie** besteht aus zwei zusammenlebenden Eltern, einem Krippenkind mit acht Stunden Betreuungsbedarf und 80.000 € Haushaltsjahresbrutto. Die Vergleichsfamilie ist über Haushaltskonstellation, Kinderkategorien, sechs Einkommensstufen und den Betreuungsbedarf je Kita-Kind konfigurierbar. Karte und Liste zeigen die monatlichen Betreuungskosten der Familie. Details zeigen Wochenstunden, Einzelbeiträge, Verpflegung und Quellen. [Modellfamilien](docs/MODELLFAMILIEN.md)

## Lokal starten

Voraussetzungen sind Node.js ab 22.12 und Python ab 3.11. Die Python-Skripte verwenden die Standardbibliothek. Die Website nutzt React, Vite, Leaflet und einen TypeScript-Rechenkern im Browser.

```bash
npm ci
npm run dev
```

Der reguläre Stand läuft auf [localhost:5173](http://127.0.0.1:5173/). Für die lokale Vorschau aller 49 Kommunen `npm run dev:expansion` starten und [localhost:5174](http://127.0.0.1:5174/) öffnen. Die Vorschau verwendet eigene generierte Dateien unter `build/expansion-preview/`.

## Prüfen, bauen und exportieren

```bash
python3 -m kita_costs validate
python3 -m unittest discover -s tests -v
npm test
npm run test:expansion
npm run build
npm run preview
```

`npm run build` prüft das reguläre Datenregister und erzeugt `dist/`. `npm run preview` zeigt diesen Build auf [localhost:4173](http://127.0.0.1:4173/). Der Workflow prüft Pull Requests gegen `main` und veröffentlicht erfolgreiche Builds von `main`. [Webanwendung](docs/WEBANWENDUNG.md) · [Pages-Workflow](.github/workflows/pages.yml)

```bash
python3 -m kita_costs compare --municipality stuttgart
python3 -m kita_costs compare --profile data/profiles/highest_band.json
python3 -m kita_costs export --output build/exports
```

Der Python-Export schreibt Referenzvergleiche als JSON, CSV und Markdown in das gewählte Verzeichnis. Hinzu kommen Register, Tarifkatalog sowie CSV-Tabellen für Angebote, Einzelpreise, Einkommensstufen und Zusatzkosten. Beträge stehen in Cent und Zeitangaben in Minuten. Der Browservergleich verwendet die aktuellen Wochenziele. Die archivierten Python-Berichte halten ihre damalige Auswahl mit acht Stunden pro Wochentag fest.

## Dokumentation und Datenpflege

- [Datenpipeline](docs/DATENPIPELINE.md) für Quellen, Kataloge, Stichproben, Kartenvorschau und Freigabe.
- [Regelwerk](docs/REGELWERK_DATENANALYSE.md) für Zeitpakete, Einkommens- und Geschwisterregeln, Kosten und Quellen.
- [Projektanforderungen](docs/PROJECT_REQUIREMENTS.md) für fachlichen Umfang und Abnahme.
- [Webanwendung](docs/WEBANWENDUNG.md), [Datenmodell](docs/DATENMODELL.md) und [Browserberechnung](docs/BROWSERBERECHNUNG.md) für Architektur, Laufzeit und Schnittstellen.
- [Quellenübersicht](docs/QUELLENUEBERSICHT.md) für die anfänglichen zwölf Kommunen sowie Verweise auf die Erweiterungserhebungen.

Die kanonischen Kataloge stehen unter [data/municipalities/](data/municipalities/). Das [Kommunenregister](data/municipality_registry.json) verbindet Tarife und Kartenflächen. Das [Quellenmanifest](data/source_manifest.json) verknüpft URLs, lokale Originaldateien, Abrufzeitpunkte und SHA-256-Prüfsummen. Quellenabgleich und fachliche Erfassung werden bei Bedarf angestoßen.
