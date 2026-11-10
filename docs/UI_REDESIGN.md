# UI-Neugestaltung: Familienatlas

**Stand:** 9. November 2026

**Status:** Familienatlas in der React-/Leaflet-Anwendung umgesetzt. Datensatz-Erweiterung und anschließendes Design-Rework wurden auf `Datensatz-Erweiterung` lokal geprüft und auf Nutzerwunsch für Merge und Pages-Veröffentlichung freigegeben. Die nachfolgende Vorschau bleibt als ursprünglicher Planungsstand erhalten.

**Gewählte Variante:** Familienatlas. Die zuvor untersuchten Varianten Kartenatelier und Vergleichstisch werden nicht weiterverfolgt.

**Nacharbeiten vom 10. November 2026:** Die UI-Punkte aus [NAECHSTE_SESSION.md](NAECHSTE_SESSION.md) sind lokal umgesetzt: animierte Kommunennamen auf lila Balken, plakative Familienkarten-Beschriftungen und kompakte Methodik ohne Verpflegungsblock oder Bildmotiv direkt auf dem Seitenhintergrund. Die zuletzt gelieferten Familien- und Logoillustrationen bleiben erhalten. SEO ist weiterhin nur eine Erinnerung.

**Kurzes Design-Rework vom 10. November 2026:** Zusätzliche Überschrift und Kommunenzähler über der Karte sowie Pausenbutton entfernt. Beide Familienkartentitel verwenden dieselbe Schrift, Größe und Balkengestaltung; die Vergleichsfamilie hat einen lila Balken. Die Illustrationsmaße wurden an allen Bildschirmstufen mit Faktor 1,3 vergrößert und auf die verfügbare Kartenbreite begrenzt. Kräftigere Schatten betonen die auswählbaren Karten. Lokal auf Port 5174 geprüft; Gebührenberechnung und Datensätze bleiben unverändert.

## Lokaler Implementierungsstand

Die echte Anwendung verwendet das Familienatlas-Layout mit großer Karte und vollständigen Kommunendetails darunter, Familienkarten und absteigender Gebührenliste. Die Liste verwendet dieselbe `FamilyDetails`-Komponente wie der Kartenbereich. Die tatsächlichen Modellwerte werden weiterhin im Browser mit dem bestehenden Rechenkern berechnet; die zwei vorberechneten Beispiele gehören ausschließlich zur archivierten Planungsansicht.

- Seitenhintergrund Flieder, Inhaltsflächen warmes Weiß, Kartenhintergrund Pastellhellblau. Auf Flächen ohne Geometrie ist ein leichtes Punktemuster sichtbar; Umgebungsgebiete sind grau.
- Leaflet-Zoom, Verschieben und **Region anzeigen** bleiben erhalten. Alle zwölf Vergleichskommunen sind dauerhaft beschriftet; bei Platzmangel werden Namen mit kurzen Verbindungslinien versetzt. Die 128 Umgebungsgebiete erhalten keine Namensschilder. Diese Abgrenzung wurde ausdrücklich bestätigt.
- Die Auswahlkontur liegt in einer eigenen Leaflet-Ebene über sämtlichen Gebühren- und Umgebungsflächen und unter den Beschriftungen.
- Die Legende zeigt nur **günstig** und **teuer** an den Enden des Farbbalkens. Die festen Gebührenklassen des Entwurfs bleiben von der gewählten Familie unabhängig; fehlende Ergebnisse werden grau dargestellt.
- Die Kinderdetails sind zunächst zugeklappt; Verpflegung und Zusatzkosten stehen direkt im geöffneten Kindbereich. Listenansicht und Kartenansicht erhalten eindeutige Kennungen für ihre Quellen- und Kindbereiche.
- Die Familienkarten öffnen den echten Konfigurator beziehungsweise setzen auf die Modellfamilie zurück. Die sichtbare Kinderzahl ist auf 1–4 begrenzt, der Rechenkern behält seine Unterstützung für bis zu zwölf Kinder. Einkommensszenarien und Gebührenberechnung wurden fachlich nicht verändert.
- Die angeforderten Entwurfstexte **Frei gewählte Modellfamilien …** und **Im Entwurf: zwei Kinder in Betreuung** erscheinen nicht in der Anwendung. Die Rücksetzaktion heißt **Zurück zur Modellfamilie**.
- Bilder werden an zwei Stellen verwendet: Logo im Kopfbereich und Illustration der Modellfamilie. Der Hamburger wurde aus dem Methodikbereich entfernt. Die Familienkarte wählt bei jedem Seitenladen eines von sechs nutzerseitig gelieferten Motiven und hält die Wahl während der Bedienung fest. Kopfbereich und Favicon verwenden das kräftigere der beiden gelieferten Kita-Pin-Symbole. Aktive WebP-Dateien und Aufbereitung stehen in [BILDASSETS.md](BILDASSETS.md); die Herkunft der früheren Pixelart bleibt in [PIXELART_ASSETS.md](PIXELART_ASSETS.md) dokumentiert.
- Bricolage Grotesque wird lokal als WOFF2 ausgeliefert. Die OFL-Lizenz wird mitgeliefert und in die erzeugten Drittanbieterhinweise aufgenommen. Es werden zur Laufzeit keine Google-Font-Dateien nachgeladen.

