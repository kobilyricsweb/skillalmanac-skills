---
name: csv-to-json-records
description: Converts a CSV file with a header row into a JSON array of records keyed by the header, infers integer, float and boolean columns, and prints a column type table. Use when a CSV must become JSON records without losing number or boolean types, or when a column's inferred type needs checking before import. Do not use for Excel .xlsx files, nested or hierarchical JSON, JSON-to-CSV conversion, or files over 2 MB.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# CSV to JSON records

This skill runs `scripts/csv_to_json.py` on one CSV file. The script writes a new JSON file holding an array of objects, one per data row, keyed by the header row, and prints a column type table. The agent's job is to confirm the intake facts, run the script once, read its exit code, and report the result in the output contract below.

## Workflow

1. **Intake.** Confirm four facts with the user: the input CSV path, the output JSON path (it must not exist yet), the delimiter (default comma; use `tab` for TSV), and whether empty cells become `null` (`--empty-null`) or `""` (default). Output: a four-line intake block. If the input or output path is missing, stop and return the numbered question list in "Open questions" (see Refuse / stop when).
2. **Pre-check size.** The input must be 2 MB (2,097,152 bytes) or smaller. Output: the file size in bytes. Over the cap, stop; the skill does not split files.
3. **Run the script once** with the command line in the Script contract section. Output: the stdout lines (`rows: N` and the type table) and the exit code.
4. **Branch on the exit code.** Exit 0: go to step 5. Exit 1: go to step 5 and list every column whose note starts with `mixed`. Exit 2: stop, quote the one-line JSON error, and do not retry until the user fixes the cause.
5. **Spot-check the output.** Confirm the `rows: N` value equals the number of objects in the JSON array, and that every object has exactly the header names as keys in header order. Output: the two counts and a yes or no for the key check. A mismatch is a defect; report it and stop.
6. **Report** using the output contract. Output: the three sections below, in this order.

## Type inference rules

Every cell is trimmed of leading and trailing whitespace before inference and before output. Header names are trimmed too. Blank lines are skipped. Empty cells are excluded from inference.

| Column's non-empty cells | Inferred type | JSON value written |
|---|---|---|
| all `true` or `false` in any letter case | boolean | `true` or `false` |
| all integers, no leading zero (`0`, `-12`, `+7`) | integer | number |
| all integers or floats (`1.5`, `-0.25`, `1e5`, `100`) | float | number, always with a decimal point or exponent when written from a float column |
| any other mix, or any non-finite float such as `1e400` | string | cell text as-is |
| no non-empty cells at all | string | empty cells only |

Leading-zero values such as `007` or `02134` are not integers; a column containing them becomes a string column. A string column that also contains at least one numeric or boolean cell gets the note `mixed: N cell(s) look numeric or boolean` and a finding (exit 1).

| Cell is empty | Without `--empty-null` | With `--empty-null` |
|---|---|---|
| in any column | `""` (a JSON string, even in a number column) | `null` |

## Output contract

The agent's report has three sections, in this order.

```
## Conversion result
| Field | Value |
|---|---|
| Input | <input-file> |
| Output | <output-file> |
| Delimiter | comma, tab, or the character used |
| Empty cells | "" or null |
| Records | N |
| Exit code | 0, 1 or 2 |
| Status | complete, complete with findings, or stopped |

## Column types
| column | type | non_empty | empty | note |
|---|---|---|---|---|
(one row per column, copied from the script table without edits)

## Findings and open questions
- one bullet per mixed column: name, count of numeric or boolean cells, and the decision needed
- one bullet per open question, numbered when more than one
```

Status mapping: exit 0 is `complete`; exit 1 is `complete with findings`; exit 2 is `stopped`. For `stopped`, the Records row reads `0` and the Column types section is omitted; the Findings section carries the quoted error line.

## Script contract

Run from the skill folder. Command line:

`python -I scripts/csv_to_json.py <input-file> <output-file> [--delimiter CHAR] [--empty-null]`

| Item | Rule |
|---|---|
| `input-file` | existing CSV, UTF-8 (a UTF-8 byte order mark is accepted), 2 MB or smaller, with a header row |
| `output-file` | must not exist; written in exclusive-create mode; never overwritten; never equal to the input path |
| `--delimiter CHAR` | one character, or `tab` for a tab; default `,` |
| `--empty-null` | write empty cells as `null`; default writes `""` |
| stdout | line `rows: N`, then a table with columns `column`, `type`, `non_empty`, `empty`, `note` |
| stderr | one line of JSON, `{"error": "..."}`, on exit 2 only |

Exit codes:

| Code | Meaning |
|---|---|
| 0 | JSON written; no column is mixed |
| 1 | JSON written; at least one column has the note `mixed` |
| 2 | usage or input error; nothing written |

Error messages (stderr, exit 2):

| Message | Cause |
|---|---|
| `input file is missing or unreadable` | path does not exist or cannot be read |
| `input file exceeds the 2 MB limit` | file is larger than 2,097,152 bytes |
| `input file is not valid UTF-8` | bytes do not decode as UTF-8 |
| `CSV parse error: <detail>` | the csv reader rejected the text |
| `input has no header row` | file is empty or has only blank lines |
| `blank header at column N` | header cell N is empty after trimming |
| `duplicate header 'NAME'` | two header cells have the same trimmed name |
| `data row N has X fields, expected Y` | data row N (first data row is 1) has the wrong field count |
| `delimiter must be one character or 'tab'` | `--delimiter` value is not one character or `tab` |
| `output path must differ from the input path` | the two paths resolve to the same file |
| `output file already exists; choose a new path` | the output path exists |
| `output file cannot be created` | the output folder is missing or not writable |
| argparse usage text, then exit 2 | a required positional argument is missing or an option is unknown |

Column note values printed by the script: `mixed: N cell(s) look numeric or boolean`. Column type values: `integer`, `float`, `boolean`, `string`.

## Refuse / stop when

- The input is over 2 MB. Stop and say so; do not split or truncate the file.
- The output path already exists, or equals the input path. Stop and ask for a new output path. Never delete, rename or overwrite a file to make room.
- The input is an Excel workbook (`.xlsx`, `.xls`), a JSON document, or text that is not UTF-8. Stop and ask the user to re-save as UTF-8 CSV. Do not transcode it.
- The header has a blank or duplicate name, or a data row has the wrong field count. Stop, quote the error line, and ask the user to fix the named row or header.
- The input has no header row. Stop; the script cannot key records without one.
- The request is JSON-to-CSV, nested or hierarchical output, or a schema design task. Out of scope; say so.
- Intake is incomplete. Return a numbered list of the missing facts under Open questions and do not run the script.

## Files shipped

- [scripts/csv_to_json.py](scripts/csv_to_json.py): the converter described above.
- [fixtures/sample.csv](fixtures/sample.csv): six-row smoke input with integer, float, boolean and text columns and one empty cell. Expected exit 0.
- [fixtures/mixed_column.csv](fixtures/mixed_column.csv): three-row input whose `quantity` column holds `n/a`. Expected exit 1.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.
