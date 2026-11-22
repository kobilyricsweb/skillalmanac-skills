---
name: text-entity-extractor
description: Extracts URLs, hashtags, @mentions and ISO or numeric dates from one plain UTF-8 text file, reporting counts, first line and every line number. Use when a list of links, tags, handles or dates must be complete and countable from notes, drafts, transcripts or exports. Do not use for names or organizations, for checking whether links work or fetching pages, for sentiment or topic analysis, or for files over 2 MB.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Text entity extractor

Use the script for every extraction. Reading the text by eye misses links that
wrap across visual lines, hashtags next to punctuation and dates written in two
styles. The script reads the file, applies the rules below and returns JSON. The
agent then checks the exit code, resolves ambiguous dates with the user and writes
the report.

## Workflow

1. Confirm the input. It must be one plain text file, UTF-8, at most 2 MB. Output: the
   absolute path of the file. If the user has a Word, PDF or spreadsheet file, ask for a
   plain text export first (see Refuse / stop when).
2. Run the script from the skill folder:
   `python -I scripts/extract_entities.py <input-file>`
   Output: the JSON object (see the output contract) on stdout.
3. Read the exit code (table below). Exit 2 ends the run with the error message in the
   report. Exit 0 or 1 continues.
4. For each entry in `dates` with `"ambiguous": true`, list the `as_written` text, the
   line numbers and both readings (`iso` and `alt_iso`). Ask the user which reading is
   correct. Do not choose for the user. If the user does not answer, keep both readings
   in the report under Open questions.
5. Copy every `rejected_dates` item into the report, with its line number. Do not
   repair them; the calendar date does not exist.
6. Write the report using the sections in the output contract. Each list keeps the
   script order (first line, then value). Do not add entities the script did not return.

## Rules and thresholds

| Rule | Value |
|---|---|
| Input size cap | 2,097,152 bytes (2 MB), working value; larger input exits 2 |
| Encoding | UTF-8; a byte-order mark is accepted; any other byte sequence exits 2 |
| Line numbers | 1-based, split on LF, a trailing CR removed; a final empty line is not counted |
| URL start | `http://`, `https://` or `www.` (case-insensitive); bare domains are not URLs |
| URL host | must contain a dot, and must not start or end with one |
| URL trailing characters | `.` `,` `;` `:` `!` `?` `'` `"` removed, plus `)` `]` `}` when unbalanced |
| URL dedup | exact string after trimming |
| Hashtag | `#` then a letter, then 1 to 49 letters, digits or underscores (2 to 50 characters), working value |
| Hashtag context | not preceded by a letter, digit, underscore, `&` or `#` (so `C#` is not a tag) |
| Hashtag dedup | case-insensitive; the first spelling is shown |
| Mention | `@` then 1 to 30 letters, digits or underscores, working value |
| Mention context | not preceded by a word character, `@`, `.`, `+` or `-` (so email addresses are not mentions) |
| Mention dedup | case-insensitive; the first spelling is shown |
| URL masking | text inside a found URL is hidden from the hashtag, mention and date scans |
| ISO date | `YYYY-MM-DD`, must be a real calendar date |
| Slash date | `N/N/YYYY` with a four-digit year; US month/day order is the default reading |
| Unambiguous slash date | one part is above 12, so that part is the day |
| Ambiguous slash date | both parts are 12 or less and differ; `iso` is the month/day reading, `alt_iso` the day/month reading (US default, working value) |
| Same-value slash date | both parts are equal (for example 05/05/2026); not ambiguous |
| Impossible date | fails the calendar check (for example 2026-02-30, or 13/13/2026); goes to `rejected_dates` |
| Date dedup | by the pair `iso` and `alt_iso`, so an ambiguous date and an ISO date for the same day stay separate |

## Exit codes

| Code | Meaning | Agent action |
|---|---|---|
| 0 | Scan finished; no ambiguous date | Report with status `complete` |
| 1 | Scan finished; at least one ambiguous date | Resolve dates with the user; status `review` until resolved |
| 2 | Usage or input error; one-line JSON on stderr | Report the message and stop; status `stopped` |

Exact stderr messages (exit 2): `usage: python -I extract_entities.py <input-file>`,
`input is not a readable file`, `input exceeds the 2 MB cap`, `input is not valid UTF-8`,
`input could not be read`.

## Script contract

- Path: `scripts/extract_entities.py`, Python 3.9+ standard library only.
- Arguments: exactly one positional argument, the input file path. No options.
- Reads the file. Writes no files. Makes no network calls, starts no subprocess.
- Stdout (exit 0 or 1): one JSON object with the keys below, indented, ASCII-escaped.
- Stderr (exit 2): one line, `{"error": "<message>"}`.

## Output contract

Top-level JSON keys: `input` (file base name), `summary`, `urls`, `hashtags`,
`mentions`, `dates`, `rejected_dates`.

`summary` keys: `lines_scanned`, `url_unique`, `hashtag_unique`, `mention_unique`,
`date_unique`, `ambiguous_date_unique`, `rejected_date_candidates`.

`urls`, `hashtags`, `mentions` items: `value`, `count` (occurrences), `first_line`,
`lines` (distinct line numbers).

`dates` items: `iso`, `alt_iso` (null unless ambiguous), `ambiguous`, `as_written`
(distinct spellings), `count`, `first_line`, `lines`.

`rejected_dates` items: `as_written`, `line`.

Report sections, in this order: `## Summary` (status and the `summary` counts as a
table), `## URLs` (columns: value, count, first line, lines), `## Hashtags` and
`## Mentions` (same columns), `## Dates` (columns: iso, alt_iso, ambiguous,
as written, count, first line, lines), `## Rejected dates` (columns: as written,
line), `## Open questions` (ambiguous dates awaiting the user, refused clauses,
or `None`).

## Refuse / stop when

- The path does not exist, is not a file, is over 2 MB, or is not UTF-8: exit 2, status
  `stopped`, report the message only.
- The file is a Word, PDF, spreadsheet or image: stop and ask for a plain text export.
  Do not convert it with another tool.
- The user asks for names, people or organizations: out of scope. Say so under Open
  questions and deliver the other entities unchanged.
- The user asks to fetch URLs, test whether they work or follow redirects: refused for
  that clause only; the extraction still runs. Say so under Open questions.
- The user asks for the output to be saved: write the report to a new file with an unused
  name. Never overwrite an existing file and never write into the input folder path
  that holds the source text.
- The user asks you to pick one reading of an ambiguous date without their answer: keep
  both readings and state the question.
- The result is status `review` and the user has not answered: deliver the report with
  the ambiguous dates still open.

## Shipped files

- `scripts/extract_entities.py`: the extractor.
- `fixtures/sample_notes.txt`: a 25-line text used for the self-check below.
- `LICENSE.txt`: Apache-2.0 license text.

## Self-check

Run `python -I scripts/extract_entities.py fixtures/sample_notes.txt` from the skill folder.
Expected: exit 1; `summary` shows 6 URLs, 4 hashtags, 2 mentions, 5 dates, 1 ambiguous
date and 1 rejected date candidate. If the counts differ, the script or its
environment has changed; report that before using it on user files.
