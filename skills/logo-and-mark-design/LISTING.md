# Listing page content: logo-and-mark-design

**One line:** Designs a logo or mark as clean SVG for founders, and audits it for small sizes, print and one-colour use.

## What it does

The skill gives an agent a fixed procedure: fill a brief contract, draw three directions that each carry one idea, construct the chosen one on a 64-unit grid with numeric rules for strokes, smallest features and optical corrections, test it at 16, 32 and 64 px, then build black, white and reversed versions. A script reads each SVG and prints strict JSON: viewBox and aspect ratio, path and node counts, stroke-width consistency, distinct colours, gradients and opacity, live text, embedded raster images, and an estimate of legibility at 16, 32 and 64 px from the smallest feature size. A trademark rule forbids similarity or uniqueness claims and requires a search and attorney recommendation.

## Capabilities

- Brief template with defaults for every missing field
- Three-direction sheet (letterform, concrete symbol, abstract geometry), one-sentence idea each
- Construction rules: grid, live area, keyline sizes, optical corrections, one stroke weight, 6.25% smallest-feature rule
- Mono, knockout and reversed-contrast rules with the WCAG contrast formula
- File list and usage-note defaults (clear space, minimum sizes)
- `scripts/logo_audit.py`: JSON audit with verdict pass, review or fail

## When to use

You ask for a logo, wordmark, symbol, favicon or app icon as SVG, or your existing logo is blurry small, too detailed, full of live text, or rejected by a printer.

## When not to use

Full brand books (use the brand-guidelines skill), posters and layouts (the poster skill), photo editing, raster-to-vector tracing, or any request to confirm that a mark is unique, available or safe to trademark. It differs from the neighbouring skills: this one produces and checks the mark file itself.

## Requirements

Python 3.9 or newer, standard library only, no network, for the audit script. Without Python the agent follows the manual audit in `SKILL.md`. Rendering at 16, 32 and 64 px needs any SVG rasteriser or a browser.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill design run exists yet, so no saved designed logo is shown. What exists is the audit on saved fixtures (outputs from `python evals/run_fixtures.py`, 10 of 10 cases pass):

1. `python scripts/logo_audit.py evals/fixtures/thin_strokes.svg` (three paths with stroke widths 1, 3 and 6 on a 100-unit box): verdict `review`, exit 0; findings `stroke_widths_inconsistent`, `strokes_not_outlined`, `legibility_high`; smallest feature 1.0 unit, 0.16 px at 16 px, 0.32 px at 32 px, 0.64 px at 64 px.
2. `python scripts/logo_audit.py evals/fixtures/bad_text_raster.svg`: verdict `fail`, exit 1; findings `aspect_not_square`, `gradient_used`, `opacity_used`, `text_not_outlined` (fonts Arial, Helvetica) and `raster_embedded` (1 data URI image).
3. `python scripts/logo_audit.py --kind wordmark evals/fixtures/wordmark_outlined.svg`: verdict `pass`, exit 0; 3 paths, 18 nodes, 1 colour, smallest feature 10 units of a 60-unit height, 2.67 px at 16 px.

## Limits

- The audit is geometric: it does not render, does not read CSS rules or `<use>`, and does not measure gaps between shapes.
- Thresholds (1 px at 16 px, 3 colours, 200 nodes, 3:1 contrast) are working values, not measured optima.
- Optical corrections are starting points to judge by eye.
- No taste judgement, no name-availability check, no legal advice.

## Evidence

See `VERIFICATION.md`. In short: static lint and the 10 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review, rendering of any designed logo.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Prompt: a founder names the product and the smallest place the logo must work.
2. The agent fills the brief, shows three one-sentence directions and recommends one.
3. The agent saves colour, black and white SVGs and runs the audit: `review` with a thin-feature warning.
4. The agent thickens the stroke and re-runs: `pass`, risk low at 16 px; the report ends with the trademark search note.

## FAQ seeds

- Does it need network access? No.
- Can it make a logo from my name alone? It asks for the exact name, the business line and the smallest use, and defaults the rest, listing its assumptions.
- Will it tell me the logo is safe to trademark? No. It never claims uniqueness and recommends a knockout search and an attorney.
- Can it fix a logo I already have? Yes: the audit lists what is wrong (live text, raster, gradients, mixed strokes) and the agent repairs it.
- Does it make PNG files? Only if an SVG rasteriser exists; otherwise it lists them as not produced.
- How is it different from the brand-guidelines skill? That one writes the brand book; this one makes and checks the mark.
- Can it use my brand font? Only after your editor converts the letters to outlines and the font licence allows logo use.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet; the accountable editor is Global Media Holdings.
