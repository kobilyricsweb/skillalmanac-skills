---
name: docx-paragraph-diff
description: Compares two Word .docx files paragraph by paragraph and table cell by table cell, then lists each changed, added, or removed text with its old and new value. Use when a user asks to compare two Word documents, highlight what changed between two .docx drafts, or find edits in a contract, memo, or report without Microsoft Word. Do not use for PDF or Google Docs files, tracked-change or comment review, formatting or style differences, or text inside headers, footers, footnotes, or text boxes.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# docx-paragraph-diff

Compares the visible text of two .docx files and lists what differs. The script
`scripts/docx_diff.py` does the comparison; you run it, read its JSON, and write the report.

## Workflow

1. **Confirm the two files.** Need: the earlier file (`<old-docx>`) and the later file
   (`<new-docx>`), both .docx. Output: the two file names in order. If either is missing,
   stop and use the question list in the Refuse section.
2. **Check size and type.** Each file must end in `.docx` and be 2 MB (2,097,152 bytes)
   or smaller. Output: one line per file, `ok` or the reason it failed.
3. **Choose a report path.** Pick a `<report-json>` name that does not exist yet. Output:
   the chosen path. Never reuse an existing file.
4. **Run the script.** Output: the exit code and the JSON printed to stdout.
5. **Read the exit code.** 0 means identical, 1 means differences, 2 means input error.
   On 2, report the `message` field and stop. Do not guess a diff.
6. **Write the report** in the output contract below. Output: the Result block and the
   Differences table, with one row per entry in `differences`.

## Thresholds and rules

| Item | Value | Basis |
|---|---|---|
| Input file size | 2 MB maximum (2,097,152 bytes) | working value |
| Zip entries per package | 2,000 maximum | working value |
| Uncompressed package size | 20 MB maximum | working value |
| Paragraph match | exact text equality, difflib, no autojunk | fixed |
| Replaced block | i-th old paragraph pairs with i-th new paragraph; extra old lines are `paragraph_removed`, extra new lines are `paragraph_added` | fixed |
| Table cell match | same table number, row number, and cell number (1-based) | fixed |
| Formatting | ignored; bold or style-only edits produce no entry | fixed |
| Tracked insertions | counted as text; tracked deletions are not | fixed |

## Output contract

The report is a Markdown reply with two headings, in this order.

```
## Result
Status: complete | partial
Result: differences | identical
Files: <old_file> -> <new_file>
Paragraphs: old <n>, new <n>. Tables: old <n>, new <n>.
Counts: paragraph_changed <n>, paragraph_added <n>, paragraph_removed <n>, cell_changed <n>, cell_added <n>, cell_removed <n>.

## Differences
| # | Kind | Location | Old text | New text |
```

- `Result` and `Status` values are fixed words. `Status: partial` is used only when a
  requested clause was refused (see Refuse). Add `## Open questions` after the table when
  it is partial.
- `Kind` is one of the six kinds in the table below. `Location` is `body paragraph <old_index>`
  (or `body paragraph <old_index> -> <new_index>` when the index differs), or
  `table <table>, row <row>, column <col>` for cells.
- Empty old or new text is written as `(empty)`. Text is copied exactly, never shortened.
- If `differences` is empty, the Differences table is replaced by one line: `No text differences.`

## Difference kinds

| Kind | Index fields set | Meaning |
|---|---|---|
| `paragraph_changed` | old_index, new_index | Paragraph text differs at an aligned position |
| `paragraph_added` | new_index | Paragraph exists only in the new file |
| `paragraph_removed` | old_index | Paragraph exists only in the old file |
| `cell_changed` | table, row, col | Cell text differs at the same position |
| `cell_added` | table, row, col | Cell exists only in the new file |
| `cell_removed` | table, row, col | Cell exists only in the old file |

Body paragraphs and table cells are reported separately. A paragraph inside a table is
never counted as a body paragraph.

## Refuse / stop when

- Either input does not end in `.docx`, or is a legacy `.doc`, `.pdf`, or Google Docs export.
  Stop; the script cannot read those.
- Either file is larger than 2 MB, or the script exits 2 with a `message` such as
  "input file is larger than 2 MB", "not a readable .docx (zip) package",
  "word/document.xml is missing", "DTD or entity declarations are refused", or
  "word/document.xml is not well-formed UTF-8 XML". The DTD refusal scans the raw bytes
  in UTF-8, UTF-16 LE and UTF-16 BE; a UTF-16 or UTF-32 byte-order mark or any NUL byte
  gives the second message. Stop and report the message.
- The file is password-protected or encrypted (exit 2). Ask the user for an unlocked copy.
- `--out` names an existing file or one of the inputs. Choose a new name; never overwrite.
- The user asks for more than two files at once. Ask which pair to compare.
- The user asks for tracked-change or comment review, formatting or style differences, or
  a visual redline. Refuse only that clause: finish the text comparison, set
  `Status: partial`, and list the refused item under `## Open questions`.
- Missing intake, as a numbered question list: (1) which file is the earlier version,
  (2) which file is the later version, (3) where the report should be saved.

## Script contract

`scripts/docx_diff.py`, Python 3.9+ standard library only. It opens files read-only, uses no
network, no subprocess, and no eval or exec.

- Arguments: `old` (positional), `new` (positional), `--out <report-json>` (optional, new file only).
- Output (stdout, one JSON object): `result` (`differences`, `identical`, or `error`),
  `old_file`, `new_file` (base names only), `paragraphs` (`old`, `new`), `tables` (`old`, `new`),
  `counts` (the six kinds above), `differences` (list of objects with `kind`, `old_index`,
  `new_index`, `table`, `row`, `col`, `old_text`, `new_text`; unused fields are null).
- Error output (stdout, one line): `{"result": "error", "message": "<text>"}`.
- Exit codes: 0 = identical, 1 = differences found, 2 = usage or input error.
- Command line: `python -I scripts/docx_diff.py "<old-docx>" "<new-docx>" --out "<report-json>"`

Shipped with the skill:

- `scripts/docx_diff.py`: the comparison script described above.
- `fixtures/make_fixtures.py`: builds a smoke-test pair (`old.docx`, `new.docx`) into an empty
  folder at runtime. Command: `python -I fixtures/make_fixtures.py "<new-empty-folder>"`.
  Its pair has two changed body paragraphs (2 and 4), one changed cell (table 1, row 2,
  column 2), and one paragraph that only became bold, which must not be listed. It also
  writes `hostile.docx` (UTF-16 with a DOCTYPE and ENTITY), which the script must refuse.
- `LICENSE.txt`: Apache-2.0 license text.

## Limits

- Only `word/document.xml` is read. Headers, footers, footnotes, endnotes, comments, and
  text boxes are not compared.
- Matching is positional after alignment, not semantic. A moved paragraph shows as a
  removal and an addition, not as a move.
- A merged cell is matched by its position in the row, so merges can shift later columns.
- Empty paragraphs count as paragraphs and can appear as changes.
- The script does not check whether the files are the right versions, who edited them,
  or whether the layout or visual appearance matches.
