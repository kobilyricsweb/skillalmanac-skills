---
name: html-table-extractor
description: Extracts tables from one local HTML file into JSON or CSV files, expanding rowspan and colspan and reporting every merged cell, ragged row, and missing header as a finding. Use when a user has an HTML page with data tables and needs them as JSON or CSV, or asks how to convert an html table to json. Do not use for HTML without table elements, for fetching a URL, for tables rendered by JavaScript after page load, or for XLSX or DOCX tables.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# HTML table extractor

Use `scripts/html_tables.py` to turn each top-level `<table>` in one local HTML file into rows of text. The script never fetches anything, never overwrites a file, and reports every cell it had to expand.

## Workflow

1. **Intake.** Confirm the input is one local `.html` file, UTF-8 encoded, at most 2 MB. Ask which format is wanted: `json` (one file) or `csv` (one file per table plus `index.json`). Output: the input path, the format, and the output path or directory.
2. **Check output targets.** A JSON output path must not exist. A CSV output directory must already exist and must not already contain `table-NN.csv` or `index.json` for the table count you expect. If a target exists, choose a new name; never delete or overwrite. Output: confirmed target.
3. **Run the script** with the command line in the Script contract section. Output: one stdout summary line and the exit code.
4. **Act on the exit code** using the table in step 4 below. Output: the decision.
5. **Review findings.** For each finding in the output, list table index, row, column, code, and detail. Output: a findings table (see Output contract).
6. **Hand back.** Name the output files, the table count, the row count, and the finding count. State that merged cells were expanded by copying the text into every covered position. Output: the final summary.

### Exit code decisions

| Exit | Meaning | Action |
|---|---|---|
| 0 | Tables extracted, zero findings | Deliver the output. |
| 1 | Tables extracted, one or more findings | Deliver the output with the findings table. Ask the user to confirm before the data is used for analysis. |
| 2 | Usage, input, or output error | Stop. Quote the one-line JSON error. Do not retry with a different output path unless the user supplies one. |

### Finding codes

| Code | Trigger | Action |
|---|---|---|
| MERGED_COLSPAN | A cell has colspan above 1. Its text is copied into each covered column. | Confirm the copies are intended. |
| MERGED_ROWSPAN | A cell has rowspan above 1. Its text is copied into each covered row below it. | Confirm the copies are intended. |
| OVERLAP | A colspan cell lands on a column still held by a rowspan from an earlier row. | Treat that table as unreliable and check it against the source. |
| SPAN_CLAMPED | A colspan or rowspan value is not a positive integer (set to 1) or is above 1000 (capped at 1000). Working value for the cap. | Check the table against the source. |
| RAGGED_ROW | A row is narrower than the widest row. It is padded with empty strings. | Check whether the source omitted cells. |
| NO_HEADER | No header row was found. `header` is null. | Ask the user whether the first row is a header. |
| NESTED_TABLE | A table sits inside another table. Its text is flattened into the outer cell. | Check the outer cell. |
| EMPTY_TABLE | No data rows remain after the header is removed. | Report the table as empty. |
| NO_TABLES | The file contains no table element. Written to `file_findings`. | Stop and report. Exit code is 1. |

### Header rule

A header is taken from the first table row only if every cell in that row is a `th`. If the first row is not all `th`, the first `thead` row is used. Otherwise `header` is null. The header row is removed from `rows`, but its findings keep their row numbers.

## Thresholds

| Item | Value | Note |
|---|---|---|
| Input size limit | 2 MB (2,097,152 bytes) | Working value. Larger files exit 2. |
| Span cap | 1000 | Working value. Larger spans are capped and flagged. |
| Row numbers | Non-empty `tr` elements, counted from 1, header row included | Fixed by the script. |
| Column numbers | Expanded grid position, counted from 1 | Fixed by the script. |

## Script contract

Command for JSON (one new file):

```
python -I "<skill-folder>/scripts/html_tables.py" "<input-file>" --format json --out "<output-file>"
```

Command for CSV (existing directory):

```
python -I "<skill-folder>/scripts/html_tables.py" "<input-file>" --format csv --out-dir "<output-dir>"
```

Arguments: `input_file` (positional), `--format json|csv` (required), `--out` (JSON only), `--out-dir` (CSV only).

Exit codes: 0 no findings, 1 findings present (outputs written), 2 usage, input, or output error.

Stdout summary, one line: `{"status": "ok|findings", "tables": n, "rows": n, "findings": n, "outputs": [...]}`.

Stderr on exit 2: one line `{"error": "<message>"}`.

## Output contract

JSON file keys: `source_name`, `table_count`, `row_count`, `findings_count`, `file_findings`, and `tables`. Each table has `index`, `caption`, `header`, `rows`, `row_count`, `column_count`, and `findings`. Each finding has `code`, `row`, `col`, and `detail`. `row_count` counts data rows only.

CSV mode writes `table-NN.csv` (header row when present, then data rows) and `index.json`. `index.json` repeats the top-level keys and each table's `index`, `caption`, `row_count`, `column_count`, `findings`, and `file` name, without `rows` or `header`.

Findings table, as delivered to the user: `table`, `row`, `col`, `code`, `detail`.

## Refuse / stop when

- The input is missing, not UTF-8, larger than 2 MB, or cannot be parsed (exit 2).
- The output path already exists. Choose a new name; do not delete the existing file.
- The user asks for a URL to be fetched or a page to be rendered. This skill reads local files only.
- `NO_TABLES` is reported for a page whose tables are created by JavaScript. Say that the source HTML has no table markup to extract.
- The user asks for XLSX, DOCX, or PDF tables. This skill handles HTML only.

## Files shipped

- `scripts/html_tables.py`: the extractor (Python 3.9+ stdlib).
- `fixtures/two_tables.html`: a two-table sample used for the smoke run.
- `LICENSE.txt`: Apache License 2.0.
