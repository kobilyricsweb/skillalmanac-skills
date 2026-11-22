# CSV Structure Validator

## One line

Checks a CSV file for ragged rows, blank or duplicate headers, and per-column rule failures, and reports each finding with its row and column number.

## What it does

The skill runs a single standard-library Python script over a CSV file. Without a rules file it checks structure only: every data row must have as many fields as the header, and header names must be present and unique. With a rules JSON file it also checks each named column for type (whole number, decimal, ISO date, or email shape), required values, enum membership, a regular expression, numeric minimum and maximum, and uniqueness across rows.

Each finding lists the row number (the header is row 1), the 1-based column index, the header name, a short code such as TYPE_DATE or UNIQUE, and a message. Duplicate IDs name the first row where the value appeared. The output never repeats the cell value, so the report itself does not spread personal data. The JSON line caps the detailed list at 200 findings, while the per-code counts always cover every finding.

## When to use

Use it when a CSV import keeps rejecting rows and someone needs the exact row and column to fix. It also suits a quick check of an export before loading it into another system, or a repeatable rules file kept beside a recurring feed.

## When not to use

Do not use it to repair or rewrite the file, to judge whether a date is plausible or an address is live, to read Excel workbooks or JSON, or to compare values against a database. The script writes nothing and makes no network calls, so any saving or sending must be done separately.

## Requirements

Python 3.9 or later, with no packages to install. The input must be UTF-8 text (a byte order mark is accepted) and no larger than 2 MB. The rules file has the same size cap and uses only the keys listed in the skill.

## Example

Command run from the skill folder against the smoke fixture:

```
python -I scripts/csv_validate.py fixtures/orders_sample.csv --rules fixtures/orders_rules.json
```

Output, exit code 1:

```
{"status": "findings", "rows_checked": 20, "blank_rows_skipped": 0, "columns": 5, "findings_total": 3, "truncated": false, "counts_by_code": {"RAGGED_ROW": 1, "TYPE_DATE": 1, "UNIQUE": 1}, "findings": [{"row": 5, "column_index": null, "column": null, "code": "RAGGED_ROW", "message": "expected 5 fields, found 4"}, {"row": 9, "column_index": 2, "column": "order_date", "code": "TYPE_DATE", "message": "expected an ISO date YYYY-MM-DD"}, {"row": 17, "column_index": 1, "column": "id", "code": "UNIQUE", "message": "duplicate of row 3"}]}
```

## Limits

The checks are format and rule checks only. They do not confirm that a value is true, current, or deliverable. The email shape is a working pattern, not the full RFC 5322 grammar. Cells are compared after trimming spaces. Only one delimiter character is supported, with no detection of quoting style. A quoted field that spans lines is counted as one record, so row numbers are record numbers rather than physical line numbers. An unclosed quote swallows the rest of the file into one record, which shows up as a RAGGED_ROW finding. A user-supplied regular expression runs without a time limit, so a pathological pattern can be slow. The script does not check cross-file or cross-column logic such as totals or foreign keys.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
