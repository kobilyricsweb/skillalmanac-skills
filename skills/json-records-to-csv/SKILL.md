---
name: json-records-to-csv
description: Converts a JSON array of objects into a CSV file with a header row, flattening nested objects into dot-named columns and joining arrays with a separator or expanding them into rows. Use when a user pastes or uploads JSON records and wants a spreadsheet-ready CSV, asks for a JSON to CSV conversion, or needs nested fields turned into columns. Do not use for JSON whose top level is not an array of objects, for CSV to JSON, for Excel workbooks, or for data that must stay in a database.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# JSON records to CSV

This skill runs `scripts/json_to_csv.py` on a local JSON file. The script does
the conversion; the agent chooses the mode, runs the command, and reports the
result. Follow the steps in order.

## Workflow

1. **Collect the intake facts.** Need: the input file path (a `.json` file whose
   top-level value is an array), the output path (a `.csv` name that does not
   exist yet), and whether the user wants arrays joined or expanded into rows.
   Output: three written values. If the output name is missing, ask for it.
2. **Check the input size.** The file must be 2,097,152 bytes or smaller. Output:
   the size in bytes. Above the limit, stop (see Refuse / stop when).
3. **Pick the array mode** with the decision table below. Output: the mode and
   any separator.
4. **Run the script** with the exact command line in the Script contract section.
   Output: the exit code and the one-line stdout summary (exit 0 or 1) or the
   one-line stderr error (exit 2).
5. **Check the result.** Exit 0 means every array item was an object. Exit 1 means
   the CSV was written but some items were skipped; list the `skipped_indices`.
   Exit 2 means nothing was written; map the `reason` to the table.
6. **Check the blanks.** If `missing_values` is more than 25 percent of
   `rows` times `columns`, name the three columns with the most blanks, found by
   reading the CSV. Working value: 25 percent.
7. **Report** using the output contract below.

## Decision table

| Situation | Setting | Working value or fixed value |
|---|---|---|
| Arrays hold short labels such as tags | Default join mode | Separator `"; "` (semicolon, space) |
| Array items already contain `"; "` | Join with a different separator | `--separator " / "` |
| Each array item needs its own row for filtering | Row mode | `--one-row-per-item` |
| Several arrays in one record | Row mode pairs items by position | Row count is the longest array; shorter arrays leave blank cells |
| Items are objects, for example `items` | Row mode flattens them | Columns named `items.name`, `items.qty` |
| Input file size | Proceed | 2,097,152 bytes or less |
| Input file size | Stop | More than 2,097,152 bytes |
| Separator text | Must not contain a line break | No CR or LF characters |
| Some array items are not objects | Exit 1, still delivered | Report `skipped_records` and `skipped_indices` |
| Column mostly blank | Name it to the user | More than 25 percent blank cells (working value) |

## Conversion rules (fixed)

- An object value is flattened: the child key joins the parent key with a dot.
  Example: `{"address": {"city": "London"}}` gives column `address.city`.
- An empty object becomes the cell `{}`.
- `null` becomes an empty cell. A missing key also becomes an empty cell.
- `true` and `false` become the text `true` and `false`.
- Numbers keep the decimal text Python gives them: `9.50` becomes `9.5`.
- Columns are the union of all output keys, in first-seen order across rows.
- Join mode: each array element becomes text, elements are joined with the
  separator, and an empty array becomes an empty cell. Object or array elements
  are written as compact JSON.
- Row mode: row `i` takes element `i` of every array in the record. A record
  yields as many rows as its longest array, and at least one row.

## Output contract

Exit 0 or 1 writes one line of JSON to stdout with these keys:

| Key | Type | Meaning |
|---|---|---|
| `status` | string | `ok` or `findings` |
| `mode` | string | `join` or `rows` |
| `rows` | integer | Data rows written, not counting the header |
| `columns` | integer | Number of columns |
| `missing_values` | integer | Empty cells across all data rows |
| `skipped_records` | integer | Array items that were not objects |
| `skipped_indices` | list of integers | 0-based positions of skipped items, first 20 only |
| `column_names` | list of strings | Column names in output order |
| `output_file` | string | File name only, without the folder |

Exit 2 writes one line of JSON to stderr with keys `status` (always `error`),
`reason`, and `message`.

Reply to the user with: the output file name, rows, columns, missing values,
skipped records (if any), and the status. Quote the column names in a list.

## Status and reason values

| Exit | `status` | Meaning |
|---|---|---|
| 0 | `ok` | CSV written, no items skipped |
| 1 | `findings` | CSV written, `skipped_records` is 1 or more |
| 2 | `error` | Nothing written; see `reason` below |

| `reason` | Exit | Meaning and fix |
|---|---|---|
| `usage` | 2 | Arguments missing or unknown. Give both file paths. |
| `bad_option` | 2 | Separator contains a line break. Use one line of text. |
| `option_conflict` | 2 | `--separator` used with `--one-row-per-item`. Drop one. |
| `same_path` | 2 | Output path equals input path. Choose a new name. |
| `file_missing` | 2 | Input file does not exist. Check the path. |
| `file_unreadable` | 2 | Input is a folder or cannot be opened. |
| `file_too_large` | 2 | Input is over 2,097,152 bytes. |
| `invalid_utf8` | 2 | Input is not UTF-8. Re-save it as UTF-8. |
| `invalid_json` | 2 | Parse error, or `NaN` or `Infinity` appears. |
| `too_deep` | 2 | Nesting is too deep for the parser or the flattener. |
| `not_array` | 2 | Top-level value is not an array. |
| `no_records` | 2 | Array is empty or has no object items. |
| `output_exists` | 2 | Output file already exists. Nothing was overwritten. |
| `output_unwritable` | 2 | Output folder is missing or not writable. |

## Script contract

Script: `scripts/json_to_csv.py`. Standard library only. Reads one local file and
writes one new file. No network, no subprocess.

Arguments:

- `input_file` (required): path to the JSON file.
- `output_file` (required): path for the new CSV file. Must not exist.
- `--separator TEXT` (optional, default `"; "`): join text for join mode.
- `--one-row-per-item` (optional flag): row mode.

Exit codes: 0 ok, 1 findings, 2 usage or input error.

Exact command line, run from the skill folder:

```
python -I scripts/json_to_csv.py <input-file> <output-file>
```

Row mode: `python -I scripts/json_to_csv.py <input-file> <output-file> --one-row-per-item`

CSV format: header row first, UTF-8 without a byte-order mark, CRLF line
endings, and RFC 4180 quoting from Python's csv module.

## Refuse / stop when

- The output path already exists. Stop, ask for a new file name, and never
  delete or overwrite the existing file.
- The output path is the input path. Stop and ask for a new name.
- The input is larger than 2,097,152 bytes. Stop and tell the user the size. Do
  not split the file silently.
- The top-level value is an object, a string, or a number. Stop and ask which
  array to convert. Do not unwrap an object on your own.
- The user asks for the file to be fetched from a URL or sent to an online
  service. This skill reads local files only. Ask the user to save the file first.
- The user asks for a spreadsheet file format other than CSV, such as `.xlsx`.
  Stop; this skill writes CSV only.
- Exit 1 occurred. Deliver the CSV, and list every skipped index. Never drop
  skipped items without saying so.
