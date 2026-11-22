# csv-delimiter-converter

## One line

Rewrites delimited text between comma, tab, semicolon and pipe, checks that every cell value survives the change, and never overwrites a file.

## What it does

Some import tools accept only one delimiter. A comma file that a spreadsheet or database loader expects as tab-separated fails in ways that are hard to spot, because the rows look fine to a person. This skill runs a small standard-library Python script that reads the input file, detects which of the four supported delimiters it uses (or takes one given with a flag), parses it with the csv module, and writes the same records with the target delimiter. Quoted cells keep their quotes where the target format needs them, so a cell that holds a comma or a line break stays one cell.

Before anything is written, the script parses its own output and compares every cell with the original. Only a passing comparison produces a file. The script also lists ragged records (rows whose column count differs from the file's usual count) and records that contain embedded line breaks, so the person can decide what to fix. The output file must be new; an existing file is refused.

## When to use

- A comma-separated export must be imported as tab-separated, or the reverse.
- A semicolon file from a European export must reach a tool that expects commas.
- An import fails with wrong column counts and the cause is a delimiter mismatch.
- A converted copy needs a cell-by-cell check against the original before it is used.

## When not to use

- Excel workbooks, JSON, XML, or fixed-width text. The script reads delimited text only.
- Changing the content of cells, such as dates, currency or names.
- Repairing ragged rows. They are reported and kept as they are.
- Any delimiter other than the four supported ones.
- Converting a file in place. The output must be a different new file.

## Requirements

- Python 3.9 or newer. The script uses only the standard library and makes no network calls.
- An input file of at most 2 MB in UTF-8 encoding.
- A writable folder for the output file.
- A text-capable agent or a terminal to run the command line in the SKILL.md script contract.

## Example

Command run on the bundled comma fixture, output to a scratch file and the printed result:

```
python -I scripts/delim_convert.py fixtures/sample_comma.csv <output-file> --to tab
{"status": "ok", "input_delimiter": "comma", "delimiter_source": "detected", "output_delimiter": "tab", "records": 4, "modal_columns": 3, "ragged_records": 0, "ragged_record_numbers": [], "embedded_newline_records": 1, "embedded_newline_record_numbers": [2], "cells_compared": 12, "values_equal": true, "output_written": true}
```

The exit code is 0. The one record with a line break (record 2) is reported as information and kept as one cell.

## Limits

- Verifies only that parsed cell values match after conversion. It does not check the meaning of values, number or date formats, or whether the importing tool accepts the result.
- Delimiter detection is a heuristic based on column-count uniformity. A file where another delimiter looks more uniform can be detected wrongly; the flag `--from` forces the source delimiter.
- A UTF-8 byte order mark is removed from the output. Line endings in the output are LF.
- Inputs above 2 MB, non-UTF-8 files, and single cells larger than the csv module field limit are refused with exit code 2.
- The 20-item cap on listed record numbers is a working value.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
