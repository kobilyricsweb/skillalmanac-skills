---
name: plain-text-columns-to-csv
description: Converts aligned plain-text tables into CSV. Use when a report arrives as a plain-text table with fixed columns or repeated spaces and must become a CSV file, or when the user asks to convert a text file to CSV. Flags rows whose layout does not match the header. Do not use for spreadsheets, PDFs, Word files, JSON, or to overwrite an existing CSV.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Plain-text columns to CSV

The script parses the table and writes a new CSV. The agent checks the intake facts, picks the mode, runs the command, reads the JSON, and writes the report in the output contract below.

## Workflow

1. Intake. Collect three values: the input text file path, the output CSV path, and the layout (aligned columns or tab/space-separated). Required output: the three values, each confirmed. If one is missing, follow the stop rule for missing intake.
2. Check the input. It must be a text file, UTF-8 (a byte order mark is accepted), at most 2,097,152 bytes, with a header line. Required output: byte size, and a layout guess (fixed or split) with one line of reason.
3. Pick the mode with the decision table. Required output: mode and reason.
4. Run the command from the script contract. Required output: exit code and the JSON line, copied as printed.
5. Classify the findings. Divide the number of flagged data rows by `data_rows`, rounded to one decimal percent. Apply the threshold table. Required output: flagged rows, percent, and the threshold row that applies.
6. Write the report in the output contract. Required output: every section present, with "None" where a section is empty.

## Decision and threshold table

| Condition | Action |
|---|---|
| Values line up under the header letters | Use fixed mode (default) |
| Values are separated by a tab or by two or more spaces, and they do not line up | Use `--split` |
| A column name contains a single space, such as "Sales Rep" | Use `--split`. Fixed mode would split that name into two columns |
| Input larger than 2,097,152 bytes | Stop. Ask the user to split the file |
| Zero flagged data rows | Status `ok`. Deliver the CSV |
| Flagged rows above zero, up to 5 percent of `data_rows` (working value) | Status `findings`. Deliver the CSV and list every flagged line |
| Flagged rows above 5 percent of `data_rows` (working value) | Status `partial`. Do not present the CSV as final. Ask the user to confirm the layout |

The 5 percent limit is a working value, not a published standard.

## Finding codes

| Code | Mode | Meaning | Action |
|---|---|---|---|
| `short_row` | fixed | The line has no text at or after the last column start, so trailing values may be missing | Check the source line. Keep the empty trailing cells |
| `misaligned_row` | fixed | A token starts in a gap between columns, or crosses a column start | Check the value. It may sit under the wrong column |
| `column_count_mismatch` | split | The field count differs from the header field count | Check the line. Extra or missing separators cause this |

Only these codes appear in the JSON. Any other code means the script changed and this file is out of date.

## Script contract

Run from the skill folder. Replace the quoted placeholders with the user's paths:

```
python -I scripts/text_table_csv.py "<input-file>" "<output-csv>"
python -I scripts/text_table_csv.py "<input-file>" "<output-csv>" --split
```

Arguments:
- `input-file`: an existing text file. Read only.
- `output-csv`: a path that does not exist yet. The script never overwrites and refuses an input path.
- `--split`: optional. Split on tabs or two or more spaces instead of header columns.

Stdout is one JSON line. Keys: `status` (`ok`, `findings`, or `error`), `input` and `output` (base names only), `mode` (`fixed` or `split`), `header_line`, `columns`, `data_rows`, `blank_lines`, `rule_lines`, and `findings` (a list of objects with `line`, `code`, and `detail`). An error line has `status` set to `error` and an `error` message.

Exit codes:
- `0`: no findings. CSV written.
- `1`: findings. CSV written.
- `2`: usage or input error. No CSV is written.

## Output contract

Write the report with these headings, in this order:

1. `## Result`: `Status` (`ok`, `findings`, or `partial`), `Mode`, `Columns`, `Data rows`, `Output` (base name of the CSV).
2. `## Findings`: a table with columns `Line | Code | Detail`. Write "None" when there are no findings.
3. `## Flagged share`: flagged rows, percent, and the threshold row applied.
4. `## Open questions`: a numbered list of decisions for the user. Write "None" when there are none.
5. `## Files`: the full path of the CSV the user should open.

The script checks layout only. It does not check values, types, totals, or whether a column means what its header says. State this in Open questions when the user relies on the values.

## Refuse or stop when

- The output path already exists. Ask for a new path. Never overwrite a file.
- The input path and the output path are the same file.
- The input is not UTF-8 text. Spreadsheets, PDFs, Word files, and binary files are out of scope.
- The input is larger than 2,097,152 bytes.
- The script finds no header line (the file is empty or holds only rules and blank lines).
- The user asks you to fill missing values, guess values, or correct figures. Keep the parsed values and list the affected lines under Open questions.
- The flagged share is above 5 percent (working value). Set status `partial`.
- Intake facts are missing. Hand back this numbered question list and set status `partial`:
  1. The path to the input text file.
  2. The path for the new CSV. It must not exist yet.
  3. The layout: aligned columns, or separated by tabs or spaces.

## Shipped files

- [scripts/text_table_csv.py](scripts/text_table_csv.py): the converter.
- [fixtures/sample_report.txt](fixtures/sample_report.txt): a 12-line aligned report with a rule line and one short row. Use it to check the command.
- [fixtures/clean_report.txt](fixtures/clean_report.txt): a 5-line aligned report with no findings.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
