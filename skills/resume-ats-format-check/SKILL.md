---
name: resume-ats-format-check
description: Checks a plain-text or Markdown resume for layout and wording patterns that applicant tracking systems commonly misparse. Use when the user asks to check a resume for ATS problems, asks why a resume parses badly, or wants to know which headings, tables, bullets, dates or symbols to fix before applying. Do not use for scoring a resume, promising an interview or pass rate, rewriting resume content, judging candidate quality, or checking a PDF or Word file.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Resume ATS format check

Runs `scripts/ats_check.py` on one resume saved as plain text or Markdown and reports the lines that applicant tracking systems often misread. The check reports patterns only. It does not score the resume and does not predict how any system will parse it.

## Workflow

1. Confirm the intake. You need one file path to a `.txt` or `.md` resume. If the user has only a PDF or Word file, stop and follow the Refuse or stop list. Output: the input path, noted as accepted.
2. Run the script with the command in the Script contract section. Output: the JSON object from stdout, kept for steps 4 and 5.
3. Branch on the exit code. 0: no findings, go to step 5. 1: findings, go to step 4. 2: report the error value from the Error values table and stop. Output: the exit code and, for 2, the error value.
4. Map each finding to its priority in the Decision thresholds table. Sort rows by priority (P1 first), then by line number, with line 0 (whole file) first inside each priority. Output: the rows for the Findings table and the Fix order list.
5. Write the report in the Output contract. Output: the four headings in order, with the Summary values filled in.

## Decision thresholds

| Code | Threshold (working values unless stated) | Priority | Fix |
|---|---|---|---|
| MISSING_SECTION | No heading for Experience, Education or Skills (accepted names below) | P1 | Add a plain heading with a standard name |
| MISSING_EMAIL | No email address pattern anywhere in the file | P1 | Put an email address in the header |
| MISSING_PHONE | No run of 10 to 15 digits in the file | P1 | Put a phone number in the header |
| NO_DATE_RANGE | No line with two years, or a year with Present or Current | P1 | Write each job with a date range on its own line |
| TAB_OR_SPACE_RUN | A tab, or three or more spaces between text | P1 | Remove column layouts and use one column |
| TABLE_PIPE | Any pipe character | P1 | Replace pipes with commas or line breaks |
| NONSTANDARD_HEADING | Heading-like line not in the accepted names | P2 | Rename it to an accepted name |
| UNUSUAL_BULLET | Line starts with a glyph other than hyphen, asterisk or plus | P2 | Use a hyphen |
| SPECIAL_SYMBOL | Non-ASCII bullet, arrow, star or symbol inside text | P2 | Replace with a comma or a hyphen |
| DATE_FORMAT_MIXED | Line uses a date format that is not the most common in the file | P2 | Use the most common format throughout |
| LONG_LINE | More than 200 characters on one line | P3 | Split the line into two bullets |

Heading and date rules used by the script:

| Rule | Value |
|---|---|
| Accepted names (case-insensitive, leading `#` and trailing colon ignored) | Experience, Work Experience, Professional Experience, Employment, Employment History, Work History, Education, Academic Background, Skills, Technical Skills, Core Skills, Key Skills, Core Competencies, Summary, Profile, Professional Summary, Projects, Certifications, Certificates, Awards, Publications, Languages, Volunteer Experience, References, Contact |
| Heading-like line | Starts with `#`, or ends with a colon, or is all capitals of at least 3 letters; 1 to 4 words; at most 40 characters; does not start with a bullet or digit |
| Name line | The first non-empty line is skipped for heading checks |
| Date formats | `month_name` (Jan 2019), `numeric_slash` (03/2021 or 3/12/21), `iso` (2023-07) |
| Date range | Two years, or a year with Present or Current, joined by a hyphen, en dash, em dash or "to" |
| DATE_FORMAT_MIXED | Only checked when two or more formats appear; the format used on the most lines is the dominant one |

## Script contract

Command (replace `<input-file>` with the user's file; `<skill-folder>` is the folder holding this SKILL.md):

    python -I "<skill-folder>/scripts/ats_check.py" "<input-file>"

- Arguments: exactly one positional argument, the path to the resume file.
- Input: UTF-8 (a BOM is allowed), at most 2 MB, no NUL bytes. LF and CRLF line endings both work.
- Stdout: one JSON object with the keys in the JSON contract below.
- Stderr: on exit 2, one line of JSON, `{"error": "<value>"}`.
- Writes no files, reads no other files, makes no network calls.
- Exit codes: 0 no findings, 1 one or more findings, 2 usage or input error.

JSON contract (stdout):

| Key | Type | Meaning |
|---|---|---|
| lines_scanned | integer | Number of lines read |
| total | integer | Number of findings |
| counts | object | Finding count per code, keys sorted |
| findings | array | Objects with `line` (integer, 0 means whole file), `code` (one of the 11 codes above) and `detail` (fixed text) |

Error values (stderr, exit 2):

| Value | Meaning |
|---|---|
| usage: ats_check.py <input-file> | Argument count is not exactly one |
| file_not_found | The path does not exist |
| unreadable_input | The path is a directory or cannot be read |
| input_over_2_mb | The file is larger than 2 MB |
| binary_input | A NUL byte was found, so the file is likely a PDF, Word or other binary file |
| invalid_utf8 | The bytes are not valid UTF-8 |

## Output contract

The report has exactly these four headings, in this order.

1. `## Summary`: bullet list with `Exit code`, `Lines scanned`, `Findings` (the `total` value) and `Input` (the path as given, or `accepted`).
2. `## Findings`: table with the columns `Line`, `Code`, `Priority`, `Detail`. Use `file` in the Line column when `line` is 0. One row per finding.
3. `## Fix order`: numbered list, one line per distinct code present, P1 codes first. Each line gives the code, its count and the Fix text from the Decision thresholds table.
4. `## Not checked`: bullet list of the limits in the Limits section below.

## Refuse or stop when

- No file path is given. Ask the user for the path to a `.txt` or `.md` file. Do not guess a path.
- The file is a PDF, Word or other binary file (exit 2, `binary_input`). Ask the user to paste the resume text into a `.txt` file, or to save it as plain text, then run again.
- The file is larger than 2 MB or is not valid UTF-8 (exit 2). Report the error value and stop.
- The user asks for a score, a pass probability, a ranking against other candidates, or a claim about how one named tracking system behaves. Refuse that part only. Keep the rest of the report and say so.
- The user asks for rewritten bullets or new wording. This is outside the check. Give the Fix order only.
- Do not repeat the resume text, names, email addresses or phone numbers in the report. Cite line numbers only.

## Limits

- The check looks for patterns. It does not measure how any tracking system parses the file, and it has no vendor-specific rules.
- A name written in capitals on a heading-like line can be flagged as NONSTANDARD_HEADING, and a year range can be read as a phone number. Read each finding before editing.
- A heading in title case with no colon and no `#` (for example 'Career Summary') is not recognized as heading-like and is never flagged.
- Visual layout, fonts, images, headers and footers, and text boxes are not visible in plain text and are not checked.

## Shipped files

- [scripts/ats_check.py](scripts/ats_check.py): the checker described in the Script contract.
- [fixtures/sample_resume.txt](fixtures/sample_resume.txt): a 40-line text resume with a spacing block, an odd heading and mixed dates, for a smoke run.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
