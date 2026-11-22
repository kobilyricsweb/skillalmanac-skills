---
name: typography-scale-generator
description: Generates a modular type scale as CSS custom properties from a base size and a ratio, with rem values and line-height suggestions for each step. Use when a UI or document theme needs consistent font sizes, when someone asks for a modular scale, a minor-third or major-third ratio, or ':root' type tokens for headings and body text. Do not use for choosing typefaces, writing layout or grid CSS, fluid clamp() viewport scales, or sizes that must follow no fixed ratio.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Typography Scale Generator

This skill produces one geometric type scale. Step n has size `base * ratio^n` in px, and `base * ratio^n / root` in rem (root is the html font-size, default 16 px), for whole-number steps n. The script `scripts/type_scale.py` does the arithmetic and the formatting. Run it; do not compute the values by hand.

## Settings

| Setting | Flag | Config key | Allowed range | Default |
|---|---|---|---|---|
| Base size | `--base` | `base` | 8 to 48 px | 16 |
| Ratio | `--ratio` | `ratio` | 1.05 to 2.0, or a known name | 1.25 |
| Steps below 0 | `--below` | `below` | whole number, 0 to 6 | 2 |
| Steps above 0 | `--above` | `above` | whole number, 0 to 12 | 5 |
| Root font size | `--root` | `root` | 8 to 32 px | 16 |
| Output file | `--out` | none | path to a new file; must not exist and must not be the config file | none |

Known ratio names (working values from a common list, not a published standard):

| Name | Ratio |
|---|---|
| minor-second | 1.067 |
| major-second | 1.125 |
| minor-third | 1.2 |
| major-third | 1.25 |
| perfect-fourth | 1.333 |
| augmented-fourth | 1.414 |
| perfect-fifth | 1.5 |
| golden | 1.618 |

Line-height rule (working values, applied by the script to the px size of each step):

| Step size in px | Suggested line-height |
|---|---|
| up to 20 | 1.5 |
| above 20, up to 32 | 1.35 |
| above 32 | 1.2 |

## Workflow

1. Collect the five settings (base, ratio, below, above, root) from the request. For any setting the user did not give, use the default in the Settings table and record that choice for the reply.
2. Check each value against the Allowed range column. If a value is outside its range, stop and use the refusal text in the Refuse list below. Do not clamp values silently.
3. If the user wants a reusable file, write a config JSON object with only the keys base, ratio, below, above, root. Keep it under 2 MB, with scalar values only.
4. Run the script with the exact command line in the Script contract section. Save stdout as the scale record.
5. Read the exit code. 0 means the scale is ready. 1 means findings were printed; keep the scale and list each finding line in the reply, then ask whether to change base, ratio or the step counts. 2 means an input error; show the JSON error line and stop.
6. Check the table: the step 0 row must show px equal to base and rem equal to base divided by root (1 when base equals root). If it does not, stop and report a script defect.
7. If the user asked for a file, pass `--out` with a new file name in an existing folder, then confirm the file exists by listing it.
8. Write the reply using the Output contract. Do not add advice on typefaces, spacing or colour.

## Output contract

The script writes this stdout layout, in this order:

1. Line `type scale: base <N>px, ratio <R>, root <M>px`
2. Header `step px rem line-height` with fixed column widths
3. One row per step, from the lowest step to the highest
4. A `:root {` block whose first line is a comment giving the html font-size the rem values assume (the root, in px), then one `--type-step-<tag>` line per step with the rem value and px in a trailing comment, then one `--type-line-<tag>` line per step, closed by `}`
5. Zero or more `finding:` lines
6. Last line `findings: <count>`

Tags: step 0 is `0`, positive steps are `1`, `2` and so on, negative steps are `n1`, `n2` and so on.

Numeric formatting: px to 2 decimals, rem to 4 decimals, trailing zeros removed. Line-height to 2 decimals.

The agent reply uses these headings in this order:

- `## Scale`: the table, copied from stdout, in a code block
- `## CSS`: the `:root` block, in a code block, followed by one line: "The rem values assume an html font-size of <M>px (the root); otherwise use the px values in the comments."
- `## Findings`: each finding line, or the word `none`
- `## Settings used`: one line per setting with its value and whether it came from the request or the default

## Script contract

Script: `scripts/type_scale.py`. Python 3.9+, standard library only. It makes no network calls, starts no subprocess, uses no eval or exec, and never writes to an input file.

Arguments (all optional; flags override config keys):

- `--config PATH`: JSON object file, at most 2 MB, scalar values only, keys from the Settings table
- `--base`, `--ratio`, `--below`, `--above`, `--root`: values as in the Settings table
- `--out PATH`: writes the `:root` block to PATH as a new file; refused if PATH already exists, resolves to the config file, is a directory, or has a parent folder that does not exist

Output: text on stdout as in the Output contract. Input errors print one JSON line on stderr, for example `{"error": "base must be between 8 and 48"}`.

Exit codes: 0 ok; 1 findings (a step is below 10 px or above 120 px; output is still printed); 2 usage or input error.

Exact command line for the default smoke run:

`python -I scripts/type_scale.py --base 16 --ratio 1.25 --below 2 --above 5`

Config run with a file write:

`python -I scripts/type_scale.py --config fixtures/scale_basic.json --out type-scale.css`

The fixture `fixtures/scale_basic.json` holds the same values as the smoke run.

## Files

- `SKILL.md`: this file
- `scripts/type_scale.py`: the generator
- `fixtures/scale_basic.json`: the smoke-run config
- `LICENSE.txt`: Apache-2.0 text

## Refuse / stop when

- Base is outside 8 to 48 px, the ratio is outside 1.05 to 2.0 or is not a known name, or a step count is not a whole number inside its range, or the root is outside 8 to 32 px.
- The config has an unknown key, a nested object or list, invalid UTF-8, invalid JSON, or is larger than 2 MB.
- `--out` names an existing file (including the config file), a directory, or a path with a missing parent folder. Ask for a new file name.
- The request asks for fluid or viewport-based sizing (clamp, vw units), a typeface choice, or sizes picked one by one with no ratio. Say that this skill only builds one geometric scale and stop.
- The request asks to fetch fonts, metrics or pages from the web. This skill has no network access.
- The request asks to call the output an industry standard. Describe the ratio names and line-height values as working values.
- A finding appears and the user has not chosen a new setting. Report it and wait.
