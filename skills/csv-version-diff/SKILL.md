---
name: csv-version-diff
description: Compares two versions of the same CSV export by key column and reports added, removed and changed rows with per-cell changes, schema changes, type drift and numeric tolerance, as strict JSON plus an optional Markdown report. Use when the user says what changed between these two CSVs, diff the old and new export, compare file versions, or which rows and columns differ. Do not use to profile one file, find duplicates, audit a data contract, check train/test leakage or merge files.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual fallback at the end.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# CSV version diff

Answer one question exactly: between the old and the new version of this table, what changed? Rows are matched by a key the user confirms, never by position. The script does the counting; you decide what the result means and say what it could not check.

## Workflow

```
- [ ] 1 Get both files and the key
- [ ] 2 Decide which tolerances to switch on (default: none)
- [ ] 3 Run the script
- [ ] 4 Read warnings before the numbers
- [ ] 5 Resolve questions with the user (renames, key problems)
- [ ] 6 Report
```

1. **Files and key.** You need the old file, the new file and the column or columns that identify one row. If the user has not named a key, do not guess and do not compare row by row. Run `python scripts/csv_version_diff.py OLD NEW --suggest-keys`, show the candidates (columns that are filled and unique in both files) and ask which one is the real identifier. Repeat `--key` for a composite key. Never write over either input; save reports to new paths.
2. **Tolerances.** All are off unless the user asks. Use the table below.
3. **Run.** `python scripts/csv_version_diff.py OLD NEW --key ID [--abs-tol X] [--rel-tol X] [--trim] [--ignore-case] [--null-tokens NA,null] [--out report.json] [--markdown report.md]`. JSON goes to stdout. Exit 0 means identical or equivalent, 1 differences, 2 a problem you must fix (the message says what). Run the script as it is; do not edit it to make a result come out.
4. **Warnings first.** Read `warnings[]` and `complete` before quoting any count. If `complete` is false, rows were left out (duplicate or blank keys) and "no changes" must not be said without that qualifier.
5. **Questions.** Ask, do not decide: every `renamed_candidate`, every `key_format_drift`, every `type_changed` whose `direction` is `to_text` or `from_text`. Re-run only if the user's answer changes the key or the options.
6. **Report** in the fixed shape at the end.

## Change classes

| Class | Where it appears | Meaning |
|---|---|---|
| column added / removed | `schema_changes[]` | header present in one file only |
| renamed candidate | `schema_changes[]` | a removed and an added column hold the same value in at least 90 percent of matched rows (at least 3 rows compared); a question, never applied |
| type changed | `schema_changes[]` | inferred type moved (int, float, date, text); lists up to N new values that do not fit the old type |
| column order changed | `schema_changes[]` | same columns, different order; not a data change |
| row added / removed | `rows`, `examples[]` | key only in the new / only in the old file |
| value changed | `column_change_counts`, `examples[]` | same key, different cell after the active options |
| order only | `verdict: order_only` | same keys and values, rows or columns reordered |

A row counts as changed when at least one non-key cell changed. Key columns are never compared as values.

## Tolerance and normalisation

| Option | Effect | Turn on when |
|---|---|---|
| none (default) | any text difference is a change, except below | always the starting point |
| built in, always on | numbers equal in value but written differently ("5.00" and "5.0", " 5" and "5") are counted as `format_only_cells`, not changes; two missing values are equal | cannot be turned off; they are still listed |
| `--abs-tol X` | numeric cells within X are equal (`within_tolerance_cells`) | the user says tiny rounding or float noise does not matter; ask for X |
| `--rel-tol X` | numeric cells within X times the larger magnitude are equal | values span orders of magnitude |
| `--trim` | whitespace stripped and collapsed in non-key cells (`normalised_cells`) | stray spaces from the export tool |
| `--ignore-case` | case-folded comparison of non-key cells | casing of labels is not meaningful |
| `--null-tokens` | extra spellings of missing (NA, null, N/A) | the export writes missing values as text |

