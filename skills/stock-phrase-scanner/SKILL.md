---
name: stock-phrase-scanner
description: Scans a plain-text draft for stock filler phrases, hedges and repeated sentence openers, reporting each hit with its line numbers and the phrase density per 1,000 words. Use when a draft reads as boilerplate and the author wants a line-level count of generic phrases and repeated openers before an edit pass. Do not use for deciding whether a text was written by AI, for rewriting sentences, or for grammar, spelling or style checks.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Stock Phrase Scanner

Counts stock phrases, hedges and repeated sentence openers in one draft and reports the line numbers where each appears. The scanner reports counts only. It does not judge authorship and does not rewrite text.

## Workflow

1. Confirm the input. It must be one plain-text UTF-8 file of 2 MB or less. Output: the input file name and a yes or no on each condition.
2. Run the scanner with the command in the Script contract section. Output: the raw JSON from stdout, or the one-line error from stderr.
3. Read the exit code. Output: the exit code, stated as 0, 1 or 2 with its meaning from the Exit codes table.
4. List each phrase hit with its line numbers, sorted as the script sorts them (count descending, then list order). Output: the Phrase hits table.
5. List each repeated opener with its line numbers, sorted by count descending, then alphabetically. Output: the Repeated openers table.
6. Write the report in the Output contract format. Do not add replacement sentences. Output: the full report.

## Thresholds and decisions

| Check | Value | Basis |
|---|---|---|
| Phrase list size | 50 entries: 41 filler, 9 hedge | working value |
| Opener length | first 2 words of each sentence | working value |
| Opener repeat threshold | 3 or more sentences with the same 2 words | working value |
| Maximum input size | 2,097,152 bytes (2 MB) | script limit |
| Sentence boundary | `.`, `!` or `?` followed by whitespace, inside one line | script rule |
| Density | phrase hits x 1,000 / words, rounded to 2 decimals | script rule |
| Density band: none | 0.00 | working value |
| Density band: low | above 0.00 and below 10.00 | working value |
| Density band: high | 10.00 or more | working value |

Decision for the report:

| Finding | Rule | Note to the author |
|---|---|---|
| Filler phrase | any count of 1 or more | Review each listed line in the edit pass. |
| Hedge | any count of 1 or more | Keep the hedge only where the claim needs qualifying. |
| Repeated opener | count of 3 or more | Vary the opening words on the listed lines. |
| Density | band from the table above | State the band. Do not compare to other documents. |

## Output contract

The JSON from the script has these keys: `file`, `words`, `lines`, `phrase_hit_total`, `hits_per_1000_words`, `phrase_hits`, `opener_repeats`, `finding_count`. Each `phrase_hits` item has `phrase`, `category`, `count`, `lines`. Each `opener_repeats` item has `opener`, `count`, `lines`.

The report uses these headings in this order:

1. `## Summary`: a table with columns Metric and Value. Rows: File, Words, Lines, Phrase hits, Hits per 1,000 words, Density band, Findings.
2. `## Phrase hits`: a table with columns Phrase, Category, Count, Lines. Lines are comma-separated. If there are no hits, write the single line `No phrase hits.`
3. `## Repeated openers`: a table with columns Opener, Count, Lines. If there are none, write `No repeated openers.`
4. `## Exit status`: one line with the exit code and its meaning.

## Script contract

Script: `scripts/phrase_scan.py`

Arguments: exactly one positional argument, the path to the input file.

Command line:

```
python -I "<skill-folder>/scripts/phrase_scan.py" "<input-file>"
```

Output keys on stdout (JSON, indented): `file` (base name only), `words`, `lines`, `phrase_hit_total`, `hits_per_1000_words`, `phrase_hits`, `opener_repeats`, `finding_count`.

Exit codes:

| Code | Meaning |
|---|---|
| 0 | No findings. |
| 1 | One or more findings (phrase hits or repeated openers). |
| 2 | Usage or input error. The error is one line of JSON on stderr. |

Error codes on stderr, each with exit code 2:

| Code | Cause |
|---|---|
| usage | Argument count is not exactly one. |
| file_missing | The path does not exist. |
| not_a_file | The path is a directory or other non-file. |
| too_large | The file is larger than 2 MB. |
| invalid_utf8 | The bytes are not valid UTF-8 (a UTF-8 byte order mark is accepted). |
| empty_input | The file contains no words. |

The script never writes files and never opens a network connection. Curly apostrophes are treated as straight apostrophes before matching. Matching is case-insensitive and whole-word.

## Refuse or stop when

- The user asks whether a person or an AI system wrote the text. Refuse to label authorship. Report the counts only.
- The user asks for rewritten sentences or a cleaned-up version. Refuse. The scanner reports; the author edits.
- The script exits 2. Stop, report the error code and the input condition that caused it, and ask for a corrected file.
- The input is not a draft of prose, such as a binary file or a data table. Stop and ask for a text draft.

## Shipped files

- `SKILL.md` (this file)
- `LICENSE.txt` (Apache-2.0 text)
- `scripts/phrase_scan.py` (the scanner)
- `fixtures/draft_sample.txt` (a 210-word smoke-test draft with five planted phrases and three repeated openers)
