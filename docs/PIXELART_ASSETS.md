# Pixelart für den Familienatlas

**Aktualisierung:** Die Familienkarte verwendet inzwischen die sechs vom Nutzer bereitgestellten Familienillustrationen mit Zufallsauswahl beim Seitenladen; Kopfbereich und Favicon verwenden dessen kräftigeres Kita-Pin-Symbol. Der Hamburger wurde aus dem Methodikbereich entfernt. Aktive Dateien und Konvertierung stehen in [BILDASSETS.md](BILDASSETS.md). Die folgende Beschreibung bewahrt ausschließlich die Herkunft der früher generierten Motive; sie sind nicht mehr in die aktive Oberfläche eingebunden.

Die drei Motive wurden mit dem integrierten Werkzeug `image_gen` neu erzeugt, jeweils mit transparentem Hintergrund. Die ausgewählten PNG-Ergebnisse wurden geprüft, für die Website verkleinert und als WebP mit Alphakanal lokal gespeichert. Die WebP-Kompression ist verlustfrei; für die Verkleinerung wurde ein nächster-Nachbar-Filter verwendet. Die Anwendung benötigt zum Anzeigen weder den Bildgenerator noch einen externen Bilddienst.

## Dateien und Verwendung

| Motiv | Lokale Datei | Verwendung |
|---|---|---|
| Familie mit Schlummerotter | [`web/public/images/model-family.webp`](../web/public/images/model-family.webp) | Illustration der auswählbaren Modellfamilie |
| Kita, Karte und Münze | [`web/public/images/kita-map-logo.webp`](../web/public/images/kita-map-logo.webp) | Logo im Kopfbereich sowie Browser-Favicon |
| Hamburger | [`web/public/images/pixel-burger.webp`](../web/public/images/pixel-burger.webp) | Hinweis auf Essen und Zusatzkosten in der Methodik |

Die Dateien bleiben als früherer Entwurfsstand erhalten. Sie werden nicht mehr im sichtbaren Seiteninhalt verwendet. Die Altersdarstellung der gezeichneten Figur verändert keine fachlichen Modellalter oder Tarifdaten.

## Verwendete Generierungs-Prompts

Die Original-Prompts sind für eine spätere Reproduktion in ihrer englischen Eingabesprache erhalten.

### Familie

```text
Use case: illustration-story. Asset type: transparent pixel-art family illustration for an illustrated family card on a German childcare fee comparison website. Create exactly three full-body characters standing close together and facing the viewer: dad, mum, and their child in front between them. Dad wears a dad cap, has a beard and brown hair, and a lumberjack plaid shirt. Mum wears mum jeans, has blonde shoulder-length hair, a visible necklace, and a striped shirt. The child is approximately four years old with medium-length hair and holds a sleeping otter plush toy with both hands in front of their belly; make the cuddly otter recognizable with its little face, paws and pale belly. Style: charming polished gaming pixel art, chunky clean square pixels, limited cohesive palette, crisp stepped edges, subtle pixel shading, warm and friendly character expressions. Wide compact group composition, all three people and the otter fully visible, generous transparent margin, suitable for legibility at about 280px wide. Genuine transparent background. No scenery, ground, frame, lettering, logos, watermark or extra characters. Preserve the specific clothing and family details.
```

### Logo

```text
Use case: logo-brand. Asset type: tiny transparent pixel-art website logo, icon only, for a childcare fee map called Kita-Kosten. Create one charming original 16-bit gaming-style pixel icon combining a small cozy nursery building with a pitched lilac roof and warm white walls, a blue folded map peeking behind it, and one tiny golden coin at its corner. Clear crisp square pixels and stepped silhouettes, chunky dark anthracite outlines, restrained lilac, pastel blue, warm orange and cream palette. Legible at 48px square. Centered single isolated icon, generous transparent margin. Genuine transparent background. No text, letters, numbers, currency symbols, watermark, frame or scenery.
```

### Hamburger

```text
Use case: stylized-concept. Asset type: small transparent pixel-art hamburger icon for a childcare website's food-cost explanation. One appetizing cute 16-bit videogame hamburger with sesame bun, green lettuce, tomato and cheese, crisp chunky square pixels and stepped silhouette, anthracite outline, subtle limited pixel shading, friendly warm orange and cream palette. Readable at 40px square. Centered isolated single burger, generous transparent margin. Genuine transparent background. No plate, face, arms, scenery, frame, text or watermark.
```

## Lokal mitgelieferte Schrift

Die Überschriftenschrift Bricolage Grotesque wird als lateinische variable WOFF2-Datei unter `web/public/fonts/bricolage-grotesque-latin.woff2` mitgeliefert. Quelle ist die offizielle [Google-Fonts-Schriftdefinition](https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&display=swap). Die [OFL-Lizenz](../web/public/fonts/OFL.txt) stammt aus dem [offiziellen Google-Fonts-Repository](https://github.com/google/fonts/tree/main/ofl/bricolagegrotesque) und wird außerdem in `THIRD_PARTY_NOTICES.txt` übernommen. Die Oberfläche lädt die Schrift ausschließlich von ihrem eigenen Ursprung.
