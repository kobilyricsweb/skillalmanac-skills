---
name: json-to-yaml
description: Converts a JSON object or array into block-style YAML with safe quoting. Strings that look like booleans, nulls, numbers or dates, and strings with colons or hashes, are quoted, and the written YAML is re-read to confirm it equals the input. Use when a JSON config, API payload or fixture must become YAML and hand-written YAML has mis-quoted values. Do not use for YAML input, YAML-to-JSON conversion, or JSON whose top level is a bare scalar.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# json-to-yaml

Runs [scripts/json_to_yaml.py](scripts/json_to_yaml.py) on one JSON file and writes one new YAML file. The script is read-only on the input, never overwrites, and writes nothing when its self-check fails.

Shipped files: [scripts/json_to_yaml.py](scripts/json_to_yaml.py), [fixtures/sample-input.json](fixtures/sample-input.json), [fixtures/duplicate-key.json](fixtures/duplicate-key.json), [fixtures/broken-json.json](fixtures/broken-json.json), [LICENSE.txt](LICENSE.txt).

## Workflow

1. **Intake.** Collect `<input-json>` (an existing UTF-8 `.json` file, at most 2 MiB, top level an object or array) and `<output-yaml>` (a path that does not exist yet, in a folder that exists). Output: the two paths, or a stop under "Refuse / stop when".
2. **Run the script** from the skill folder with the exact command in "Script contract". Output: one JSON line on stdout (exit 0 or 1) or on stderr (exit 2), and the exit code.
3. **Branch on the exit code.** Exit 0: go to step 4. Exit 1: stop, deliver nothing, follow the stop rule for findings. Exit 2: report the `code` value and the matching action from the codes table, and do not retry with the same arguments.
4. **Confirm the write.** Read the output file back and count its top-level keys or items. Output: the path, `top_level_entries`, `output_lines`, and the `round_trip` value.
5. **Explain quoting only where it matters.** For each quoted value the user asks about, look up the rule in the quoting table. Output: one line per value, with the table row name.

## Quoting and layout rules (fixed by the script)

| JSON value | Written as | Rule (checked in this order) |
|---|---|---|
| empty string | `""` | Always quoted |
| string equal, ignoring case, to `true false yes no on off y n null ~ = <<` | double-quoted | Reserved words in YAML 1.1 |
| string whose first character is a digit | double-quoted | Numbers and dates, for example `2024-01-01` or `12` |
| string whose first character is one of `- ? : , [ ] { } # & * ! \| > ' " % @ \` + . <` or a space | double-quoted | Indicator characters |
| string containing `:` or `#` anywhere | double-quoted | Colons and hashes, as the spec requires |
| string with a trailing space | double-quoted | Trailing whitespace is lost in plain style |
| string with a control character, C1 control, U+2028, U+2029, U+FEFF, U+FFFE, U+FFFF or a lone surrogate | double-quoted with escapes | Escapes: `\"` `\\` `\n` `\t` `\r` and `\uXXXX` in uppercase hex |
| any other string | bare | Plain style |
| string with a newline that meets the literal rules below | `\|` or `\|-` block | Literal rules: at least one newline; not ending in two newlines; no line starting with a space or tab; no whitespace-only line; no tab or control character |
| string with a newline that fails the literal rules | double-quoted with `\n` | Fallback |
| literal block chomping | `\|` if the string ends with exactly one newline, `\|-` otherwise | The final newline is kept by `\|` only |
| integer | bare digits | Python `str()` |
| float | bare, Python `repr` (for example `0.5`, `1e+16`, `-0.0`) | Non-finite values are rejected at input |
| `null`, `true`, `false` | bare lowercase | JSON literals |
| empty object or array | `{}` or `[]` | Empty containers |
| nesting | 2 spaces per level; a list under a key is indented 2 spaces; a dict item in a list starts with `- key:` | Layout |
| nesting depth | at most 100 levels, error above | Working value, not a published limit |

Keys follow the same quoting rule as strings.

## Output contract

