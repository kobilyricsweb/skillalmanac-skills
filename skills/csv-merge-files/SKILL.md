---
name: csv-merge-files
description: Merges several CSV files into one new CSV, either by stacking them under a unified header or by joining them on a key column, and reports per-file row counts, duplicate keys and dropped rows. Use when the user asks to merge, combine, stack, append or join CSV files and must not lose rows silently. Do not use for Excel workbooks, database tables, fuzzy or case-insensitive key matching, files over 2 MB each, or editing a CSV in place.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# CSV merge files

This skill runs `scripts/csv_merge.py` on the user's CSV files. The script
either stacks the files under one header or joins them on a key column, writes
a new CSV, and prints counts. It never edits its inputs and never overwrites
an existing file.

Shipped files: `scripts/csv_merge.py` (the script), `fixtures/orders_jan.csv`,
`fixtures/orders_feb.csv` (has an extra `coupon` column), `fixtures/orders_mar.csv`
(repeats order 1005 from feb), and `fixtures/customers.csv` (sample join
target). The fixtures are for a dry run only; never merge them into user data.
`LICENSE.txt` holds the license text.

## Workflow

1. **Intake.** Collect the input file paths (two or more), the mode (`stack` or
   `join`), the output path (a file that does not exist yet), and for `join` the
   key column name and `inner` or `left`. Output: a short intake list. If any
   required fact is missing, stop and ask for it (see Refuse / stop when).
2. **Choose the mode** with the decision table below. Output: the mode and flags.
3. **Check the inputs** against the intake table: at least two files, each at
   most 2 MB, UTF-8 text, a unique non-empty header, and every data row with the
   same cell count as its header. Output: pass, or the first failing file name.
   The script performs these checks; this step is to catch them before the run.
4. **Run the script** from the skill folder with the command line in the
   Script contract section. Output: the one-line JSON report and an exit code.
5. **Read the exit code** with the exit code table. Output: the next action.
6. **Check the counts.** Stack: `rows_written` must equal the sum of the
   per-file `rows` values, and `rows_dropped` must be 0. Join: `rows_dropped`
   must equal the sum of the per-file `rows_dropped` values. If either check
   fails, stop and report the mismatch; do not hand over the file.
7. **Write the answer** in the output contract format.

## Decision table

| Situation | Mode and flags |
|---|---|
| Same kind of rows in several exports (monthly files, one per region) | `stack` |
| Need to know which file each stacked row came from | `stack --source-column source_file` (name is the user's choice; must not already exist) |
| Add columns from one file to rows of another by a shared id | `join --key <key-column> --how left` |
| Keep only rows whose key appears in every file | `join --key <key-column> --how inner` |
| Key is expected to be unique in every file | `join`; any `duplicate_keys` above 0 is a finding to report |

Thresholds (working values, not a published spec):

| Check | Value | Response when exceeded |
|---|---|---|
| Input size per file | 2 MB (2,097,152 bytes) | Stop; ask for a smaller file or a split |
| Input files per run | 2 or more | Stop if fewer than 2 |
| Dropped share of input rows (join) | more than 5 percent | State the share first in the answer, then list each file |
| Duplicate keys in a file (join) | any count above 0 | List the file and count; the rows multiply in the output |

## Exit code table

| Exit | Meaning | Next action |
|---|---|---|
| 0 | Run completed; no rows dropped and no duplicate keys | Report the counts |
| 1 | Run completed; rows were dropped or duplicate keys were found. The output file is written. | Report every file with a non-zero `rows_dropped` or `duplicate_keys`; ask the user to confirm before using the output |
| 2 | Usage or input error. No output file is written. | Quote the one-line JSON error and stop |

## Script contract

Command line, run from the skill folder:

```
python -I scripts/csv_merge.py stack [--source-column <name>] --output <output-file> <input-file> <input-file> [<input-file> ...]
python -I scripts/csv_merge.py join --key <key-column> [--how inner|left] --output <output-file> <input-file> <input-file> [<input-file> ...]
```

Arguments:

- `stack` or `join`: the mode (required).
- `--source-column <name>` (stack only): adds a final column with each row's input file name.
- `--key <key-column>` (join only, required): column present in every input header.
- `--how inner|left` (join only, default `inner`): `left` keeps every row of the first input.
- `--output <output-file>` (required): a new file. The run exits 2 if it exists.
- `<input-file>` (two or more): read-only inputs. The first input is the base for `join`.

Report (one line of JSON on stdout). Keys: `mode`, `key`, `how` (join only),
`columns`, `files` (each with `file`, `rows`, and for join `duplicate_keys` and
`rows_dropped`), `rows_written`, `rows_dropped`. Stack always reports
`rows_dropped` 0.

Errors: one line of JSON on stderr, `{"error": "..."}`, exit 2.

Exit codes: 0 ok with no findings; 1 ok with findings; 2 usage or input error.

## Output contract

The answer to the user has these headings, in this order:

1. `## Result`: mode, key and how (join only), exit code, output file name.
2. `## Per-file counts`: a table. Stack columns: `file`, `rows`. Join columns:
   `file`, `rows`, `duplicate_keys`, `rows_dropped`.
3. `## Totals`: `columns`, `rows_written`, `rows_dropped`.
4. `## Findings`: one bullet per file with a non-zero `duplicate_keys` or
   `rows_dropped`; write `None` when the exit code is 0.

## Refuse / stop when

- Fewer than two input files are given.
- Any input is over 2 MB, is not valid UTF-8, or is not a readable file.
- The output path already exists or is the same path as an input. Ask for a new
  output path; never overwrite.
- A header has an empty name or a duplicate name, or a data row has a different
  cell count from its header. Report the file and the data row number; ask the
  user to fix the source file.
- `join`: the key column is missing from any input, or a non-key column name
  appears in more than one input. Ask the user to rename the column; do not
  guess a suffix.
- The user asks for fuzzy, case-insensitive or partial key matching. The script
  matches keys exactly after trimming spaces. Refuse that clause, keep the rest
  of the job, and list the clause under Findings.
- The user asks to edit an input in place. Refuse; write the merge to a new file.

## Notes on behavior

- Empty key cells never match, in either direction. In `left` mode an empty-key
  base row is kept with empty cells for the other columns.
- Duplicate keys multiply output rows, as a SQL join does. Report the count
  before the user relies on the output.
- Stack mode never checks for duplicate rows or keys. Repeated rows are written
  as they are and never reported; `duplicate_keys` exists in join mode only.
- Cells are copied as text; the script does not reformat numbers or dates.
