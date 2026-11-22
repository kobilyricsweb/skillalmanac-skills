---
name: logo-and-mark-design
description: Designs or fixes a logo, wordmark or mark as clean SVG. Use when a founder asks to design, redo or fix a logo, mark, favicon or app icon, or says it is blurry, too detailed or breaks small. Covers a brief contract, three one-idea directions, grid construction, tests at 16, 32 and 64 px, one-colour and reversed versions, clear space, a file list, and an audit script (viewBox, nodes, strokes, colours, live text, embedded rasters, thin features). Do not use for brand books, posters, photo editing, or to certify a mark is unique or free to trademark.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer, standard library only, no network. Without Python, run the manual audit in step 6. Rendering at 16, 32 and 64 px needs any SVG rasteriser or a browser; if none exists, say so in the report.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Logo and mark design

Produce a mark that still works at 16 px, in one colour and on a dark background, as a file another tool can open without fonts or fixes. The deliverable is the mark itself. Colour systems, voice and usage books belong to the brand-guideline skill; posters and layouts belong to the poster skill.

## Workflow

```
- [ ] 1 Brief contract
- [ ] 2 Three directions (one idea each)
- [ ] 3 Pick one and construct it
- [ ] 4 Test at 16, 32, 64 px
- [ ] 5 Build mono and reversed versions
- [ ] 6 Audit every SVG
- [ ] 7 Write the usage note and deliver the file list
- [ ] 8 Trademark caution and report
```

1. **Brief contract.** Fill every field from [assets/logo-brief.md](assets/logo-brief.md). Ask only for what is missing and cannot be defaulted: exact name spelling and capitalisation, what the business does in one line, mark type (symbol, wordmark or lockup), the smallest place it must work (favicon, app icon, avatar, print), any fixed colours, and what to avoid. Anything else you assume goes into an "Assumptions" list in the report. Do not start drawing without the exact name and the smallest use.
2. **Three directions.** Draw three small sketches in SVG, each carrying exactly one idea that fits in one sentence ("the P is a pin"). Use three different idea types: letterform or monogram, a concrete symbol from the business, and an abstract geometric form. Reject any direction that needs two sentences or combines two ideas. Avoid the stock symbols in [references/construction.md](references/construction.md) section 5. Present the three with the idea sentence, why it fits the brief, and its main risk. Recommend one; do not ask the user to choose between close calls.
3. **Construct** the chosen direction on the rules below. Detail, formulas and the SVG hygiene list are in [references/construction.md](references/construction.md); read sections 1 to 3 when you start drawing.
4. **Test sizes.** Render at 16, 32 and 64 px on white and on dark, if a rasteriser exists, and look at each. Pass: at 16 px the silhouette is still recognisable, no gap or counter has closed, and the script reports legibility risk low. Medium is acceptable only with a separate simplified small-size file (strokes at least 12.5% of the box, inner detail removed, gaps at least as wide as strokes). High is a redraw.
5. **Variants.** Always make full colour, one-colour black and one-colour white. The mono files use one flat fill, no opacity, no gradient, and no white shapes: interior knockouts are real holes (`fill-rule="evenodd"` or subtracted paths) so the file works on any background. Reversed (white on a dark brand colour) needs contrast of at least 3:1 between the logo colour and the background, computed with the WCAG relative-luminance formula; state the ratio.
6. **Audit** every SVG you deliver (see Scripts), fix, and re-run until no `fail` finding is left and every `warn` is fixed or explained in the report. Do not edit the script to change a result.
7. **Usage note** and **files**: see Deliverables.
8. **Trademark caution and report**: see the rule below and the report format.

## Construction rules (defaults; state any you break)

| Rule | Value |
|---|---|
| Grid | `viewBox="0 0 64 64"` for marks, `0 0 W 64` for wordmarks and lockups; integer coordinates where possible, at most 2 decimals |
| Live area | Keep all artwork 4 units inside the box (56 x 56 on 64) |
| One stroke weight | Every stroke the same width (within 2%); 8 to 12% of the box (5 to 8 units on 64) |
| Smallest feature | At least 6.25% of the longest side (4 units on 64), so it is 1 px at 16 px; gaps between shapes at least as wide as the stroke |
| Optical size | A circle looks smaller than a square of equal width: draw the circle about 10% wider (20 against 18 on a 24 grid) and let round shapes overshoot flat edges by 1 to 3% |
| Optical weight | Horizontal strokes look heavier than vertical: make horizontals about 8% thinner in letterforms |
| Corners | One radius family (for example 0, stroke/2, stroke); do not mix |
| Colours | 1 or 2 flat colours in the master, 3 at most; no gradients, shadows, blur or transparency |
| Complexity | Up to 80 nodes is simple; above 200 nodes or 25 paths is complex; above 1,000 nodes looks auto-traced |
| Text | No `<text>`. Letters are paths. Draw custom letterforms from primitives, or use a licensed typeface only after the user's editor has converted it to outlines; never embed or link a font |
| Pure vector | No `<image>`, no `<script>`, no filters, no `<style>` block, no `<use>` |

