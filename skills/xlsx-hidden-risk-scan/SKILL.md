---
name: "xlsx-hidden-risk-scan"
description: "Scans an .xlsx workbook for hidden risk: hidden and very hidden sheets, defined names, external link parts, error-valued cells such as #DIV/0!, and formulas that embed large literal numbers. Use when a spreadsheet must be checked before it is shared, reviewed, or reused, or when someone asks what a workbook hides from view. Do not use for editing or recalculating a workbook, for .xls or .csv files, or for judging whether formula logic is correct."
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# xlsx-hidden-risk-scan

Run a read-only scan of one `.xlsx` file and report the signals a reviewer
usually misses: sheets hidden from the tab bar, external workbook links, cells
showing error values, and formulas that contain large typed-in numbers. The
script reads the package with `zipfile` and `xml.etree`. It never recalculates
formulas, so cached values are reported as stored in the file.

## Inputs

- One path to an `.xlsx` file, 2 MB or smaller (larger files are refused).
- Optional `--threshold N`. Default 1000 (working value, not a standard).
- Optional `--out PATH` for the JSON report. Never the input path.

If the user has a `.xlsm`, `.xls`, or `.csv`, stop and say so (see Refuse list).

## Workflow

1. **Confirm the file.** Check that the path exists and ends in `.xlsx`.
   Output: the file name and size in bytes.
2. **Run the scan** with the exact command below. Keep stdout or the `--out` file.
   Output: the exit code (0, 1, or 2) and the JSON report.
3. **Read the summary block.** Copy `hidden_sheet_count`, `external_link_count`,
   `error_cell_count`, `large_constant_count`, and `findings` into the reply.
   Output: a five-line count table.
4. **Map findings to actions** using the decision table below. Output: one row per
   non-zero count with the recommended action.
5. **Check truncation.** If `truncated_lists` is not empty, say which lists were
   cut at 100 items and that the summary counts are complete.
   Output: one sentence.
6. **Write the reply** in the output contract below. Stop there. Do not fix the
   workbook.

## Command

```
python -I scripts/xlsx_scan.py "<path to workbook>.xlsx" --threshold 1000
```

Add `--out "<path to report>.json"` to save the report instead of printing it.

## Script contract (scripts/xlsx_scan.py)

Arguments: `input` (required path), `--threshold` (number 0 or more, default
1000), `--out` (optional output path, refused when it is the input file).

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Scan completed, no findings |
| 1 | Scan completed, `summary.findings` is above 0 |
| 2 | Usage or input error; one line of JSON `{"error": "..."}` on stderr |

JSON keys on success: `tool`, `version`, `input` (base name only), `threshold`,
`summary` (`sheet_count`, `hidden_sheet_count`, `defined_name_count`,
`hidden_defined_name_count`, `external_link_count`, `formula_count`,
`error_cell_count`, `large_constant_count`, `findings`), `sheets`,
`defined_names`, `external_links`, `error_cells`, `large_constants`,
`truncated_lists`.

`findings` = hidden sheets + external link parts + error cells + large
constants + hidden defined names.

## Decision table

| Count that is above 0 | Meaning | Recommended action |
|-----------------------|---------|--------------------|
| `hidden_sheet_count` | Sheet has state hidden or veryHidden | List the sheet names; ask the owner whether the data may be shared |
| `external_link_count` | Formulas read another workbook | List the `target` values; check the linked file is expected |
| `error_cell_count` | Cached value is an error such as #DIV/0! or #REF! | List the first 10 cells; note the sheet and cell |
| `large_constant_count` | Formula contains a number above the threshold | Show the first 5 formulas; suggest moving the number to a labelled input cell |
| `hidden_defined_name_count` | Defined name has hidden set to 1 | List the names and `refers_to` values |

Threshold choice: keep 1000 for general review. Use 100 for budget or rate
sheets where any typed-in rate matters. Use 1000000 to see only very large
literals. These three values are working values.

## Output contract (reply to the user)

```
## Hidden-risk scan: <file name>
Exit code: <0|1|2>, threshold <N>

| Signal | Count |
|--------|-------|
| Hidden sheets | <n> |
| External links | <n> |
| Error cells | <n> |
| Large constants | <n> |
| Hidden defined names | <n> |
| Findings | <n> |

### Findings
- <one bullet per non-zero signal: sheet, cell or part, value, action>

### Not checked
- Formula logic, recalculated values, macros, and cell content outside the cached values.
```

If exit code is 2, the reply is only the error line and one sentence on what to fix.

## Refuse / stop when

- The file is `.xlsm`, `.xls`, `.ods`, `.csv`, or `.tsv`. The script reads only `.xlsx` packages.
- The file is larger than 2 MB or has more than 1000 zip entries. Say the file was not scanned.
- The user asks for a fix, a recalculation, or a changed copy. The skill only reports.
- The `--out` path is the input file. Pick another path and rerun.
- The user asks whether a formula is correct. The scan does not evaluate logic.
- The workbook is password protected. The script exits 2 and the reply stops.

## Files

- `scripts/xlsx_scan.py` - the scanner described above.
- `LICENSE.txt` - Apache License 2.0.
