---
name: markdown-to-docx
description: Converts a Markdown file into a new Word .docx file using a standard-library Python script, then re-opens the new file and counts headings, paragraphs, list items and tables. Use when a user has Markdown notes, a memo, a draft or a report and needs an editable Word document, or asks how to turn a .md file into Word. Do not use for editing an existing .docx, producing PDF or slide output, embedding images, or Markdown that depends on HTML layout, footnotes or math.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Markdown to DOCX

This skill runs `scripts/md_to_docx.py` on one Markdown file and writes one new `.docx` file. It does not edit an existing Word file. It never overwrites an existing file, and it never writes to the input path.

## Workflow

1. **Intake.** Confirm the input is one UTF-8 text file of at most 2 MB and that it is Markdown. Output: `Intake: <input name>, <size in bytes>`.
2. **Choose the output name.** It must end in `.docx`, must not exist yet, and must be in a folder that exists. If the requested name exists, choose a new name such as `<name>-2.docx`. Output: `Output: <output name>`.
3. **Run the script** with the command in the Script contract section. Capture the single JSON line on stdout and the exit code.
4. **Apply the decision table** below to the exit code and the `status` value.
5. **Report** using the output contract. Quote only counts and finding codes, never document text.
6. **Offer a fix path when findings exist.** Name each finding that lost formatting, and offer to edit the Markdown and convert again to a new file name. Do not delete the first file.

## Supported syntax and the Word result

| Markdown | Word result |
|---|---|
| `#`, `##`, `###` at line start, followed by a space | Heading 1, Heading 2, Heading 3 styles |
| Consecutive plain lines | One Normal paragraph; the lines are joined with one space |
| `- item`, `* item`, `+ item` | List Paragraph with a bullet |
| `1.` or `1)` at line start | List Paragraph; the number is kept as typed |
| `**bold**` | Bold run |
| `*italic*` | Italic run |
| `` `code` `` | Consolas run |
| Link text in square brackets, then the target in round brackets | Link text, then the target in round brackets, as plain text |
| Pipe table with a separator row such as `\| --- \| --- \|` | Word table; header row bold and repeated on each page |

## Decision table

| Exit | JSON `status` | Meaning | Action |
|---|---|---|---|
| 0 | `ok` | Converted, read-back matches, zero findings | Deliver the file and report the counts |
| 1 | `findings` | Converted, with one or more findings | Deliver the file, list every finding in the output contract, and offer the fix path in step 6 |
| 1 | `findings` with `READBACK_MISMATCH` | The stored file does not match what was written | Do not deliver the file; report the mismatch and stop |
| 2 | none (error JSON on stderr) | Nothing written | Fix the input or the output name for the error code, then re-run |

## Thresholds

| Item | Value | Basis |
|---|---|---|
| Input size cap | 2,097,152 bytes (2 MB) | script constant |
| Heading levels converted | 1 to 3 | script rule; levels 4 to 6 become Normal paragraphs |
| Indent that triggers `NESTED_LIST_FLATTENED` | 2 or more columns after tab expansion to 4 | working value |
| Table column width | 2000 twips per column | working value |
| Findings echoed in the JSON | first 200 in line order; `findings_total` gives the full count | script constant |
| Page size and margins | Letter 12240 by 15840 twips, 1-inch margins | script constant |

## Output contract (final reply to the user)

Use these three headings in this order.

`## Result` is a table with the columns `Input | Output | Paragraphs | Headings | List items | Tables | Read-back match`. Fill it from the `written` counts and the `match` value.

`## Findings` is a table with the columns `Line | Code | What happened`, one row per entry in the JSON `findings` list. Write `None.` when the list is empty. Copy each `code` exactly as the script prints it.

`## Open questions` is a bulleted list of what the user must decide, such as which findings to fix first. Write `None.` when there are none.

## Findings codes

| Code | What happened | What the user can do |
|---|---|---|
| `CODE_FENCE_AS_PARAGRAPH` | Fence lines dropped; code lines kept as plain paragraphs | Accept, or paste code in a monospace font later |
| `HEADING_LEVEL_UNSUPPORTED` | Heading level 4 to 6 written as a Normal paragraph | Use level 1 to 3 headings |
| `HORIZONTAL_RULE_DROPPED` | Rule line removed | Add a page or section break in Word |
| `BLOCKQUOTE_AS_PARAGRAPH` | `>` marker removed; text kept | Restyle as a quote in Word |
| `HTML_TEXT_KEPT` | Raw HTML line kept as literal text | Remove the tag or rewrite the line |
| `NESTED_LIST_FLATTENED` | Indented list item placed at the top level | Restructure the list |
| `TABLE_MISSING_SEPARATOR` | Pipe line without a separator row kept as text | Add a `\| --- \|` separator row |
| `TABLE_RAGGED_ROW` | A row has a different cell count from the header; padded or cut | Fix the row |
| `IMAGE_NOT_EMBEDDED` | Image shown as alt text and path | Insert the image in Word |
| `NESTED_EMPHASIS_LITERAL` | Asterisks inside bold kept as literal characters | Remove the inner emphasis |
| `UNDERSCORE_EMPHASIS_LITERAL` | `_text_` kept with its underscores | Use `*text*` instead |
| `READBACK_MISMATCH` | Re-opened file does not match the counts written, or failed to open | Do not deliver; report it |

## Script contract

Command line, with `<skill-folder>` set to the folder that holds this file:

`python -I "<skill-folder>/scripts/md_to_docx.py" "<input-file>" "<output-file>.docx"`

- Argument 1: path to the input Markdown file.
- Argument 2: path of the new `.docx` file. It must not exist.
- Exit 0: converted, no findings. Exit 1: converted with findings. Exit 2: usage or input error, nothing written.
- Stdout, one JSON line: `status`, `input`, `output` (base names only), `written` and `readback` (each with `paragraphs`, `headings`, `list_items`, `tables`), `match`, `findings_total`, `findings` (each with `line`, `code`, `detail`).
- Stderr on exit 2, one JSON line: `error` and `detail`.
- Error codes: `USAGE`, `OUTPUT_NOT_DOCX`, `INPUT_MISSING`, `INPUT_TOO_LARGE`, `INPUT_NOT_UTF8`, `OUTPUT_SAME_AS_INPUT`, `OUTPUT_DIR_MISSING`, `OUTPUT_EXISTS`, `WRITE_FAILED`.
- No network, no subprocess, no eval. The input is read only. The output is created with exclusive-create mode.

## Refuse or stop when

- The input is over 2 MB (`INPUT_TOO_LARGE`). Stop and ask the user to split the file.
- The input is not UTF-8 text (`INPUT_NOT_UTF8`). Ask the user to re-save it as UTF-8.
- The output name already exists (`OUTPUT_EXISTS`). Choose a new name. Never delete or overwrite the existing file.
- The request is to edit an existing `.docx`, convert a `.docx` to Markdown, or produce PDF or slides. This skill does not do those.
- The read-back gives `READBACK_MISMATCH`. Do not deliver the file.
- The user asks for a finding to be ignored in a way that hides it from the report. Keep every finding in the output contract.

## Shipped files

- `scripts/md_to_docx.py`: the converter and read-back check.
- `fixtures/sample.md`: a 25-line clean input used for the smoke run.
- `fixtures/unsupported.md`: an input that triggers several findings.
- `LICENSE.txt`: Apache License 2.0.
