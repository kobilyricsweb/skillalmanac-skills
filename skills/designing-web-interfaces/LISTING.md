# Listing page content: designing-web-interfaces

**One line:** Gives an agent concrete design rules and a script that audits HTML, CSS or tokens JSON, so UIs stop looking machine-made.

## What it does

The skill makes an agent decide before it styles: a type scale, a 4px spacing scale, a small palette with checked contrast pairs, three breakpoints, and a state matrix (hover, focus, disabled, loading, empty, error). The agent writes a tokens file, audits it, builds from the tokens, then audits the page or stylesheet. The audit script reads one file and prints strict JSON: findings with rule, severity, line and evidence, plus counts and a verdict. It checks type sizes and scale, spacing grid, WCAG text contrast (including dark-scheme overrides), removed focus outlines, viewport meta, fixed widths, reduced motion, heading order, missing empty/error/loading states, and a list of machine-made tells (violet gradients, gradient text, stacked blur, emoji icons, stock copy, shadow and radius sprawl).

## Capabilities

- `scripts/ui_audit.py <file>`: JSON audit of `.html`, `.css` or tokens `.json`; exit 1 on FAIL
- A tokens file format with contrast pairs, checked by the same script
- Default token set, state matrix and a table of machine-made tells with replacements
- A fixed report: tokens chosen, audit result, what was left on purpose, what was not checked

## When to use

You say: make this look designed, restyle this, my UI looks AI-generated, set up design tokens, add hover and error states, check my CSS for design problems.

## When not to use

Converting a Figma file or screenshot to code, React performance, full accessibility audits with assistive technology, branding and logos, UX research, copywriting.

## How it differs from nearby skills

`design-to-code-handoff` starts from a finished design artefact and turns it into code; this skill starts from no design, or a bad one, and sets the rules. `react-best-practices` is about component and rendering code. `accessibility-audit` is the full accessibility review; this skill only checks the few accessibility facts that are also visual quality (text contrast, focus visibility, zoom, target size). Names were compared; their text was not read.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent applies the defaults table and state matrix by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent output. What exists is the script on the saved fixtures (`python scripts/ui_audit.py <file>`):

1. `evals/fixtures/bad_landing.html` (a generic generated-style landing page): verdict `fail`, 3 FAIL, 28 WARN, 1 info. FAIL: viewport fixed at `width=1024`; body text `#777777` on `#ffffff` at 4.48:1; `outline: none` on `button` with no replacement. WARN includes a violet gradient, gradient text, three blurred surfaces, three emoji list icons, four stock phrases ("unlock the power", "seamless", "next-generation", "welcome to our"), five radii, five shadows, off-grid spacing (13, 18, 22, 37px) and a `h1` to `h3` jump.
2. `evals/fixtures/tokens_bad.json`: verdict `fail`; `text #999999` on `background #ffffff` is 2.85:1 and `on-primary #a78bfa` on `primary #6a11cb` is 3.02:1; 14 font sizes including 13/14/15/16; spacing 3, 5, 10, 15, 25 off the grid; 6 radii; breakpoints out of order.
3. `evals/fixtures/good_landing.html` and `tokens_good.json`: verdict `pass`, no findings.

## Limits

- The audit reads source text only: no rendering, no inherited backgrounds across elements, no images, web fonts or JavaScript-built DOM.
- Assumed-background contrast is WARN, not FAIL; gradients and translucent colours are skipped.
- Thresholds are working values; tell checks are style judgements.
- Linked stylesheets and utility-class frameworks are not audited.
- A passing audit removes common defects; it does not make a design good.

## Evidence

See `VERIFICATION.md`. In short: lint 0 FAIL / 0 WARN; 9 of 9 script fixture cases pass. Not tested: any with/without efficacy run, trigger behaviour, native discovery, cross-tool runs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Prompt: "My landing page looks AI-generated, restyle it." Run the audit on the page: `fail`, 3 FAIL, 28 WARN.
2. The agent writes `tokens.json`, audits it (`pass`), then rebuilds the CSS from variables.
3. Re-run the audit on the page: `pass`; show the state matrix covered.
4. Show the report: tokens chosen, remaining WARNs left on purpose, what was not checked (rendering).

## FAQ seeds

- Does it need network access? No.
- Will it work with Tailwind or CSS-in-JS? Only the CSS present in the file is audited; utility classes are not, so run it on the built or generated CSS.
- Does a pass mean the design is accessible? No. It checks text contrast, focus visibility, zoom and target size only.
- How is it different from `design-to-code-handoff`? That skill converts an existing design; this one sets the rules and audits the result.
- Can I use my own design system? Yes; existing tokens win over the defaults.
- Does it copy a brand's look? No; it takes principles, not marks or layouts.
- What data leaves my machine? None; the script reads one local file.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.

## Behaviour notes (fix round 2026-11-21)

- The type-step range is 4 to 8 everywhere (SKILL.md, rules.md and the script agree).
- Not detected by the script: off-grid spacing values such as 7 or 13px, emoji used as icons, and marketing words other than the listed ones. Treat them as manual checks.
