---
name: xlsx-cell-diff
description: Compares two .xlsx workbooks sheet by sheet and lists every cell whose value or formula differs, plus sheets added or removed, using a stdlib-only script that writes a JSON report. Use when someone asks to compare two spreadsheet files, find what changed between two versions of a workbook, or audit edits made to a budget, price list or report. Do not use for formatting, charts, macros, .xls or .csv files, online spreadsheet links, or for merging or editing workbooks.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# XLSX Cell Diff

Compares two .xlsx workbooks with `scripts/xlsx_diff.py` and turns the JSON report into a change summary. The script reads both files in place with zipfile and xml.etree, matches sheets by name, and compares each cell's stored value and formula. Formatting is ignored.

Shipped files: `scripts/xlsx_diff.py` (the comparison script), `fixtures/make_fixtures.py` (builds a smoke-test pair of workbooks at runtime), and `LICENSE.txt` (Apache-2.0).

## Workflow

1. Intake. Collect three paths: the old workbook, the new workbook, and a report file name that does not exist yet. If any is missing, reply with this numbered list and stop: 1. Old workbook path. 2. New workbook path. 3. New report file name. Output: the three confirmed paths.
2. Check the inputs. Each workbook must end in `.xlsx`, be 2 MB (2,097,152 bytes) or smaller, and the report folder must already exist. Output: a pass, or a stop message that names the failed check.
3. Run the script from the skill folder with the command in the script contract below. Output: the one-line stdout JSON and the exit code. Branch on the exit code using the decision table.
4. Read the report file. Copy counts from its `summary` object and take rows from its `changes`, `sheets_added` and `sheets_removed` arrays. Do not count rows from memory. Output: the data for the three output sections.
5. Write the reply using the output contract. Output: the four headings in the order given.

## Decision and threshold table

| Check | Value | Result |
|---|---|---|
| Input file size | over 2,097,152 bytes (2 MB) | Stop, exit 2, ask for a smaller copy. Brief cap. |
| Zip entries per workbook | over 2,000 | Exit 2. Working value. |
| Uncompressed size per workbook | over 33,554,432 bytes (32 MB) | Exit 2. Working value. |
| One XML part | over 16,777,216 bytes (16 MB) | Exit 2. Working value. |
| Non-empty cells per sheet | over 200,000 | Exit 2. Working value. |
| Report path already exists | any | Exit 2. Ask for a new name. Never overwrite. |
| Changed cells listed in the reply | more than 50 | List the first 50 in report order and state how many remain in the report. Working value. |
| Exit code 0 | no differences | Say that the workbooks match on values and formulas. |
| Exit code 1 | differences found | Write the full reply. |

Numeric cells are compared after trailing zeros are removed, so 1.50 and 1.5 match. Text is compared exactly, including case and spaces. Cached formula results are compared as stored; nothing is recalculated.

## Matching and change kinds

Sheets are matched by exact name, case-sensitive. A cell counts as present when it has a stored value or a formula; a styled cell with neither is ignored. Changes are listed by sheet in the old file's order, then by row and column. `added` and `removed` apply to cells on sheets present in both files. Cells on an added or removed sheet are not listed; the sheet appears only in the Sheets table.

| Change kind | Meaning | What the reply says |
|---|---|---|
| `value` | Same formula state, different stored value | The value changed; no formula change. |
| `formula` | Different formula text, same stored value | The logic changed but the stored result did not. Flag it for review. |
| `value+formula` | Both changed | Report both old and new. |
| `added` | Cell present only in the new file | A new entry; old columns show (none). |
| `removed` | Cell present only in the old file | A deleted entry; new columns show (none). |

## Output contract

Use these four headings, in this order.

### Summary
Table with columns `Measure | Count`. Rows, in this order: Sheets compared (length of `sheets_compared`), Sheets added (`summary.sheets_added`), Sheets removed (`summary.sheets_removed`), Cells changed (`summary.cells_changed`), Change: value, Change: formula, Change: value+formula, Change: added, Change: removed (each from `summary.by_change`).

### Changed cells
Table with columns `Sheet | Cell | Change | Old value | New value | Old formula | New formula`. One row per entry in `changes`, in report order. Write a null field as `(none)`. Apply the 50-row limit from the decision table.

### Sheets
Table with columns `Sheet | Status`. Status is `compared`, `added` or `removed`. List every name from `sheets_compared`, `sheets_added` and `sheets_removed`.

### Limits
Write these five points every time: formatting, fonts, fills, column widths, charts, images, comments, macros, data validation, named ranges and pivot tables are not compared; cached formula results are compared, not recalculated, so a file saved without recalculation can show stale results; a shared formula is compared by its shared-formula index, not by expanded text; a renamed sheet appears as one removed sheet and one added sheet; cells on an added or removed sheet are not listed; the sheet appears only in the Sheets table.

## Script contract (type A)

- Command line, run from the skill folder: `python -I scripts/xlsx_diff.py <old-xlsx> <new-xlsx> <report-json>`
- Arguments: exactly three positional paths and no options. The report path must not exist.
- Writes: one new report file, UTF-8 JSON with indent 2, created in exclusive-create mode. It never writes to either input. A failed write after creation can leave a partial file that the user must delete.
- stdout: one line of JSON with keys `status`, `cells_changed`, `sheets_added`, `sheets_removed`, `report`.
- stderr on exit 2: one line of JSON, `{"status": "error", "message": "..."}`.
- Status values: `differences_found`, `no_differences`, `error`.
- Report keys: `tool`, `version`, `old_file`, `new_file`, `sheets_compared`, `sheets_added`, `sheets_removed`, `summary` (with `sheets_added`, `sheets_removed`, `cells_changed`, `by_change`), and `changes`. Each change has `sheet`, `cell`, `change`, `old_value`, `new_value`, `old_formula`, `new_formula`.
- Change kinds: `value`, `formula`, `value+formula`, `added` (cell present only in the new file), `removed` (cell present only in the old file).
- Exit codes: 0 for `no_differences`, 1 for `differences_found`, 2 for `error` (usage, input or write failure).
- Smoke test: `python -I fixtures/make_fixtures.py <output-folder>` writes `old.xlsx` and `new.xlsx` into an existing folder. Those two files then go into the script command above. It also writes `hostile.xlsx`, a refusal fixture that the script must reject with exit 2; it is not part of the smoke pair.

## Refuse / stop when

- Either input does not end in `.xlsx`, for example `.xls`, `.xlsm`, `.csv`, or a link to an online spreadsheet. Stop and say which file is wrong.
- The script exits 2 for a corrupt, encrypted or over-cap workbook. Stop and quote the script's message. Do not try a different tool.
- The script reports that DTD or entity declarations are refused, or that UTF-16 and UTF-32 workbook parts are refused. Stop. Do not strip them, re-encode them and retry.
- The report path already exists or equals an input path. Stop and ask for a new name. Never overwrite and never delete a file.
- The request asks for formatting, fonts, fills, charts, images or comments to be compared. Refuse that part only. Deliver the cell diff and state under Limits that it was not compared.
- The request asks to change either workbook, merge them, or write changes back. Refuse. This skill only reports differences.
- Cell values contain personal data, such as names, account numbers or ID numbers. Show counts and cell references only, and do not quote the values.
