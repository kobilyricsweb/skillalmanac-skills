---
name: figma-to-code-handoff
description: Turns a Figma export into code-ready decisions. Validates a design-tokens or variables JSON (W3C design tokens subset) for unresolved aliases, missing mode values, naming violations and duplicate values, then previews flattened CSS custom properties; maps auto layout to flex, component properties to code props and layer names to asset filenames. Use when the user has Figma variables, tokens JSON, an exported frame or component spec, or says convert Figma to CSS, Figma modes to dark mode, auto layout to flexbox. Do not use for generic handoff docs, screenshot diffing, Figma plugins or API calls.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the check list in references/token-subset.md by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Figma export to code

This is the Figma-export path only: tokens and variables JSON, modes, auto layout, component properties and exported asset names. Writing a general design-to-code spec belongs to a generic handoff skill; this one decides concrete values and checks them.

## Rules that save rework

- Tokens come from the export, never from reading colours off a screenshot. If only screenshots exist, say so and stop at "values are approximate".
- A semantic token (`color.text.default`) must be an alias to a primitive (`color.neutral.900`), never a repeated literal. Literals repeated across tokens are what the duplicate check finds.
- A Figma "state" variant (hover, pressed, focused, disabled) becomes CSS pseudo-classes or a native attribute, not a prop. A state that the app drives (loading, selected, error) is a prop.
- Auto layout is flexbox, not absolute positioning. Only layers marked absolute inside auto layout get `position: absolute`.
- One modes collection per JSON file. Figma lets each collection have its own modes (theme, density); the script reads one `$modes` list, so split the export and check each file.

## Workflow

```
- [ ] 1 Identify the export and convert to the subset
- [ ] 2 Run the token check, fix errors, re-run
- [ ] 3 Decide warnings (duplicates, naming style)
- [ ] 4 Map layout, components and assets
- [ ] 5 Emit CSS, verify, report
```

1. **Identify the export.** Tokens usually arrive as a plugin export or a REST response of the variables endpoint. The script reads only the subset in [references/token-subset.md](references/token-subset.md): `$value`, `$type`, `$modes`, `$extensions.modes`, aliases as `{dotted.path}`. If the file is another shape (flat Figma variable list, Style Dictionary `value` keys, Tokens Studio sets), convert it by the table in that reference first, keeping a record of every rename you make. Read the "Figma variable to token" section only when converting.
2. **Check.** Run `python scripts/tokens_check.py check tokens.json`. It prints strict JSON (contract below) and exits 0 when no error findings exist, 1 when any exist, 2 when the file cannot be read or parsed. Fix every error in the source JSON, or in the converted copy, and re-run until `ok` is true. Do not edit the script to make a check pass.
3. **Warnings.** `duplicate_value`: alias all but one source token (keep the primitive, alias the semantic ones); if two tokens are meant to diverge later, keep both and say why in the report. `naming_violation` as a warning: rename to lower-case kebab segments unless the design system already uses another style consistently; then leave it and report it. `undeclared_mode`: add it to `$modes` or drop it, never ignore it.
4. **Map.** Read [references/figma-mapping.md](references/figma-mapping.md) only for the parts the task has: the auto layout table, the component property table, or the asset naming rules. Write the mapping as a table (Figma property, value, CSS or prop) so the designer can check it. Anything with no exact CSS equivalent (centre strokes, some blend modes) goes under "Left for the designer", not into guessed CSS.
5. **Emit and verify.** `python scripts/tokens_check.py css tokens.json` prints the CSS custom properties: `:root` holds each token's default `$value`; each mode gets a `[data-theme="<mode>"]` block with only the tokens that vary. Aliases become `var(--...)`. Use the dark-mode selector the project already has (media query or class) instead of `data-theme` when it differs, and say so. Re-run `check` on the final JSON and report.

## Script contract

`python scripts/tokens_check.py check <file>` prints one JSON object:

```
{
  "command": "check", "file": "<path>", "ok": true|false,
  "tokens": <int>, "modes": ["light","dark"], "modes_declared": true|false,
  "counts": {"error": <int>, "warning": <int>},
  "counts_by_code": {"<code>": <int>},
  "findings": [{"severity": "error|warning", "code": "<code>", "path": "<dotted.path>", "message": "<text>"}],
  "css_skipped": [{"path": "<dotted.path>", "reason": "<text>"}],
  "css_preview": "<css text>"
}
```

Findings are sorted errors first, then by path. Tokens with an error finding are left out of `css_preview` and listed in `css_skipped`, so a preview is trustworthy only when `ok` is true.

| Code | Severity | Meaning and fix |
|---|---|---|
| `unresolved_alias` | error | `{path}` does not exist or names a group; fix the path or add the token |
| `circular_alias` | error | alias loop (checked per mode); break it by pointing one token at a literal |
| `alias_type_mismatch` | error | alias target has another `$type` (a colour aliased from a dimension) |
| `missing_mode_value` | error | a mode in `$modes` has no value on a token that uses modes |
| `undeclared_mode` | warning | a token uses a mode that `$modes` does not list |
| `naming_violation` | error or warning | error: characters unusable in a CSS name (space, slash, dot); warning: not lower-case kebab, or deeper than 5 levels |
| `css_name_collision` | error | two paths flatten to the same `--name` (`a.b-c` and `a-b.c`) |
| `duplicate_value` | warning | several tokens of one type share one literal value after normalising (`#FFF` equals `#ffffff`, `16px` equals `16.0px`) |
| `invalid_value` | error | literal does not fit `$type` (colour not hex, dimension without unit, weight outside 1-1000) |
| `missing_type` | error | no `$type` on the token or any parent group |
| `unsupported_value` | warning | valid but not converted (colour space other than srgb); left out of CSS |
| `unknown_type` | warning | type outside the subset; value not validated and not emitted |
| `duplicate_key` | error | an object repeats a key; JSON parsers silently keep the last, so a token vanished |
| `legacy_value_key` | error | `value` instead of `$value` (older Style Dictionary shape) |
| `not_a_token` | error | a leaf under a group is not an object |
| `invalid_modes` | error | `$modes` or `$extensions.modes` has the wrong shape |
| `empty_group` | warning | group with no tokens |

The check compares default `$value` literals for duplicates and does not judge whether two equal values are meant to be equal.

## Report format

```
Checked: <file>, <n> tokens, modes <list>, ok <true|false>
Fixed: <each rename or edit as old -> new>
Warnings kept: <code, path, reason>
Mapped: <layout / components / assets covered, with the tables>
Left for the designer: <no exact CSS, ambiguous names, missing states>
Not checked: <rendered output, contrast, components not in the export>
```

## Limits

- The script validates structure and literal values. It does not check colour contrast, whether a token is used anywhere, or whether the export matches the Figma file.
- Only one `$modes` list per file, only srgb colours are converted, composite types (shadow, typography, border, gradient) are accepted but not emitted as CSS.
- Duplicate detection is on default values; a duplicate that exists only inside one mode is not reported.
- The conversion table for Figma variables is guidance. Export formats differ between plugins and change over time; a converted file must pass `check` before the mapping starts.
- Auto layout, component and asset rules cover the common cases. Grid auto layout, variable-driven layout and interactive prototypes are not covered.
- Public pages behind these rules are listed in [references/sources.md](references/sources.md); read it only to re-verify a rule or to cite one.
- Short manual fallback without Python: for each token confirm the alias target exists, every mode has a value, names are kebab-case, and no two tokens share a literal.
