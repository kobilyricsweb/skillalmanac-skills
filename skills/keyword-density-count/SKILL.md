---
name: keyword-density-count
description: Counts how often each keyword or phrase appears in plain page text and reports case-insensitive, whole-word counts and density percentages, plus the top 15 non-stopword terms and bigrams. Use when an editor needs a keyword density check on a page draft, wants to confirm which target phrases are absent before publishing, or needs repeatable counts to compare two revisions of the same page. Do not use for ranking prediction, HTML or rendered-page parsing, synonym or semantic matching, or any claim that a density value improves search position.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Keyword density count

This skill counts keyword and phrase matches in the visible text of one page and reports density as a percentage of total words. It runs one script, `scripts/keyword_density.py`, and then writes a report from its JSON output. The script reports numbers only. No density value is a ranking target, and this skill never assigns a pass or fail mark to a density.

## Workflow

1. **Intake.** Confirm two files: a page text file (UTF-8, plain text, at most 2 MB) and a keyword file (UTF-8, one keyword or phrase per line, at most 100 keywords, each at most 10 words). Output: a two-line intake record with both file names. If the page is supplied as HTML, stop and ask for the visible text (see the refuse list).
2. **Check the page text.** Confirm it holds the body copy only, without menus, footers, or navigation labels. Output: a yes or no, with the word count you expect in one line.
3. **Run the script.** Output: the raw JSON on stdout and the exit code.
   `python -I scripts/keyword_density.py <input-file> <keyword-file>`
4. **Read the exit code** using the decision table below. Output: the status value for the report.
5. **Check the arithmetic.** For every keyword row, and for the first row of each top list, confirm `density_pct = round(matches x words / total_words x 100, 2)`, where `words` is the phrase's word count. Output: "arithmetic checked" or the row that failed. A failed row means the report is not written; rerun step 3.
6. **Write the report** in the output contract below. Output: the report only, with no advice on targets.

## Decision and threshold table

| Condition | Value | Result |
|---|---|---|
| Script exit code 0 | every keyword has at least one match | status `complete`, no absent list |
| Script exit code 1 | one or more keywords have status `ABSENT` | status `complete`, list each absent keyword |
| Script exit code 2 | usage or input error | status `failed`, report the error code only |
| Input file size cap | 2 MB (2,097,152 bytes) | over the cap: `file_too_large` |
| Keyword file size cap | 2 MB | over the cap: `file_too_large` |
| Keywords per file | 100 | more than 100: `too_many_keywords` |
| Words per keyword | 10 | more than 10: `phrase_too_long` |
| Top terms and bigrams listed | 15 each | fixed |
| Minimum length for a top unigram | 2 characters (working value) | shorter tokens are skipped |
| Stopword list | 68 words (fixed in the script) | skipped in top lists only |
| Density pass mark or target | none | do not invent one |

## Counting rules the script applies

- Text is lowercased. A token is a run of letters a to z and digits 0 to 9. An apostrophe inside a word is kept (`don't` is one token). A curly apostrophe or any other non-ASCII letter ends a token.
- A keyword matches only whole tokens. `page` does not match `pages` or `webpage`.
- Matches overlap, and a phrase may cross a sentence or paragraph break, because the token stream ignores punctuation and line breaks.
- `density_pct` uses the phrase's word count: a 2-word phrase with 5 matches in 416 words gives 5 x 2 / 416 x 100 = 2.40.
- Top terms: unigrams with a stopword or a token under 2 characters removed, ranked by matches (highest first) and then alphabetically.
- Top bigrams: bigrams where neither word is a stopword, ranked the same way.

## Output contract

Write the report with these headings, in this order:

1. `## Summary`: a line with `Status: complete | partial | failed`, `Total words: <n>`, and `Keywords checked: <n>`.
2. `## Keyword counts`: a table with the columns `Keyword | Words | Matches | Density % | Status`, one row per keyword in file order. `Status` is `FOUND` or `ABSENT`, copied from the script.
3. `## Absent keywords`: a bulleted list of the absent keywords, or the line `None`.
4. `## Top terms`: a table with the columns `Term | Matches | Density %`, up to 15 rows.
5. `## Top bigrams`: a table with the columns `Term | Matches | Density %`, up to 15 rows.
6. `## Method note`: the script's `note` value, copied exactly.
7. `## Open questions`: items the user must decide, or `None`.

The script's JSON keys are `total_words`, `keywords` (each with `keyword`, `words`, `matches`, `density_pct`, `status`), `absent_keywords`, `top_terms` and `top_bigrams` (each with `term`, `matches`, `density_pct`), and `note`.

## Script contract (type A)

- Arguments: `<input-file>` (page text) then `<keyword-file>`. Exactly two arguments are required.
- Reads both files and writes nothing. No network and no subprocess.
- Stdout: one JSON object, indented by 2 spaces.
- Stderr on exit 2: one line of JSON, `{"error": "<code>"}`, with `"line": <n>` added where the code names a keyword line.
- Exit codes: `0` every keyword matched; `1` at least one keyword is `ABSENT`; `2` usage or input error.

| Error code | Cause |
|---|---|
| `usage` | argument count is not 2 |
| `file_unreadable` | a file is missing, a directory, or cannot be opened |
| `file_too_large` | a file is over 2 MB |
| `not_utf8` | a file is not valid UTF-8 (a leading byte-order mark is accepted) |
| `no_words` | the page text has no letters or digits |
| `no_keywords` | the keyword file has no non-blank lines |
| `keyword_without_words` | a keyword line has no letters or digits (give its `line`) |
| `phrase_too_long` | a keyword has more than 10 words (give its `line`) |
| `duplicate_keyword` | a keyword repeats an earlier one after normalization (give its `line`) |
| `too_many_keywords` | more than 100 keywords |

## Refuse or stop when

- The page is HTML, a rendered DOM, or a document export with markup. Stop and ask for the visible text. Do not strip tags by hand.
- Any script exit code is 2. Report the error code and stop; do not estimate counts.
- The user asks for a target density, a pass mark, or a "safe" percentage. Refuse only that clause: keep the counts, set status `partial`, and list the request under Open questions.
- The user asks whether a density value improves ranking. Refuse that clause the same way, set status `partial`, and state that the script measures text only.
- The user asks to add repeated keywords to raise a density. Refuse that edit. The counts can still be reported.

## Files in this skill

- [scripts/keyword_density.py](scripts/keyword_density.py): the counting script.
- [fixtures/page_text_300.txt](fixtures/page_text_300.txt): a 300-word page text used for the smoke run.
- [fixtures/keywords_3.txt](fixtures/keywords_3.txt): three keywords, one of which is absent from the fixture.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.
