## Contents

1. Grid, live area and keyline sizes
2. Optical corrections
3. Strokes, gaps and the small-size variant
4. SVG hygiene and file skeleton
5. Idea types and stock symbols to avoid
6. Mono, knockouts and reversed contrast
7. Wordmark and lockup notes

## 1. Grid, live area and keyline sizes

Work on a 64-unit grid for marks. Everything that must look centred is centred on the box centre (32, 32), then adjusted by eye (section 2).

Keyline sizes: shapes of different geometry need different measured sizes to look equally big. On a 64 grid with a 4-unit live margin (56 x 56 live area), use these starting sizes and adjust by eye:

| Shape | Size on the 64 grid | Why |
|---|---|---|
| Square | 48 x 48 | The reference |
| Circle | 53 diameter | Round shapes look smaller; about 10% wider matches the square |
| Portrait rectangle | 40 x 50 | Keeps equal visual area with the square |
| Landscape rectangle | 50 x 40 | Same |
| Equilateral triangle | 54 wide, 47 high, centred on its centroid (one third up from the base), not its bounding box | A triangle centred by bounding box looks low |
| Tall thin form (a pin, a flame) | Full 56 height allowed | Thin forms carry less area |

If the mark will be placed in a circular avatar mask, keep the artwork inside a circle of 52 units diameter around the centre; corners of the box are cut off. For an app icon, keep the main artwork inside the central 60% (about 38 units on 64) because platforms apply their own masks.

Size relationships inside one mark use a small set of ratios (for example 1, 1/2 and 1/4 of the stroke weight or the box). More than three distinct sizes of repeated elements reads as accidental.

## 2. Optical corrections

Mathematically exact usually looks wrong. Apply, then compare at 64 px by eye.

| Situation | Correction |
|---|---|
| Round shape next to flat shape of the same nominal height | Round shape overshoots top and bottom by 1 to 3% of its height |
| Circle against a square of equal width | Circle about 10% wider |
| Horizontal stroke against vertical stroke | Horizontal about 8% thinner |
| Where two strokes meet at an acute angle | The join gets dark and heavy; thin each stroke by 5 to 10% near the join, or cut a small notch |
| Pointed shapes (triangle tip, arrow) | Tip overshoots the boundary by 3 to 5% so it does not look cut short |
| Shape inside a container (a letter in a circle) | Centre on the optical centre: shift 1 to 2% toward the heavier side's opposite, and test with the grid hidden |
| Play-button style triangle in a circle | Shift the triangle right by about one eighth of its width |
| Visual symmetry with unequal parts | Move the lighter side slightly outward, never resize the parts |

Do not apply an optical correction to a shape that is repeated or tiled; repetition shows the inconsistency.

## 3. Strokes, gaps and the small-size variant

Numbers below assume the longest side of the mark is the reference L, rendered at S pixels.

- Pixel size of a feature: feature_units / L * S.
- A feature under 1 px blurs into a grey smear. At S = 16 that means a feature must be at least L/16 = 6.25% of L.
- Comfortable strokes are 1.5 to 2 px at 16 px: 9.4% to 12.5% of L. On a 64 grid that is 6 to 8 units.
- Gaps (the space between two shapes, the opening of a counter) follow the same limit and should be at least as wide as the stroke; gaps close first when a mark is shrunk, and the script cannot measure them, so check them by eye at 16 px.
- Use one line cap and one line join style throughout (round or butt, round or miter). Miter joins at angles under 30 degrees spike; use bevel or round there.

Small-size variant recipe (for a favicon when the audit risk is medium or high):

1. Keep only the silhouette and the single strongest inner feature.
2. Set strokes to 12.5% of the box (8 units on 64).
3. Make every gap at least equal to the stroke.
4. Remove all elements below 6.25% of the box.
5. Re-run the audit on the variant, and test at 16 px.

## 4. SVG hygiene and file skeleton

