---
name: html-to-markdown
description: Converts an HTML fragment or page to Markdown offline, keeping headings, links, lists, code, blockquotes and simple tables while dropping script, style and navigation, and reports every tag it dropped or kept as plain text. Use when copied web content must become clean Markdown, when headings, links or tables must survive a paste, or when a conversion must run without network access. Do not use for fetching pages by URL, resolving relative links or images, converting Markdown to HTML, or converting spreadsheets or PDFs.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# HTML to Markdown

This skill converts one HTML file into one new Markdown file using a fixed tag mapping. The script never makes a network request, never fetches a link or image, and never overwrites a file.

## Files shipped

- `scripts/html_to_md.py`: the converter (type A script, stdlib only).
- `fixtures/sample_page.html`: a small smoke input with a nav, a nested list, a table, a link, an image and a code block.
- `LICENSE.txt`: Apache-2.0 license text.

## Workflow

1. Check the input. It must be an existing file, at most 2,097,152 bytes, and valid UTF-8 (a leading byte order mark is allowed). Output: the input path, its byte size and the encoding result.
2. Choose a new output path ending in `.md` inside an existing folder. The file must not exist and must not be the input path. Output: the output path.
3. Run the script with the command line in the Script contract section. Output: the one-line JSON summary from stdout, or the one-line error from stderr, and the exit code.
4. Act on the exit code using the decision table. Output: the status and, for exit 1, each unsupported tag with its count.
5. Spot-check the Markdown against the source. Compare headings, links, lists, tables and code blocks with the summary counts, and count the table rows in the source by hand. Output: a check table with the columns Item, Summary count, Source count and Match (yes or no).

## Decision table

| Condition | Value | Action |
|---|---|---|
| Input size | at most 2,097,152 bytes (2 MB) | Above this, stop with `input_too_large`. |
| Input encoding | strict UTF-8, BOM allowed | Invalid bytes stop with `input_not_utf8`. |
| Exit 0 | status `ok` | Accept the output. |
| Exit 1 | status `findings` | Accept the output, list each unsupported tag with its count, and tell the user the text was kept. |
| Exit 2 | error line on stderr | Stop and report the error code from the Error codes table. |
| Table header row | first row of the table | A table with no header row still uses its first row as the header (working value). |
| Indent per list level | 2 spaces (working value) | Nested items are indented by 2 spaces per level. |
| Hand-fix threshold | any unsupported tag | Do not hand-edit the Markdown unless the user asks. Report the tags. |

## Tag mapping

| Class | Tags | Output |
|---|---|---|
| Dropped with content | script, style, nav, noscript, template, head, title | Nothing. Only the outermost dropped element is counted. |
| Converted | h1 to h6, p, a, ul, ol, li, strong, b, em, i, code, pre, blockquote, table, tr, th, td, br | Markdown syntax. |
| Pass through | div, section, article, main, body, html, hr, thead, tbody, tfoot, span, meta, link | Text kept. Block tags end the paragraph; span and meta add no output. |
| Unsupported | every other tag, for example img, figure, dl, caption | Text kept, tag markup removed. Counted in `unsupported`. |
| Spanned cell | td or th with colspan or rowspan | Cell text kept, spans not applied. Counted as `td[colspan/rowspan]`. |

## Output contract

The Markdown file is UTF-8 with LF newlines. Headings use ATX `#` markers. Links keep the anchor text in square brackets, followed by the href in parentheses, with spaces in the href written as `%20`. Tables are pipe tables with a `---` separator row, and a cell pipe is written as `\|`. Code blocks are fenced with three backticks. Blockquote lines start with `> `. In plain text, backslash, backtick, asterisk, underscore, and square brackets are backslash-escaped.

The stdout summary is one JSON object with sorted keys:

- `status`: `ok` or `findings`
- `headings`, `links`, `lists`, `tables`, `code_blocks`: integer counts
- `dropped`: object mapping tag name to count
- `unsupported`: object mapping tag name (or `td[colspan/rowspan]`) to count
- `bytes_written`: integer

Errors are one JSON object on stderr with a single key, `error`:

| Error code | Exit | Meaning | Next step |
|---|---|---|---|
| usage | 2 | Wrong number of arguments. | Fix the command line. |
| input_missing | 2 | Input is not an existing file. | Check the input path. |
| input_too_large | 2 | Input is over 2,097,152 bytes. | Split or trim the input. |
| input_unreadable | 2 | The operating system refused the read. | Check file permissions. |
| input_not_utf8 | 2 | Input bytes are not valid UTF-8. | Re-save the file as UTF-8. |
| output_is_input | 2 | Output path equals the input path. | Choose a new output name. |
| output_dir_missing | 2 | Output folder does not exist. | Create the folder first. |
| output_exists | 2 | Output file already exists. | Choose a new name. Never overwrite. |
| output_unwritable | 2 | The operating system refused the write. | Check the output location. |
| parse_failed | 2 | The HTML parser raised an error. | Stop and report the error. |

## Script contract

Command line (run from the skill folder):

`python -I scripts/html_to_md.py <input-file> <output-file>`

- Arguments: exactly two positional paths, input then output.
- Exit 0: converted with no unsupported tags.
- Exit 1: converted, and at least one unsupported tag was kept as text. The output file is still written.
- Exit 2: usage or input/output error. No output file is written.
- The script reads only the input and writes only the output, which it creates with exclusive-create mode.
- No network, no subprocess, no eval.

## Refuse or stop when

- The input is a binary file (Word, PDF, image, archive) or fails UTF-8 decoding. Stop with `input_not_utf8`.
- The input is over 2,097,152 bytes. Stop with `input_too_large`.
- The user gives a URL and asks for the page to be fetched. The script has no network access. Ask the user to save the page as a file first.
- The user asks for relative links or images to be resolved or embedded. This is not supported. Convert the rest, report the unsupported tag, and keep the text (status `findings`).
- The output path already exists or equals the input path. Do not overwrite. Ask for a new name.
- The user asks for Markdown features outside the tag mapping (footnotes, task lists, math, front matter). Not produced. Say so.
- The user needs the HTML sanitized for untrusted display. This script copies href values as written and does not sanitize them. Stop and say that a sanitizer is required.

## What the script does not verify

It does not check that links resolve, that the rendered Markdown looks like the source page, or that the content is safe. Nested tables, lists inside table cells, and indentation inside code blocks are not preserved. Text is not checked for Markdown syntax that it may contain beyond the escaped characters.
