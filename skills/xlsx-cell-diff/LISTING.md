# xlsx-cell-diff

## One line

Lists the cells and sheets whose stored values or formulas differ between two .xlsx workbooks, written to a JSON report.

## What it does

The script opens each workbook as a zip container, reads the sheet list, the shared strings and every worksheet's cells, and compares the two files sheet by sheet. Sheets are matched by exact name, so a renamed sheet appears as one removal and one addition. For each cell present in either file, it compares the stored value and the formula text, then records one of five change kinds: value, formula, value+formula, added or removed. Formatting, fonts, fills and column widths are ignored, so a change that only restyles a cell produces no output. Numeric values are compared after trailing zeros are removed, so 1.50 and 1.5 match, while text is compared exactly. Results go to a new JSON report whose path must not exist yet. The script never overwrites a file and never writes to either input. It prints one line of JSON to the console and exits with 0 when the workbooks match, 1 when differences exist, and 2 for a usage or input problem. Inputs are capped at 2 MB, and the parser refuses any XML that declares a DTD or entities.

## When to use

Use it when two versions of one workbook need a cell-level comparison: a budget before and after a review round, a price list exported twice, or a report regenerated from changed inputs. It fits a question such as which cells changed, what their old and new values were, and whether a formula was edited without changing its stored result. The formula kind exists for that last case. The sheet lists also show which sheets were added or removed.

## When not to use

Do not use it for formatting audits, charts, images, comments, macros, data validation or pivot tables, because none of those are read. Do not use it for .xls, .xlsm or .csv files, for online spreadsheet links, or for workbooks above 2 MB. It does not recalculate formulas, so a workbook saved without recalculation can show stale results. It is not a merge tool and cannot write changes back into either file.

## Requirements

Python 3.9 or later, standard library only. No network access and no subprocess calls. The report folder must already exist. The smoke pair is produced by `fixtures/make_fixtures.py`, which needs an existing output folder.

## Example

Run from the folder that holds the smoke pair built by `fixtures/make_fixtures.py`:

```
python -I <skill-folder>/scripts/xlsx_diff.py old.xlsx new.xlsx report.json
```

Console line, exit code 1:

```
{"status": "differences_found", "cells_changed": 4, "sheets_added": 1, "sheets_removed": 0, "report": "report.json"}
```

Contents of `report.json`:

```json
{
  "tool": "xlsx_diff",
  "version": "0.1.0",
  "old_file": "old.xlsx",
  "new_file": "new.xlsx",
  "sheets_compared": [
    "Budget",
    "Notes"
  ],
  "sheets_added": [
    "Summary"
  ],
  "sheets_removed": [],
  "summary": {
    "sheets_added": 1,
    "sheets_removed": 0,
    "cells_changed": 4,
    "by_change": {
      "value": 3,
      "formula": 1,
      "value+formula": 0,
      "added": 0,
      "removed": 0
    }
  },
  "changes": [
    {
      "sheet": "Budget",
      "cell": "A2",
      "change": "value",
      "old_value": "Rent",
      "new_value": "Housing",
      "old_formula": null,
      "new_formula": null
    },
    {
      "sheet": "Budget",
      "cell": "A3",
      "change": "value",
      "old_value": "Food",
      "new_value": "Groceries",
      "old_formula": null,
      "new_formula": null
    },
    {
      "sheet": "Budget",
      "cell": "C4",
      "change": "formula",
      "old_value": "750",
      "new_value": "750",
      "old_formula": "B4*0.5",
      "new_formula": "B4/2"
    },
    {
      "sheet": "Budget",
      "cell": "B5",
      "change": "value",
      "old_value": "0.05",
      "new_value": "0.06",
      "old_formula": null,
      "new_formula": null
    }
  ]
}
```

## Limits

- Only stored values and formula text are compared. Formatting, charts, images, comments, macros, data validation, named ranges and pivot tables are not read.
- Cached formula results are compared as stored, never recalculated.
- Cells on an added or removed sheet are not listed; the sheet appears only in the Sheets table. `added` and `removed` apply to cells on sheets present in both files.
- Shared formulas are compared by their shared-formula index. An edit to a shared formula shows on its master cell, while dependent cells that reuse the index show no change.
- Caps: 2 MB per input file (brief cap), 2,000 zip entries, 32 MB uncompressed and 16 MB per XML part per workbook, and 200,000 non-empty cells per sheet (working values).
- A failed write after the report file is created can leave a partial file, which the user must delete before a rerun.
- The smoke test used only workbooks built at runtime by the fixture helper. Output from other spreadsheet programs has not been checked.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
