---
name: design-token-naming-lint
description: Checks a design-token JSON file for naming pattern breaks, duplicate raw values, raw hex inside semantic or alias tokens, dangling references and circular references, and prints a JSON report. Use when a token file has grown by hand and needs a naming and reference check before a release, or when a reviewer asks whether tokens follow the lowercase kebab-case dot pattern and resolve. Do not use for choosing colors, judging contrast, generating token files, or linting CSS, Figma exports or component code.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Design token naming lint

This skill runs one read-only script over one token file and turns its JSON report into a fix list. The script is [scripts/token_lint.py](scripts/token_lint.py). A smoke input is in [fixtures/tokens_smoke.json](fixtures/tokens_smoke.json). The script writes nothing to disk and prints its report to stdout.

## Accepted input

- One JSON object. Nested form: `{"color": {"brand": {"500": "#1a73e8"}}}`. Flat form with dotted keys: `{"color.brand.500": {"value": "#1a73e8"}}`.
- A leaf is a string or a number, or an object whose `value` key holds a string or number.
- Booleans, null and arrays are not accepted as token values.
- References are written `{dotted.name}` with no spaces and no nested braces.

## Workflow

1. Confirm the request names exactly one token file. Required output: the file path as given by the user.
2. Confirm the file is at most 2,097,152 bytes, is valid UTF-8, and nests at most 8 object levels. Required output: pass, or a refusal from the list below.
3. Run the command in the Script contract section. Required output: the raw JSON report and the exit code.
4. Count findings per code. Required output: the summary table in the output contract.
5. Attach one fix action per code using the decision table. Fix order is DANGLING_REFERENCE, CIRCULAR_REFERENCE and DUPLICATE_NAME first, because they break resolution, then NAME_PATTERN, RAW_HEX_IN_SEMANTIC and DUPLICATE_VALUE. Required output: one fix line per finding.
6. Return the report in the output contract. Do not edit the token file. Changes are the user's decision.

## Decision table

| Code | Meaning in the report | Fix action | Priority |
|---|---|---|---|
| DANGLING_REFERENCE | A `{name}` points to a token that does not exist | Add the missing token, or correct the spelling in the reference | 1 |
| CIRCULAR_REFERENCE | A chain of references returns to a token already on the chain | Break one link so one token holds a raw value | 1 |
| DUPLICATE_NAME | The same full dotted name is defined twice, for example nested and as a dotted key | Keep one definition and delete the other | 1 |
| NAME_PATTERN | The name has uppercase letters, underscores, spaces, or an empty segment | Rename to lowercase kebab-case segments joined by dots | 2 |
| RAW_HEX_IN_SEMANTIC | A `semantic.` or `alias.` token holds `#rgb`, `#rrggbb` or `#rrggbbaa` | Replace the value with a reference to a base token | 2 |
| DUPLICATE_VALUE | Two or more reference-free tokens share one raw value, compared case-insensitively after trimming | Report only. Suggest one base token that the others reference. Do not force a merge | 3 |

## Thresholds

| Rule | Working value | Behavior above the value |
|---|---|---|
| Input size | 2,097,152 bytes (2 MB) | Exit 2 |
| Object nesting | 8 levels, the root object counts as level 1 | Exit 2 |
| Name pattern | `^[a-z0-9]+(-[a-z0-9]+)*(\.[a-z0-9]+(-[a-z0-9]+)*)*$` | NAME_PATTERN finding |
| Hex length | 3, 6 or 8 digits after `#` | Only these count as raw hex |
| Semantic prefixes | `semantic.` and `alias.` | RAW_HEX_IN_SEMANTIC applies |

These are working values chosen for this skill. They are not an industry standard.

## Output contract

The final answer uses these sections in this order.

1. `## Summary`: one line with the file name, `token_count`, `finding_count` and the exit code.
2. `## Findings`: a table with the columns `Code | Token | Detail | Fix action`, one row per entry in the report `findings` list, in the same order.
3. `## Not checked`: one bullet per limit that applies, for example "Contrast and color meaning are not checked".

The raw report is a JSON object with exactly these keys:

- `tool`: always `token_lint`
- `file`: base name of the input file
- `token_count`: integer
- `finding_count`: integer
- `summary`: object mapping each code that occurred to its count
- `findings`: list of objects with keys `code`, `token`, `detail`

## Refuse / stop when

- The request names more than one file, a folder, or no file.
- The file is missing, unreadable, larger than 2 MB, not UTF-8, or not valid JSON.
- The root value is not a JSON object, or nesting exceeds 8 levels.
- A token value is a boolean, null, or an array.
- The user asks to edit the token file, or to write the report to the input path. This skill never writes files.
- The user asks whether a color is accessible or on-brand. Stop and say contrast and brand fit are outside this skill.

## Script contract

Arguments: exactly one positional argument, the path to the token JSON file. No options.

Command, run from the skill folder:

```
python -I scripts/token_lint.py <tokens.json>
```

Output keys: `tool`, `file`, `token_count`, `finding_count`, `summary`, `findings`, as listed in the output contract. Errors print one line of JSON with keys `error` and `exit` to stdout.

Exit codes:

- `0`: the file was read and no findings were reported.
- `1`: the file was read and at least one finding was reported.
- `2`: usage error, or the input was refused by a rule in the Thresholds table or the Refuse list.

Smoke run: `python -I scripts/token_lint.py fixtures/tokens_smoke.json` exits 1 with 12 tokens and 7 findings.

## Files in this package

- `SKILL.md`: this file.
- `scripts/token_lint.py`: the checker described above.
- `fixtures/tokens_smoke.json`: a 12-token input with one dangling reference, one duplicate hex value and one reference cycle, used for the smoke run.
- `LICENSE.txt`: Apache License 2.0 text.
