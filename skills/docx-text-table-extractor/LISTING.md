# docx-text-table-extractor

## One line

Pulls the paragraphs (with style names) and every top-level table out of a Word .docx file, writing a text file and one CSV per table.

## What it does

The script opens the .docx as a zip package and reads two parts: the document body and the style sheet. It walks the body in order. Each non-empty paragraph becomes one line in `paragraphs.txt`, prefixed by its style name, so heading levels stay visible. Each top-level table becomes its own CSV file, and a marker line in the text file shows where the table sat in the document.

Before reading anything it applies caps: a 2 MB input limit, a 2,000-entry package limit, and a 20 MB uncompressed total. It refuses any part that declares a DTD or entity. It never extracts zip members to disk and never writes to the input file. Every output file is created in exclusive-create mode, so a second run into the same folder stops with an error instead of replacing earlier results.

Merged cells are reported as findings rather than silently flattened. A horizontal merge puts the text in the first column and leaves the spanned columns empty. A vertical merge puts the text in the restart cell only. The summary lists each finding with its table number and count, and the exit code is 1 when any finding exists, so a batch job can detect the case without reading the JSON.

## When to use

- A table in a Word report needs to become rows in a spreadsheet or a data pipeline.
- You need the heading structure of a long memo or specification as plain text, with the heading level kept on each line.
- You want a quick count of tables, rows and headings across a document before deciding how to process it.

## When not to use

- The source is a .doc, .pdf, .pages or scanned image. The script reads only .docx packages with text runs.
- The table has nested tables, floating layout or a text box. Those are not extracted.
- You need to change the Word file itself, track edits, or produce a formatted document.

## Requirements

Python 3.9 or newer, standard library only. No network access, no third-party packages, and no write permission needed on the input folder. The output folder must already exist and must not be the input file's folder.

## Example

Command run on a generated test package with two headings, two body paragraphs and one three-row table, using the placeholder `<workspace>` for the working folder:

```
python -I "<workspace>/scripts/docx_extract.py" "<workspace>/sample.docx" "<workspace>/out"
```

Summary printed to stdout (exit code 0):

```
{
  "status": "ok",
  "input": "sample.docx",
  "headings": 2,
  "paragraphs": 4,
  "tables": 1,
  "rows": 3,
  "table_list": [
    {
      "table": 1,
      "rows": 3,
      "columns": 2,
      "file": "table-001.csv"
    }
  ],
  "files_written": [
    "paragraphs.txt",
    "table-001.csv"
  ],
  "findings": []
}
```

`paragraphs.txt` (tab between style and text):

```
heading 1	Quarterly Report
Normal	Revenue by region.
heading 2	Regions
(table)	see table-001.csv
Normal	End of report.
```

`table-001.csv`:

```
Region,Revenue
"North, east",1200
South,950
```

## Limits

The tool reads text runs only. It does not check that the numbers, dates or names in a table are correct, and it does not check visual layout, borders, colors, images, charts, headers, footers, footnotes or comments. Tracked deletions are skipped and tracked insertions are kept. Text boxes and content controls at the body level are not read. Spreadsheet formulas are not neutralized, so a cell beginning with an equals sign is written as plain text. Inputs over 2 MB, packages over the entry or size caps, and documents with DTD or entity declarations are refused. The tool does not verify deliverability or security beyond those caps.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
