## Contents

- Screen export sizes
- Print sizes and bleed
- Safe areas on stories and covers
- Choosing the canvas
- Sources

# Formats, export sizes and print rules

All sizes are pixels unless stated. Short side matters most: the audit scales its thresholds from it.

## Screen export sizes

| Use | viewBox | Ratio | Notes |
|---|---|---|---|
| Instagram or Facebook feed, portrait | 1080 x 1350 | 4:5 | Default for event posts; most screen area in a feed |
| Square post | 1080 x 1080 | 1:1 | Safe on every grid and carousel |
| Story, Reel cover, vertical video poster | 1080 x 1920 | 9:16 | Keep top and bottom 14% (about 270) free of text and the CTA; interface sits there |
| Link preview, LinkedIn or Facebook share image | 1200 x 630 | about 1.91:1 | Keep text inside the central 80%; some feeds crop to 1:1 |
| X (Twitter) post image | 1600 x 900 | 16:9 | Wide crops are applied in the timeline; keep the headline left-centre |
| Pinterest pin | 1000 x 1500 | 2:3 | Headline in the top half, because the lower part is cut in grids |
| YouTube thumbnail | 1280 x 720 | 16:9 | Text must stay readable at about 200 px wide; use 3 words or fewer |
| Email header | 1200 x 400 | 3:1 | Export at 2x for retina, display at 600 wide |

Export at the exact pixel size, or 2x for retina. Name files `<topic>-<WxH>.png`. SVG is the master; PNG is what most platforms accept.

## Print sizes and bleed

| Format | Trim size | With 3 mm bleed (viewBox in mm) |
|---|---|---|
| A5 flyer | 148 x 210 mm | 154 x 216 |
| A4 flyer | 210 x 297 mm | 216 x 303 |
| A3 poster | 297 x 420 mm | 303 x 426 |
| A2 poster | 420 x 594 mm | 426 x 600 |
| US Letter | 8.5 x 11 in (215.9 x 279.4 mm) | 221.9 x 285.4 |
| US Tabloid | 11 x 17 in (279.4 x 431.8 mm) | 285.4 x 437.8 |
| Poster 24 x 36 in | 609.6 x 914.4 mm | 615.6 x 920.4 |

Rules:

1. Bleed: 3 mm on each side is the common printer default (some ask 5 mm; ask the printer). Background colour and any image that touches an edge must run to the bleed edge, so the background rect covers the whole viewBox.
2. Safe margin: keep all text and logos at least 5 mm inside trim, so 8 mm from the file edge when bleed is 3 mm. Run `--bleed 3 --safe 5`.
3. Colour: SVG is RGB. Tell the user a printer will convert to CMYK and saturated blues, greens and oranges will look duller; ask for the printer's profile when colour matters.
4. Resolution: raster images inside the poster need 300 pixels per inch at final size (A3 at 300 ppi is about 3508 x 4961). Vector shapes and text need nothing.
5. Text: tell the user to convert text to outlines (or embed fonts) for the print file, and keep the live-text SVG as the master.
6. Small print: nothing under 6 pt at print size; body facts at 9 to 12 pt for A4 and 14 to 18 pt for A3.

## Safe areas on stories and covers

| Surface | Keep clear |
|---|---|
| 1080 x 1920 story | top 14% and bottom 14% |
| 1080 x 1350 feed post | outer 5% (54); feed crops this format to 1:1 in grids, so the headline must also fit the central 1080 x 1080 |
| 1200 x 630 share image | outer 10% horizontally |
| Circular avatar crop | inscribed circle only |

## Choosing the canvas

- One event, many places: make a 1080 x 1350 master, then derive 1080 x 1920 by moving the CTA, not by scaling.
- Printed and shared: build the print file first (larger, with bleed), then crop for screen.
- If the user does not say where it will appear, ask once; if there is no answer, use 1080 x 1350.

## Sources

- WCAG 2.2, success criterion 1.4.3 contrast minimum, and the relative luminance definition: https://www.w3.org/TR/WCAG22/#contrast-minimum
- SVG 1.1 specification, viewBox and coordinate systems: https://www.w3.org/TR/SVG11/coords.html
- Platform image sizes change often; take the current figure from the platform's own help centre before a paid campaign. Values above are working defaults written from general practice, not copied from any one page.