Skeleton for a colour mark:

```
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <title>Acme mark</title>
  <path fill="#1a56db" d="..."/>
</svg>
```

Checklist for each file:

- `viewBox` present; no fixed `width` and `height` unless they match the viewBox ratio (a fixed size stops it scaling in some embeds).
- `<title>` present; no editor metadata, comments with file paths, or generator namespaces left over.
- No `<text>`, `<image>`, `<script>`, `<foreignObject>`, filters, masks that only hide stray geometry, or `<style>` rules. Use presentation attributes.
- No transforms if you can bake them into the coordinates; a scale on a group changes the stroke width.
- Strokes expanded to outlines in the final export. Live strokes are fine while drawing.
- Colours as 6-digit hex. One hex per role; list them in the usage note.
- Unique ids if any exist; remove unused `defs`.
- Coordinates rounded to 2 decimals at most; an exact number of nodes where an arc or circle primitive would do (a circle is 4 nodes, a hand-traced one is often 20).
- File size: a simple mark is under 2 KB, a wordmark under 10 KB. Above 30 KB check for auto-trace.

## 5. Idea types and stock symbols to avoid

Three idea types, pick one of each for the three directions:

| Type | One-sentence form | Example sentence |
|---|---|---|
| Letterform or monogram | "The initial becomes X" | "The P is a map pin" |
| Concrete symbol | "A single object from the business, simplified" | "A key whose bow is a house" |
| Abstract geometry | "Two or three primitives with a rule" | "Two quarter circles meeting at a point, for a meeting-scheduling tool" |

A direction fails the one-idea test if its sentence contains "and" joining two different objects, or if the symbol would still make sense with a different name.

Stock symbols to avoid because they are interchangeable and often already registered in some class: globe with orbit rings, lightbulb, handshake, generic swoosh, rising arrow bars for finance, interlocking people figures, a leaf for anything green, a shield with a checkmark, an infinity loop, a hexagon cluster for technology. Use one only if the brief demands it and say that you did.

## 6. Mono, knockouts and reversed contrast

- A one-colour file has one fill value for all shapes (`#000000` for the black file, `#ffffff` for the white file). No opacity, no tints; tints are a different colour.
- A shape that was white inside a coloured shape in the colour file becomes a hole in the mono file. In SVG: put both outlines in one `<path>` and set `fill-rule="evenodd"`, or subtract the shape in the editor and export the result. A white-filled shape on top is wrong because it paints white on a coloured background.
- Reversed means light logo on dark ground. Compute contrast with the WCAG formula: linearise each sRGB channel (c/255 divided by 12.92 when at most 0.03928, else ((c/255 + 0.055)/1.055) to the power 2.4), luminance L = 0.2126 R + 0.7152 G + 0.0722 B, ratio = (lighter + 0.05)/(darker + 0.05). Require at least 3:1 for the logo against its background. State the two colours and the ratio.
- Test the colour logo on white, on near-black (`#111111`), and on a mid-tone photo-like grey (`#808080`). If it fails on one, say where the colour version may not be used and provide the white or black file for it.

## 7. Wordmark and lockup notes

- Spacing: set the gaps between letters by area, not by distance. Pairs like "AV" and "LT" need tighter spacing; pairs of straight stems ("ll", "nn") need wider.
- A wordmark in a ready-made typeface is lettering, not a custom drawing; it must be converted to outlines by the user's tool, and the typeface licence must allow logo use. If you cannot confirm the licence, say so in "Not checked".
- Lockup relation: mark height about 1.5 to 2 times the cap height of the wordmark for a horizontal lockup; the gap between mark and word equals the width of the wordmark's letter "n" or half the cap height, one value for the whole lockup.
- Stacked lockup: centre the wordmark under the mark on its optical centre; the mark is at most 60% of the wordmark width.
- A tagline is a separate small line, not part of the logo; it is dropped below the size given in the usage note.
