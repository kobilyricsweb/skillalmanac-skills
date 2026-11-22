---
name: page-title-meta-checker
description: Checks page titles and meta descriptions in a CSV of url, title and description for empty tags, length limits, a pixel-width proxy, duplicates across URLs and titles that repeat their description. Use when auditing a list of page titles and meta descriptions before publishing or after a template change, or when a CSV export needs a quick tag check. Do not use for crawling live sites, rendering real search result snippets, judging keyword quality, or rewriting tag text.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Page Title and Meta Description Checker

This skill runs one script over one CSV file and reports every title and meta description that breaks a rule. It does not fetch pages, and it does not write new tag text.

## Workflow

1. **Confirm the input.** The file must be UTF-8 CSV with a header row that contains the columns `url`, `title` and `description`. Other columns are ignored. Ask for the file path if the user did not give one.
   Output: the file name and the header check result (pass or the missing column names).

2. **Run the script** with this exact command line:
   `python -I scripts/title_meta_check.py <input-file> --format json`
   Output: the raw JSON object (see the output contract) and the exit code.

3. **Handle the exit code.**
   - Exit 2: report the `error` text from the JSON object. Ask the user for a corrected file. Stop here.
   - Exit 0: report that no rule was broken. Go to step 6.
   - Exit 1: go to step 4.

4. **Group findings by row.** Sort by `row`, then keep the order the script gave. Output: one block per row with `url` and its findings.

5. **Attach the fix hint from the table below** to each finding. Output: one line per finding in the form `row | code | detail | fix hint`. Do not write replacement text for titles or descriptions.

6. **Write the summary.** Output: the summary block described in the output contract below.

## Decision and threshold table

Lengths count characters after trimming the ends and keeping inner spaces. All limits are working values, not published search engine specifications.

| Code | Rule | Limit (working value) | Fix hint |
|---|---|---|---|
| `EMPTY_TITLE` | title is blank after trimming | none | Write a title of 25 to 60 characters that names the page topic. |
| `TITLE_TOO_SHORT` | title length below minimum | 25 characters | Add the page subject so the title reaches 25 characters. |
| `TITLE_TOO_LONG` | title length above maximum | 60 characters | Cut the title to 60 characters or fewer, keeping the topic word first. |
| `TITLE_PIXELS_OVER` | pixel-width proxy above maximum | 580 px | Shorten the title; wide capitals and letters such as W and M add the most width. |
| `EMPTY_DESCRIPTION` | description is blank after trimming | none | Write a description of 70 to 160 characters that states what the page covers. |
| `DESCRIPTION_TOO_SHORT` | description length below minimum | 70 characters | Add one concrete detail to reach 70 characters. |
| `DESCRIPTION_TOO_LONG` | description length above maximum | 160 characters | Cut the description to 160 characters or fewer. |
| `DESCRIPTION_PIXELS_OVER` | pixel-width proxy above maximum | 920 px | Shorten the description until the proxy is under 920 px; wide capitals and letters such as W and M add the most width. |
| `DUPLICATE_TITLE` | same title, after case and whitespace normalization, in two or more rows | 2 rows | Give each listed row a title that names its own page. |
| `DUPLICATE_DESCRIPTION` | same description, after normalization, in two or more rows | 2 rows | Give each listed row a description that names its own page. |
| `TITLE_EQUALS_DESCRIPTION` | title and description are the same text after normalization | none | Rewrite the description so it adds information beyond the title. |

Normalization for duplicates and equality: trim the ends, collapse runs of whitespace to one space, then compare case-insensitively.

Pixel-width proxy: the script adds a fixed width per character, in pixels, from an approximation table. The table is: default 9; uppercase 11, except I 5, M 13, W 15; i j l . , : ; 4; f 5; r t 6; m 14; w 12; space 4; apostrophe 3; ! | - ( ) 5. The result is an approximation, not a font render.

## Output contract

The script prints one JSON object to stdout with exactly these keys:

| Key | Type | Meaning |
|---|---|---|
| `file` | string | base name of the input file |
| `rows` | integer | number of data rows checked, header excluded |
| `status` | string | `ok` (no findings) or `findings` |
| `counts` | object | one key for each of the 11 codes in the decision table, zero included |
| `findings` | array | objects with `row` (integer), `url` (string), `code` (string), `detail` (string) |

`row` is the 1-based data row number. The header is not counted and blank records are skipped.

On bad input the script prints one line: `{"status": "input_error", "error": "<message>"}`.

The summary block in the chat reply has three lines: `Rows checked: <rows>`, `Findings: <total>`, then one line per code with a non-zero count, in the table order.

## Script contract

- Path: `scripts/title_meta_check.py`
- Arguments: `input_file` (required, path to the CSV); `--format json` (default) or `--format table`.
- Output: stdout only. The script writes no files and reads the input once.
- Limits: input larger than 2 MB is refused. Invalid UTF-8 is refused. Missing or unreadable files are refused.
- Exit codes: `0` no findings; `1` one or more findings; `2` usage or input error.
- Command line used in this skill: `python -I scripts/title_meta_check.py <input-file> --format json`

## Refuse or stop when

- The input is larger than 2 MB, is not UTF-8, or lacks one of the columns `url`, `title`, `description`. Stop, quote the error, and ask for a corrected file.
- The user asks to fetch pages, crawl a site or read live search results. This skill has no network access; say so and offer to check the CSV instead.
- The user asks what a search engine will display for a tag. Report only the pixel-width proxy and label it as an approximation.
- The user asks for new title or description text. Return the findings and the fix hints; the author writes the text.

## Files shipped with this skill

- [scripts/title_meta_check.py](scripts/title_meta_check.py): the checker described above.
- [fixtures/smoke_pages.csv](fixtures/smoke_pages.csv): an 8-row test input with duplicate titles, an empty description, a 90-character title and other faults. Use it to confirm the script runs; it is not user data.
- [LICENSE.txt](LICENSE.txt): the Apache License 2.0 text.
