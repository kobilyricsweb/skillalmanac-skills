# docx-structure-inspector

## One line

Reads a Word .docx file without changing it and reports heading outline, heading level skips, empty paragraphs, tables, images, comments, tracked insertions and deletions, and the authors behind them.

## What it does

The script opens the .docx as a zip container and parses two parts: word/document.xml and, when present, word/comments.xml. It walks the body in document order. It counts paragraphs and tables, notes every drawing or picture, and flags a paragraph as empty when it carries no text and no drawing, picture, object, break or tab. Paragraphs whose style ID is Heading1 through Heading9 build the outline; a heading that jumps more than one level is recorded as a skip, and a first heading deeper than level 1 counts as a skip too. Every w:ins and w:del element is counted, including paragraph-mark revisions, and the author names on those revisions and on comments are collected. The result is one JSON object on stdout. Exit code 0 means no findings, 1 means findings are present, and 2 means the input was refused.

## When to use

Use it on a Word file that arrives from a colleague, a client or an export before it goes into a publishing step. It answers the questions a reviewer asks first: are there review comments still in the file, are there tracked changes that were never accepted, do the headings nest correctly, and are there blank paragraphs that will show as gaps. The output is short enough to paste into a handoff note.

## When not to use

Do not use it to edit, accept or reject revisions, or to remove comments. It does not render pages, so it cannot tell whether a table looks right or whether an image is cropped. It reads only the body and the comments part; headers, footers, footnotes and styles.xml are not inspected. Files over 2 MB are refused on purpose, and so are zip files with more than 2000 entries.

## Requirements

Python 3.9 or newer, standard library only. No network access, no packages to install. Run with `python -I scripts/docx_inspect.py <file.docx>` from the skill folder, or pass the full path to the script. Works on Windows, macOS and Linux; the smoke fixture builder writes to the system temp folder.

## Example

Smoke run on the fixture built by `fixtures/make_fixture.py` (stdout, verbatim, exit code 1):

```
{
  "paragraphs": 6,
  "empty_paragraphs": 1,
  "tables": 1,
  "images": 0,
  "comments": 1,
  "tracked_insertions": 1,
  "tracked_deletions": 0,
  "heading_outline": [
    {
      "paragraph": 1,
      "level": 1,
      "text": "Intro"
    },
    {
      "paragraph": 4,
      "level": 2,
      "text": "Details"
    }
  ],
  "heading_skips": [],
  "authors": [
    "Ana",
    "Ben"
  ],
  "findings": 3
}
```

## Limits

Heading detection depends on the style ID, not on the style name, so a file whose headings use custom style IDs will show an empty outline. Caps are working values chosen for this release (2 MB input, 2000 zip entries, 200 XML levels, compression ratio 100 to 1), not published standards. The script does not evaluate content quality, spelling or the meaning of comments. Results were checked on one generated fixture only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
