# CSV to JSON records

## One line

Converts a header-row CSV into a JSON array of records and reports the type it inferred for each column.

## What it does

The script reads one CSV file, takes the first row as the header, and builds one object per data row keyed by those header names. Each column is typed as a whole: integer, float, boolean, or string. A column becomes boolean only when every non-empty cell is true or false in any letter case, and integer only when every non-empty cell is a whole number with no leading zero, so a ZIP code such as 02134 stays text. Integer and float cells mixed together make a float column. Anything else falls back to string, and the script flags that column when some of its cells look numeric or boolean. Empty cells are written as an empty string by default, or as null with the empty-null option. The script writes a new JSON file, refuses to overwrite an existing one, and prints the row count plus a table with the type, non-empty count, and empty count for each column.

## When to use

Use it when a CSV export has to become JSON for an import, a fixture, or an API test, and the numbers and true/false flags must stay numbers and booleans in the output. It is also useful for checking what a column's type will be before a downstream loader reads it, because the type table makes the decision visible.

## When not to use

Do not use it for Excel workbooks, nested or hierarchical JSON, JSON-to-CSV conversion, CSV files without a header row, or files larger than 2 MB. It does not split large files, and it does not repair ragged rows.

## Requirements

Python 3.9 or later, standard library only. No network access, no subprocess calls, and no third-party packages. The input must be UTF-8 text, with or without a byte order mark.

## Example

Command, run from the skill folder against the shipped smoke input:

```
python -I scripts/csv_to_json.py fixtures/sample.csv <workspace>/sample.json --empty-null
```

Standard output, exit code 0:

```
rows: 6
column  type     non_empty  empty  note
------  -------  ---------  -----  ----
id      integer  6          0
price   float    5          1
active  boolean  6          0
name    string   6          0
```

Contents of the written file:

```json
[
  {
    "id": 1,
    "price": 9.99,
    "active": true,
    "name": "Apple"
  },
  {
    "id": 2,
    "price": 12.5,
    "active": false,
    "name": "Banana"
  },
  {
    "id": 3,
    "price": null,
    "active": true,
    "name": "Cherry"
  },
  {
    "id": 4,
    "price": 3.0,
    "active": true,
    "name": "Dragon fruit, red"
  },
  {
    "id": 5,
    "price": 0.75,
    "active": false,
    "name": "Elderberry"
  },
  {
    "id": 6,
    "price": 100.0,
    "active": true,
    "name": "Fig"
  }
]
```

## Limits

Cells and header names are trimmed of surrounding whitespace before typing, so the output differs from the raw text in that respect. The script does not parse dates, currency symbols, thousands separators, or percentages; those columns become strings. Float cells are re-serialized as numbers, so the text 3.00 is written as 3.0 and the text 100 in a float column is written as 100.0. The 2 MB cap is a working value chosen for this skill. The script does not check meaning, does not check that a column is correct for the user's purpose, and does not verify that the output loads in any particular consumer. It does not detect duplicate rows, and it does not validate values against a schema.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
