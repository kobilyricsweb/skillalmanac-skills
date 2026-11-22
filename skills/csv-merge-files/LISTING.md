# csv-merge-files

## One line

Stacks or joins several CSV files into one new CSV and reports per-file counts, duplicate keys and dropped rows.

## What it does

The skill runs a standard-library Python script over two or more CSV files. In stack mode it writes every data row under one header built from the union of all input headers, in first-seen order, and leaves a cell empty when its file lacks that column. An optional source column records each row's input file name. In join mode it joins the files in order on one key column, either inner (rows whose key appears in every file) or left (every row of the first file is kept). Each file's row count, duplicate key count and dropped row count are printed as one JSON line, so a merge that loses rows is visible instead of silent. The script refuses to overwrite an existing output file, refuses to write over an input, and caps each input at 2 MB.

## When to use

Use it when several exports share a layout, such as monthly order files that gained a column partway through the year, and the result must keep every row. Use it also when one file holds attributes (region, plan, owner) that must be added to another file by a shared identifier.

## When not to use

Do not use it for fuzzy or case-insensitive key matching, for spreadsheets with several sheets, for database tables, or for files larger than 2 MB each. It does not edit a CSV in place and does not reformat numbers or dates.

## Requirements

Python 3.9 or later. No third-party packages and no network access. The input files must be UTF-8 text with a unique, non-empty header row.

## Example

Command, run from the skill folder with the output written to a new file named `stacked.csv` in a scratch folder:

```
python -I scripts/csv_merge.py stack --source-column source_file --output stacked.csv fixtures/orders_jan.csv fixtures/orders_feb.csv fixtures/orders_mar.csv
```

Report line (stdout, exit code 0):

```
{"mode": "stack", "columns": 5, "files": [{"file": "orders_jan.csv", "rows": 3}, {"file": "orders_feb.csv", "rows": 2}, {"file": "orders_mar.csv", "rows": 2}], "rows_written": 7, "rows_dropped": 0}
```

Contents of `stacked.csv`:

```
order_id,customer,amount,coupon,source_file
1001,Ana Lopez,25.00,,orders_jan.csv
1002,Ben Carter,40.50,,orders_jan.csv
1003,Ana Lopez,12.75,,orders_jan.csv
1004,Cara Diaz,30.00,SPRING10,orders_feb.csv
1005,Ben Carter,18.00,,orders_feb.csv
1005,Ben Carter,18.00,,orders_mar.csv
1006,Dan Ortiz,22.40,,orders_mar.csv
```

Order 1005 appears twice because feb and mar both contain it; stack mode does not report repeats.

## Limits

The script checks structure only: header names, cell counts, encoding and file size. It does not check whether a key means the same thing in each file, whether amounts or dates are valid, or whether a duplicate key is an error or a legitimate repeat. Keys are compared after trimming spaces and are otherwise exact. Empty key cells never match. Blank lines are skipped. Duplicate keys in join mode multiply output rows, and the report counts them but does not remove them. The output is plain text; the script does not check that a spreadsheet program will open it cleanly. Security, privacy of the data itself, and the correctness of the source exports are outside what this tool verifies.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
