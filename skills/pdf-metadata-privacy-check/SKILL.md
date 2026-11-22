---
name: pdf-metadata-privacy-check
description: Checks a PDF file's document metadata for personal names, e-mail addresses and local file paths before the file is shared. Use when a PDF is about to go to a client, a public page or an outside uploader and its Author, Creator or XMP fields may reveal a person or a folder layout. Do not use for editing or removing metadata inside a PDF, for scanned pages where personal data is visible in the image, or for Word, spreadsheet or image files.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# PDF metadata privacy check

This skill runs one read-only script over one PDF and turns its output into a
sharing decision. The script reads the Info dictionary and four XMP fields. It
does not decompress streams, so it can miss values stored in compressed object
streams. Say so in every report where `objstm_present` is true.

## Script contract

- Command: `python -I scripts/pdf_meta.py INPUT.pdf`
- Argument: exactly one path to a regular file. Input cap is 2 MB (2,097,152 bytes).
- Keys read from the Info dictionary: Author, Creator, Producer, Title, Subject,
  Keywords, CreationDate, ModDate. Literal and hex strings are decoded.
- XMP fields read: dc:creator, xmp:CreatorTool, pdf:Producer, dc:title.
- Stdout on success: one pretty-printed JSON object with the keys `file`,
  `size_bytes`, `pdf_version`, `entries`, `flags`, `objstm_present`, `notes`,
  `scrub_advice`. Each entry is `{key, value, source}`; each flag is `{key, value, reason}`.
- Stdout on error: one line, `{"error": "<message>"}`.
- Exit codes: 0 = no flagged value. 1 = at least one flagged value. 2 = usage
  or input error (missing file, not a regular file, over 2 MB, no `%PDF-` header).
- The script writes no file and never changes the input.

## Workflow

1. Confirm the input is a `.pdf` file and its size is 2 MB or less. Required output:
   file name and size in bytes. If the size is over 2 MB, stop (see Refuse list).
2. Run the command in the script contract. Required output: exit code and the
   full JSON object, copied without edits into your working notes.
3. Read `objstm_present`. Required output: one line, `Object streams: yes` or
   `Object streams: no`. If yes, add the note text from the JSON `notes` array
   to the Limits section of the report.
4. Classify each item in `flags` with the decision table below. Required output:
   one row per flag in the Flags table.
5. Check `entries` for values not flagged but still useful to the sender, such as
   Producer software names and dates. Report them; do not change them.
6. Write the report in the output contract. Required output: all sections present,
   even when a section is empty (write "none").

## Decision table: flag to action

| Flag reason | Rule the script applies | Action to recommend |
|---|---|---|
| possible personal name | Key is Author or dc:creator and the value matches 2 or 3 words, first letter uppercase, each following word starting uppercase | Clear the field, or set a team or role name |
| e-mail address | Value contains text shaped like name@domain.tld | Remove, or replace with a role mailbox |
| local file path | Value contains a drive path such as C:\ or a path starting with /Users/ or /home/ | Re-export from the source program with document properties cleared |
| none (Producer, Creator software name) | No rule matched | Keep. Mention only if the software name is sensitive |
| none (CreationDate, ModDate) | No rule matched | Report the value. Flag to the sender only if it reveals a timing they meant to hide |

Working values, not published standards: input cap 2 MB; literal string nesting
cap 8 levels; string length cap 512 characters; at most 20 occurrences read per
key and 20 XMP matches. The name pattern accepts "Acme Corp" as well as a person,
so a reviewer must confirm each name flag.

## Output contract

The report is Markdown with these headings in this order:

```
## File
name, size in bytes, PDF version, Object streams yes or no

## Entries
| key | value | source |

## Flags
| key | reason | action |

## Limits
bullet list: the script's limits that apply to this file, including every note from the JSON

## Next step
one sentence: send as is, or clear the listed fields and run the check again
```

## Refuse / stop when

- The input does not end in `.pdf` or the script exits 2. Stop and report the
  `error` text. Do not guess values from the file name.
- The file is over 2 MB. Stop. Do not split, truncate or re-save the file to make
  it fit the cap.
- The request is to remove, rewrite or edit metadata. This skill only reports.
  Say that the change must be made in the source program or with a separate tool.
- The request is to send the PDF to an outside service for a second opinion.
  The script has no network access, and this skill does not upload files.
- The request is to find personal details about a named private person across
  several PDFs. Refuse; this skill checks one file for sharing.
- `objstm_present` is yes and the user asks for a clean verdict. Give the result
  with the limit stated; do not call the file clean.

## Files in this package

- `scripts/pdf_meta.py`: the checker described in the script contract.
- `fixtures/jane_author.txt`: hand-written PDF-syntax test file with Author "Jane Doe"
  and a Windows path in Creator. Expected exit code 1. The script checks the
  `%PDF-` header and not the extension, so copy it to a `.pdf` name to test in a PDF reader.
- `fixtures/clean_title.txt`: hand-written PDF-syntax test file with hex-encoded Title
  and Author and no flagged value. Expected exit code 0.
- `LICENSE.txt`: Apache License 2.0 text.
  description and the verification record.

## Example run

```
python -I scripts/pdf_meta.py fixtures/jane_author.txt
```

Expected: exit code 1, two flags (Author as a personal name, Creator as a local
path), and the scrub advice lines for both.
