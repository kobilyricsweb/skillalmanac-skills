---
name: csv-split-by-rows
description: Splits a CSV file into numbered part files of a fixed data-row count, repeating the header row in each part. Use when a CSV is too large to open comfortably or must be sent or imported in chunks of N rows. Use when the parts must be checked against the original row count. Do not use for editing, merging or converting CSV files, for files over 2 MB, or for spreadsheet files such as xlsx.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# CSV split by rows

This skill splits one CSV file into part files of a fixed number of data rows.
Every part gets the header row. Records are parsed with the csv module, so a quoted
field that spans several lines stays in one record. The script never edits the input,
never overwrites a file, and checks that the parts add up to the original row count.

Shipped files: `scripts/csv_split.py` (the splitter), `fixtures/sample_25_rows.csv`
(a 25-row test input with one multiline cell), `LICENSE.txt`.

## Workflow

1. **Intake.** Collect `<input-file>`, `<rows>` (data rows per part), `<out-dir>` (an
   existing folder) and `<prefix>` (default `part`). Output: a four-line list of these
   values. If `<input-file>` or `<out-dir>` is missing, stop and return a numbered
   question list (see Refuse / stop when).
2. **Check the input size.** Read the byte size of `<input-file>`. Apply the size table
   below. Output: the byte size and the decision (run, or stop).
3. **Set rows per part.** If the user gave no value, use 5000 (working value). Apply the
   rows table below. Output: the chosen value.
4. **Run the script.** Use the command line in the Script contract with the user's real
   paths. Output: the exit code and the JSON object from stdout or stderr.
5. **Branch on the exit code.** Exit 0 means the parts are verified and clean. Exit 1
   means the parts exist but need review (ragged rows, or verification failed). Exit 2
   means nothing was written. Apply the status table. Output: one status line.
6. **Report the parts.** Build the output below from the JSON. Output: the parts table,
   the totals line and, if any, the ragged rows list.

## Decision and threshold tables

| Input size (bytes) | Action |
|---|---|
| 0 | Stop. The script exits 2 with `input file is empty`. |
| 1 to 2,097,152 | Run the script. |
| Above 2,097,152 | Stop. The script refuses with the 2 MB cap message. Do not run it. |

| Rows requested | Action |
|---|---|
| Not given | Use 5000 (working value). |
| 1 to 1,000,000 | Run the script. |
| Below 1 or above 1,000,000 | Stop and ask for a valid value. The script exits 2. |

| Ragged rows found (`ragged_row_count`) | Status and exit code |
|---|---|
| 0 and `verified` true | `ok`, exit 0 |
| 1 or more, `verified` true | `ragged_rows`, exit 1. Parts are written. List up to 50 row numbers. |
| Any, `verified` false | `verification_failed`, exit 1. Keep the files, report it, do not call the parts good. |

## Output contract

The script prints one JSON object on stdout for exit codes 0 and 1. Keys:

| Key | Type | Meaning |
|---|---|---|
| `status` | string | `ok`, `ragged_rows` or `verification_failed` |
| `input_data_rows` | integer | Data rows in the input, header excluded |
| `rows_per_part` | integer | The `--rows` value used |
| `header_columns` | integer | Field count of the header row |
| `parts` | list | One object per part: `file` (name only) and `data_rows` |
| `parts_data_rows_total` | integer | Sum of `data_rows` across parts |
| `verified` | boolean | True when every part reads back equal to its slice of the input |
| `ragged_row_count` | integer | Data rows whose field count differs from the header |
| `ragged_rows` | list of integers | 1-based data row numbers, first 50 only |

The report to the user has this shape:

```
Parts: <n> files, <total> data rows of <input_data_rows>. Verified: yes or no.
| Part | Data rows |
|---|---|
| <file> | <data_rows> |
Ragged rows: none, or the list of row numbers.
```

## Refuse / stop when

- The input is over 2 MB, is empty, or has a header row but no data rows.
- The input is not UTF-8 (the script exits 2 with `input file is not valid UTF-8`). Ask
  the user to re-save the file as UTF-8 CSV. Do not convert it yourself.
- The file is not CSV: xlsx, json, PDF, or any other format.
- `<out-dir>` does not exist. Ask the user to create it. The script does not create folders.
- A part file already exists in `<out-dir>`. Stop. Ask for a new `<prefix>` or another
  folder. Never delete, rename or overwrite an existing file.
- The user asks to overwrite existing parts or to write parts over the input file.
- The status is `verification_failed`. Report it and keep the files.

## Script contract

Command line, run from the skill folder:

```
python -I scripts/csv_split.py "<input-file>" --rows <rows> --out-dir "<out-dir>" --prefix <prefix>
```

| Argument | Required | Rule |
|---|---|---|
| `input-file` | yes | Regular file, 1 byte to 2 MB, UTF-8, a leading BOM is accepted |
| `--rows` | yes | Integer from 1 to 1000000 |
| `--out-dir` | yes | Existing directory |
| `--prefix` | no | 1 to 64 characters from A-Z, a-z, 0-9, underscore, hyphen. Default `part` |

Part files are named `<prefix>_001.csv`, `<prefix>_002.csv`, and so on. The number has
at least 3 digits. Each part is written with LF line endings.

| Exit code | Meaning | Files written |
|---|---|---|
| 0 | Parts written, verified, no ragged rows | Yes |
| 1 | Parts written; ragged rows found, or verification failed | Yes |
| 2 | Usage or input error | No, or removed again if a write failed |

Errors go to stderr as one JSON line: `{"status": "error", "message": "..."}`.

| Error message (start of text) | Action |
|---|---|
| `usage:` | Fix the command line and run again |
| `--rows must be an integer from 1 to 1000000` | Ask for a valid value |
| `--prefix must be` | Ask for a shorter or valid prefix |
| `input file not found` | Check the path |
| `input file is empty` | Stop |
| `input file exceeds the 2 MB cap` | Stop |
| `input file could not be read` | Check the path and permissions |
| `input file is not valid UTF-8` | Ask for a UTF-8 re-save |
| `input file has no records` | Stop |
| `malformed CSV` | Stop and report the parser message |
| `header row is empty` | Stop |
| `no data rows to split` | Stop |
| `--out-dir does not exist` | Ask the user to create it |
| `part file already exists` | Ask for a new prefix or folder |
| `a part path would overwrite the input file` | Ask for another prefix or folder |
| `writing a part file failed` | Parts from this run were removed. Report it. |

The script reads the input only, makes no network calls and starts no subprocesses.