**Verifikation:** 153 JavaScript-Tests erfolgreich, einschließlich der vorhandenen Python-Gegenprüfung; zusätzlich 70 Python-Tests, TypeScript-Prüfung und statischer Build erfolgreich. Im Browser wurden Auswahl, Verschieben, Zoom und Regionsansicht, vollständige identische Kommuneninformationen in Karte und Liste, Zweikindmodell (Sindelfingen 354,20 €), Tastaturbedienung der Kinderdetails mit direkt sichtbarem Essen, Nullbeträge bei Kindern ohne Kita sowie Zurücksetzen geprüft. Bei 390 und 320 Pixeln wurden keine horizontalen Überläufe oder defekten Bilder gefunden; alle zwölf Vergleichsnamen bleiben sichtbar. Drei geladene Bilddateien und eindeutige Elementkennungen wurden kontrolliert; die Browserkonsole zeigte keine Fehler. Diese Prüfungen sind keine vollständige fachliche Nutzerabnahme.

## Ergänzende UI-Prüfung vom 10. November 2026

Die neue Überschrift bezieht ihre Namen aus dem aktiven Kommunenregister und wechselt sie alle 3,5 Sekunden. Der Pausenbutton wurde beim anschließenden kurzen Design-Rework auf Nutzerwunsch entfernt; bei `prefers-reduced-motion: reduce` bleibt der Wechsel statisch. Der Screenreader erhält eine feste verständliche Frage statt laufender Namensmeldungen. Die Größe aller Namen wird im Layout berücksichtigt, sodass auch der Wechsel zwischen Leinfelden-Echterdingen und kurzen Namen die Kartenposition nicht verschiebt. Die Überschrift verändert weder Kommunenauswahl noch Gebühren.

Die rechte Familienkarte trägt den größeren, schrägen Schriftzug **Deine Vergleichsfamilie** weiß auf kräftigem Lila. **Die Modellfamilie** steht weiß und fett auf einem leicht angeschrägten anthrazitfarbenen Balken. Die Familienbilder und die übrigen Karteninhalte bleiben erhalten. Der Methodikbereich ist kleiner, transparent und rahmenlos; Verpflegung bleibt ausschließlich in den Kommunen-/Kinderdetails zugänglich.

Im Browser wurden Namenswechsel, längeres Pausieren, Fortsetzen, konstante Kartenposition, korrekte Farben und der Methodikbereich ohne Bilder oder Verpflegung geprüft. Mobilansichten mit 320 und 390 Pixeln haben keine horizontalen Überläufe; die linke Beschriftung wurde für die schmalste Ansicht angepasst. Der Produktionsbuild einschließlich TypeScript-Prüfung ist erfolgreich. Eine Veröffentlichung oder SEO-Überarbeitung erfolgte nicht.

## Archivierter Planungsentwurf

Die [Familienatlas-Vorschau](design/familienatlas.html) ist eine eigenständige, im Browser aufrufbare Planungsansicht. Sie zeigt die neue Anordnung, Farben sowie aufklappbare Kommunen- und Kinderdetails. Sie ist kein neuer Build der veröffentlichten Website und wird nicht durch den Pages-Workflow veröffentlicht.

Der Entwurf enthält zwei fest eingebettete, mit dem vorhandenen TypeScript-Rechenkern vorberechnete Modellkonfigurationen für alle zwölf Kommunen:

