# Mögliche Datenerweiterung nach Stabilisierung der Website

**Stand:** 8. November 2026

**Status:** Für die nächste mögliche Erweiterung vorgemerkt; Umsetzung zurückgestellt bis zum Abschluss der Stabilisierung und vollständigen UI/UX-Prüfung.

## Voraussetzung und Reihenfolge

Die Website mit den bestehenden zwölf Vergleichskommunen hat Vorrang. Weitere Kommunen werden erst aufgenommen, wenn die Website stabil läuft und die vollständige UI/UX-Prüfung abgeschlossen und dokumentiert ist. Die bisherigen automatisierten Tests und punktuellen Browserprüfungen bedeuten noch keine vollständige UI/UX-Abnahme.

Die Prüfung umfasst insbesondere Modellkonfiguration und Zurücksetzen, Karten- und Listenauswahl, Familien- und Einzelbeiträge, Quellen, Nullbeträge sowie fehlende und unvollständige Ergebnisse. Desktop, Mobilansicht und Tastaturbedienung sind einzubeziehen. Vor der Gebietserweiterung sind offene blockierende Fehler zu beheben und die geltenden technischen Prüfungen erfolgreich abzuschließen.

Nach diesem Abschluss werden die Kandidaten priorisiert und schrittweise in die einheitliche Datenpipeline aufgenommen: offizielle Quellen ermitteln und archivieren, Tarife in das gemeinsame Schema übertragen, örtliche Regeln und Referenzfälle prüfen und die Kommune anschließend im Register aktivieren. Die Liste legt keine Erhebungs- oder Veröffentlichungsreihenfolge fest.

## Auswahlgrundlage

Die 33 Kandidaten haben jeweils eine gemeinsame Grenzlinie mit mindestens einer der aktuell zwölf Vergleichskommunen. Grundlage sind die [archivierten BKG-Gemeindegrenzen](../output/municipalities-original.geojson) mit Grenzstand **1. Januar 2025**, abgerufen am 7. November 2026. Herkunft und Prüfsumme stehen in [data/geodata/source.json](../data/geodata/source.json); die Ausgangskommunen im [Kommunenregister](../data/municipality_registry.json).

Die Nachbarschaft wurde über gemeinsam genutzte Grenzabschnitte bestimmt; reine Punktberührungen zählen nicht als gemeinsame Grenzlinie. Die Zuordnung erfolgt über den amtlichen Gemeindeschlüssel (AGS). Alle Grenzen der zwölf Ausgangskommunen haben im verwendeten Geodatenausschnitt einen zugeordneten Nachbarn.

Die bereits auf der Karte vorhandenen Flächen sind der geografische Ausgangspunkt. Für diese vorgemerkte Erweiterung sind Tarif- und Quellenrecherche noch nicht begonnen; die Kandidaten werden durch dieses Dokument nicht als aktive Vergleichskommunen registriert. Bei Aufnahme aller Kandidaten würde der Vergleich von zwölf auf 45 Kommunen wachsen.

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

Die derzeitigen zwölf Tarifkataloge, Vergleichswerte und aktiven Registereinträge bleiben während der Stabilisierung die fachliche Grundlage. Historische Preisreihen und weitere Nachbarschaftsringe sind keine Bestandteile dieser Kandidatenliste.
