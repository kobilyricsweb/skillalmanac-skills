# Markdown to DOCX

## One line

Converts one Markdown file into a new Word .docx file with a standard-library Python script, then counts what it wrote by re-opening the file.

## What it does

The script reads one UTF-8 Markdown file of up to 2 MB. It turns `#`, `##` and `###` lines into Word heading styles, plain lines into paragraphs, bullet and numbered lines into list paragraphs, bold and italic spans into bold and italic runs, backtick spans into monospace runs, and simple pipe tables into real Word tables with a bold header row. Link syntax becomes the link text followed by the target in round brackets, because the script does not create hyperlinks.

Anything it cannot convert is still written, but a finding is recorded with the line number and a code. Examples are a heading level of four or deeper, an image that is not embedded, a code fence that loses its fence markers, and a table row with the wrong number of cells.

The output is built directly in the Office Open XML format with zipfile and xml. After the write, the script re-opens the new file, reads the stored document XML, and counts paragraphs, headings, list items and tables. If those counts differ from the counts it wrote, the run reports a mismatch.

## When to use

Use it when a person has Markdown notes, a memo, a draft or a report and needs a Word file they can edit, comment on or send. It is also suitable for a quick, repeatable conversion in an environment where only Python 3.9 or later is available and installing packages is not an option.

## When not to use

Do not use it to change an existing Word file, to produce PDF or slides, or to embed images, footnotes, math or raw HTML layout. Do not use it for Markdown whose meaning depends on styling that the supported list does not cover. Nested lists are flattened, and the findings say so.

## Requirements

Python 3.9 or later, standard library only. No network access and no subprocess calls. The input must be a UTF-8 text file of at most 2 MB. The output path must end in .docx, must not already exist, and must sit in a folder that exists.

## Example

Run on the shipped clean fixture, which is 25 lines with headings, a bullet list, a numbered list and a three-row table. The command uses placeholders for the folder and the output name:

`python -I "<skill-folder>/scripts/md_to_docx.py" "<input-file>" "<output-file>.docx"`

Result on stdout, pasted from the run:

```
{"status": "ok", "input": "sample.md", "output": "sample.docx", "written": {"paragraphs": 12, "headings": 5, "list_items": 5, "tables": 1}, "readback": {"paragraphs": 12, "headings": 5, "list_items": 5, "tables": 1}, "match": true, "findings_total": 0, "findings": []}
```

Exit code 0.

## Limits

The script does not check how the document looks. It does not render pages, so line breaks, table widths and fonts are not compared with the Markdown. Its read-back proves that the package opens as a zip, that the document XML parses, and that the element counts match. It does not prove that Word, LibreOffice or Google Docs will display the file the same way.

Lazy continuation lines are not merged into the preceding list item; each becomes its own paragraph. Table cell widths are fixed at equal working values. Hyperlinks are not created. Headers, footers, page numbers, comments and tracked changes are not produced. The script was run on Python 3.11 only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
