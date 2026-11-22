---
name: canvas-poster-design
description: Designs a poster, flyer, event graphic or social post image as one SVG file, with a margin grid, three-size type scale, one headline, one call to action, contrast limits and print bleed, then audits it with a script reporting text sizes, WCAG contrast, safe-area overruns and a missing title as JSON. Use when the user asks for a poster, flyer, Instagram or LinkedIn graphic, story, banner or cover as SVG, or says a design looks amateur or cluttered. Do not use for web or app UI layouts, logos or icon sets, photo editing, multi-page documents, or illustrations with no text.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer, standard library only, no network. Without Python, run the manual checks in step 6. Converting SVG to PNG or PDF needs a tool the user already has (browser, Inkscape); this skill does not install one.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Canvas poster design

Produce one SVG that a stranger reads in three seconds: what it is, when and where, what to do next. Everything below is a decision already made, so do not reopen it unless the user's brief forces it.

## Workflow

```
- [ ] 1 Fix the brief in four lines
- [ ] 2 Pick canvas and margins
- [ ] 3 Pick the type scale and colours
- [ ] 4 Lay out on the grid
- [ ] 5 Write the SVG
- [ ] 6 Audit, fix, re-audit
- [ ] 7 Report
```

1. **Brief, four lines**: headline (at most 6 words), one supporting line, the facts (date, time, place), one call to action (CTA). If the user gave two goals, ask which one is the CTA; the other becomes a facts line. Never write more than 40 words in total on a poster; move the rest to a note for the user.
2. **Canvas and margins.** Choose the size from [references/formats.md](references/formats.md) (export sizes, bleed, platform crops). Safe margin is 5% of the short side for screen; for print, 3 mm bleed beyond trim plus a 5 mm safe margin inside trim. Set `viewBox` to the full canvas including bleed, never rely on width and height alone.
3. **Type scale and colour.**
   - Exactly three sizes, ratio about 2.5 between headline and supporting line and about 1.7 between supporting line and facts. On a 1080 px short side: 120, 48, 28. Scale in proportion for other canvases (headline about 11% of the short side).
   - One typeface family; weight carries emphasis (700 for the headline and CTA, 400 elsewhere). Use system stacks (`Arial, Helvetica, sans-serif`) unless the user supplies a font, because SVG viewed elsewhere will not load fonts it does not have; for print, ask whether to convert text to outlines at the end.
   - Two colours plus a neutral: background, text, one accent used only for the CTA. Text contrast: 4.5:1 for text under 24 px (and under 18.66 px when bold), 3:1 for 24 px and larger (18.66 px and larger when bold). Never place text on a photo or gradient without a solid or 60%-opacity scrim rect; the script cannot measure those.
4. **Grid.** Divide the safe area into 12 columns and place everything on the left edge of one column (left-aligned beats centred for anything over two lines). Vertical order, top to bottom: headline in the top 40%, supporting line directly below at one headline-height gap, facts in the lower third, CTA last and lowest, in an accent-coloured rect with text at 28 or larger. White space target: at least 35% of the canvas empty. One headline: no second element within 70% of its size.
5. **Write the SVG** with this skeleton, in document order (background first, because the audit reads the rect that is behind each text):

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1350" width="1080" height="1350">
  <title>Specific name of the poster, with date</title>
  <rect id="bg" x="0" y="0" width="1080" height="1350" fill="#111111"/>
  <text x="90" y="420" font-size="120" font-weight="700" fill="#FFFFFF">HEADLINE</text>
  ... supporting line 48, facts 28, then the CTA rect and its text
</svg>
```

   Use plain `fill` and `font-size` attributes, not CSS classes or `<style>` blocks (the audit does not resolve them). Keep text as `<text>`, not paths, until the final print export. Estimate widths before placing: a line of N characters is about `0.55 x size x N` wide (0.6 when bold); if it overruns the safe area, shorten the words before you shrink the size.
6. **Audit.** Run, then fix every `fail`, then read each `warn`:

```bash
python scripts/svg_poster_audit.py poster.svg
python scripts/svg_poster_audit.py poster_print.svg --bleed 3 --safe 5
```

   Fix order: `viewbox-missing`, `title-missing`, `contrast`, `text-too-small`, `outside-safe-area`, `bleed-background`, then warnings. Re-run until `verdict` is `pass`. Run the script; do not edit it to make a check pass. Without Python, check by hand: viewBox present, `<title>` present, three sizes, contrast of each colour pair with a contrast calculator, every line inside the margin.
7. **Report** in this shape: file path; canvas and export size; audit verdict with counts; any `warn` you kept and why; what was not checked (see Limits); the export sizes the user needs.

## Audit output contract

The script prints one JSON object. Exit 0 = no fail, 1 = at least one fail, 2 = unreadable or non-SVG file (then only `tool` and `error`).

| Key | Content |
|---|---|
| `canvas` | `viewBox`, `short_side`, `aspect`, `bleed`, `safe_margin`, `safe_inset_from_edge` |
| `title` | text of the direct-child `<title>` or null |
| `text` | `count`, `sizes_distinct` (largest first), `min_allowed`, per-element sizes |
| `contrast` | per text: `ratio`, `required` (3.0 or 4.5), `status` pass, fail or unresolved |
| `outside_safe_area` | text and shapes crossing the safe inset |
| `findings` | list of `{severity: fail or warn, check, message, element}` |
| `summary`, `verdict` | counts and `pass` or `fail` |
| `limits` | what the run could not measure |

Options: `--safe N` margin in viewBox units (default 5% of short side), `--bleed N` bleed in viewBox units (also requires a background rect that reaches every viewBox edge), `--min-text-pct P` smallest text as a percentage of the short side (default 1.8).

Check names and thresholds: `text-too-small` (below 1.8% of short side, 19.4 on 1080), `too-many-sizes` (more than 4), `sizes-too-close` (ratio under 1.25), `headline-not-unique`, `weak-hierarchy` (largest under 2.5 times smallest), `text-count-high` (over 10), `contrast`, `outside-safe-area`, `shape-outside-safe-area` (warn only: a deliberate full-bleed panel is allowed), `bleed-background`, `title-missing`, `viewbox-missing`.

## Boundaries

- Do not invent event facts, prices, URLs or QR targets; leave a visible placeholder in the text and list it in the report.
- Do not copy a brand's logo or a living person's likeness; use a labelled empty rect for the user to fill.
- Fonts, photos and logos the user supplies are used as given; check licences are theirs to settle.

## Limits

- Text widths are estimated, not rendered, so safe-area results on text are approximate (about plus or minus 15%). Open the SVG in a browser for a final look; the script cannot see overlap between text lines, kerning or the real fallback font.
- Contrast uses solid hex, `rgb()` and seven named colours against the nearest earlier rect. Gradients, images and opacity come back `unresolved`. Text or a background rect styled through a CSS class (when a `<style>` sheet exists) gets contrast status `unknown` and a `css-class-unresolved` warning; the script never reports a pass for it, so check it by hand or switch to plain `fill`. A `fill` set on a parent `<g>` attribute is inherited correctly.
- Only `translate` transforms are followed. `scale`, `rotate`, `matrix` and `skew` are ignored in the output (positions, sizes and safe-area boxes of transformed elements may be wrong) and the run lists this under `limits`. Paths, images and outlined text are not measured.
- The numeric defaults (5% margin, 1.8% minimum size, 2.5 headline ratio, 4 sizes) are working values from design practice, not standards; WCAG 4.5:1 and 3:1 are the only external thresholds.
- Platform sizes and crops change; confirm against the platform before a paid campaign.
