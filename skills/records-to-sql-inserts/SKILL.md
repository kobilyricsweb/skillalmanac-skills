---
name: records-to-sql-inserts
description: Generates SQL CREATE TABLE and INSERT statements from a CSV or JSON records file, inferring column types and escaping text values. Use when converting a CSV or JSON export into SQL INSERT statements, or when a table needs a quick CREATE TABLE with types inferred from sample rows. Do not use for schema migrations, reading or writing a live database, or input files larger than 2 MB.
license: Apache-2.0
compatibility: Python 3.9+ standard library only, no network and no database connection (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# records-to-sql-inserts

Converts one CSV or JSON records file into one `.sql` file: a CREATE TABLE, then INSERT statements of up to 100 rows each. All parsing, typing and escaping is done by [scripts/records_to_sql.py](scripts/records_to_sql.py). Run it from this skill folder. The license text is in [LICENSE.txt](LICENSE.txt).

## Workflow

1. Intake. Collect the input file path, the output path (must end in `.sql`, must not exist yet) and an optional table name. With no table name, the input file name without its extension is used, and it must match the identifier pattern in the type table below. Output: a three-line list of the values. If a value is missing or invalid, follow Refuse / stop when.
2. Size check. The input must be 2,097,152 bytes (2 MB) or smaller. Output: the input size in bytes.
3. Run the script:
   `python -I scripts/records_to_sql.py <input-file> <output-file.sql> [--table NAME]`
   Output: the stdout block described under Script contract.
4. Branch on the exit code. 0: go to step 5. 1: the file was written; copy every FINDING line and go to step 5. 2: nothing was written; report the `message` from stderr and stop.
5. Build the column table from the `column,type,nulls` lines. Attach each FINDING to its column. Choose the dialect row from the Dialect adjustments table that matches the user's database. Output: the report in Report contract.
6. Tell the user which statements to run and in what order. Do not connect to a database and do not execute the SQL.

## Type inference

The script checks each column against its non-NULL values. The first row that matches wins.

| Non-NULL values in the column | SQL type | Finding |
|---|---|---|
| All `true` or `false`, any letter case | BOOLEAN | none |
| All numeric-looking, and at least one has a leading zero (`007`, `00.5`, `-01`) | TEXT | LEADING_ZEROS |
| All whole numbers, all within -9223372036854775808 to 9223372036854775807 | INTEGER | none |
| All whole numbers, at least one outside that range | TEXT | OUT_OF_RANGE_INTEGER |
| Numbers with a decimal part or exponent (`10.50`, `-3.2`, `1e5`), whole numbers allowed | REAL | none |
| All `YYYY-MM-DD` and each a real calendar date (year `0000` is not a date) | DATE | none |
| No non-NULL values | TEXT | EMPTY_COLUMN |
| Anything else, including `+5`, `1.`, `.5`, `yes`, `NULL` as a word | TEXT | none |

Identifier pattern for table and column names: first character a letter or underscore, then letters, digits or underscores, at most 63 characters (working value, set by the script, not a published spec). Column names must also be unique when compared without case.

## Cell rules

| Input cell | Written as |
|---|---|
| Empty, spaces only, or JSON `null` or `""` | `NULL` |
| Leading or trailing spaces | trimmed before typing and before writing |
| TEXT or DATE value | single-quoted; each `'` becomes `''`; nothing else is escaped |
| BOOLEAN value | `TRUE` or `FALSE` |
| INTEGER or REAL value | unquoted, as read |
| JSON boolean in a TEXT column | `'true'` or `'false'` |

## Findings

| Code | Meaning | What to tell the user |
|---|---|---|
| EMPTY_COLUMN | The column has no non-NULL values and is typed TEXT | Ask whether the column is needed; the type can be changed by hand. |
| LEADING_ZEROS | Numeric-looking values would lose their leading zeros as numbers, so the column is TEXT | Confirm the zeros matter (codes, ZIP-style values) and keep TEXT. |
| OUT_OF_RANGE_INTEGER | A whole number does not fit in 64 bits, so the column is TEXT | Offer REAL or TEXT by hand; REAL loses digits above about 15 significant figures. |

## Script contract (type A)

Arguments:

| Argument | Required | Meaning |
|---|---|---|
| `input-file` | yes | `.csv` with a header row, or `.json` holding a non-empty array of flat objects |
| `output-file` | yes | Path ending in `.sql`. Must not exist. Must differ from the input path. |
| `--table NAME` | no | Table name. Default: the input file name without extension. |

Exit codes:

| Code | Meaning | Files |
|---|---|---|
| 0 | Written, no findings | Output written |
| 1 | Written, one or more findings | Output written |
| 2 | Usage or input error | Nothing written; one-line JSON on stderr: `{"status": "error", "message": "..."}` |

Stdout for exit 0 and exit 1, in this order:

```
records_to_sql: written <output file name>
rows: <count>
statements: <count> (batch size 100)
column,type,nulls
<column>,<TYPE>,<null count>
FINDING <CODE> <column>: <detail>
findings: <count>
```

The `column,type,nulls` line is followed by one line per column in input order. FINDING lines are present only when findings exist.

Output file layout: five comment lines (one generation note, four dialect notes), a blank line, one CREATE TABLE with double-quoted identifiers, then one INSERT per batch of up to 100 rows, each ending in a semicolon. No primary key and no NOT NULL constraints are emitted.

## Dialect adjustments

| Target | Change to the .sql file before running |
|---|---|
| PostgreSQL, SQLite 3.23 or later | None needed. TRUE and FALSE are accepted. |
| SQLite before 3.23 | Replace TRUE with 1 and FALSE with 0 in the INSERT rows. |
| MySQL 8 | Enable ANSI_QUOTES, or change each double-quoted identifier to backticks. Review any string containing a backslash, because backslashes are not escaped. |

## Refuse / stop when

- The input is neither `.csv` nor `.json`, is over 2 MB, is not valid UTF-8, or contains a NUL character. Stop and report the exit 2 message.
- The output name does not end in `.sql`, already exists (the script never overwrites), or is the same path as the input. Stop and ask for a new output name.
- A table or column name fails the identifier pattern, or two column names match without case. Stop and ask the user to rename the source columns. Do not rename silently.
- A CSV row has a different field count from the header, or the CSV has no data rows.
- A JSON file is not an array of flat objects (a nested object or array in a field), or contains NaN or Infinity.
- The request asks to run the SQL, connect to a database, alter an existing table, or insert into one. This skill only writes a file. Refuse that clause and keep the rest of the report.

## Report contract

Return these headings in this order.

1. `## Status`: one of `written`, `written with findings`, `failed`.
2. `## Column types`: a table with the columns `column`, `type`, `nulls`, `finding`. One row per column, in input order. `finding` is the code or `none`.
3. `## Run next`: the statement count, the dialect row that applies, and the file name.
4. `## Open questions`: only when a request was refused or a finding needs a decision. Numbered list.

## Shipped files

- [scripts/records_to_sql.py](scripts/records_to_sql.py): the converter (type A script).
- [fixtures/sample_records.csv](fixtures/sample_records.csv): a 7-row, 5-column CSV with an apostrophe, a quoted comma and quotes, a date column and one empty cell. Expected result: exit 0, types INTEGER, TEXT, DATE, REAL, BOOLEAN, one INSERT.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
