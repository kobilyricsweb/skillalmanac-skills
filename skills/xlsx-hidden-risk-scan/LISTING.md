# xlsx-hidden-risk-scan

## One line

Read-only scanner for one .xlsx workbook that lists hidden sheets, external link parts, error-valued cells, and formulas with large typed-in numbers.

## What it does

The skill runs a Python script that opens an .xlsx file as a zip package and reads the workbook part, the sheet relationships, the worksheet XML, and the external link parts. It reports every sheet whose state is hidden or veryHidden, every defined name with its scope and refers-to text, every external workbook link target, every cell whose stored value is an error such as #DIV/0! or #REF!, and every formula that contains a numeric literal above a threshold. The threshold defaults to 1000 and is a working value chosen for this skill, not a published standard.

The script never recalculates formulas. It reports cached values exactly as the file stores them, which is the value a reader of the file would see before any recalculation. It writes nothing unless an output path is given, and it refuses an output path that resolves to the input file. Output is a JSON report with a summary block, one list per signal, and a truncated_lists field that names any list cut at 100 items.

## When to use

Use it before a workbook leaves the team: a budget, a price sheet, or a monthly report that someone else will open. Use it when a reviewer asks what a file hides, for example a sheet that is hidden from the tab bar, or a link to a file on another drive. Use it when a numbers review finds an error value and you need every other error cell in the same pass.

## When not to use

Do not use it for macro-enabled files, for legacy .xls files, or for comma-separated text. Do not use it to check whether a formula is logically right, because the script does not evaluate formulas. Do not use it to repair a workbook; the skill only reports.

## Requirements

Python 3.9 or newer, standard library only. No network access and no packages to install. The input must be an .xlsx package of 2 MB or less. Password-protected workbooks are not zip packages and exit with code 2.

## Example

Smoke run on a small generated workbook with one hidden sheet and one #DIV/0! cell. Command: `python -I scripts/xlsx_scan.py smoke.xlsx`. Exit code 1.

```
{
  "tool": "xlsx_scan",
  "version": "0.1.0",
  "input": "smoke.xlsx",
  "threshold": 1000.0,
  "summary": {
    "sheet_count": 2,
    "hidden_sheet_count": 1,
    "defined_name_count": 1,
    "hidden_defined_name_count": 0,
    "external_link_count": 0,
    "formula_count": 3,
    "error_cell_count": 1,
    "large_constant_count": 1,
    "findings": 3
  },
  "sheets": [
    {
      "name": "Data",
      "index": 0,
      "state": "visible",
      "part": "xl/worksheets/sheet1.xml",
      "formula_count": 3,
      "error_count": 1,
      "scanned": true
    },
    {
      "name": "Old",
      "index": 1,
      "state": "hidden",
      "part": "xl/worksheets/sheet2.xml",
      "formula_count": 0,
      "error_count": 0,
      "scanned": true
    }
  ],
  "defined_names": [
    {
      "name": "Rate",
      "scope_index": 0,
      "hidden": false,
      "external_reference": false,
      "refers_to": "Data!$D$1*1000"
    }
  ],
  "external_links": [],
  "error_cells": [
    {
      "sheet": "Data",
      "cell": "B2",
      "error": "#DIV/0!"
    }
  ],
  "large_constants": [
    {
      "sheet": "Data",
      "cell": "C2",
      "constants": [
        "1500"
      ],
      "formula": "A2+1500"
    }
  ],
  "truncated_lists": []
}
```

## Limits

- Cached values only. A workbook saved by a tool that did not store values shows no error cells even when formulas would fail.
- Large-constant detection is a text heuristic on formula strings. It strips string literals, sheet prefixes, and cell references, then reads the remaining numbers. Function arguments such as a typed-in tax rate are caught; a number hidden in a named range is not, because defined names are listed but not parsed for constants.
- Lists stop at 100 items. Summary counts stay complete.
- Macros, data connections, pivot caches, and conditional formats are not reported.
- Workbooks with more than 1000 zip entries or more than 32 MB uncompressed are refused.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