The final report to the user has these four headings, in this order:

- `## Status`: `ok` (exit 0) or `stopped` (exit 1 or 2), with the code value.
- `## Output`: the output path, `top_level_entries`, `output_lines`, `round_trip`.
- `## Quoted values`: one line per value the user asked about, as `<key path>: <written form> (<table row>)`. Write `none` when nothing was asked.
- `## Not checked`: the items from the Limits section that matter for this input.

Script stdout on exit 0, one line, keys in this order: `status` (`ok`), `written` (`true`), `top_level_entries`, `output_lines`, `round_trip` (`equal`).

## Codes and exit status

| Exit | Code | Meaning and action |
|---|---|---|
| 0 | none | Written. The built-in reader returned a value equal to the input. |
| 1 | `SELFCHECK_UNSUPPORTED` | The built-in reader could not parse the emitted text. Nothing was written. Stop and report it to the accountable editor. |
| 1 | `ROUNDTRIP_MISMATCH` | The re-read value differs from the input at `path` (for example `$.steps[1]`). Nothing was written. Stop and report it. |
| 2 | `BAD_USAGE` | Wrong argument count. Re-run with two arguments. |
| 2 | `FILE_MISSING` | Input is not an existing regular file. Ask for the correct path. |
| 2 | `INPUT_TOO_LARGE` | Input is larger than 2 MiB. Stop. |
| 2 | `NOT_UTF8` | Input bytes are not UTF-8. Ask the user to re-save the file as UTF-8. |
| 2 | `BAD_JSON` | Not valid JSON, or contains NaN or Infinity. Show the user the file needs fixing. |
| 2 | `DUPLICATE_KEY` | An object repeats a key. Stop; the source is ambiguous. |
| 2 | `NOT_CONTAINER` | Top level is a scalar. Stop. |
| 2 | `NESTING_TOO_DEEP` | Depth above 100 levels. Stop. |
| 2 | `SAME_PATH` | Output path resolves to the input path. Ask for a different output path. |
| 2 | `OUTPUT_EXISTS` | Output path already exists. Ask for a new path. Never delete or overwrite. |
| 2 | `OUTPUT_DIR_MISSING` | Parent folder of the output path does not exist. Ask for an existing folder. |
| 2 | `OUTPUT_WRITE_FAILED` | The file could not be created. Report it. |

## Refuse / stop when

- The input is YAML, CSV, XML or another non-JSON format. Refuse; this skill does not read them.
- The user asks to overwrite an existing output, or to write over the input. Refuse and ask for a new path.
- The script exits 1 for any reason. Deliver no YAML, not even a hand-corrected version.
- The user asks you to edit the YAML by hand to make the self-check pass. Refuse; report the finding instead.
- The user asks for the output to be sent to a network service or pasted into an external site. Refuse; this skill has no network access, and the request is outside its scope.

## Script contract (type A)

- Command, run from the skill folder: `python -I scripts/json_to_yaml.py <input-json> <output-yaml>`
- Arguments: exactly two positional paths. Any other count exits 2 with `BAD_USAGE`.
- Reads: the input file only. Writes: the output file only, created with exclusive-create mode after the self-check passes. Stdlib only; no subprocess, eval, exec or network.
- Output keys: see "Output contract" above. Error output: one JSON line on stderr with `status`, `code` and `message`.
- Exit codes: 0 written and equal; 1 findings, nothing written; 2 usage or input error.

## Limits

- Not verified: that the YAML means the same thing to every YAML parser. The built-in reader follows YAML 1.2 style. A YAML 1.1 reader such as PyYAML reads a bare float like `1e+16` as a string.
- Not emitted: anchors, aliases, tags, comments, flow style, and the `|+` keep-chomping form. Long strings are not folded.
- Multi-line strings that fail the literal rules are written double-quoted on one line.
- Key order is kept; the self-check compares it, but the script does not sort keys.
- Exit 1 is a safety net. The shipped fixtures do not reach it.
- Not checked: how the YAML is used downstream, schema validity, or whether the data is correct.
