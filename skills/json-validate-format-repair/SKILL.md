---
name: json-validate-format-repair
description: Validates JSON text, reports the line and column of the first syntax error, pretty-prints valid JSON with two-space indentation, and repairs six listed mistakes while logging each repair. Use when a JSON file fails to parse, a pipeline rejects a file with a trailing comma, single quotes, comments, unquoted keys, Python True/False/None or missing closing brackets, or a test JSON needs formatting. Do not use for JSON Schema checks, editing data values, JSON5 or JSONC files that must keep their comments, or files over 2 MB.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# JSON validate, format and repair

Type A script skill. The script reads one JSON file, prints one JSON report line on stdout, and can write one new pretty-printed file. It never edits the input.

## Workflow

1. **Intake.** Required: the input file path, and whether the user allows repairs. Optional: an output file name. Output: a three-line summary of input path, repair yes or no, and output path. If the user wants a formatted file, the output name must be new; ask for one if none is given.
2. **Size and encoding check.** The input must be at most 2,097,152 bytes (working value) and valid UTF-8. A leading byte-order mark is ignored. Output: pass, or the exit 2 error code from the error table below.
3. **Validate without changes.** Run the script with no `--repair` flag. Output: the `status` and `first_error` values from the report.
   - `valid`: skip to step 5 with zero repairs.
   - `invalid`: go to step 4.
4. **Repair.** Run again with `--repair` and `--output`. Output: the `repairs` list and the `refused` value.
   - `refused` is not null: no output is written. Go to step 6.
   - `status` is `repaired`: go to step 5.
5. **Deliver.** Output: the output path, the final `status`, and the count of repairs. Do not describe the output as verified against the user's schema; the script only confirms it parses.
6. **Report.** Output: one table with the columns `line`, `fix or refusal`, and `detail`. Use one row per entry in `repairs`, or one refusal row built from `refused`.

## Decision and threshold table

| Check | Value | Result when crossed |
|---|---|---|
| Input size | at most 2,097,152 bytes (working value) | exit 2, `input_too_large` |
| Output indentation | 2 spaces, fixed | not configurable |
| Key order in output | source order; sorted only with `--sort-keys` | sorting is opt-in |
| Ambiguous token | any one token the rules below cannot map | run stops, status `invalid`, exit 1, no output file |
| Output path | new path, not the input path | exit 2, `output_exists` or `output_is_input` |
| Duplicate object key | any repeat within one object | status `invalid`, `first_error.line` is null |
| NaN, Infinity | any occurrence | status `invalid`, `first_error.line` is null |

## Repair catalog (only these six fixes)

| fix code | Input form | Rule | Written as |
|---|---|---|---|
| `single_quotes` | `'text'` as a key or value | single-quoted string, only `\'` allowed as escape | `"text"`; an inner `"` becomes `\"` |
| `comment` | `// note` or `/* note */` outside strings | removed; newlines inside a block comment are kept | nothing |
| `trailing_comma` | comma directly before `}` or `]` | removed; also removed at end of input when a closer is appended | nothing |
| `unquoted_key` | bare identifier before `:`, after `{` or `,` | quoted | `"name":` |
| `python_literal` | `True`, `False`, `None` in value position | mapped | `true`, `false`, `null` |
| `missing_closer` | input ends with `{` or `[` still open | closers appended in reverse open order | `}` or `]` |

## Refusal reasons (stop the repair, write nothing)

| reason prefix | Meaning |
|---|---|
| `unterminated string` | double-quoted string has no closing quote before a newline or end of input |
| `unterminated single-quoted string` | single-quoted string has no closing quote on its line |
| `unterminated block comment` | `/*` has no matching `*/` |
| `backslash escape in single-quoted string` | a backslash other than `\'` appears in a single-quoted string |
| `closing bracket without opener` | `}` or `]` with nothing open |
| `mismatched closing bracket` | `]` closes `{`, or `}` closes `[` |
| `comma without a preceding value` | comma right after `{`, `[`, `,`, or `:` |
| `unknown bare word: <word>` | bare word that is not a key, `true`, `false`, `null`, `True`, `False`, or `None` |
| `unexpected character <char>` | any other character outside strings, such as a leading `+` or `.5` |
| `still invalid after repairs: <message>` | all listed repairs ran but the result still does not parse |

## Output contract

The script prints one JSON object on stdout:

| key | Type | Meaning |
|---|---|---|
| `status` | string | `valid`, `repaired`, or `invalid` |
| `first_error` | object or null | `line`, `column`, `message` of the original parse error |
| `repairs` | list | each item has `line`, `fix` (one of the six codes), `detail` |
| `refused` | object or null | `line` and `reason` (see refusal table) |
| `output` | string or null | output path when a file was written |

Errors before parsing go to stderr as one JSON line `{"error": "<code>", "detail": "..."}` with exit 2. Codes: `usage`, `file_not_found`, `input_too_large`, `invalid_utf8`, `read_error`, `output_is_input`, `output_exists`, `output_dir_missing`, `unencodable_text`, `write_error`.

## Script contract

Command line (replace the placeholders; the script name is the only fixed part):

```
python -I "<skill-folder>/scripts/json_fix.py" "<input-file>" [--repair] [--sort-keys] [--output "<new-file>"]
```

- `<input-file>`: required, existing file.
- `--repair`: apply the six listed repairs; without it the script only validates.
- `--sort-keys`: sort object keys in the written output.
- `--output`: new file; written only when status is `valid` or `repaired`.
- Exit 0: `valid` with no repair needed. Exit 1: `repaired` or `invalid`. Exit 2: usage or input error.

## Files shipped

- [scripts/json_fix.py](scripts/json_fix.py): the validator and repair script.
- [fixtures/broken_12_lines.json](fixtures/broken_12_lines.json): 12-line smoke input with one single-quoted string, one comment, and one trailing comma. Expected: status `repaired`, three repairs.
- [fixtures/ambiguous_bare_word.json](fixtures/ambiguous_bare_word.json): refusal example with an unquoted value `maybe`. Expected: status `invalid`, exit 1.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.

## Refuse or stop when

- The input is missing, larger than 2 MB, or not UTF-8: stop, report the error code, and ask for another file.
- `refused` is not null: do not guess the intended value. Quote the line and reason, and ask the user to correct that line.
- The user asks for output to overwrite an existing file or the input file: refuse that clause, offer a new file name, and keep the validation result.
- The user asks for JSON Schema checks, data edits, or an output that keeps comments: out of scope. Comments are always removed by repair.
- The file holds credentials or personal data: the report can show up to 40 characters of a key or bare word. Do not paste the file content into chat.