- Modellfamilie: zwei zusammenlebende Eltern, ein Krippenkind, 80.000 € Haushaltsbrutto pro Jahr, acht Stunden durchgehende Betreuung täglich von Montag bis Freitag.
- Beispiel einer angepassten Modellfamilie: gleiche Haushalts- und Einkommensannahmen, ein Krippenkind und ein Kindergartenkind mit jeweils acht Stunden täglichem Bedarf.

Die Familienkarten wechseln zwischen diesen Beispielen. Die Formularfelder zeigen die vorgesehene Position und bleiben in der Planungsansicht deaktiviert. Ein frei bedienbarer neuer Konfigurator ist nicht Teil dieses Planungsschritts. Gebühren, Kinderdetails, Essensvarianten und Quellen werden aus den bestehenden generierten Browserdaten übernommen; es wurden keine Tarife neu recherchiert oder verändert. Stichtag der Beispielberechnung ist der 4. November 2026, Quellenprüfung und Abruf der Gebührenquellen erfolgten am 7. November 2026.

Für die Vorschau werden D3 7.9.0 über jsDelivr und die Schriften Bricolage Grotesque, DM Sans und Caveat über Google Fonts geladen. Diese Entwurfsabhängigkeiten legen keine zusätzlichen Produktionsabhängigkeiten fest. Die Geometrie ist direkt eingebettet und stammt aus den bereits archivierten und vereinfacht aufbereiteten BKG-Gemeindegrenzen, Grenzstand 1. Januar 2025, Lizenz dl-de/by-2-0. Die Kartenansicht des Entwurfs demonstriert Auswahl und Farben; sie ersetzt noch nicht die bestehende Leaflet-Interaktion mit Zoom und Regionsansicht.

## Sprache und Modellbegriff

- In der sichtbaren Oberfläche heißt die frei gewählte Ausgangskonstellation durchgehend **Modellfamilie**, niemals Standardfamilie. Sie stellt weder einen Durchschnitts- noch einen Medianhaushalt dar.
- Erste Familienkarte: **Die Modellfamilie**. Zweite Familienkarte: **Eine Modellfamilie, die zu dir passt.**
- Die endgültige Rücksetzbeschriftung lautet **Zurück zur Modellfamilie**; die archivierte Vorschau enthält noch die frühere Formulierung.
- **Tarifstichtag <Datum>** wird als prominente Datumsangabe durch **Datenerhebung <Datum>** ersetzt. Hier muss das belegte Erhebungsdatum stehen, nicht lediglich der bisherige Tarifstichtag unter neuem Namen. Der Berechnungsstichtag bleibt in der Methodik nachvollziehbar; Quellenprüfung und Tarifgültigkeit bleiben in den Details erhalten.
- **Wenige Auswahlen. Gleiche Annahmen in jeder Kommune.** wird durch **Die gleiche Berechnungsgrundlage in jeder Kommune.** ersetzt.
- Die Überschrift des Familienbereichs lautet **Vergleiche die Gebühren mit deiner Familie**.
- Die Texte **Du hast die Karten …**, **Die Gebühren auf einen Blick** auf der Karte und **Standardfamilie · 8 Std./Tag** über der Karte entfallen.

## Farben und Gestaltung

Die helle Pastellgestaltung ist bewusst festgelegt und gilt im Entwurf auch bei dunkler Systemdarstellung:

| Element | Vorgesehene Gestaltung | Entwurfswert |
|---|---|---|
| Seitenhintergrund | Helles Flieder/Pastelllila | `#eeebf8` |
| Inhaltsbereiche | Warmes Weiß | `#fffdf8` |
| Kartenhintergrund | Leichtes Pastellhellblau | `#e8f2fa` |
| Umgebungsflächen ohne Gebühren | Neutrale Grautöne, keine Brauntöne | `#cbd1dc` |
| Text und Auswahlkontur | Anthrazit | `#303440` / `#363d4b` |
| Günstige bis teure Gebühren | Blau → Lila → warmes Orange | Bestehende Entwurfsabstufungen erhalten |

