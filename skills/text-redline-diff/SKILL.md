---
name: text-redline-diff
description: Redlines two plain-text or Markdown versions of a document by paragraph, then by word, marking changed words as [-deleted-] and [+inserted+] and counting moved paragraphs. Use when a reviewer asks what changed between two text or Markdown drafts, or asks for a redline document. Do not use for Word, PDF or spreadsheet files, for binary inputs, or for judging whether a change is correct.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Text redline diff

This skill runs `scripts/redline.py` on two UTF-8 text or Markdown files and reports what changed, paragraph by paragraph and word by word. The script does the comparison. The agent chooses flags, runs the command, checks the counts, and returns the output.

## Workflow

1. **Confirm the inputs.** Both files must be UTF-8 text or Markdown, each 2 MB or smaller. Output: the old file name and the new file name, in that order. Old is the earlier version.
2. **Choose the flags** with the decision table below. Output: the flag list, one line.
3. **Run the script** with the command in the Script contract section, using the user's files in place of the placeholders. Output: the full stdout text and the exit code.
4. **Check the exit code** against the exit code table. Exit 2 stops the workflow; report the one-line JSON error and ask for a corrected input.
5. **Check the counts.** `paragraphs old` must equal `unchanged + changed + whitespace_only + deleted + moved`, and `paragraphs new` must equal `unchanged + changed + whitespace_only + inserted + moved`. If either fails, the run is invalid: re-run once, then stop. Output: the two equations with their values.
6. **Write the report file** only if the user asks for one. Add `--report <report-file>` with a new name. Output: the report path and the exit code.
7. **Return the redline.** Output: the stdout text unchanged, followed by a one-sentence summary that quotes the `paragraph_counts` and `word_counts` lines.

## Decision table

| Situation | Action | Value |
|---|---|---|
| Every change must show, including spacing and line breaks | No flag (strict) | default |
| Only capitalization changes must be ignored | Add `--ignore-case` | words and paragraphs compared casefolded |
| Only spacing or line wrapping changes must be ignored | Add `--ignore-whitespace` | paragraph text whitespace-collapsed before comparison |
| Both kinds of change must be ignored | Add both flags | both rules apply |
| Input file is above the size cap | Stop | 2 MB per file |
| Two paragraphs are paired as a changed paragraph | Word similarity must reach the threshold | 0.5 (working value, not a published spec) |
| Paragraph boundary | One or more blank lines | fixed |
| Word boundary | Any whitespace run | fixed |

## Output contract

Stdout is plain text in this order. Every line is required, even when a count is 0.

```
# Redline
old: <old file name>
new: <new file name>
flags: case=<sensitive|ignored> whitespace=<strict|ignored>
paragraphs: old=<n> new=<n>
paragraph_counts: changed=<n> inserted=<n> deleted=<n> moved=<n> whitespace_only=<n> unchanged=<n>
word_counts: inserted=<n> deleted=<n>
```

After the header, each differing paragraph gets a blank line and one block. Block headings use exactly these forms:

| Heading form | Meaning | Body |
|---|---|---|
| `## Changed: old P<n> -> new P<n>` | Paragraph paired and words differ | inline text with `[-deleted-]` and `[+inserted+]` |
| `## Whitespace-only: old P<n> -> new P<n>` | Words equal, spacing differs (strict mode only) | new paragraph text, unchanged |
| `## Moved: old P<n> -> new P<n>` | Exact text removed at one place and added at another | new paragraph text, unchanged |
| `## Deleted: old P<n>` | Paragraph removed | `[-` words `-]` |
| `## Inserted: new P<n>` | Paragraph added | `[+` words `+]` |

If nothing differs, the body is the single line `No differences.` after the header.

Error output goes to stderr as one line of JSON with keys `error` and `code`:

| Code | Exit | Cause |
|---|---|---|
| `usage` | 2 | Missing or unknown argument |
| `missing_file` | 2 | Input is not a regular file, or cannot be opened |
| `too_large` | 2 | Input is larger than 2 MB |
| `invalid_utf8` | 2 | Input is not UTF-8 text (for example .docx or .pdf) |
| `output_exists` | 2 | Report path already exists |
| `output_is_input` | 2 | Report path is one of the two inputs |
| `output_write_failed` | 2 | Report could not be created, for example a missing folder |

## Script contract

Command, run from the skill folder:

`python -I scripts/redline.py <old-file> <new-file> [--report <report-file>] [--ignore-case] [--ignore-whitespace]`

- Arguments: `old_file` and `new_file` are required, in that order. `--report` names a new file to create. `--ignore-case` and `--ignore-whitespace` are optional flags.
- Output keys: the header keys and the count keys in the output contract above.
- Exit codes: `0` no differences; `1` differences found (any changed, inserted, deleted, moved, or whitespace-only paragraph); `2` usage or input error.
- The script reads its inputs only. It creates at most one file, with exclusive mode, and never overwrites.

## Refuse or stop when

- An input is a binary format (.docx, .pdf, .xlsx) or is not UTF-8. Stop with code `invalid_utf8` and ask the user for a plain-text or Markdown export.
- An input is larger than 2 MB. Stop with code `too_large` and ask the user to split the file.
- The user asks for the redline to be written over an input file or over an existing report. Refuse that part only: write to a new name and say so.
- The user asks for a comparison by sentence or by page. This skill compares paragraphs and words only.
- The user asks whether a change is correct, legal, or factually accurate. This skill shows differences; it does not judge them.

## Shipped files

- [scripts/redline.py](scripts/redline.py): the comparison script described above.
- [fixtures/old_version.txt](fixtures/old_version.txt) and [fixtures/new_version.txt](fixtures/new_version.txt): two 12-paragraph versions with three edits, one deleted paragraph, and one added paragraph, for a smoke run.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.
