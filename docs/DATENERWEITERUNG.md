# Direkte Nachbarkommunen des ursprünglichen Kartenbestands

Die Liste hält die geografische Auswahl vom 10. November 2026 fest. Alle 33 Kandidaten sind als Kataloge erfasst und in die lokale Vorschau eingebunden. Acht gehören auch zum regulären Kartenstand mit 20 Kommunen. Die zweite Erhebung mit vier zusätzlichen Orten wird separat geführt. [Erweiterungsintegration](ERWEITERUNGSINTEGRATION.md) · [Zweite Erhebung](DATENERHEBUNG_2026-11-20.md)

Die Prüfung und Freigabe neuer Datensätze richten sich nach der [Datenpipeline](DATENPIPELINE.md).

## Auswahlgrundlage

Die 33 Kandidaten haben jeweils eine gemeinsame Grenzlinie mit mindestens einer der zwölf ursprünglichen Vergleichskommunen. Grundlage sind die [archivierten BKG-Gemeindegrenzen](../output/municipalities-original.geojson) mit Grenzstand **1. Januar 2025**, abgerufen am 7. November 2026. Herkunft und Prüfsumme stehen in [data/geodata/source.json](../data/geodata/source.json); die Ausgangskommunen im [Kommunenregister](../data/municipality_registry.json).

Die Nachbarschaft wurde über gemeinsam genutzte Grenzabschnitte bestimmt; reine Punktberührungen zählen nicht als gemeinsame Grenzlinie. Die Zuordnung erfolgt über den amtlichen Gemeindeschlüssel (AGS). Alle Grenzen der zwölf Ausgangskommunen haben im verwendeten Geodatenausschnitt einen zugeordneten Nachbarn.

Die Tabelle bildet die Nachbarschaft der zwölf ursprünglichen Vergleichskommunen ab.

## Kandidaten

Alphabetische Reihenfolge. Die letzte Spalte nennt ausschließlich angrenzende Kommunen aus dem bisherigen Vergleichsbestand.

| Nr. | Kommune | AGS | Landkreis | Angrenzende bisherige Vergleichskommunen |
|---:|---|---|---|---|
| 1 | Affalterbach | 08118001 | Ludwigsburg | Ludwigsburg |
| 2 | Aichwald | 08116076 | Esslingen | Esslingen am Neckar |
| 3 | Aidlingen | 08115001 | Böblingen | Sindelfingen |
| 4 | Altbach | 08116004 | Esslingen | Esslingen am Neckar |
| 5 | Asperg | 08118003 | Ludwigsburg | Ludwigsburg |
| 6 | Baltmannsweiler | 08116007 | Esslingen | Esslingen am Neckar |
| 7 | Benningen am Neckar | 08118006 | Ludwigsburg | Ludwigsburg |
| 8 | Deizisau | 08116014 | Esslingen | Esslingen am Neckar |
| 9 | Denkendorf | 08116015 | Esslingen | Esslingen am Neckar |
| 10 | Eberdingen | 08118012 | Ludwigsburg | Ditzingen |
| 11 | Ehningen | 08115013 | Böblingen | Böblingen, Sindelfingen |
| 12 | Erdmannhausen | 08118014 | Ludwigsburg | Ludwigsburg |
| 13 | Filderstadt | 08116077 | Esslingen | Leinfelden-Echterdingen, Stuttgart |
| 14 | Freiberg am Neckar | 08118078 | Ludwigsburg | Ludwigsburg |
| 15 | Grafenau | 08115054 | Böblingen | Sindelfingen |
| 16 | Hemmingen | 08118027 | Ludwigsburg | Ditzingen, Korntal-Münchingen |
| 17 | Holzgerlingen | 08115024 | Böblingen | Böblingen |
| 18 | Kernen im Remstal | 08119093 | Rems-Murr-Kreis | Esslingen am Neckar, Fellbach, Stuttgart |
| 19 | Magstadt | 08115029 | Böblingen | Leonberg, Sindelfingen |
| 20 | Marbach am Neckar | 08118049 | Ludwigsburg | Ludwigsburg |
| 21 | Möglingen | 08118051 | Ludwigsburg | Korntal-Münchingen, Kornwestheim, Ludwigsburg, Stuttgart |
| 22 | Ostfildern | 08116080 | Esslingen | Esslingen am Neckar, Stuttgart |
| 23 | Plochingen | 08116056 | Esslingen | Esslingen am Neckar |
| 24 | Remseck am Neckar | 08118081 | Ludwigsburg | Fellbach, Kornwestheim, Ludwigsburg, Stuttgart |
| 25 | Renningen | 08115041 | Böblingen | Leonberg |
| 26 | Rutesheim | 08115042 | Böblingen | Ditzingen, Leonberg |
| 27 | Schönaich | 08115044 | Böblingen | Böblingen, Leinfelden-Echterdingen |
| 28 | Schwieberdingen | 08118067 | Ludwigsburg | Korntal-Münchingen |
| 29 | Steinenbronn | 08115046 | Böblingen | Leinfelden-Echterdingen |
| 30 | Tamm | 08118071 | Ludwigsburg | Ludwigsburg |
| 31 | Waiblingen | 08119079 | Rems-Murr-Kreis | Fellbach |
| 32 | Waldenbuch | 08115048 | Böblingen | Leinfelden-Echterdingen |
| 33 | Weissach | 08115052 | Böblingen | Ditzingen |

## Umfang nach Landkreis

| Landkreis | Vorgemerkte Kommunen |
|---|---:|
| Böblingen | 11 |
| Esslingen | 8 |
| Ludwigsburg | 12 |
| Rems-Murr-Kreis | 2 |
| **Gesamt** | **33** |

Historische Preisreihen und weitere Nachbarschaftsringe liegen außerhalb dieser geografischen Bestandsaufnahme.
