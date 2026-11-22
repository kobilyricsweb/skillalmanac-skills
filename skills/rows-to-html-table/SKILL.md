---
name: rows-to-html-table
description: Renders CSV or JSON rows as an accessible HTML table fragment with a caption, scoped column headers, thead and tbody, and escaped cell text. Use when a user needs to turn a CSV export or a JSON array of records, such as SQL query output saved to a file, into a table for a web page. Do not use for spreadsheet files, charts, live database connections, or front-end component code.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Rows to HTML table

The script does the escaping, the column header scope, and the row counts. The agent checks the intake facts, runs the script once, reads the exit code, and checks the output file.

## Workflow

1. Check the intake facts. Required: an input file ending in `.csv` or `.json`, a non-empty caption, and an output path that does not exist yet. Output: a three-line fact list (input, caption, output). If one fact is missing, stop (see "Refuse / stop when").
2. Choose the format. `.csv` means a CSV file whose first row is the header. `.json` means a JSON array of objects. Any other extension needs `--format csv` or `--format json`. Output: the format name.
3. Run the command in "Script contract". Output: the stdout summary line (exit 0 or 1) or the stderr error line (exit 2), plus the exit code.
4. Set the status from the exit code: 0 is `ok`, 1 is `review`, 2 is `failed`. Output: one status word.
5. For `review`, list each number in `ragged_rows` with its cause: a CSV row with fewer or more cells than the header, or a JSON object whose keys differ from the union of all keys. Do not edit the output file by hand. Ask the user to fix the source and rerun to a new output path. Output: the ragged list.
6. Check the output file. Count the `<table>` elements (must be 1), the `<th scope="col">` cells (must equal `columns`), and the `<td` cells (must equal `rows` times `columns`). Output: the three counts and match or mismatch. A mismatch sets the status to `failed`.
7. Hand back the status block in "Output contract". Output: the block only, with no extra prose beyond the ragged list.

## Decision thresholds

| Check | Value | Result |
|---|---|---|
| Input size | at most 2,097,152 bytes (2 MB, working value) | larger: exit 2 |
| Text encoding | UTF-8; a leading byte order mark is accepted | not valid UTF-8: exit 2 |
| Data rows | at least 1 | 0 rows: exit 2, "no data rows" |
| Column names | at least 1; none blank; all unique | blank or duplicate: exit 2 |
| Ragged row, CSV | cell count differs from the header count | exit 1; row number in `ragged_rows` |
| Ragged row, JSON | key set differs from the union of keys across all objects | exit 1; row number in `ragged_rows` |
| Numeric column (`--align-numeric`) | every non-empty cell matches `-?[0-9]+(\.[0-9]+)?` and at least one cell is non-empty (working value) | every cell in the column gets `class="num"` |
| Caption | non-empty after trimming spaces | exit 2, "caption must not be empty" |
| Output path | must not exist and must differ from the input path | exists: exit 2, nothing written |
| Cell escaping | `&`, `<`, `>`, `"`, `'` always escaped | no raw markup is ever emitted from cells |

## Output contract

Output file (`<output-file>`): one HTML fragment, UTF-8, LF line endings, no `<html>` or `<body>` wrapper. Element order:

- `<table>`
- `<caption>` holding the escaped caption text
- `<thead>` with one `<tr>` of `<th scope="col">` cells in column order
- `<tbody>` with one `<tr>` per data row and one `<td>` per column
- `</table>`

Stdout on exit 0 or 1, one JSON line with exactly these keys:

| Key | Meaning |
|---|---|
| `rows` | data rows written (header not counted) |
| `columns` | header column count |
| `numeric_columns` | column names given `class="num"`; empty without `--align-numeric` |
| `ragged_rows` | 1-based data row numbers that did not match the column set; empty on exit 0 |
| `output_bytes` | size of the written file in bytes |

Stderr on exit 2, one JSON line with keys `error` (short text) and `exit` (always 2).

Status block returned to the user:

```
status: ok | review | failed
rows: <rows>   columns: <columns>
output: <output-file>
ragged_rows: <numbers or none>
td_check: <count> of <rows x columns> | match or mismatch
```

## Refuse / stop when

- The output path already exists. Stop and ask for a new path. Never delete or overwrite.
- The caption is missing or blank. Stop and hand back this numbered question: 1. What is the table about, in one short caption? Status `partial`.
- The format cannot be inferred and `--format` is not given. Ask which format the file is.
- The input is not CSV or JSON, or the JSON root is not an array of objects. Exit 2. Do not guess a conversion.
- The user wants raw HTML or links inside cells. Every cell is escaped text. Say so and offer plain text.
- The user asks for CSS, sorting, paging, a full HTML page, or a live database query. Out of scope. The script reads a file only.
- Any intake fact is missing and cannot be inferred from the request. Hand back the numbered question list and status `partial`.

## Script contract (type A)

Path: `scripts/rows_to_html.py`. Python 3.9+, standard library only. No network, no subprocess, no eval.

Arguments:

- `input` (positional, required): the CSV or JSON file to read. Read-only.
- `--output <output-file>` (required): a new file to create. Opened in exclusive-create mode.
- `--caption "<caption>"` (required): non-empty table caption.
- `--format csv|json` (optional): overrides the extension.
- `--align-numeric` (optional flag): adds `class="num"` to all-numeric columns. The page CSS must define `.num`.

Flattening rule for JSON: nested objects join keys with dots (`buyer.name`), arrays use indexes (`lines.0.sku`), `null` becomes an empty cell, booleans become `true` or `false`, and an empty object or array becomes one empty cell.

Exit codes:

- 0: table written, every row matches the column set.
- 1: table written, at least one row is ragged (listed in `ragged_rows`). Review before publishing.
- 2: usage or input error. Nothing is written.

Command line:

```
python -I scripts/rows_to_html.py <input-file> --output <output-file> --caption "<caption>"
```

Add `--format csv` or `--format json` and `--align-numeric` when needed.

## Shipped files

- [scripts/rows_to_html.py](scripts/rows_to_html.py): the renderer and its exit codes.
- [fixtures/sample.csv](fixtures/sample.csv): five data rows and four columns, with ampersands and angle brackets in cells.
- [fixtures/nested.json](fixtures/nested.json): two objects with nested objects, arrays, a boolean, and a null.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