Never choose a tolerance size yourself and never apply one silently: say which options were on in the report. A number with a leading zero ("007", "00123") is an identifier and is compared as text, never as a number.

## What the script checks

| Check | Warning code | Threshold |
|---|---|---|
| duplicate keys in a file | `duplicate_keys_old` / `_new` | any; those keys are excluded from both sides |
| blank key | `blank_keys_old` / `_new` | any; row excluded |
| keys differing only by case, spaces or leading zeros inside one file | `near_duplicate_keys` | any |
| removed and added keys that match after trim, case-fold and dropping leading zeros | `key_format_drift` | any; probably a reformatted key, not real adds and removes |
| row count change | `row_count_shift` | more than 20 percent (`--row-shift-pct`) |
| share of missing values in a column | `null_rate_jump` | 20 points or more (`--null-jump`) |
| different delimiter or encoding between files | `delimiter_differs`, `encoding_differs` | any |
| byte-order mark; non-UTF-8 text read as cp1252 or latin-1 | `bom_present`, `encoding_fallback` | any |
| rows with the wrong number of fields | `ragged_rows` | any; padded or cut |
| repeated or whitespace-padded header names | `duplicate_header`, `header_whitespace_trimmed` | any |

A `key_format_drift` or a large `row_count_shift` together with many added and removed rows usually means the key changed format or the export was filtered, not that the data changed. Say so before listing adds and removes.

## Output contract

Strict JSON on stdout (ASCII only, no NaN). Top level: `verdict` (`identical`, `equivalent`, `order_only` or `differences`), `complete`, `inputs`, `key`, `options`, `schema_changes[]`, `rows{old_total,new_total,excluded_old,excluded_new,common,added,removed,changed,unchanged,cell_changes,order_changed}`, `column_change_counts{column: {changed_cells, format_only_cells, within_tolerance_cells, normalised_cells, null_to_value, value_to_null, whitespace_or_case_only, numeric_changes, max_abs_delta}}`, `column_summary[]`, `examples[]` (kind `changed_cell`, `added_row` or `removed_row`, at most N each, `--examples`), `warnings[]`. Field details are in [references/output-fields.md](references/output-fields.md); read it when you must quote a field you are unsure of or build a report from the JSON by hand.

## Report format

```
Compared: <old> (<rows> rows) against <new> (<rows> rows), key <columns>, options <none or list>
Verdict: <verdict>, complete: <yes/no and why>
Schema: <columns added, removed, type changes, rename questions>
Rows: <added>, <removed>, <changed>, <unchanged>
Where the changes are: <top columns by changed_cells, 2 or 3 examples with key, old, new>
Warnings: <each warning in one line, or none>
Questions for you: <renames, key drift, type changes>
Not checked: <semantic meaning of changes, rows excluded by key problems, anything outside the key-matched rows>
```

If the user wants a file, pass `--markdown path.md` to a new path; it carries the same sections.

## Scripts

- `scripts/csv_version_diff.py` - run it. Reads both files completely into memory and writes JSON to stdout; writes `--out` and `--markdown` files only to new paths, and refuses any path that is the same file as an input, even with `--force`.

## Limits

- Both files are loaded into memory; very large files (more than a few hundred MB) need a database or a sampled key list instead.
- Types are inferred from the values: int, float, date (ISO-like and day/month/year patterns, recognised by shape only, never parsed or compared as dates) and text. Date cells are compared as text.
- Rows excluded for duplicate, blank or ambiguous keys are not diffed; the counts are in `rows.excluded_*`.
- Rename detection compares values only for keys present in both files and needs at least 3 non-blank rows; it can miss a rename where values were also edited, and can propose a wrong pair when two columns share values.
- Multi-line cells and quoting follow Python's csv module; malformed quoting stops with an error rather than guessing.
- It says what differs, not whether a difference is right.

## If the script cannot run

Open both files, confirm the key is unique and non-blank in each, and compare headers first. Sort both by key, then list keys missing on either side, and compare the remaining rows column by column, noting numeric versus text differences. State plainly that the comparison was manual and which columns you did not check.