## Deliverables

For brand `acme`, deliver at minimum: `acme-mark-color.svg`, `acme-mark-black.svg`, `acme-mark-white.svg`, `acme-favicon.svg` (the small-size file, or the mark if low risk), `acme-app-icon.svg` (full-bleed square, no pre-rounded corners, artwork inside the central 60%), and for wordmark or lockup also `acme-wordmark-*.svg` or `acme-lockup-horizontal-*.svg` and `acme-lockup-stacked-*.svg`. Add `acme-logo-usage.md` with: hex values, clear space, minimum sizes, and the rules for do and do not. Rasters (PNG at 16, 32, 180, 192, 512) are produced only if a rasteriser exists; otherwise list them as not produced.

Usage note defaults: clear space X = 25% of the artwork height on all sides, never less than 4 px; minimum size for the mark 16 px digital and 8 mm print, for a wordmark 80 px wide digital and 20 mm print, and a tagline is dropped below 160 px wide. These are house defaults, not standards; the owner may change them.

## Trademark caution (always)

- Never write that the mark is unique, original, does not resemble anything, is available, is safe, or will not infringe. You cannot know this.
- If asked for "like X but different", do not copy or trace the distinctive shape of a named mark. Name the quality wanted (speed, calm, trust), and draw a new idea.
- End every delivery with: a recommendation to run a knockout search of the brand name and the mark in the intended countries and classes (national trademark databases, EUIPO TMview, WIPO Global Brand Database, see [references/sources.md](references/sources.md)) and to ask a trademark attorney before filing or large print runs. Say that artwork made with an AI tool may have limited copyright protection in some countries, and to confirm ownership with a lawyer.

## Scripts

`scripts/logo_audit.py [--kind mark|wordmark|lockup] file.svg`: run it, do not edit it. Prints one strict JSON object. `--kind mark` (default) expects a near-square box and measures features against the longest side; `wordmark` and `lockup` measure against the height.

Keys: `verdict` (`pass`, `review`, `fail`), `viewbox`, `elements`, `complexity` (`nodes`, `paths`, `class`), `strokes` (`distinct_widths`, `consistent`), `colours` (`distinct`, `values`, `gradients_defined`, `opacity_used`), `text`, `raster`, `legibility` (`smallest_feature_units`, `feature_px` at 16, 32, 64, `risk` low, medium, high or unknown), `findings` (each with `severity` fail, warn or info, a `code` and a `message`). Exit 0 for pass or review, 1 for fail, 2 for unreadable input (JSON with an `error` key).

Manual fallback without Python: open the file as text and check that the root has a `viewBox`; search for `<text`, `<image`, `<script`, `filter`, `gradient`, `opacity`; list the distinct `stroke-width` and colour values; count path commands; and judge the thinnest feature as a fraction of the box against the 6.25% rule.

## Report format

```
Files: <list with sizes in bytes>
Direction: <chosen idea sentence> (others: <one line each>)
Audit: <verdict per file, nodes, colours, risk at 16 px>
Render test: <done at 16/32/64 on white and dark, or not done and why>
Reversed contrast: <ratio and colours>
Assumptions: <from the brief>
Trademark note: <the search and attorney recommendation>
Not checked: <e.g. gaps between shapes, real-device rendering, font licence>
```

## Limits

- The script measures geometry from attributes and inline style. It does not render, does not read CSS rules, does not follow `<use>`, and ignores rotation and skew. Gaps between shapes and hairline sliver shapes are not measured.
- Feature size uses subpath bounding boxes, curves use control points, so thin curved slivers can be over-estimated.
- The thresholds (1 px at 16 px, 3 colours, 200 nodes, 2% stroke tolerance, 3:1 contrast) are working values, not measured optima.
- The 10%, 8% and 1 to 3% optical corrections are starting points; judge the result by eye at size.
- The skill does not judge taste, check name availability or give legal advice.
