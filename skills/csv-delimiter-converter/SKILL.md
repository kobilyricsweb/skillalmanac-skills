---
name: csv-delimiter-converter
description: Converts delimited text between comma, tab, semicolon and pipe while keeping quoted cells intact. Use when a CSV must be imported as tab-delimited or with another delimiter, when an import fails because the delimiter differs from what the target expects, or when a new delimited file must be checked to hold identical cell values. Do not use for Excel workbooks, JSON or XML conversion, fixed-width files, or changing the content of cells.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# CSV delimiter converter

This skill rewrites a delimited text file with a different delimiter. It runs
`scripts/delim_convert.py`, which parses the input with the csv module, writes the
output into a new file, parses that output back and compares every cell with the
original. The original file is never modified.

Supported delimiters: `comma` (`,`), `tab` (TAB character), `semicolon` (`;`),
`pipe` (`|`). Any other delimiter is out of scope.

## Workflow

1. Intake. Collect the input file path, the target delimiter (one of the four names
   above) and the source delimiter if the user knows it. Output: a three-line intake
   note with `input`, `target`, `source` (`auto` if unknown). Stop if `target` is
   missing and ask for it (see Refuse / stop when).
2. Pre-check the input. It must be a regular file of at most 2,097,152 bytes
   (2 MB working value) and valid UTF-8. A UTF-8 byte order mark is accepted and removed.
   Output: `pre-check: pass` or the failing rule.
3. Choose the output path. Use a new file name in an existing folder. The file must
   not exist. Output: the output path.
4. Run the command in the Script contract section. Output: the one-line JSON result
   (stdout) or the one-line error (stderr) and the exit code.
5. Map the exit code to an action with the decision table. Output: the status and
   the action taken.
6. List ragged records (record numbers, first 20 only). A ragged record has a column
   count different from the file's modal column count. Its values are kept as they
   are; the script never pads or trims them. Output: the list or `none`.
7. Report embedded-newline records as information only. A quoted cell that contains a
   line break is valid and is kept. Output: the record numbers or `none`.
8. Write the final report in the Output contract. Output: the report.

## Decision and threshold table

| Input or result | Value or rule | Action |
| --- | --- | --- |
| Input size | above 2,097,152 bytes (working value) | exit 2, `input_too_large`, stop |
| Input encoding | not valid UTF-8 | exit 2, `invalid_utf8`, stop |
| Delimiter detection | candidate needs a modal column count of 2 or more | otherwise `delimiter_undetected` |
| Detection score (working value) | share of non-empty records at the modal column count, then modal column count | highest score wins; ties go to comma, tab, semicolon, pipe in that order |
| Ragged records | column count differs from the modal column count | status `findings`, exit 1, output still written |
| Value check | parsed output cells equal parsed input cells | required before any write; otherwise `verify_failed` |
| Record list cap (working value) | 20 record numbers | longer lists are cut and the total is still reported |

## Output contract

The final report to the user has exactly these parts, in this order.

- Heading `## Conversion result`, then a two-column table `Field | Value` with these
  rows, in this order: `Status`, `Input delimiter`, `Delimiter source`,
  `Output delimiter`, `Records`, `Modal columns`, `Ragged records`,
  `Embedded newline records`, `Cells compared`, `Values equal`, `Output written`.
  Values come from the JSON keys `status`, `input_delimiter`, `delimiter_source`,
  `output_delimiter`, `records`, `modal_columns`, `ragged_records`,
  `embedded_newline_records`, `cells_compared`, `values_equal`, `output_written`.
- Heading `## Ragged records`, then either the numbers from `ragged_record_numbers`
  as a comma-separated line or the word `none`.
- Heading `## Next step`, one sentence: the output path to import, or the fix to make
  before rerunning.

## Script contract

Command line (type A, exact form):

    python -I scripts/delim_convert.py <input-file> <output-file> --to <target> [--from <source>]

- `<input-file>`: the user's file. Read only.
- `<output-file>`: a new path. Created with exclusive-create mode.
- `--to`: required; one of `comma`, `tab`, `semicolon`, `pipe`.
- `--from`: optional; one of `auto` (default), `comma`, `tab`, `semicolon`, `pipe`.

Success JSON on stdout (one line) has these keys: `status`, `input_delimiter`,
`delimiter_source` (`detected` or `flag`), `output_delimiter`, `records`,
`modal_columns`, `ragged_records`, `ragged_record_numbers`,
`embedded_newline_records`, `embedded_newline_record_numbers`, `cells_compared`,
`values_equal`, `output_written`.

Error JSON on stderr (one line) has the keys `error` and `code`. Error codes:

| Code | Exit | Meaning |
| --- | --- | --- |
| `input_missing` | 2 | input is not a regular file |
| `input_too_large` | 2 | input is over 2 MB |
| `invalid_utf8` | 2 | input is not UTF-8 |
| `csv_parse_error` | 2 | csv module rejected the input (for example a cell over the csv field size limit) |
| `no_rows` | 2 | input is empty or has no non-empty record |
| `delimiter_undetected` | 2 | no candidate delimiter; rerun with `--from` |
| `output_is_input` | 2 | output path is the input path |
| `output_exists` | 2 | output path already exists; nothing is written |
| `output_write_failed` | 2 | output could not be created |

Status values on stdout and exit codes:

| Status | Exit | Output written | Meaning |
| --- | --- | --- | --- |
| `ok` | 0 | yes | values equal and no ragged records |
| `findings` | 1 | yes | values equal, but ragged records exist |
| `verify_failed` | 1 | no | parsed output did not match the input; stop |

Argument errors from the command parser also exit 2.

## Refuse / stop when

- The input is missing, larger than 2 MB, or not UTF-8. Report the error code.
- The output path already exists. Never overwrite; ask for a new file name.
- The output path is the input path, or the user asks to convert the original file
  in place. Ask for a separate output file.
- The target or source delimiter is not one of the four supported names, or the user
  asks for a colon, caret or other delimiter. Only the four names are supported.
- `delimiter_undetected` is returned and the user has not given `--from`. Ask which
  delimiter the file uses.
- The file is not delimited text (Excel, JSON, XML, fixed-width). Stop and say so.
- Status `verify_failed` is returned. Report it and deliver no file.

## Files in this skill

- `scripts/delim_convert.py`: the converter described in the Script contract.
- `fixtures/sample_comma.csv`: a comma file with a quoted comma, a quoted quote and a
  quoted line break; a clean run gives status `ok`.
- `fixtures/ragged_semicolon.csv`: a semicolon file with two ragged records; a run
  gives status `findings`.
- `LICENSE.txt`: Apache License 2.0 text.

## Limits

- Checks only that parsed cell values match after conversion. It does not check the
  meaning of values, the date or number formats, or whether the target importer
  accepts the file.
- Does not repair ragged records and does not add or remove columns.
- Output always uses minimal csv quoting and LF line endings. Input line endings are
  not preserved.
- A UTF-8 byte order mark in the input is removed from the output.
- Detection is a heuristic. A file where another delimiter gives a more uniform
  column count can be detected wrongly; use `--from` to force the delimiter.
