---
name: tabular-to-xlsx
description: Writes a new Excel .xlsx workbook from a CSV or JSON record file using only the Python standard library, so Excel does not need to be installed. Use when a user has a CSV or JSON table and needs an Excel file from it, or when Excel is not available on the machine. Do not use for editing an existing workbook, reading .xlsx files for analysis, adding formulas, charts or macros, or converting to PDF or Word.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Tabular to XLSX

This skill runs `scripts/to_xlsx.py` once on the user's file and reports what the script wrote and checked. The script never overwrites a file, never writes macros or formulas, and never edits the input.

## Workflow

1. **Intake.** Collect three values: the input path (must end in `.csv` or `.json`), the output path (must end in `.xlsx` and must not exist yet), and the sheet name (default `Sheet1`). Output: the three values in a short list. If the input or output path is missing, ask the numbered questions under Refuse / stop when and stop.
2. **Pre-check.** Confirm the input is UTF-8 text and no larger than 2,097,152 bytes (2 MB, working value). A CSV needs a header row. A JSON file needs a non-empty array of flat objects. Output: "pass", or the blocking item.
3. **Run** the command in the Script contract section with the three values. Do not add flags the script does not list. Output: the exit code and the single JSON line from stdout or stderr.
4. **Read the result.** Exit 0 means status `ok`. Exit 1 means status `findings`: the workbook exists and must be reviewed. Exit 2 means no workbook was written; use the `code` in the error table. Output: the status and the codes.
5. **Report** using the Output contract. Output: the three headings in order, with one row per finding or error.

## Cell rules (fixed; the script applies them without asking)

| Input value | Cell written |
|---|---|
| Empty CSV field, or JSON `null` | Blank cell (nothing written) |
| CSV text matching `-?(0\|[1-9][0-9]*)(\.[0-9]+)?` with at most 15 significant digits, for example `3`, `-0.5`, `4.50` | Numeric cell; the text is kept as typed (`4.50` shows as 4.5) |
| CSV text such as `007`, `1,000`, `1e5`, `.5`, `12%`, `2026-01-05` | Inline text |
| JSON number (finite; integer with at most 15 significant digits, or any float) | Numeric cell |
| JSON string, including `"02134"` and `"42"` | Inline text |
| JSON `true` or `false` | Inline text `TRUE` or `FALSE` |
| Header row (first CSV row or JSON key names) | Inline text in bold, always |
| Text starting with `=`, `+`, `-` or `@` | Inline text; never a formula |

| Layout measure | Value | Basis |
|---|---|---|
| Column width | longest text in the column + 2 characters, bounded to 8 to 60 | working value |
| Input size cap | 2,097,152 bytes | working value |
| Significant digits kept as a number | 15 | Excel display precision |
| Data rows | 1,048,575 at most | Excel row limit |
| Columns | 16,384 at most | Excel column limit |

Ragged CSV rows are padded with blanks to the widest row. Extra cells in a long row are kept in new columns with no header text. Each such row is counted under `ragged_rows`.

## Output contract

The script prints one JSON line on success with these keys, in this order: `status`, `output`, `sheet`, `columns`, `data_rows`, `read_back_rows`, `ragged_rows`, `findings`. `read_back_rows` counts the header row, so it equals `data_rows` + 1 when the check passes.

The reply to the user uses these headings, in this order:

- `## Workbook`: a table with columns `Output | Sheet | Columns | Data rows | Read-back rows`.
- `## Checks`: one line stating the `ragged_rows` count and the read-back result (match or mismatch).
- `## Findings`: a table with columns `Code | Meaning | Action`. Write "None" under the table when `findings` is empty.

## Findings and error codes