Der kreative, handgezeichnete Eindruck entsteht durch illustrierte Familienkarten, leicht unregelmäßige Konturen und einzelne handschriftliche Akzente. Zahlen, Quellen, Listen und Formularbeschriftungen bleiben gut lesbar. Die Gestaltung orientiert sich am Charakter der [Pudding-Referenz](https://pudding.cool/2023/03/same-name/), ohne deren Inhalte zu übernehmen.

Die Kartenlegende zeigt einen zusammenhängenden Farbbalken mit **günstig** links und **teuer** rechts; die Beschriftungen liegen unmittelbar unter den passenden Enden des Balkens. Numerische Euro-Farbstufen entfallen aus der sichtbaren Legende. Interne Eurogrenzen bleiben feste Regeln: Sie werden durch das Weglassen der Beschriftungen nicht automatisch zu relativen Rangfarben und dürfen beim Familienwechsel nicht stillschweigend ihre Bedeutung ändern. Die zunächst übernommenen Entwurfsgrenzen sind vor Produktionsübernahme auch für höhere Familiengesamtsummen zu prüfen. Konkrete Beträge stehen weiterhin in Kommunendetails und Liste. Umgebungsflächen ohne Daten werden gesondert erklärt und erhalten keine Gebührenfarbe.

## Reihenfolge der Bereiche

1. Kopfbereich mit Titel, kurzer Erklärung und Datenerhebung.
2. Große, zentrierte Datenkarte über die verfügbare Inhaltsbreite; Legende und Geodatenhinweise gehören zum Kartenbereich.
3. **Ausgewählte Kommune** direkt unter der Karte innerhalb desselben Bereichs.
4. **Vergleiche die Gebühren mit deiner Familie** mit den beiden auswählbaren Familienkarten. Die Konfiguration klappt bei Auswahl der anpassbaren Modellfamilie darunter auf.
5. **Alle Kommunen im Vergleich**, nach Familien-Monatsäquivalent absteigend, teuer bis günstig. Nicht berechenbare Ergebnisse folgen getrennt erkennbar am Ende und werden nicht als kostenlos behandelt.
6. Methodik und Quellen-/Lizenzhinweise.

Auf schmalen Bildschirmen bleiben Karte und Kommunendetails unmittelbar zusammen. Familienkarten und Formularfelder ordnen sich bei Bedarf untereinander an. Öffnen von Details in der Kommunenliste darf keinen unbemerkten Wechsel zu einem weiter oben stehenden Informationsfeld voraussetzen.

## Kommunendetails: vollständige Inhalte der bestehenden Website

Die Detailansicht wurde mit der veröffentlichten GitHub-Pages-Version und `web/src/components/FamilyDetails.tsx` abgeglichen. Fachliche Informationen werden erhalten, ihre Sichtbarkeit wird neu organisiert.

Ständig sichtbar sind Kommunenname, Anzahl der Haushaltskinder und der Kita-Kinder, vollständiger Familienbeitrag pro Monat sowie der Hinweis auf die Umlegung auf zwölf Monate und separat ausgewiesenes Essen/Zusatzkosten. Gründe für fehlende oder mehrdeutige Berechnungen, der Hinweis auf unvollständige Familiensummen und der Sonderfall ohne Kita-Kind bleiben sichtbar, wenn sie zutreffen.

Pro Kind gibt es einen zunächst geschlossenen, per Tastatur bedienbaren Aufklappbereich. Die geschlossene Zeile zeigt Kindnummer, Kinderkategorie und das Monatsäquivalent beziehungsweise den fehlenden Wert oder den Hinweis auf keine Kita-Kosten. Im geöffneten Bereich stehen:

- Monatsäquivalent; bei Bedarf Wertebereich und Hinweis auf unklaren Geschwisterrang.
- Betreuungsbedarf pro Tag von Montag bis Freitag.
- Monatsbeitrag laut Tarif und Zahl der Beitragsmonate.
- Gebuchte Wochenstunden und zusätzlich gebuchte Zeit.
- Originalbezeichnung des gewählten Betreuungsmodells und Tarifgültigkeit.
- Zutreffende kindbezogene Hinweise und Gründe für fehlende Werte.
- **Direkt sichtbare Verpflegung und Zusatzkosten**, einschließlich Einheit, Beitragsmonaten, Angebotsvarianten und Sonderfällen. Dafür gibt es keinen weiteren verschachtelten Aufklappbereich.
- Hinweis auf getrennte Varianten und den Verzicht auf eine geschätzte Essens-/Zusatzkostensumme. Fehlende Angaben werden als solche ausgewiesen.

Kinder ohne Kita-Betreuung bleiben mit ihrer Kategorie und dem Hinweis auf Berücksichtigung als Geschwisterkind sichtbar. Unter den Kinderdetails folgen wie bisher die Erläuterung der Familien-Jahressumme, der Rundungshinweis, der erste offizielle Quellenlink, das Quellenprüfdatum sowie ein aufklappbares Verzeichnis **aller Quellen und Fundstellen**.

## Verbindung von Karte und Kommunenliste

Die Auswahl auf der Karte aktualisiert den vollständigen Detailbereich unmittelbar unter der Karte. Die Auswahl in der Liste öffnet **dieselben vollständigen Inhalte** direkt unter der gewählten Listenzeile; es gibt dort keine auf wenige Angaben reduzierte Ersatzansicht. Auch hier sind die Kinder zunächst einzeln zugeklappt und enthalten nach dem Öffnen ihre Verpflegungs- und Zusatzkosten.

In der späteren React-Umsetzung sollen beide Darstellungen dieselbe Detailkomponente und dieselben Berechnungsergebnisse verwenden. Karte und Liste bleiben auf dieselbe Kommune und Modellkonfiguration bezogen. Ein Klick in der Liste darf weder einen automatischen Sprung nach oben auslösen noch eine andere Familieneinstellung verwenden. Die eingebettete Listenansicht zeigt jeweils eine geöffnete Kommune; Quellen und Kinderdetails bleiben am Auswahlort erreichbar.

## Kinderzahl und spätere Umsetzung

Für den sichtbaren Konfigurator wurde zunächst eine Auswahl von **1 bis 4 Kindern** vorgeschlagen: Die hinterlegten Geschwisterstaffeln reichen bis zur vierten Stufe; eine weitere fünfte Rabattstufe ist im aktuellen Datensatz nicht erfasst. Die technische Unterstützung größerer Familien muss deshalb nicht aus Rechenkern oder Daten entfernt werden.

Eine Auswahl **4+** würde eine beliebige Kinderzahl unzulässig mit vier gleichsetzen, da jedes zusätzlich betreute Kind die Familiensumme beeinflussen kann. Außerdem ist die Anwendung der vierten Stufe auf größere Haushalte in Korntal-Münchingen, Kornwestheim, Leonberg und teilweise Leinfelden-Echterdingen nicht durchgängig belegt. Die lokale Familienatlas-Oberfläche übernimmt diese Begrenzung inzwischen; Rechenkern und Tarifdaten bleiben davon unberührt.

## Prüfung vor Veröffentlichung der späteren Umsetzung

**Prüfung dieses Planungsstands:** Die eigenständige Vorschau wurde im Desktop-Browser angesehen. Beide vorberechneten Konfigurationen enthalten für alle zwölf Kommunen vollständige Familienbeträge. Geprüft wurden der Wechsel zwischen den Familienkarten, die aktualisierte Gebührenreihenfolge, die vollständigen Kommunendetails in der Liste und das Öffnen eines Kindes mit direkt sichtbaren Verpflegungsvarianten. Der Stand wurde zusätzlich auf JavaScript-Syntaxfehler und unerwünschte alte Oberflächentexte geprüft. Das ist keine vollständige mobile oder barrierefreie Abnahme und keine Prüfung einer neu implementierten Produktionsoberfläche.

- Vollständigkeit und Gleichheit der Kommuneninformationen aus Karte und Liste prüfen, einschließlich Einzelbeiträgen, Zusatzkosten und Fundstellen.
- Ein- und Mehrkindfamilien, Kinder ohne Kita, Nullbeträge, fehlende Angaben und unvollständige Familiensummen prüfen.
- Aufklappbereiche, Fokusführung und Familienkarten mit Tastatur sowie auf Desktop und schmalen Bildschirmen prüfen.
- Gebührenfarben einschließlich hoher Familiengesamtsummen, neutraler Umgebungsflächen und Textkontrast prüfen.
- Datenerhebung, Quellenprüfdatum, Tarifgültigkeit und Berechnungsstichtag fachlich auseinanderhalten.
- Bestehende Rechenkern-, Python-Gegenprüfungen und Produktionsbuild vor Veröffentlichung erfolgreich ausführen. Dieser Planungscommit ändert deren Implementierung nicht.

Die Aufnahme der vorgemerkten Nachbarkommunen bleibt bis zur stabilen Website und abgeschlossenen, dokumentierten UI/UX-Prüfung zurückgestellt; siehe [Datenerweiterung](DATENERWEITERUNG.md).
