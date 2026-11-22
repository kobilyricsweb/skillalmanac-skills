# XLSX to CSV export

## One line

Exports every worksheet of an .xlsx workbook to its own CSV file using only the Python standard library, keeping stored numbers exact.

## What it does

The skill runs one script, `scripts/xlsx_to_csv.py`, against a workbook of 2 MB or less. The script opens the file as a zip package, reads the shared strings, the cell styles and the workbook sheet list, and then writes one new CSV per worksheet into a folder you name. A number cell is copied as the text that Excel stored in the file, so a value such as 0.123456789012345 keeps all fifteen digits. Date cells are written as serial numbers by default; a single flag turns them into ISO dates or date-times. Formula cells contribute their cached results, because the script never recalculates. Cells that hold an error value, such as #DIV/0!, are written as that text and reported. Formula cells with no cached result are written blank and reported. The script prints one JSON line that lists each sheet, its row and column counts, its formula count and the findings. Exit codes separate a clean export from an export with findings and from a refused input.

## When to use

Use it when Excel is not installed on the machine that holds the workbook, when a workflow needs one CSV per sheet, or when someone must confirm that cached formula results are present before a CSV goes into a loader. It suits a single workbook of modest size where a reviewer wants the exact stored digits and a list of every error cell.

## When not to use

Do not use it for .xls, .xlsb, .xlsm or .ods files, which the script does not handle as supported input. Do not use it to write or edit a workbook, to convert CSV back to Excel, or to recalculate formulas. It is not the right tool for a workbook above 2 MB, for a sheet with more than 100,000 rows, or for a file that is encrypted with a password.

## Requirements

Python 3.9 or later, with the standard library only. No network access and no install step. The script runs with the `-I` flag so that no file in the current folder can shadow a standard module. The output folder must already exist and must not hold a CSV with the same name as a sheet.

## Example

Command, with the user's paths substituted:

```
python -I "<skill-folder>/scripts/xlsx_to_csv.py" "<input-file>" "<output-dir>"
```

Run on the two-sheet smoke workbook built by `fixtures/build_fixture.py`. Output, verbatim from the run:

```
{"status": "findings", "sheets": [{"sheet": "Prices", "file": "Prices.csv", "rows": 4, "columns": 2, "formula_cells": 1}, {"sheet": "Q1 Rates", "file": "Q1 Rates.csv", "rows": 4, "columns": 2, "formula_cells": 1}], "skipped_sheets": [], "findings_total": 1, "findings": [{"code": "F_ERROR_VALUE", "sheet": "Q1 Rates", "cell": "B4"}]}
```

Exit code 1. Prices.csv:

```
Item,Rate
Alpha,0.123456789012345
Beta,1234567890.12345
Doubled,0.24691357802469
```

Q1 Rates.csv:

```
Code,Value
x,2.71828182845905
y,45658
z,#DIV/0!
```

## Limits

The script does not recalculate formulas, so a stale cached value is exported as it stands. It does not detect date formats perfectly: it reads the number-format code and treats any code containing y, m, d, h or s outside quotes and brackets as a date. It does not escape CSV formula injection, so a text cell that starts with an equals sign is written as is. It does not check sheet names against Excel rules and does not special-case Windows reserved device names such as CON. Chart sheets are listed as skipped, not exported. Hidden sheets are exported. Macros, pivot caches and external links are ignored. If a write fails after some CSV files were created, the earlier files remain in the output folder. Reading an uncommon but valid workbook layout may produce an error that the script reports as malformed XML.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
