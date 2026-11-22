---
name: csv-structure-validator
description: Checks a CSV file for ragged rows, blank or duplicate headers, and per-column rule failures such as bad ISO dates, duplicate IDs, and out-of-range numbers, reporting each finding with its row and column. Use when a CSV import keeps failing, when you need to validate a CSV file before loading it, or when a column rules JSON must be applied to a CSV. Do not use for editing or repairing the CSV, for Excel workbooks, for JSON or XML files, or for checks against a database.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# CSV Structure Validator

Validates a CSV file and reports every finding with its row and column. The checks run in [scripts/csv_validate.py](scripts/csv_validate.py), which uses the Python standard library only, makes no network calls, and writes no files. The skill never edits the CSV.

## Workflow

1. Intake. Confirm the input is a text file with one delimiter character (comma unless told otherwise), encoded as UTF-8 (a byte order mark is accepted), and no larger than 2 MB (working value). Output: the input file name, the delimiter, and whether a rules file was supplied.
2. Rules. If the user gave column rules, write them as a rules JSON file that follows the schema below, at a new path. Never overwrite an existing file. If no rules were given, skip this step and run structure checks only. Output: the rules file path, or `none`.
3. Run the script from the skill folder using the command in the Script contract. Output: the single JSON line and the exit code.
4. Branch on the exit code: 0 means clean, 1 means findings, 2 means error. For 2, stop and report the `error` text (see Refuse / stop when). Output: the status value for the report.
5. Build the report in the Output contract. Each entry in the JSON `findings` array becomes one table row, in the script's order. Output: the Summary, Findings, Counts by code, and Open questions sections.
6. Check truncation. If `truncated` is true, the table shows only the first 200 findings. State the full count from `findings_total` in the Summary. Output: the "table shows" line.
7. Run the smoke check when asked. Run the command on `fixtures/orders_sample.csv` with `fixtures/orders_rules.json`. The expected result is status `findings`, total 3, exit 1. Output: one line stating whether the result matched.

## Thresholds and limits

| Item | Value | Basis |
|---|---|---|
| Input file size | 2 MB (2,097,152 bytes) | working value; exit 2 above it |
| Rules file size | 2 MB | working value; same cap |
| Findings in JSON output | 200 | working value; `counts_by_code` still counts all findings |
| Regex length in rules | 200 characters | working value |
| Cell comparison | after removing leading and trailing spaces | script behavior |
| Email shape | one @, no spaces, a dot after the @ | working value, not RFC 5322 |
| Row numbering | header is row 1; first data row is row 2 | script behavior |
| Field size | csv module default, 131,072 characters | exit 2 when exceeded |
| Checks per cell | first failing value check only; UNIQUE can add a second finding | script behavior |

## Rules file schema

The top-level value must be an object whose only key is `columns`. Each key under `columns` must equal a header name after trimming spaces. Each rule may use only these keys:

| Key | Allowed value | Check |
|---|---|---|
| `type` | `int`, `float`, `date`, `email` | int: optional sign then digits. float: decimal or exponent form. date: YYYY-MM-DD that is a real calendar date. email: the working shape above |
| `required` | `true` or `false` | an empty cell gives REQUIRED |
| `unique` | `true` or `false` | a repeat of a non-empty value gives UNIQUE and names the first row |
| `enum` | non-empty list of strings | the cell must equal one entry exactly (case-sensitive) |
| `regex` | string, at most 200 characters | the whole cell must match |
| `min` | finite number | cell must parse as a number and be at least `min` |
| `max` | finite number | cell must parse as a number and be at most `max`; `min` must not exceed `max` |

An empty cell skips every check except REQUIRED. Unknown keys, a column name that is not in the header, or a wrong value type exit 2 instead of being ignored.

## Script contract

Command line, run from the skill folder:

`python -I scripts/csv_validate.py <input-file> [--rules <rules-json>] [--delimiter <char>]`

- `<input-file>`: required path to the CSV.
- `--rules`: optional path to a rules JSON file.
- `--delimiter`: optional single character, default comma. It may not be a quote or a line break.
- Output: one JSON line on stdout with the keys `status` (`clean`, `findings`, or `error`), `rows_checked`, `blank_rows_skipped`, `columns`, `findings_total`, `truncated`, `counts_by_code`, and `findings`. Each finding has `row`, `column_index` (1-based; null for row-level findings), `column` (header name; null when blank or row-level), `code`, and `message`. An error line has `status` set to `error` and an `error` string.
- Exit codes: 0 no findings; 1 one or more findings; 2 usage or input error (missing file, not UTF-8, over 2 MB, malformed CSV, bad rules file).
- The script prints no data values. Findings carry row and column only.

## Finding codes

| Code | Scope | Meaning |
|---|---|---|
| BLANK_HEADER | row 1 | a header cell is blank |
| DUPLICATE_HEADER | row 1 | a header name repeats; rules apply only to the first occurrence |
| RAGGED_ROW | row | field count differs from the header; rule checks skip that row |
| REQUIRED | cell | a required column is empty |
| TYPE_INT | cell | not a whole number |
| TYPE_FLOAT | cell | not a number |
| TYPE_DATE | cell | not a valid ISO date |
| TYPE_EMAIL | cell | not an email shape |
| ENUM | cell | not in the enum list |
| REGEX | cell | does not match the regex |
| NOT_NUMERIC | cell | min or max is set and the value is not a number |
| MIN | cell | below min |
| MAX | cell | above max |
| UNIQUE | cell | repeats an earlier non-empty value; the message gives the first row |

## Output contract (report)

```
## Summary
- Status: clean | findings | error | partial
- Rows checked: <rows_checked>; blank rows skipped: <blank_rows_skipped>; columns: <columns>
- Findings: <findings_total>; table shows: <rows in table>; truncated: yes | no

## Findings
| Row | Column | Code | Message |
|---|---|---|---|

## Counts by code
| Code | Count |
|---|---|

## Open questions
Numbered list, or "none".
```

Findings rows follow the script order. Show `-` in the Column cell when `column` is null. Counts rows follow the key order in `counts_by_code`. Status `partial` means a request clause was declined and the rest of the report is complete.

## Refuse / stop when

- The input is over 2 MB, is not UTF-8, or is not a CSV (for example .xlsx, .zip, or JSON). Stop and ask for a UTF-8 CSV export under 2 MB.
- The script exits 2 for any reason. Stop, set Status to `error`, and quote the `error` text. Do not guess a fix.
- The rules name a column that is not in the header. Stop, list the header names, and ask which one was meant.
- The rules contain an unlisted key or a wrong value type. Stop and quote the `error` text.
- The user asks you to fix, rewrite, or delete rows in the CSV. Decline only that clause, keep the report, set Status to `partial`, and list the request under Open questions. The skill never modifies the file.
- The user asks for the findings to be saved to a file. Decline that clause the same way and show the report in chat. The script writes no files.
- The user asks whether values are correct, such as whether a date is a real order date or an address is live. Decline that clause; the checks are format and rule checks only.

## Shipped files

- [scripts/csv_validate.py](scripts/csv_validate.py): the validator.
- [fixtures/orders_sample.csv](fixtures/orders_sample.csv): 20-row smoke input with one ragged row, one bad date, and one duplicate ID.
- [fixtures/orders_rules.json](fixtures/orders_rules.json): rules for the smoke input.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
