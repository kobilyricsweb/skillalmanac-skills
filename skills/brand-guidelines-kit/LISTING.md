# Listing page content: brand-guidelines-kit

**One line:** Writes a usable brand guidelines document for founders and marketers, and checks the palette and type scale with a script.

## What it does

The skill gives an agent a fixed eight-section structure for a brand guidelines document and a contract for each section: a one-sentence positioning statement with named failure tests, a voice and tone table with do and don't examples and five situations, logo rules with numeric defaults and an 8-item misuse list, a colour palette defined by roles, a type scale, testable imagery rules and a template list. Facts the user did not supply are written as `[needs input]`, never invented. The agent records the palette and type scale in a `brand-tokens.json` and runs a standard-library script that checks it: invalid hex, missing roles, duplicate colours, text and background pairs under WCAG 4.5:1 (computed), and a type scale that does not grow.

## Capabilities

- `scripts/brand_tokens_check.py check <tokens.json>`: strict JSON report with errors, warnings and every contrast ratio computed
- A brand-tokens template (`assets/brand-tokens.template.json`) that passes the check
- Reference rules: contrast formula with a worked example, logo, tone and imagery checklists
- A fixed report listing what was proposed, what is open and what was not checked

## Brand book versus design system

This skill produces the human-facing brand document: positioning, voice, logo use, palette roles, type, imagery, templates. A UI component and design-token system for code (components, states, spacing in CSS, Storybook) is a different job covered by the design-system skill. The only overlap is the tokens file, which here is a small validated record of colours, type scale and spacing, not a component library.

## When to use

You say brand book, brand guidelines, style guide, brand voice, or you want a palette and fonts a freelancer or agency can follow, or you have a palette file whose text colours may fail contrast.

## When not to use

UI component libraries, design tokens for engineering, logo or name creation, trademark or legal advice, ad or landing page copy, a full accessibility audit of a site.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent computes contrast by hand from the formula in `references/brand-rules.md`.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill document run exists yet, so no saved brand document is shown. What exists is the checker on saved fixtures:

1. `python scripts/brand_tokens_check.py check evals/fixtures/bad.json` returns exit code 1 with `"ok": false`, 6 errors and 2 warnings: `duplicate_color` (#1D4ED8 used twice), `invalid_hex` (`#12GG45`), `low_contrast` ("fog on paper is 4.48:1, needs 4.5:1 for normal text"), two `type_scale_not_monotonic`, `spacing_not_ascending`, and two `spacing_off_grid` warnings.
2. `python scripts/brand_tokens_check.py check evals/fixtures/good.json` returns exit code 0 with `"ok": true` and five contrast pairs from 6.7:1 to 16.96:1.
3. `evals/fixtures/edge.json`: #767676 on white is 4.54:1 (pass); #949494 on white is 3.03:1 (pass as large text, fail as normal text).

## Limits

- Validates numbers, not taste; a palette can pass and look wrong.
- Contrast is for flat sRGB colours only: no images, gradients, transparency, dark mode or colour-blind simulation.
- Does not create logos or fonts, and does not check font licences or trademarks.
- No CMYK or Pantone conversion.
- Step ratio and spacing grid thresholds are working values, reported as warnings.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL, and 6 of 6 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a three-line brief for a small business; the agent asks one batched question and marks gaps `[needs input]`.
2. The agent writes the positioning statement and the voice table.
3. Run the checker on the palette: it reports `low_contrast` for a pale grey; the agent darkens it and re-runs to `ok: true`.
4. Show the assembled eight-section document with its open items list.

## FAQ seeds

- Does it design my logo? No. It writes rules for a logo you supply.
- How is it different from a design-system skill? That one builds UI components and code tokens; this one writes the brand document.
- Will it invent my mission or customers? No; missing facts become `[needs input]` items.
- Does it need network access? No.
- Does passing the check mean my brand is accessible? It means listed text pairs meet WCAG 2.x 4.5:1 (or 3:1 for large text); images, dark mode and other criteria are not checked.
- Can I use my own palette file? Yes; follow the JSON contract in SKILL.md.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
