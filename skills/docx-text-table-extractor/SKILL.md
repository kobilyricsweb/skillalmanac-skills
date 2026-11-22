---
name: docx-text-table-extractor
description: Extracts paragraphs with their style names and every top-level table from a .docx file into a text file and one CSV per table, then prints a JSON summary of headings, tables and rows. Use when a user needs data out of a Word document, such as a table moved into a spreadsheet, paragraphs with their heading styles, or a count of tables and rows. Do not use for .doc or .pdf files, for editing or writing Word files, for nested or floating tables, or for reading layout, images or comments.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# docx-text-table-extractor

Runs `scripts/docx_extract.py` on one .docx file and reports what it wrote. The script reads only the
package parts `word/document.xml` and `word/styles.xml`. It never writes to the input and never
overwrites an output file.

## Workflow

1. **Check the intake.** Confirm the input is a `.docx` file that exists, and that the output
   directory exists, is not the input file's folder, and does not already contain `paragraphs.txt`
   or any `table-NNN.csv` name the run will produce. Output: one line, `input ok` or the reason it
   failed. If the output directory already holds those names, stop and ask for a new folder. Do not
   delete the old files.
2. **Run the script** with the command in the Script contract section. Output: the JSON summary on
   stdout (or a one-line JSON error on stderr) and the exit code.
3. **Map the exit code** with the decision table below. Exit 2 means no output was written, except
   the rare race case in the error table. Output: the status line.
4. **Report findings.** For each entry in `findings`, state the code, the table number and the
   count, and say that the CSV for that table may not match the visual grid. Output: the findings
   table in the output contract.
5. **Hand over the files.** List `files_written` with the output directory. Remind the user that
   paragraph text lives only in `paragraphs.txt` and the CSVs. Output: the final report.

## Decision and threshold table

| Check | Value | Result when crossed |
|---|---|---|
| Input file size | 2 MB (2,097,152 bytes), working value | `FILE_TOO_LARGE`, exit 2 |
| Zip entries in the package | 2,000, working value | `ZIP_LIMIT`, exit 2 |
| Total uncompressed size of all entries | 20 MB, working value | `ZIP_LIMIT`, exit 2 |
| Uncompressed size of one read part | 10 MB, working value | `ZIP_LIMIT`, exit 2 |
| `gridSpan` value in a table cell | 1 to 64, working value | `XML_INVALID`, exit 2 |
| Findings present | one or more entries in `findings` | status `findings`, exit 1, outputs kept |

Exit codes: 0 means status `ok`, 1 means status `findings`, 2 means an error. Outputs are written
only after every check passes, so an exit 2 leaves no new files in the normal case.

## Script contract

Command line, with the user's own paths:

```
python -I "<skill-folder>/scripts/docx_extract.py" "<input-file>" "<output-dir>"
```

Arguments: `<input-file>` is the .docx path. `<output-dir>` is an existing folder, different from the
input's folder. Exactly two arguments are accepted.

Written files: `paragraphs.txt` and `table-001.csv`, `table-002.csv` and so on, in document order.
Files are UTF-8 without BOM, `\n` line endings. CSV uses minimal quoting.

Summary keys on stdout (JSON, indented): `status`, `input` (basename), `headings`, `paragraphs`,
`tables`, `rows`, `table_list` (each entry: `table`, `rows`, `columns`, `file`), `files_written`,
`findings` (each entry: `code`, `table`, `count`).

Error keys on stderr (one line): `error` and `message`. Error codes:

| Code | Meaning | Exit |
|---|---|---|
| `USAGE` | Wrong number of arguments | 2 |
| `FILE_MISSING` | The input path is not a file | 2 |
| `NOT_DOCX` | No `.docx` extension, not a zip package, a missing `word/document.xml`, or an unreadable part | 2 |
| `FILE_TOO_LARGE` | Input is over 2 MB | 2 |
| `ZIP_LIMIT` | Entry count, total size or part size is over the cap | 2 |
| `DTD_FOUND` | A part declares a DTD or an entity | 2 |
| `XML_INVALID` | A part is not well-formed UTF-8 XML, has no body, or has a bad `gridSpan` | 2 |
| `OUTPUT_EXISTS` | An output file name already exists | 2 |
| `OUTPUT_PATH_INVALID` | The output folder is missing, is the input's folder, or a write failed | 2 |

Race case: if another process creates an output file between the check and the write, the script
exits 2 with `OUTPUT_EXISTS` and may leave earlier files from the same run. Report those files.

Findings codes:

| Code | Meaning | How the CSV shows it |
|---|---|---|
| `MERGED_HORIZONTAL` | A cell spans two or more grid columns (count = cells) | Text in the first column, empty cells to its right |
| `MERGED_VERTICAL` | A cell carries a vertical merge, restart or continuation (count = cells) | Text only in the restart cell, empty below it |
| `NESTED_TABLE` | A cell contains a table (count = cells) | Nested table text is not extracted |

## Output contract

`paragraphs.txt`: one line per non-empty paragraph, as `style<TAB>text`. Style is the name from
`styles.xml` (for example `heading 1`), or `Normal` when the paragraph has no style. An unknown
style ID is written as-is. A table appears as the line `(table)<TAB>see table-NNN.csv` at its
position. Whitespace runs are collapsed to one space. Tab and line-break elements become a space.

`table-NNN.csv`: one row per table row, cells in grid order. Cell text joins its paragraphs with a
single space. Rows are padded with empty cells to the widest row in the table.

Final report to the user, in this order:

| Section | Content |
|---|---|
| Status | `ok`, `findings` or `error`, with the exit code |
| Counts | headings, paragraphs, tables, rows (from the summary) |
| Findings | one row per finding: code, table, count |
| Files | each name in `files_written` with the output folder |
| Open questions | anything not extracted (nested tables, text boxes, content controls) |

## Refuse or stop when

- The input is not a `.docx` (for example `.doc`, `.pdf`, `.docm` with macros, or a renamed file).
- The output directory is the input's folder, or the user wants an existing output file replaced.
  Ask for a new folder or a new name. The script never overwrites.
- The script returns `DTD_FOUND` or `ZIP_LIMIT`. Do not raise the caps or remove the DTD check.
  Tell the user the document is outside what this tool reads.
- The user asks to edit, save, or write a Word document. This skill only reads .docx files.
- The user asks to extract text from a file that is only a scan or an image. The script reads text
  runs only, so the output would be empty.

## Limits of this tool

It does not check that the numbers, dates or names in a table are correct. It does not verify
visual layout, cell borders, colors, images, charts, headers, footers, footnotes, comments or
tracked changes beyond the rules above (tracked insertions are kept, tracked deletions are
skipped). It does not read text boxes or content controls (`w:sdt`) at the body level. It does not
neutralize spreadsheet formulas: a cell that starts with `=`, `+`, `-` or `@` is written as-is.
It does not check deliverability or security beyond the caps and the DTD refusal.

## Shipped files

- `scripts/docx_extract.py`: the extractor described in the script contract.
- `fixtures/build_fixture.py`: builds a small test .docx at runtime to the .docx path the user names
  (add `--merged` for the merged-cell sample, or `--hostile` for a UTF-16 file with a DOCTYPE, which
  the extractor must refuse). Use it to check the install; it stores no binaries.
- `LICENSE.txt`: Apache License 2.0.
