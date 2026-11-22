# table-to-markdown

## One line

Turns a CSV, TSV or first HTML table into an aligned Markdown table, with pipe characters escaped and short rows flagged.

## What it does

The script reads one text file and writes one Markdown table. It picks the format from the text itself: a case-insensitive `<table` means HTML, otherwise a first line with more tab characters than commas means TSV, and everything else is read as CSV. For HTML it takes only the first top-level table and skips any table nested inside it or placed after it. Every cell is trimmed, and runs of whitespace, including line breaks inside quoted CSV cells, collapse to one space. Pipe characters are escaped so they stay inside their cell. Each column is padded to its widest cell. Text columns are left-aligned; with the right-alignment flag, a column whose non-empty data cells all look like numbers (optional dollar sign, thousands commas, decimals, percent sign) is right-aligned. A row shorter than the widest row is padded with empty cells and reported as RAGGED_ROW, and a blank header cell is reported as EMPTY_HEADER. The table goes to stdout or to a new file that the script will not overwrite. One JSON status line goes to stderr, and the exit code says whether the table is clean (0), has findings (1), or was not written (2).

## When to use

- A table exported from a spreadsheet or downloaded as CSV has to sit inside a README, a changelog, a wiki page or a generated report.
- A pasted HTML page has several tables and the first one is the one wanted.
- A table must be checked for uneven rows before it is published, and the RAGGED_ROW list shows which row numbers are short.

## When not to use

- The input is an .xlsx, .ods, Word or PDF file. The script reads plain text only.
- The table needs totals, sorting, unit conversion or reshaping. The script never calculates.
- The HTML table uses colspan or rowspan, because spans are not expanded and cells would shift.
- The output must replace an existing file. The script refuses to overwrite.

## Requirements

Python 3.9 or newer with the standard library only. No network access, no subprocess, no third-party package. Run it from the skill folder with `python -I scripts/table_to_md.py <input-file>`.

## Example

Run on the bundled fixture with right alignment on. Stdout:

```
| item      | quantity | unit_price | note      |
| :-------- | -------: | ---------: | :-------- |
| Widget A  |        4 |       2.50 | in stock  |
| Gear \| B |       12 |      10.00 | backorder |
| Spring    |        5 |       0.75 |           |
| Bolt      |     1200 |       0.05 |           |
| Cable     |        3 |    1250.00 | fragile   |
```

Stderr, exit code 1:

```
{"status": "findings", "rows": 5, "columns": 4, "findings": [{"code": "RAGGED_ROW", "row": 4, "cells": 3, "expected": 4}]}
```

## Limits

- Column width counts characters, not display width, so wide East Asian characters and emoji will look misaligned in a monospace view.
- The input is capped at 2 MB and the table at 60 columns (working value). Larger files stop with an error.
- A CSV cell longer than the csv module default field limit (128 KB) stops with PARSE_ERROR.
- Rows in which every cell is blank are dropped without a finding.
- HTML: only the first top-level table is read, colspan and rowspan are ignored, and markup inside cells is reduced to its text.
- The script does not check that the figures are right, that the headers mean what the author intended, or how a given Markdown renderer will display the result.
- Right alignment is decided per column from the data cells. A numeric column with an empty body is left-aligned.
- The script does not verify visual equality with the source page or deliverability of the output.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
