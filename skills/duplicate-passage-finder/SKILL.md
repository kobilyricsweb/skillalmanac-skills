---
name: duplicate-passage-finder
description: Finds exact and near-duplicate paragraphs across a folder of .txt and .md files and reports each group with its file and line number. Use when comparing a document set for duplicate content, locating repeated or copy-pasted passages before a merge or edit, or checking whether drafts share repeated paragraphs. Do not use for comparing two files line by line, for matching single sentences, for .docx, .pdf or other binary files, or for rewriting or deleting duplicates.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Duplicate Passage Finder

This skill runs a read-only script over one folder and reports which paragraphs repeat. The script does the matching. Your job is to check the input, run the command, read the exit code, and write the report in the contract below.

## Thresholds

| Check | Value | Effect |
|---|---|---|
| Input size, all .txt and .md files under the folder, recursive | 2,097,152 bytes (2 MB) | Above this the script exits 2 with `input_too_large` |
| Minimum paragraph length | 8 words (working value) | Shorter paragraphs are skipped and counted in `paragraphs_skipped_short` |
| Shingle size for near-duplicate matching | 8 words (working value) | Fixed in the script |
| Near-duplicate threshold | Jaccard similarity 0.6 or higher (working value) | Two paragraphs at or above it are linked |
| Exact duplicate | Equal after whitespace collapse and case folding | Group type `exact` |
| Near duplicate | Linked through one or more pairs at or above 0.6, and not all one text | Group type `near` |
| Reported group | 2 or more occurrences | Single occurrences are not reported |

"Working value" means the number is a tuning choice of this skill, not a published standard.

## Workflow

1. **Intake.** Confirm the user gave one folder path. Output: the folder path. If the user gave a file or several paths, stop and ask for one folder.
2. **Size check.** Add the sizes of all .txt and .md files under the folder, including subfolders. Output: the total in bytes. If the total is above 2,097,152, do not run the script on a partial set; go to the error table.
3. **Run the script.** Run `python -I scripts/dup_passages.py <input-folder>` from the skill folder. Output: the captured stdout JSON and the exit code.
4. **Read the exit code.**

   | Exit code | Meaning | Next action |
   |---|---|---|
   | 0 | Scan finished, no groups | Write the report with zero groups (step 5) |
   | 1 | Scan finished, groups found | Write the full report (step 5) |
   | 2 | Usage or input error | Read the one-line JSON on stderr and use the error table |

   | Error code | Meaning | Action |
   |---|---|---|
   | `usage` | Not exactly one argument | Rerun with one folder path |
   | `not_directory` | Argument is not a folder | Ask the user for the folder path |
   | `no_files` | No .txt or .md file found | Tell the user the folder has none; stop |
   | `input_too_large` | Total over 2 MB | Stop; ask the user to split the folder into smaller folders and run each one. Do not truncate |
   | `invalid_utf8` | A file is not valid UTF-8 | Stop; name the file from the message and ask the user to re-save it as UTF-8 |
   | `read_error` | A file could not be read | Name the file from the message and stop |

5. **Write the report** in the output contract below. Copy the numbers from the JSON; do not recount paragraphs by hand.

## Output contract

The report has exactly these three parts, in this order.

**Part 1:** `## Summary`

A two-column table, `Metric (JSON key) | Value`, with these rows in this order:

| Metric (JSON key) | Source |
|---|---|
| Files scanned (`files_scanned`) | top level |
| Paragraphs compared (`paragraphs_compared`) | top level |
| Paragraphs skipped under 8 words (`paragraphs_skipped_short`) | top level |
| Groups (`counts.groups`) | counts |
| Exact groups (`counts.exact_groups`) | counts |
| Near groups (`counts.near_groups`) | counts |
| Occurrences in groups (`counts.occurrences`) | counts |

**Part 2:** `## Groups`

A four-column table, `Group | Type | File | Line`, with one row per occurrence. Repeat the group ID and type on every row of the group. Keep the script's order. File paths are relative to the input folder.

If there are zero groups, replace the table with the sentence `No duplicate groups found.`

**Part 3:** `## Not checked`

A bulleted list of the items under "Not checked" at the end of this file that apply to this run. Always include the first two items.

## Script contract

- Path: `scripts/dup_passages.py`
- Argument: exactly one, the input folder. The folder is walked recursively. Symbolic links are skipped. Only files whose names end in `.txt` or `.md` (any letter case) are read.
- Reads: UTF-8, with an optional byte order mark. Writes: nothing.
- Exit codes: 0 no groups, 1 groups reported, 2 usage or input error.
- Stdout on exit 0 or 1, JSON keys: `settings` (`min_words`, `shingle_size`, `jaccard_threshold`), `files_scanned`, `paragraphs_compared`, `paragraphs_skipped_short`, `groups` (each with `group_id`, `type` as `exact` or `near`, and `occurrences` as a list of `file` and `line`), and `counts` (`groups`, `exact_groups`, `near_groups`, `occurrences`).
- Line numbers are 1-based and point to the first line of the paragraph.
- Stderr on exit 2: one line of JSON, `{"error": <code>, "message": <text>}`. The codes are the six in the error table.
- Command line: `python -I scripts/dup_passages.py <input-folder>`

## Refuse or stop when

- The user asks you to delete, merge, rewrite, or edit duplicate passages. This skill only reports them.
- The user asks you to compare .docx, .pdf, .html, or other formats. The script does not read them. Say so and stop.
- The script returns `input_too_large`. Stop; do not run on a subset without the user's choice.
- The script returns `invalid_utf8` or `read_error`. Stop and name the file.
- The user asks you to send file contents to an outside service. The script makes no network calls, and this skill does not send content anywhere.

## Not checked

- Meaning. Paraphrases that say the same thing with different words are not matched unless their word sequences overlap enough to reach 0.6.
- Whether a repeated passage is a problem. A repeated legal notice or boilerplate paragraph is reported like any other.
- Content inside tables, code blocks, or front matter, which the script reads as plain text.
- Sentence-level duplicates. Only paragraphs of 8 words or more are compared.

## Shipped files

- [scripts/dup_passages.py](scripts/dup_passages.py): the script.
- `fixtures/docs/`: four small files, `a_q3_summary.md`, `b_field_notes.txt`, `c_audit_memo.md`, and `d_audit_memo_copy.txt`, with one exact and one near duplicate paragraph. The expected result is two groups. Run `python -I scripts/dup_passages.py fixtures/docs` to check the script before using it on real input.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.
