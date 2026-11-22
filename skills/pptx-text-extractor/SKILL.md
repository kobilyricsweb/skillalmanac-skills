---
name: pptx-text-extractor
description: Extracts slide titles, body text, table cells and speaker notes from a .pptx file in presentation order, with slide counts and empty-slide detection. Use when a user needs the text of a slide deck as Markdown or plain text, wants table cells or notes pulled out of slides, or asks to convert a slide deck to editable text. Do not use for editing or creating decks, for .ppt, .key or .odp files, for text inside images, charts or SmartArt, or for files over 2 MB.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# pptx-text-extractor

Reads a .pptx package read-only and prints each slide's title, body text, table
cells and speaker notes in presentation order. The script does not render slides,
read pictures or charts, or change the deck.

Shipped files: [scripts/pptx_text.py](scripts/pptx_text.py) (the extractor),
[fixtures/build_fixture.py](fixtures/build_fixture.py) (builds a smoke-test deck
in a temp folder), [fixtures/expected_output.md](fixtures/expected_output.md)
(the expected Markdown for that deck), and [LICENSE.txt](LICENSE.txt).

## Workflow

1. Check the input. Required output: the file name, its size in bytes and the
   decision "run" or "stop". Stop when the name does not end in .pptx, the file
   does not exist, or the size is above 2097152 bytes.
2. Choose the output channel. Required output: "stdout" or a new file path with
   the format. Use stdout when the text goes straight into the chat. Use `--out`
   when the user wants a file. The output path must not exist; choose a new name
   and never delete or overwrite an existing file.
3. Run the command in the Script contract section. Required output: the exit code
   and the one-line JSON summary from stderr.
4. Apply the decision table below to the exit code and summary. Required output:
   one status value: `ok` (exit 0), `findings` (exit 1) or `stopped` (exit 2).
5. Report with the output contract below. Required output: the summary block and
   either the rendered text or the output path. Name every empty slide by number.

## Decision and threshold table

| Check | Limit | Result when exceeded |
| --- | --- | --- |
| Input file size | 2097152 bytes (2 MB) | exit 2, code `too_large` |
| Zip entries in the package | 400 | exit 2, code `too_many_entries` |
| Total uncompressed size | 20971520 bytes (20 MB) | exit 2, code `uncompressed_too_large` |
| One XML part, uncompressed | 5242880 bytes (5 MB) | exit 2, code `part_too_large` |
| Slides in the presentation | 1 to 300 | 0 slides: `no_slides`; above 300: `too_many_slides` |
| Empty slide | no title, body or table text (notes do not count) | exit 1, status `findings` |
| Table | kept only when at least one cell has text | empty tables are dropped |

The limits are working values chosen for this tool. They are not a published
PowerPoint or Open XML specification.

## Output contract

Markdown (`--format md`, the default):

```
# Slide text: <file name>

## Slide <n>: <title, or (no title)>

Body:
<one line per paragraph, or (none)>

Table <k>:            (only when the slide has a table; one block per table)
| <header cells> |
| --- | --- |
| <row cells> |

Notes:
<one line per notes paragraph, or (none)>
```

Plain text (`--format txt`): the same sections with no `##` marker and no
separator row; cells are joined with ` | `.

Summary (stderr, one JSON line, exit 0 or 1):

| Key | Type | Meaning |
| --- | --- | --- |
| `slide_count` | integer | slides read, in presentation order |
| `empty_slides` | list of integers | 1-based numbers of empty slides; `[]` when none |
| `table_count` | integer | tables with at least one text cell |
| `slides_with_notes` | integer | slides whose notes body has text |

Error (stderr, one JSON line, exit 2): `{"error": "<code>", "message": "<text>"}`.

| Code | Meaning | What the agent does |
| --- | --- | --- |
| `usage` | bad or missing argument | fix the command line and rerun |
| `not_found` | input path is not a file | ask the user for the correct path |
| `too_large` | input above 2 MB | stop; say the file is too large |
| `unreadable` | input cannot be opened | stop; report the access problem |
| `not_zip` | not a zip package, or an empty file | stop; the file is not a .pptx package |
| `too_many_entries` | more than 400 zip entries | stop |
| `uncompressed_too_large` | uncompressed total above 20 MB | stop |
| `missing_part` | a relationship points to a part that is not in the package | stop; the file is damaged |
| `part_too_large` | one XML part above 5 MB | stop |
| `bad_part` | a part cannot be decompressed (also an encrypted deck) | stop; the deck is damaged, encrypted or uses an unsupported method |
| `unsafe_xml` | DTD or entity declaration found in UTF-8, UTF-16 LE or UTF-16 BE bytes, or a part has a UTF-16/UTF-32 byte-order mark or a NUL byte | stop and refuse; do not strip the declaration or re-encode the part and retry |
| `bad_xml` | an XML part does not parse | stop; the file is damaged |
| `bad_structure` | relationship target leaves the package or a slide link is missing | stop |
| `no_slides` | presentation lists no slides | stop; tell the user the deck is empty |
| `too_many_slides` | more than 300 slides | stop |
| `same_path` | `--out` names the input file | choose another output name |
| `exists` | `--out` names an existing file | choose a new name |
| `out_unwritable` | output folder missing or not writable | ask the user for a writable folder |

## Script contract

- Path: `scripts/pptx_text.py`, Python 3.9+, standard library only.
- Arguments: `<input-file>` (required), `--format md|txt` (default `md`),
  `--out <new-file>` (optional; must not exist and must differ from the input).
- Stdout: rendered text when `--out` is absent; empty when `--out` is given.
- Stderr: the summary line on success, or the error line on exit 2.
- Exit codes: 0 ok, 1 empty slides found (text still written), 2 usage or input error.
- Command to print text:
  `python -I "<skill-dir>/scripts/pptx_text.py" "<input-file>" --format md`
- Command to write a file:
  `python -I "<skill-dir>/scripts/pptx_text.py" "<input-file>" --format txt --out "<output-file>"`
- Smoke test: `python -I "<skill-dir>/fixtures/build_fixture.py"` prints a temp .pptx
  path; pass that path to the first command. The expected Markdown is in
  `fixtures/expected_output.md`.
- Hostile check: `python -I "<skill-dir>/fixtures/build_fixture.py" --hostile` prints a
  temp .pptx with a UTF-16 DOCTYPE part; the first command must exit 2 with `unsafe_xml`.

## Refuse or stop when

- The file name does not end in .pptx (.ppt, .key, .odp and .potx are refused).
- Any row of the decision table is exceeded, or the script returns an error code.
- The request is to edit, create, save or re-export the deck. This skill only reads.
- The request asks for text from pictures, charts, SmartArt or embedded objects.
  The script does not read them; say so and stop for that part.
- The output path is the input file or already exists.
- The file is encrypted or password protected (code `not_zip` or `bad_part`).
- A DTD or entity declaration is present (code `unsafe_xml`). Refuse; do not edit the
  XML to get past it.
