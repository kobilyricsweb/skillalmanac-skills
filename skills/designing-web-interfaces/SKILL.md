---
name: designing-web-interfaces
description: Designs and restyles web interfaces from concrete, checkable rules (type scale, 4px spacing, contrast ratios, hierarchy, hover/focus/disabled states, empty, error and loading states, breakpoints, machine-made tells) and audits an HTML file, CSS file or design-tokens JSON with a script that prints strict JSON. Use when the user asks to design, redesign, restyle, polish or fix a UI that looks generic, AI-generated, template-like, cluttered or inconsistent, or wants design tokens. Do not use for turning a Figma file or screenshot into code, React performance, full accessibility audits, branding or logos, or UX research.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checklists in steps 2 and 6 by hand.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
  license: Apache-2.0
  author_model: claude-sonnet-5-5
---

# Designing web interfaces

Generic results come from skipping decisions: no scale, no spacing unit, default gradients, no states. Make the decisions first as tokens, build from the tokens only, then audit the file.

## Workflow

Copy this checklist:

```
- [ ] 1 Collect the brief and constraints
- [ ] 2 Write tokens.json and audit it
- [ ] 3 Lay out hierarchy before styling
- [ ] 4 Build from tokens only
- [ ] 5 Cover every state
- [ ] 6 Audit the file, fix, re-audit
- [ ] 7 Report
```

1. **Brief.** Find out, or read from the repo: who uses the screen, the one thing each screen is for, the existing stack and any existing tokens or CSS (extend them, never replace silently), one brand colour if any, and one product the user likes. If a design system exists, its tokens win over the defaults below.
2. **Tokens first.** Write `tokens.json` (format in [references/tokens-schema.md](references/tokens-schema.md)) starting from the defaults below, change only with a reason, then run `python scripts/ui_audit.py tokens.json`. Fix every FAIL and justify every WARN left.
3. **Hierarchy.** For each screen name one primary action and one primary piece of content. Allow three emphasis levels (primary, secondary, quiet). Order by importance, group by proximity (smaller gaps inside a group than between groups), and use size and weight before colour to rank.
4. **Build from tokens only.** Every font size, space, radius and colour in CSS comes from a variable defined from the tokens. Mobile-first: base styles for 360px, then `min-width` breakpoints. If the product has a dark mode, define its colour overrides together with the light values.
5. **States.** Use the matrix below; read the matching section of [references/rules.md](references/rules.md) when writing the copy and markup for a state.
6. **Audit.** Run `python scripts/ui_audit.py <file>`. Fix FAIL first, then WARN, then re-run until the verdict is `pass`, or `review` with each remaining WARN explained. Run the script; do not edit it to make a check pass. Then look at the page at 360px and 1280px if a browser is available; the script cannot see rendering.
7. **Report** in this shape:

```
Tokens: <scale, base unit, accent, breakpoints chosen and why>
Audit: <verdict, counts, file>
Left on purpose: <each remaining WARN and the reason>
Not checked: <rendering, images, real content, screen readers, dark mode if untested>
```

## Defaults when the user has no system

| Area | Default | How it is checked |
|---|---|---|
| Type scale | 14, 16, 20, 24, 32, 40 px (about 1.25 ratio); body 16 | 4 to 8 steps, neighbours at least 1.1 apart, nothing under 12 |
| Weights, families | 2 to 3 weights (400, 600, 700); 1 family, 2 at most | warns above 4 weights, above 3 families |
| Line height | body 1.5, headings 1.2 to 1.3 | body 1.4 to 1.8, headings at most 1.4 |
| Measure | paragraphs at most 65ch | warns above 80ch |
| Spacing | 4, 8, 12, 16, 24, 32, 48, 64, 96 px | multiples of 4 (2 and 6 tolerated); script checks this in tokens JSON only, check HTML/CSS by eye |
| Radius | 4, 8 and full (9999) | at most 4 distinct |
| Colour | 1 accent, 1 neutral ramp, 3 status colours (success, warning, danger) | contrast pairs listed in tokens |
| Contrast | text 4.5:1, large text (24px, or 18.66px bold) 3:1, UI borders and icons 3:1 | script computes text pairs |
| Breakpoints | 640, 1024, 1280 px, `min-width` | at most 5 |
| Touch targets | controls 44px high | warns under 40 |
| Elevation | 0 to 3 shadow levels | warns above 4 distinct shadows |

## State matrix

Every interactive element needs: default, hover, `:focus-visible`, active, disabled, and loading when it triggers work. Never remove an outline without a visible replacement. Every data view needs: loading (skeleton for page areas, spinner inside buttons), empty (what is missing, why, one action), error (what happened, how to fix it, shown beside the field or region, not by colour alone), partial and populated. Forms also need inline validation and a submit button that is disabled while submitting.

## Machine-made tells to remove

Violet or indigo gradients as the main brand device; gradient-filled headings; blurred translucent cards everywhere; every block centred; one identical card repeated three times with an emoji on top; emoji as icons; five or more corner radii and five shadow depths; "unlock", "seamless", "elevate", "next-generation" copy; `transition: all`; Lorem ipsum left in. Replace each with a decision: a brand colour, left-aligned text, one icon set, real copy that says what the product does. Replacements are in [references/rules.md](references/rules.md), section "Machine-made tells". The script flags only part of this list; emoji used as icons and words such as "unlock" are manual checks.

## Script

`scripts/ui_audit.py <file> [--strict]`: run it on one `.html`, `.htm`, `.css` or tokens `.json` file. Prints one JSON object:

```
{"schema_version": 1, "command": "check", "file": str, "kind": "html"|"css"|"tokens",
 "verdict": "pass"|"review"|"fail", "counts": {"fail": n, "warn": n, "info": n},
 "findings": [{"rule": str, "severity": "fail"|"warn"|"info", "line": int|null,
               "message": str, "evidence": str}],
 "stats": {...}}
```

Exit 0 for `pass` or `review`, 1 when any FAIL (with `--strict`, any WARN too), 2 for a missing, empty or invalid file. It reads one file, follows no links and writes nothing. Rule names and thresholds are in [references/rules.md](references/rules.md); read it when a finding is unclear. The standards behind the numbers are in [references/sources.md](references/sources.md); read it only when a figure is challenged. If Python is missing, check each row of the defaults table and the state matrix by hand and say in the report that the script did not run.

## Boundaries

- Does not turn a design file or screenshot into code (use a design-handoff skill), does not tune React rendering, and does not replace an accessibility audit: it checks contrast, focus, viewport zoom and touch-target size only.
- Does not copy a specific brand's visual identity. Take principles from a reference, not its marks, copy or layout.
- Do not add tracking, third-party fonts or scripts to a design unless the user asks.

## Limits

- The audit reads source text. It cannot see rendered layout, backgrounds inherited across elements, images, web fonts or JavaScript-built DOM, and it resolves `var()` only for plain custom properties.
- Contrast with an assumed page background is reported as WARN, not FAIL. Gradients, images and translucent colours are skipped.
- Thresholds are working values (named constants in the script), not measured optima; tell checks are style judgements and a WARN may be a deliberate choice.
- Linked stylesheets and utility-class frameworks (classes with no CSS in the file) are not audited.
- Passing the audit does not make a design good; it removes common defects.
