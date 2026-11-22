---
name: xlsx-to-csv-export
description: Exports each worksheet of an .xlsx workbook to its own CSV file with the Python standard library only, copying stored numbers digit for digit and listing formula and error cells. Use when Excel is not installed and a user needs one CSV per sheet from a workbook of up to 2 MB, or needs cached formula results checked before a CSV goes downstream. Do not use for .xls, .xlsb, .xlsm or .ods files, for writing or editing workbooks, for converting CSV back to Excel, or for recalculating formulas.
license: Apache-2.0
compatibility: Python 3.9+ standard library only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# XLSX to CSV export

Type A skill. The script [scripts/xlsx_to_csv.py](scripts/xlsx_to_csv.py) does the export. The agent checks intake, runs the script once, reads its JSON result and reports it in the output contract below. The agent never edits the workbook and never reads numbers out of it by hand.

## Workflow

1. Check intake. Required: `<input-file>`, a path to an .xlsx file of 2 MB (2,097,152 bytes) or less, and `<output-dir>`, an existing folder. Output: one intake line with the file name, its size in bytes and the output folder. If a required fact is missing, stop and use the numbered question list in the refuse section.
2. Run the export once, without flags. Output: the one-line JSON result from the script, saved for the report.
3. Read the exit code and choose the branch in the decision table. Output: one status word, `complete`, `partial` or `stopped`.
4. Only when the user asks for dates as text, rerun with `--convert-dates` into a new, empty output folder. Never rerun into the same folder, because existing CSV files are never overwritten. Output: a second JSON result, reported as the second export.
5. Write the report in the output contract. Output: the export table, the findings table and the skipped-sheets line.

## Decision table

| Condition | Exit code | Action |
|---|---|---|
| All sheets exported, no findings | 0 | Status `complete`. Report the export table. |
| All sheets exported, one or more findings | 1 | Status `complete`. Report the export table and the findings table. Do not repair the workbook. |
| Input larger than 2 MB | 2 | Status `stopped`. Ask for a smaller workbook. |
| More than 500 zip entries, one entry over 10 MB uncompressed, total uncompressed size over 20 MB, or more than 100 worksheets (working values) | 2 | Status `stopped`. Quote the message line. |
| A sheet with more than 100,000 rows or more than 1,000 columns, or rows times columns over 5,000,000 (working values) | 2 | Status `stopped`. Nothing is written. |
| Output file with the same name already exists | 2 | Status `stopped`. Ask for a new output folder. Never delete or rename the existing file. |
| Not a zip package, encrypted, DTD or entity declaration (any encoding, including UTF-16 or UTF-32 byte order mark), malformed XML, bad shared-string index | 2 | Status `stopped`. Report the message. |
| Export written, but the user also asked for an upload or a recalculation | 0 or 1 | Status `partial`. Do the export, refuse the other clause, list it under Open questions. |

## Script contract

Command line (the agent substitutes the user's paths):

```
python -I "<skill-folder>/scripts/xlsx_to_csv.py" "<input-file>" "<output-dir>"
```

Add `--convert-dates` as the last argument only when step 4 applies.

Arguments:
- `<input-file>`: the .xlsx file. Read only.
- `<output-dir>`: an existing directory. One `<sheet name>.csv` is created per worksheet. Characters `\ / : * ? " < > |` and control characters become `_`. Duplicate names get `_2`, `_3`, and so on.
- `--convert-dates`: optional. Date and time formats are written as `YYYY-MM-DD`, or `YYYY-MM-DD HH:MM:SS` when a time part exists. Without the flag, the stored serial number is written.

Output on stdout, one JSON line on success: `status` (`ok` or `findings`), `sheets` (list of objects with `sheet`, `file`, `rows`, `columns`, `formula_cells`), `skipped_sheets` (chart sheets and other non-worksheet entries), `findings_total`, and `findings` (up to 50 objects with `code`, `sheet`, `cell`).

On failure, one JSON line: `{"status": "error", "message": "..."}`.

Finding codes:

| Code | Meaning | What the CSV holds |
|---|---|---|
| F_FORMULA_NO_CACHE | Formula cell has no cached result | Empty cell |
| F_ERROR_VALUE | Cell holds an error value | The error text, such as `#DIV/0!` |

Exit codes: 0 export written, no findings. 1 export written, findings listed. 2 usage or input error, nothing written.

## Output contract

Report exactly these headings, in this order.

`## Export result`: a table with columns Sheet | File | Rows | Columns | Formula cells, one row per entry in `sheets`.

`## Findings`: a table with columns Code | Sheet | Cell, one row per finding. If `findings_total` is 0, write "No findings." If it is above 50, add a line saying how many were not listed.

`## Skipped sheets`: a comma-separated list from `skipped_sheets`, or "None".

`## Open questions`: a numbered list, or "None". Put refused clauses and missing intake facts here.

Last line: `Status: complete`, `Status: partial` or `Status: stopped`.

## Refuse / stop when

- The file is not .xlsx (.xls, .xlsb, .xlsm, .ods, .numbers, .csv). Stop with status `stopped` and name the format.
- The workbook is password protected or encrypted. The script exits 2 with "not a readable .xlsx zip package". Report it and stop.
- The user asks to overwrite an existing CSV. Refuse that clause only, ask for a new output folder, keep the rest of the export.
- The user asks to send the workbook or the CSV files to a web service, an email or a URL. Refuse that clause only; the export stays local.
- The user asks to recalculate formulas or change values. The export shows cached results only. Refuse that clause and list it.
- Intake is incomplete. Reply with a numbered question list: 1. Path to the .xlsx file? 2. Path to an existing output folder? 3. Dates as text (`--convert-dates`) or serial numbers? Status `stopped` until answered.

## Files in this skill

- [scripts/xlsx_to_csv.py](scripts/xlsx_to_csv.py): the export script described above.
- [fixtures/build_fixture.py](fixtures/build_fixture.py): writes a two-sheet smoke workbook to a path you give it. Add `--hostile` to write a UTF-16 DOCTYPE test workbook instead, which the script must refuse. Use it to test the script before running on a user file. It must not be run inside the skill folder.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
