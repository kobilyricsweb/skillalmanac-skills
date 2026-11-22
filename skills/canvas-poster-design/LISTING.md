# Listing page content: canvas-poster-design

**One line:** Designs a poster, flyer or social graphic as one SVG with fixed layout and type rules, then audits it with a script.

## What it does

The skill gives an agent a seven-step procedure: a four-line brief (one headline, one supporting line, facts, one call to action), canvas and margin choice, a three-size type scale (120, 48, 28 on a 1080 px short side), a column grid with a fixed vertical order, an SVG skeleton, an audit loop and a fixed report. A reference table lists screen export sizes, print sizes with 3 mm bleed in millimetres, and safe areas for stories and covers. An audit script reads the SVG and prints strict JSON: viewBox and aspect, text count and sizes against the scale, WCAG contrast of each text colour against the rect behind it, text and shapes outside the safe area, bleed coverage, and a missing title.

## Capabilities

- `scripts/svg_poster_audit.py FILE.svg [--safe N] [--bleed N] [--min-text-pct P]`: JSON report with `verdict`, `findings` (fail or warn), `contrast`, `text`, `canvas`, `limits`; exit 0, 1 or 2
- `references/formats.md`: export size table, A-series and US print sizes with bleed, safe-area rules

## When to use

You ask for a poster, flyer, event graphic, Instagram or LinkedIn image, story, banner or cover as SVG, or you say a design looks amateur, cluttered or hard to read, or you want an existing SVG checked for contrast and margins.

## When not to use

Web or app UI layouts (see the skill `designing-web-interfaces`), logos and icon sets, photo editing, multi-page documents, illustrations with no text. Difference from `designing-web-interfaces`: that skill covers interactive interfaces; this one covers a single static graphic with a fixed canvas, print bleed and export sizes.

## Requirements

Python 3.9 or newer for the audit script (standard library only). No network. Without Python the agent follows the manual checks in step 6.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill run exists yet, so there is no saved poster to show. What exists is the audit on the saved fixtures:

1. `python scripts/svg_poster_audit.py evals/fixtures/good_event.svg`: exit 0, verdict pass, sizes 120, 48, 28, contrast 18.88, 18.88, 12.24 and 13.19 to 1.
2. `python scripts/svg_poster_audit.py evals/fixtures/bad_flyer.svg`: exit 1, 3 fails and 4 warns. Fails: missing title, contrast 4.48:1 for the 20 px grey text, "SALE SALE" estimated box starting at x 20 inside a 54 unit margin. Warns: six sizes, sizes 60 and 56 too close, two headlines at 96, a badge crossing the safe area.
3. `python scripts/svg_poster_audit.py evals/fixtures/bleed_bad.svg --bleed 3 --safe 5`: exit 1, `bleed-background` (background rect stops 1 mm short of the edge).

## FAQ seeds

- Does it render the poster? No. Text widths are estimated; open the SVG in a browser for a final look.
- Will it work for CMYK print? It checks bleed and margins only; SVG is RGB and the skill tells the user to ask the printer about conversion.
- Can it check gradients or photo backgrounds? No; those come back unresolved and need a manual check.
- Are the numbers (5% margin, 1.8% minimum size) standards? No. Only the WCAG 4.5:1 and 3:1 thresholds are external; the rest are working defaults.
- Does it need network access? No.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