| Code | Exit | Meaning | Action |
|---|---|---|---|
| `F_RAGGED_ROW` | 1 | One or more CSV rows had a field count different from the header | Check the source rows; the workbook is kept |
| `F_READBACK_MISMATCH` | 1 | Read-back sheet name or row count differs from what was written | Treat the workbook as unverified; re-run with a new output name |
| `F_XML_NOT_WELL_FORMED` | 1 | A workbook part did not parse on read-back | Treat the workbook as unverified; re-run with a new output name |
| `E_USAGE` | 2 | Wrong arguments or unknown flag | Show the command line |
| `E_SHEET_NAME` | 2 | Sheet name longer than 31 characters, empty, containing `[ ] : * ? /` or control characters, or starting or ending with an apostrophe | Ask for another name |
| `E_OUTPUT_PATH` | 2 | Output does not end in `.xlsx`, or its folder does not exist | Ask for a corrected path |
| `E_OUTPUT_EXISTS` | 2 | Output path already exists (including the input path) | Ask for a new name; never delete the old file |
| `E_INPUT_MISSING` | 2 | Input path is not a file | Ask for the path |
| `E_INPUT_TOO_LARGE` | 2 | Input is over 2,097,152 bytes | Ask the user to split the file |
| `E_INPUT_FORMAT` | 2 | Extension is not `.csv` or `.json`, text is not UTF-8, CSV has no header, or the file does not parse | Report the cause; ask for a corrected file |
| `E_JSON_SHAPE` | 2 | JSON is not a non-empty array of flat objects, a value is nested, a number is not finite, or the objects have no fields | Report the item position |
| `E_LIMIT` | 2 | More than 1,048,575 data rows or 16,384 columns | Ask the user to split the data |
| `E_XML_CHAR` | 2 | A value contains a character XML 1.0 cannot carry | Ask the user to remove the character |
| `E_XML_DTD` | 2 | A workbook part contains a DOCTYPE or ENTITY declaration (in UTF-8, UTF-16LE or UTF-16BE form), or starts with a UTF-16 or UTF-32 byte order mark; the output file is removed | Treat as a script defect; re-run with a new output name |
| `E_IO` | 2 | The input could not be read or the output could not be written | Check permissions and disk space |

## Refuse / stop when

- The input is not `.csv` or `.json`, is not UTF-8, or is over 2 MB. Stop and say which rule failed.
- The user asks to overwrite an existing file. Stop; offer a new output name. The script cannot overwrite.
- The user asks for formulas, charts, macros, pivot tables, colors, number formats, or edits to an existing `.xlsx`. Stop; this skill writes plain values and a bold header only.
- The user asks to read a `.xlsx` for analysis. Stop; this skill writes workbooks only.
- Input path or output path is missing. Reply with this numbered list and stop:
  1. Path to the input file (`.csv` or `.json`)?
  2. Path for the new output file (`.xlsx`, not yet existing)?
  3. Sheet name, or keep `Sheet1`?

## Script contract (type A)

- Command line (run from the skill folder):
  `python -I scripts/to_xlsx.py <input-file> <output-file.xlsx> [--sheet NAME]`
- Arguments: `<input-file>` is the user's `.csv` or `.json` file; `<output-file.xlsx>` is a new path; `--sheet NAME` is optional.
- Output keys: see Output contract. Error keys on stderr: `status` (always `error`), `code`, `message`.
- Exit codes: `0` status `ok`; `1` status `findings` (workbook written); `2` usage or input error (no workbook left behind).
- The script reads the input only, writes exactly one new file, and reads that file back. It uses no network, no subprocess, and no macros.

## Shipped files

- `scripts/to_xlsx.py`: the converter described above.
- `fixtures/sample_expenses.csv`: five-column CSV with numbers, text and an empty cell, for a smoke run.
- `fixtures/sample_records.json`: two flat JSON objects with a float, a null, a boolean and a ZIP-like text value.
- `fixtures/ragged_rows.csv`: CSV with one long row and one short row, for the `F_RAGGED_ROW` path.
- `LICENSE.txt`: Apache-2.0 license text.
- `SKILL.md`: this file.
