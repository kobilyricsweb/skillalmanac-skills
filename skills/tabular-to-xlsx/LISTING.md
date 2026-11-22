# Tabular to XLSX

## One line

Writes a new Excel workbook from a CSV or JSON record file with the Python standard library, for machines where Excel is not installed.

## What it does

The skill runs one script, `scripts/to_xlsx.py`, on a CSV file (first row is the header) or a JSON array of flat objects. It writes exactly one new `.xlsx` file with one worksheet. The header row is bold. Plain decimal numbers such as `3` or `4.50` become numeric cells. Everything else, including dates, ZIP codes with leading zeros, and text that looks like a formula, is stored as inline text, so a cell starting with an equals sign never becomes a live formula. Column widths follow the longest value in each column. The script refuses to overwrite a file, so a rerun needs a new name. After writing, it reads the workbook back, parses each internal part as XML, and counts the rows. Findings such as ragged CSV rows are reported with exit code 1 while the workbook is kept for review.

## When to use

Use it when someone has a CSV export or a JSON list of records and needs a file that opens in a spreadsheet program, and the machine cannot run Excel or a spreadsheet app. It suits small reporting tables, export hand-offs, and sanity checks of a data file before it goes to a colleague.

## When not to use

Do not use it to edit a workbook that already exists, to read `.xlsx` files for analysis, to add formulas, charts, pivot tables, macros, or number formats, or to convert a file into PDF or Word. Inputs over 2 MB are refused and must be split first.

## Requirements

Python 3.9 or newer. No third-party packages and no network access. The command is `python -I scripts/to_xlsx.py <input-file> <output-file.xlsx> [--sheet NAME]`, run from the skill folder.

## Example

Run on the shipped fixture `fixtures/sample_expenses.csv`, output name `tabular_listing_run.xlsx`, from a scratch folder:

```
{"status": "ok", "output": "tabular_listing_run.xlsx", "sheet": "Sheet1", "columns": 5, "data_rows": 3, "read_back_rows": 4, "ragged_rows": 0, "findings": []}
```

The output reports three data rows plus the header, which is the read-back count of four. Running the same command again with the same output name exits with code 2 and `E_OUTPUT_EXISTS`.

## Limits

- Numbers keep their typed value. A value such as `4.50` is stored as 4.5 in the cell, and text is not reformatted.
- At most 15 significant digits are stored as numbers. Longer numbers, numbers with leading zeros, thousands separators, percent signs, and exponent forms stay text.
- Dates are text. No date type or date format is written.
- Only the bold header and column widths are styled. No freeze panes, filters, table objects, or colors are written.
- The read-back check confirms that the zip container and XML parse and that the row count matches. It does not confirm that Excel or any other program opens the file without a repair prompt.
- It does not check visual layout, the meaning of values, duplicate headers, or whether the data is correct.
- JSON values that are strings stay text even when they look numeric.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
