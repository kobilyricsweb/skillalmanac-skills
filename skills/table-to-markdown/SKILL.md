---
name: table-to-markdown
description: Converts CSV, TSV or the first HTML table in a text file into an aligned Markdown table, escaping pipe characters and flagging ragged rows and empty header cells. Use when a pasted table breaks in a document, README or wiki because of stray pipes or uneven columns, or when someone asks to turn a table into Markdown. Do not use for spreadsheet files (.xlsx, .ods), Word or PDF tables, or tables that need totals, sorting, merged cells or colspan handling.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Table to Markdown

Converts one table from a text file into an aligned Markdown table. The bundled script reads CSV, TSV or the first HTML table, escapes pipe characters, pads every column to its widest cell, and reports two problems: ragged rows and empty header cells.

## Files

- [scripts/table_to_md.py](scripts/table_to_md.py): the converter (type A, stdlib only).
- [fixtures/sample.csv](fixtures/sample.csv): a five-row CSV with a pipe inside one cell and one ragged row, used for the smoke run.
- [fixtures/sample.html](fixtures/sample.html): an HTML table with a header row and two data rows, followed by a second table that must be ignored.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.

## Workflow

1. Check the input. It must be a UTF-8 text file of at most 2 MB that contains CSV, TSV or HTML with at least one table. Output: the file name, the size, and the format you expect. Stop if the file is a binary format (see the refuse list).
2. Choose the format. Use `--format auto` unless the user names one. Auto rule, applied in this order:
   - the text contains `<table` in any letter case: html
   - the first non-blank line has more tab characters than commas: tsv
   - anything else: csv

   Output: the format the script reports in its status line.
3. Run the converter with the command in the script contract. Add `--right-align-numeric` when the table goes into a document where figures should line up on the right. Output: the Markdown table (stdout, or the new file) and one JSON status line on stderr.
4. Read the exit code and choose the status value with the table below. Output: one status value for the reply.

| Exit code | Script status | Reply status | Action |
|---|---|---|---|
| 0 | ok | ok | Deliver the table |
| 1 | findings | partial | Resolve or disclose every finding in step 5, then deliver |
| 2 | error | failed | Read the error code, apply its action, and stop unless it can be fixed |

5. Handle findings. Each finding in the status line maps to one action:

| Finding code | Fields in the status line | Action |
|---|---|---|
| RAGGED_ROW | row (1 is the header), cells, expected | The script pads the row with empty cells. Ask the user for the missing values, or keep the padding and list the row number. A row wider than the header also gets this finding, and the header is padded. |
| EMPTY_HEADER | column (1-based) | The column keeps a blank heading. Ask for a name, or list the column number. |

   Output: one line per finding with the action taken.
6. Write the reply in the output contract. Output: the reply text, with the headings in the order given.

## Thresholds

| Item | Value | Basis |
|---|---|---|
| Input size cap | 2 MB (2,097,152 bytes) | Fixed in the script |
| Column cap | 60 columns | Working value |
| Minimum column width | 3 characters | Working value |
| Numeric cell pattern | optional sign, optional dollar sign, digits with optional thousands commas, optional decimals, optional percent sign | Script regular expression |
| Numeric column test | every non-empty data cell matches the numeric pattern; header excluded | Script behavior |

## Output contract

The reply has these headings, in this order:

- `## Table`: the Markdown table copied from the script output without changes.
- `## Status`: one line per item, in this order: `Status` (ok, partial or failed), `Format` (csv, tsv or html), `Data rows` (the rows value, header excluded), `Columns` (the columns value), `Findings` (`none`, or one line per finding with its code, row or column, and action).
- `## Open questions`: a numbered list of decisions the user must make, or `none`.

## Script contract

- Command: `python -I scripts/table_to_md.py <input-file> [--format auto|csv|tsv|html] [--output <new-file>] [--right-align-numeric]`
- Inputs: the input file (required); `--format` (default auto); `--output` (a path that does not exist yet); `--right-align-numeric` (a flag).
- Stdout: the Markdown table, only when `--output` is absent.
- Stderr: one JSON line. Script status `ok` or `findings` carries the keys status, rows, columns and findings. Script status `error` carries the keys status, code and message.
- Exit codes: 0 ok; 1 findings (the table is still written); 2 usage or input error (no table is written).
- Files written: only the `--output` file, created with exclusive create. The script never overwrites a file and never writes to the input path.

Script error codes:

| Code | Meaning | Action |
|---|---|---|
| USAGE | Arguments are invalid | Fix the command line |
| FILE_NOT_FOUND | The input path does not exist or cannot be read | Ask for the correct file |
| NOT_A_FILE | The input path is a folder | Ask for a file |
| INPUT_TOO_LARGE | The input is over 2 MB | Ask for a smaller excerpt |
| INVALID_UTF8 | The input is not valid UTF-8 | Ask for a UTF-8 copy |
| PARSE_ERROR | The CSV or HTML could not be parsed | Check quoting or markup, then re-run |
| NO_TABLE | HTML input has no table element | Check the input format |
| EMPTY_TABLE | No non-blank rows were found | Stop and report |
| TOO_MANY_COLUMNS | The table has more than 60 columns | Ask for a narrower table |
| OUTPUT_EXISTS | The `--output` path already exists | Choose a new name |
| SAME_AS_INPUT | The `--output` path is the input file | Choose a new name |
| OUTPUT_WRITE_FAILED | The output folder is missing or not writable | Ask for a valid path |

## Refuse / stop when

- The file is xlsx, xls, ods, docx, pdf or any other binary format. Stop, name the format, and do not convert it.
- The script returns INPUT_TOO_LARGE or INVALID_UTF8. Stop and ask for a smaller UTF-8 file.
- The HTML table uses `colspan` or `rowspan`. The script ignores spans, which shifts cells, so stop and ask for a flattened table.
- The user asks to overwrite an existing file or the input file. Refuse that clause only: print the table to stdout, set the reply status to partial, and list the refused clause under Open questions.
- The user asks for totals, sorting, unit conversion or changed values. That is outside this skill: deliver the conversion only, set the reply status to partial, and list the request under Open questions.
- The user asks you to fill a missing cell with an invented value. Do not invent; keep the padding and list the row.
