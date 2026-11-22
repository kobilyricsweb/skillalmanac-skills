# docx-paragraph-diff

## One line

Lists the text that changed between two Word .docx files, paragraph by paragraph and table cell by table cell, without needing Microsoft Word.

## What it does

The script opens each .docx as a zip package, reads only the main document part, and collects the visible text of every top-level body paragraph in order. It also collects the text of each cell in each body-level table, keyed by table, row, and cell position. Paragraphs are aligned with a standard sequence matcher that compares exact text. Each replaced block is paired position by position, so a rewritten sentence appears once as a changed paragraph with the old and new wording side by side. Extra lines on either side are reported as added or removed. Table cells are matched by position and reported as changed, added, or removed.

Formatting is ignored on purpose. A paragraph that only gains bold or a new style produces no entry, which keeps the list to real wording changes. Inputs are capped at 2 MB per file, with limits on zip entry count and uncompressed size. Before any XML parse, the raw bytes of the main part are scanned for DTD or entity declarations in UTF-8, UTF-16 LE and UTF-16 BE, and any such document is refused. A UTF-16 or UTF-32 byte-order mark or a NUL byte is also refused, so an encoding trick cannot hide a declaration. The report prints as JSON and can be written to a new file, never over an existing one.

## When to use

Use it when two drafts of a contract, memo, policy, or report need a list of wording changes, and the reviewer has only the .docx files. It is useful for a quick first pass before a human reads the redline, and for checking that a revision changed only the sentences that were meant to change.

## When not to use

Do not use it for PDF, Google Docs, or legacy .doc files, for tracked-change or comment review, for formatting or style differences, or for text inside headers, footers, footnotes, and text boxes. It does not judge meaning, so a reworded clause that means the same thing is still listed.

## Requirements

Python 3.9 or newer, standard library only. No network access, no installed packages, and no Microsoft Word. The script is run with the isolated-mode flag so that no local module can shadow the standard library.

## Example

Command, from the smoke fixture pair built at runtime by the fixture helper:

```
python -I scripts/docx_diff.py "<old-docx>" "<new-docx>"
```

Output (exit code 1):

```json
{
  "result": "differences",
  "old_file": "old.docx",
  "new_file": "new.docx",
  "paragraphs": {
    "old": 5,
    "new": 5
  },
  "tables": {
    "old": 1,
    "new": 1
  },
  "counts": {
    "paragraph_changed": 2,
    "paragraph_added": 0,
    "paragraph_removed": 0,
    "cell_changed": 1,
    "cell_added": 0,
    "cell_removed": 0
  },
  "differences": [
    {
      "kind": "paragraph_changed",
      "old_index": 2,
      "new_index": 2,
      "table": null,
      "row": null,
      "col": null,
      "old_text": "Revenue grew in the second quarter.",
      "new_text": "Revenue grew in the third quarter."
    },
    {
      "kind": "paragraph_changed",
      "old_index": 4,
      "new_index": 4,
      "table": null,
      "row": null,
      "col": null,
      "old_text": "Next steps are listed below.",
      "new_text": "Next steps are listed in the appendix."
    },
    {
      "kind": "cell_changed",
      "old_index": null,
      "new_index": null,
      "table": 1,
      "row": 2,
      "col": 2,
      "old_text": "Ana",
      "new_text": "Anya"
    }
  ]
}
```

The third paragraph in the new fixture only gained bold and is absent from the output, as intended.

## Limits

The script compares visible text in the main document part only. It does not compare headers, footers, footnotes, comments, or text boxes. Alignment is positional after exact matching, so a moved paragraph appears as a removal plus an addition. A merged cell is matched by its place in the row, so merges can shift later columns. Empty paragraphs count and can show as changes. Tracked insertions are read as text, and tracked deletions are skipped. The script does not check which file is newer, who made an edit, or how the pages look. The size caps (2 MB per file, 2,000 zip entries, 20 MB uncompressed) are working values chosen for this tool, not a published limit.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
