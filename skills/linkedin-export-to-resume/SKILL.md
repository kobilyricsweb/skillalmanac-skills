---
name: linkedin-export-to-resume
description: Drafts a reverse-chronological resume from LinkedIn profile export text that the user pastes, using only the facts in that text. Use when a user pastes profile export text (name, positions, education, skills) and asks for a resume, CV or resume draft. Writes fixed resume sections, a fact ledger that ties each line to its source, and a GAPS list for missing dates, descriptions and metrics. Do not use for fetching a live profile or web address, cover letters, inventing achievements or numbers, or editing an existing resume file.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B); no network access and no scripts are needed.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# LinkedIn export to resume

Turns pasted profile export text into a resume draft. Every line of the draft traces to one row of a fact ledger. Nothing is added from memory, from the web or from claims the user makes in chat. The license is Apache-2.0; see [LICENSE.txt](LICENSE.txt).

## Input

Accepted forms:
- Plain text with labeled blocks: `Name:`, `Headline:`, `About:`, a `Positions:` block with one entry per role, an `Education:` block, and a `Skills:` line.
- CSV rows pasted with their header line. Treat each row as one item.
- Position lines as `Position N: Title | Company | Dates | Location`, each followed by an indented `Description:` line. A blank Description value means the position has no description.

Each position needs `Title`, `Company` and `Dates`. `Location` and `Description` are optional.

Required intake facts (all must be present to proceed):
1. A name.
2. At least one position with a title and a company.

## Workflow

1. **Intake check.** Confirm the required facts. If one is missing, set Status to `blocked`, write one numbered question per missing fact (at most 5) under Open questions, and stop. Write no resume draft. If the input is only a web address, treat it as `blocked` and ask for the pasted export text.
2. **Parse positions.** For each position record Title, Company, Dates, Location and Description. Keep every value verbatim from the export. Assign ledger IDs in export order.
3. **Sort.** Order positions newest first by start date, read as month and year (Jan to Dec or full month names). Ties keep export order. A missing or unreadable start date sorts last in export order and raises NO_START_DATE.
4. **Split descriptions into bullets.** Split each Description at sentence-ending periods and keep each sentence verbatim. Use the first 5 sentences per position in export order. List any extra sentences under Open questions as not used. Do not reword, merge or add words.
5. **Check gaps.** Apply the gap codes below to each position and to the education and skills blocks. Write one GAPS row per code that is hit.
6. **Build the draft** in this fixed order: name, headline, summary (only if About text exists), experience, education, skills. Each position heading reads `Title | Company | Dates | Location`. Omit Location when absent. Write `Dates not provided` when no start date exists.
7. **Build the ledger.** Write one row per resume line: name, headline, summary, each position heading, each bullet, each education entry and the skills line.
8. **Set the status and write the output.** Tell the user that the bracketed IDs are for review and must be removed before the draft is sent.

## Thresholds

| Rule | Value | Action when hit |
|---|---|---|
| Bullets per position | max 5 (working value) | Extra sentences go to Open questions as not used |
| Bullet length | max 30 words (working value) | Keep verbatim and ask the user under Open questions which words to cut |
| Skills listed | max 15 (working value) | Extra skills go to Open questions as not used |
| Metric bullet | a bullet with at least one digit 0 to 9 (working value) | Position with bullets and zero metric bullets raises NO_METRIC |
| Required positions | at least 1 with title and company | None means `blocked` |
| Date text | verbatim as exported; `Present` or `Current` is an open end | See gap codes |

## Gap codes

| Code | Condition |
|---|---|
| NO_START_DATE | Start date missing or unreadable |
| NO_END_DATE | No end date and no `Present` or `Current` |
| NO_DESCRIPTION | Position has zero sentences |
| NO_METRIC | Position has bullets and none has a digit |
| NO_EDUCATION_DATES | Education entry has no years |
| NO_SKILLS | Skills block empty or missing |

A blank Dates value raises NO_START_DATE only, never NO_END_DATE. An education entry with no years writes `Years not provided` in its heading and raises NO_EDUCATION_DATES.

## Status values

- `complete`: no GAPS rows and no refused clauses.
- `partial`: at least one GAPS row, or at least one refused clause.
- `blocked`: a required intake fact is missing, or the input is not profile text. No resume draft is written.

## Output contract

Write these headings in this order, with this exact text:

`## Status`
One line: `Status: complete | partial | blocked`, then `Positions: N. Bullets: N. Ledger rows: N. Gaps: N.`

`## Resume draft`
- First line `# <Name>`, then the headline if present.
- `### Summary` (only if About text exists).
- `### Experience`: each position as `**Title | Company | Dates | Location** [ID]`, followed by bullets `- sentence [ID]`.
- `### Education`: each entry as `**School | Degree | Years** [ID]`; when the entry has no years, write `Years not provided` as the Years value.
- `### Skills`: one comma-separated line `[ID]`.

`## Fact ledger`
Table with columns `ID | Section | Export label | Text used (verbatim)`. IDs run F01 upward.

`## Gaps`
Table with columns `ID | Code | Location | Question to the user`. IDs run G01 upward. Each Code must appear in the gap codes table.

`## Open questions`
Numbered list covering blocked intake questions, refused clauses, bullets over the word limit, and extra sentences or skills not used. Write `None` when empty.

## Refuse or stop when

- A required intake fact is missing, or only a web address was given: stop with `blocked` (Workflow step 1).
- The input is not profile text, for example a different document: stop with `blocked` and ask for the export.
- The user asks to fetch, open or log in to a live profile: refuse that clause only, work from the pasted text, and set `partial`.
- The user asks to add or invent a title, achievement, date, number or claim that the export does not contain: refuse that clause only. Keep the source text, list the request under Open questions, and set `partial`.
- The user asks to cover letters, outreach messages or edits to an existing resume file: not this skill. Say so in one line and stop that clause.
