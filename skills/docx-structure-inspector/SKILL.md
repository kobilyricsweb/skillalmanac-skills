---
name: "docx-structure-inspector"
description: "Inspects a Word .docx file for structure problems: heading outline, heading level skips, empty paragraphs, tables, images, comments, tracked insertions and deletions, and the authors behind them. Use when a .docx arrives with hidden review marks, odd heading levels or blank paragraphs and needs a fast structural report before editing or publishing, or when checking a Word file before it is sent on. Do not use for writing or editing Word content, converting documents to PDF, or judging how a page looks."
license: Apache-2.0
compatibility: Python 3.9+ standard library only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# docx-structure-inspector

Reads a .docx file as a zip container, parses two XML parts, and reports the
structure counts and findings listed below. The file is never modified.

## Files in this skill

- `scripts/docx_inspect.py` the inspector (the only tool you run).
- `fixtures/make_fixture.py` builds a small smoke-test .docx in the system temp
  folder. Use it only to check that the script works in a new environment.
- `LICENSE.txt` Apache-2.0 license text.

## Workflow

1. **Confirm the input.** Output required: the absolute path of one .docx file.
   If the path is a folder, a glob, or several files, stop and ask for one file.
2. **Run the inspector once per file.** Output required: the exit code and the
   JSON text or the one-line error. Command:
   `python -I scripts/docx_inspect.py "<path-to-file.docx>"`
3. **Map the exit code.** Output required: one of the three labels in the table below.
4. **Apply the finding thresholds.** Output required: one line per non-zero
   count, using the rules in the thresholds table.
5. **Write the report** using the output contract below. Output required: the
   report file or message, with every heading present, even when a section is empty.
6. **State the limits.** Output required: the "Not checked" section, every time.

## Exit code decisions

| Exit code | Label | What to do |
|---|---|---|
| 0 | clean | Report counts. Say no findings were found. |
| 1 | findings | Report every non-zero finding line. Do not edit the file. |
| 2 | input error | Report the JSON error text and stop. Do not guess the counts. |

## Finding thresholds

The script sets `findings` to the sum of the five values below. Any value
above zero is a finding. The thresholds are fixed; they are not industry values.

| Field | Finding when | Working meaning |
|---|---|---|
| `comments` | at least 1 | Review comments are still in the file |
| `tracked_insertions` | at least 1 | Insertions still tracked, not accepted |
| `tracked_deletions` | at least 1 | Deletions still tracked, not accepted |
| `heading_skips` | at least 1 entry | A heading jumps more than one level (first heading below H1 counts) |
| `empty_paragraphs` | at least 1 | Paragraph with no text, drawing, picture, object, break or tab |

## Script contract

Command: `python -I scripts/docx_inspect.py <file.docx>`

Exactly one positional argument. Use forward slashes or quoted Windows paths.

Input caps (working values, not standards):

| Check | Limit | Refusal message starts with |
|---|---|---|
| File size | 2 MB | file is larger than 2 MB |
| Zip entries | 2000 | zip has more than 2000 entries |
| Declared part size | 20 MB | declares more than 20 MB |
| Compression ratio (parts over 1 MB) | 100 to 1 | has a compression ratio above 100 to 1 |
| Decompressed part size | 8 MB | exceeds 8 MB after decompression |
| XML nesting depth | 200 | nests deeper than 200 levels |

Exit codes: 0 no findings, 1 findings present, 2 usage or input error.

Output keys (single JSON object, in this order):

| Key | Type | Meaning |
|---|---|---|
| `paragraphs` | int | every w:p in word/document.xml, including table cells |
| `empty_paragraphs` | int | paragraphs with no text and no drawing, pict, object, br or tab |
| `tables` | int | every w:tbl |
| `images` | int | every drawing plus every pict element |
| `comments` | int | every w:comment in word/comments.xml (0 when the part is absent) |
| `tracked_insertions` | int | every w:ins, including paragraph-mark insertions |
| `tracked_deletions` | int | every w:del, including paragraph-mark deletions |
| `heading_outline` | list | objects with `paragraph`, `level` (1 to 9), `text` (first 120 characters) |
| `heading_skips` | list | objects with `paragraph`, `from_level`, `to_level` |
| `authors` | list | sorted unique names from w:ins, w:del and comments, max 50 |
| `findings` | int | sum of comments, insertions, deletions, skips and empty paragraphs |

Headings are recognised only by a paragraph style ID of `Heading1` to
`Heading9` (case-insensitive). A file whose headings use other style IDs shows
an empty outline. The script does not read styles.xml, headers, footers or footnotes.

Error output is one JSON line, for example `{"error": "file not found"}`, and exit code 2.
The script writes nothing to disk. Its only output is stdout, so an output path
can never resolve to an input path.

## Output contract for the report

Use these headings in this order:

1. `## Summary`: one line with the file name, exit label, and `findings` count.
2. `## Counts`: a table with columns `Field` and `Value`, one row per count key
   from `paragraphs` to `tracked_deletions`.
3. `## Heading outline`: a numbered list, one line per heading, as
   `level N: text (paragraph P)`. Write "none found" when the list is empty.
4. `## Findings`: one bullet per non-zero threshold row, with the value.
   Write "none" when `findings` is 0.
5. `## Authors`: the names from `authors`, comma separated, or "none".
6. `## Not checked`: fixed text, always: "Styles, headers, footers, footnotes,
   text boxes outside the body, and visual layout were not inspected."

## Refuse or stop when

- The path is not a single existing file.
- The file is larger than 2 MB, or the zip has more than 2000 entries.
- The file is not a zip container, or has no word/document.xml part.
- A part declares more than 20 MB, or has a compression ratio above 100 to 1 over 1 MB.
- An XML part contains a DTD or entity declaration, is not well-formed, is not valid UTF-8, or nests deeper than 200 levels.
- The user asks you to accept, reject, delete or add comments or revisions. This
  skill only reports. Editing needs another tool.
- The user asks for a write-up of the document's content. The script reports
  structure only; say so and stop.
- The exit code is 2. Report the error and do not guess the counts.

## Worked check

Run `python -I fixtures/make_fixture.py` to create a smoke file in the temp
folder, then run the inspector on it. The expected result is 6 paragraphs, 1
empty, 1 table, 1 comment, 1 insertion, 2 headings, authors Ana and Ben,
`findings` 3, exit code 1. A different result means the script or the Python
version needs attention before any real file is inspected.
