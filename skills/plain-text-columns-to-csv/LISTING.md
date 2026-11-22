# Plain-text columns to CSV

## One line

Turns a plain-text table with aligned columns, or with tabs and repeated spaces, into a new CSV file and lists the rows whose layout does not match the header.

## What it does

The skill runs a small Python script on a text report. In its default fixed mode, the script reads the header line, takes the first character of each word as a column start, and slices every data line at those positions. Rule lines such as a row of dashes under the header are skipped and counted. Blank lines are counted too. Each data line that has no text at or after the last column start is reported as a short row, and each line where a word starts in a gap between columns, or crosses a column start, is reported as a misaligned row. In split mode, the script splits each line on tabs or on two or more spaces and reports lines whose field count differs from the header. The output is a new CSV file that refuses to overwrite anything, and a one-line JSON summary with row and column counts and the findings. The agent then writes a short report that applies a threshold table to the flagged share.

## When to use

Use it when a report, export, or console print arrives as a text table and the user needs rows and columns in a spreadsheet or database. It fits monthly summaries pasted from a terminal, fixed-width reports from older systems, and tables copied from plain-text email.

## When not to use

Do not use it for Excel, PDF, Word, or JSON inputs. Do not use it when the values need to be checked, typed, totaled, or corrected, because the script only checks layout. Do not use it to replace an existing CSV, since the script refuses to write over any existing path.

## Requirements

Python 3.9 or later, standard library only. No network access and no subprocess calls. The input must be UTF-8 text no larger than 2,097,152 bytes. The output path must not exist yet.

## Example

Command on the fixture report. The run wrote the CSV to a scratch folder, and the JSON shows only the base name:

```
python -I scripts/text_table_csv.py fixtures/sample_report.txt sample_out.csv
```

Printed JSON line and exit code 1:

```
{"status": "findings", "input": "sample_report.txt", "output": "sample_out.csv", "mode": "fixed", "header_line": 1, "columns": 4, "data_rows": 10, "blank_lines": 0, "rule_lines": 1, "findings": [{"line": 10, "code": "short_row", "detail": "row has no text at or after the last column start"}]}
```

Contents of the CSV written by that run:

```
Region,Units,Revenue,Rep
North,1204,"$18,420",Ana Ruiz
South,980,"$12,515",Ben Okafor
East,1150,"$16,090",Chloe Park
West,742,"$9,870",Dev Patel
Central,1333,"$21,004",Eli Moreau
Coastal,611,"$7,140",Fatima Noor
Highlands,508,"$6,205",Gus Halvorsen
Tokyo,418,,
Lisbon,877,"$10,662",Sami Lund
Oslo,390,"$4,880",Rina Dass
```

The Tokyo row has no revenue or representative. The report flags it as a short row, and the agent reports 1 flagged row out of 10 data rows, which is 10.0 percent. That is above the 5 percent working threshold, so the agent's status is partial and the user is asked to confirm the layout before the CSV is treated as final.

## Limits

The script does not check values, data types, totals, currency formats, or the meaning of a column. It cannot recover values that a report left out. Fixed mode treats a single space inside a column name as a column break, so names with spaces need split mode. Right-aligned numbers may be flagged as misaligned even when they belong to the correct column. The 5 percent threshold and the 2 MB limit are working values. The script was run once on the included fixtures. It has not been run on real reports supplied by users.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
