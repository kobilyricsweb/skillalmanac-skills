# Listing page content: figma-to-code-handoff

**One line:** Validates a Figma-exported tokens file and turns tokens, auto layout, component properties and asset names into code decisions.

## How it differs from design-to-code-handoff

`design-to-code-handoff` (batch 1) is the generic skill: it covers any design source and the handoff process. This skill is narrower and starts after a Figma export exists. It adds what the generic one does not: a script that validates a design-tokens JSON (W3C design tokens subset), the Figma variable-to-token conversion table, one mode list per file with CSS output per mode, the auto layout to flex table with its traps, component-property to prop rules, and asset naming. If the source is not Figma, or the job is a handoff document or process, use the generic skill. The two can be used together: generic for the handoff structure, this one for the Figma-specific values.

## What it does

The agent converts the export to a small, documented token subset, runs `scripts/tokens_check.py check`, and fixes what the strict JSON report lists until `ok` is true. The script finds unresolved and circular aliases, alias type mismatches, modes without values, naming violations, CSS name collisions, duplicate literal values, invalid literals and JSON keys that were silently dropped by a duplicate. It then prints flattened CSS custom properties: defaults under `:root`, one `[data-theme]` block per mode. Reference tables cover auto layout to flexbox, frame and text properties, component properties to props, and exported asset names.

## Capabilities

- `scripts/tokens_check.py check <file>`: strict JSON report with findings, counts by code, skipped tokens and a CSS preview
- `scripts/tokens_check.py css <file>`: the CSS alone
- Figma variable to token conversion table, including modes and the one-collection-per-file rule
- Auto layout, component property and asset naming tables with their traps
- A fixed report: checked, fixed (old to new), warnings kept, mapped, left for the designer, not checked

## When to use

You have Figma variables or a tokens JSON, a frame's exported properties, a component set, or a list of layer names, and say things like convert Figma to CSS, Figma modes to dark mode, auto layout to flexbox, or validate these design tokens.

## When not to use

Generic handoff documents or process, screenshot-against-build comparison, writing Figma plugins, calling the Figma API, accessibility audits, or design sources other than Figma.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual check list in `references/token-subset.md`.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output from the saved fixture run (`python scripts/tokens_check.py check evals/fixtures/tokens_bad.json`, exit code 1):

1. Counts: 11 tokens, 10 errors and 3 warnings. By code: `alias_type_mismatch` 1, `circular_alias` 2, `duplicate_value` 1, `invalid_value` 2, `legacy_value_key` 1, `missing_mode_value` 1, `missing_type` 1, `naming_violation` 2, `undeclared_mode` 1, `unresolved_alias` 1.
2. One finding: `unresolved_alias` on `color.text.default`, "alias {color.brand.missing} does not exist". The CSS preview contains only the two tokens without errors: `--color-brand-primary: #0B5FFF;` and `--color-brand-secondary: #0b5fff;`.
3. `python scripts/tokens_check.py css evals/fixtures/tokens_good.json` prints a `:root` block, then `[data-theme="light"]` and `[data-theme="dark"]` blocks, for example `--color-text-default: var(--color-neutral-50);` in the dark block.

No with-skill agent run has been saved yet, so there is no example of a finished handoff.

## Limits

- Validates structure and literal values only; no contrast, usage or match-to-file checks.
- One `$modes` list per file; srgb colours only; composite types are not emitted.
- Duplicates are judged on default values.
- The conversion table is guidance; export formats differ and change.
- Grid auto layout, variable-driven layout and prototypes are not covered.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN, and the 6 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool use, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Show a tokens file with a space in a name, an alias to a missing token and a dark mode with no value.
2. Run `check`: 4 errors, CSS preview nearly empty.
3. The agent fixes the file, asks the designer for the missing dark value, re-runs: `ok` true.
4. Show the CSS with the light and dark blocks, then the auto layout table for one frame.

## FAQ seeds

- Does it call Figma or need a token? No. It reads an exported file; no network, no credentials.
- Does it read the native Figma file? No, only a JSON export in the documented subset; the skill says how to convert a variables export.
- How is it different from design-to-code-handoff? That one is the generic process; this one is Figma-specific and ships a validator.
- Does it handle several mode sets, such as theme and density? One per file; split the export.
- Will it pick missing dark values for me? No. A missing mode value is an error to resolve with the designer.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
