# UI-Neugestaltung: Familienatlas

**Stand:** 9. November 2026

**Status:** Abgestimmte Gestaltungsrichtung und überarbeiteter Layoutentwurf; die Übertragung in die produktive React-Anwendung ist noch nicht beauftragt.

**Gewählte Variante:** Familienatlas. Die zuvor untersuchten Varianten Kartenatelier und Vergleichstisch werden nicht weiterverfolgt.

## Entwurf und Abgrenzung

Die [Familienatlas-Vorschau](design/familienatlas.html) ist eine eigenständige, im Browser aufrufbare Planungsansicht. Sie zeigt die neue Anordnung, Farben sowie aufklappbare Kommunen- und Kinderdetails. Sie ist kein neuer Build der veröffentlichten Website und wird nicht durch den Pages-Workflow veröffentlicht.

Der Entwurf enthält zwei fest eingebettete, mit dem vorhandenen TypeScript-Rechenkern vorberechnete Modellkonfigurationen für alle zwölf Kommunen:

- Modellfamilie: zwei zusammenlebende Eltern, ein Krippenkind, 80.000 € Haushaltsbrutto pro Jahr, acht Stunden durchgehende Betreuung täglich von Montag bis Freitag.
- Beispiel einer angepassten Modellfamilie: gleiche Haushalts- und Einkommensannahmen, ein Krippenkind und ein Kindergartenkind mit jeweils acht Stunden täglichem Bedarf.

Die Familienkarten wechseln zwischen diesen Beispielen. Die Formularfelder zeigen die vorgesehene Position und bleiben in der Planungsansicht deaktiviert. Ein frei bedienbarer neuer Konfigurator ist nicht Teil dieses Planungsschritts. Gebühren, Kinderdetails, Essensvarianten und Quellen werden aus den bestehenden generierten Browserdaten übernommen; es wurden keine Tarife neu recherchiert oder verändert. Stichtag der Beispielberechnung ist der 4. November 2026, Quellenprüfung und Abruf der Gebührenquellen erfolgten am 7. November 2026.

Für die Vorschau werden D3 7.9.0 über jsDelivr und die Schriften Bricolage Grotesque, DM Sans und Caveat über Google Fonts geladen. Diese Entwurfsabhängigkeiten legen keine zusätzlichen Produktionsabhängigkeiten fest. Die Geometrie ist direkt eingebettet und stammt aus den bereits archivierten und vereinfacht aufbereiteten BKG-Gemeindegrenzen, Grenzstand 1. Januar 2025, Lizenz dl-de/by-2-0. Die Kartenansicht des Entwurfs demonstriert Auswahl und Farben; sie ersetzt noch nicht die bestehende Leaflet-Interaktion mit Zoom und Regionsansicht.

## Sprache und Modellbegriff

- In der sichtbaren Oberfläche heißt die frei gewählte Ausgangskonstellation durchgehend **Modellfamilie**, niemals Standardfamilie. Sie stellt weder einen Durchschnitts- noch einen Medianhaushalt dar.
- Erste Familienkarte: **Die Modellfamilie**. Zweite Familienkarte: **Eine Modellfamilie, die zu dir passt.**
- Zurücksetzen wird beispielsweise mit **Spielkarte umdrehen · zur Modellfamilie** bezeichnet.
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

Eine Auswahl **4+** würde eine beliebige Kinderzahl unzulässig mit vier gleichsetzen, da jedes zusätzlich betreute Kind die Familiensumme beeinflussen kann. Außerdem ist die Anwendung der vierten Stufe auf größere Haushalte in Korntal-Münchingen, Kornwestheim, Leonberg und teilweise Leinfelden-Echterdingen nicht durchgängig belegt. Die Produktionsoberfläche wird in diesem Planungsschritt noch nicht eingeschränkt; die endgültige Übernahme der vorgeschlagenen Begrenzung erfolgt mit dem Konfigurator-Umbau.

## Prüfung vor Veröffentlichung der späteren Umsetzung

**Prüfung dieses Planungsstands:** Die eigenständige Vorschau wurde im Desktop-Browser angesehen. Beide vorberechneten Konfigurationen enthalten für alle zwölf Kommunen vollständige Familienbeträge. Geprüft wurden der Wechsel zwischen den Familienkarten, die aktualisierte Gebührenreihenfolge, die vollständigen Kommunendetails in der Liste und das Öffnen eines Kindes mit direkt sichtbaren Verpflegungsvarianten. Der Stand wurde zusätzlich auf JavaScript-Syntaxfehler und unerwünschte alte Oberflächentexte geprüft. Das ist keine vollständige mobile oder barrierefreie Abnahme und keine Prüfung einer neu implementierten Produktionsoberfläche.

- Vollständigkeit und Gleichheit der Kommuneninformationen aus Karte und Liste prüfen, einschließlich Einzelbeiträgen, Zusatzkosten und Fundstellen.
- Ein- und Mehrkindfamilien, Kinder ohne Kita, Nullbeträge, fehlende Angaben und unvollständige Familiensummen prüfen.
- Aufklappbereiche, Fokusführung und Familienkarten mit Tastatur sowie auf Desktop und schmalen Bildschirmen prüfen.
- Gebührenfarben einschließlich hoher Familiengesamtsummen, neutraler Umgebungsflächen und Textkontrast prüfen.
- Datenerhebung, Quellenprüfdatum, Tarifgültigkeit und Berechnungsstichtag fachlich auseinanderhalten.
- Bestehende Rechenkern-, Python-Gegenprüfungen und Produktionsbuild vor Veröffentlichung erfolgreich ausführen. Dieser Planungscommit ändert deren Implementierung nicht.

Die Aufnahme der vorgemerkten Nachbarkommunen bleibt bis zur stabilen Website und abgeschlossenen, dokumentierten UI/UX-Prüfung zurückgestellt; siehe [Datenerweiterung](DATENERWEITERUNG.md).
