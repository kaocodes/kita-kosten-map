# Bilddateien für Familienkarte und Kopfbereich

## Aktueller Stand

Die vom Nutzer bereitgestellten Originale liegen unter `image-drafts/` und bleiben unverändert. Alle sechs Familienbilder und beide Symbolvorschläge wurden in transparente WebP-Dateien umgewandelt und nach `web/public/images/` kopiert. Sie werden von der Website selbst ausgeliefert; externe Bilddienste sind nicht beteiligt.

| Original | Website-Datei | Auflösung | Dateigröße |
|---|---|---:|---:|
| `image-drafts/family-1.png` | [`family-1.webp`](../web/public/images/families/family-1.webp) | 512 × 512 | 34.104 Byte |
| `image-drafts/family-2.png` | [`family-2.webp`](../web/public/images/families/family-2.webp) | 512 × 512 | 36.644 Byte |
| `image-drafts/family-3.png` | [`family-3.webp`](../web/public/images/families/family-3.webp) | 512 × 512 | 38.534 Byte |
| `image-drafts/family-4.png` | [`family-4.webp`](../web/public/images/families/family-4.webp) | 512 × 512 | 32.342 Byte |
| `image-drafts/family-5.png` | [`family-5.webp`](../web/public/images/families/family-5.webp) | 512 × 512 | 35.280 Byte |
| `image-drafts/family-6.png` | [`family-6.webp`](../web/public/images/families/family-6.webp) | 512 × 512 | 32.798 Byte |
| `image-drafts/icon.png` | [`kita-pin.webp`](../web/public/images/icons/kita-pin.webp) | 256 × 256 | 25.572 Byte |
| `image-drafts/icon-2.png` | [`kita-pin-bold.webp`](../web/public/images/icons/kita-pin-bold.webp) | 256 × 256 | 27.792 Byte |

Die acht Originaldateien umfassen zusammen 13.312.640 Byte, die Website-Versionen 263.066 Byte; das entspricht einer Verringerung um rund 98 %. Pro Seitenaufruf wird nur das tatsächlich gewählte Familienbild geladen.

## Aufbereitung

ImageMagick entfernt Metadaten und überschüssige transparente Außenränder. Die Bilder werden proportional mit Lanczos-Filter verkleinert, ohne Motivteile abzuschneiden, und mittig auf gleich großen transparenten Flächen angeordnet. Die einheitlichen Familienflächen verhindern wechselnde Bildrahmen beim Neuladen.

- Familien: Motiv maximal 480 × 480 Pixel auf 512 × 512 Pixeln; WebP-Qualität 90, Alpha-Qualität 100. Damit stehen für die aktuelle Darstellung mit maximal 155 CSS-Pixeln Breite auch auf hochauflösenden Displays ausreichend Bildpunkte bereit.
- Symbole: Motiv maximal 224 × 224 Pixel auf 256 × 256 Pixeln; verlustfreie WebP-Kompression. Die größere Datei deckt die Darstellung im Kopfbereich mit maximal 62 CSS-Pixeln und das Favicon ab.
- Die bisherigen Pixel-Vergrößerungsregeln sind für Familienbilder und Kopfsymbol entfernt, damit die geometrischen Illustrationen sauber geglättet dargestellt werden. Das frühere Hamburger-Pixelmotiv ist nicht mehr in die Oberfläche eingebunden.

Beispielbefehle für die Umwandlung:

```bash
magick image-drafts/family-1.png -strip -trim +repage -filter Lanczos -resize '480x480>' -background none -gravity center -extent 512x512 -quality 90 -define webp:alpha-quality=100 -define webp:method=6 web/public/images/families/family-1.webp
magick image-drafts/icon-2.png -strip -trim +repage -filter Lanczos -resize '224x224>' -background none -gravity center -extent 256x256 -define webp:lossless=true -define webp:method=6 web/public/images/icons/kita-pin-bold.webp
```

## Verhalten in der Oberfläche

Die Karte **Die Modellfamilie** wählt beim ersten Einblenden gleichverteilt eines der sechs Familienmotive. React hält diese Auswahl während der weiteren Bedienung fest. Formularänderungen, Kommunenauswahl und **Zurück zur Modellfamilie** wechseln das Bild nicht. Nach einem Neuladen der Website wird erneut zufällig gewählt; dabei darf dasselbe Motiv erneut erscheinen. Es gibt weder einen Bildtimer noch eine Speicherung der Wahl.

Für Kopfbereich und Favicon wird `icon-2.png` beziehungsweise `kita-pin-bold.webp` verwendet. Die kräftigere Außenlinie und die einfachere Hausform bleiben in der kleinen Darstellung deutlicher erkennbar als beim alternativen Symbol. Beide konvertierten Vorschläge bleiben im Bildordner verfügbar.

Die Illustrationen zeigen jeweils zwei Eltern und ein Kind. Der Alternativtext bleibt entsprechend allgemein; das Motiv ändert keine fachliche Haushaltskonfiguration, Modellalter oder Gebührenberechnung.

Die früheren, generierten Pixelart-Dateien und ihre Herkunft sind in [PIXELART_ASSETS.md](PIXELART_ASSETS.md) dokumentiert. Sie dienen für Familienkarte und Logo nicht mehr als aktive Bildquellen.

## Prüfung

TypeScript-Prüfung und Produktionsbuild sind erfolgreich; alle acht konvertierten Dateien sind im Build enthalten. Im lokalen Browser wurden mehrere zufällige Familienmotive nach Neuladen beobachtet. Die Auswahl blieb bei Änderung der Kinderzahl und beim Zurücksetzen erhalten. Das gewählte Familienbild sowie Kopfbereich und Favicon laden mit den vorgesehenen Auflösungen. Die geometrischen Illustrationen verwenden normale Bildglättung; die Browserkonsole zeigte keine Fehler oder Warnungen.
