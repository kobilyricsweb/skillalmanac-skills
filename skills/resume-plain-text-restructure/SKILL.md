---
name: resume-plain-text-restructure
description: Restructures a pasted resume into plain text with the standard headings Summary, Experience, Education and Skills, single-column bullets and one date format. Use when a candidate needs a text version that applicant tracking systems can parse, or when a two-column or designed resume must be flattened. Do not use for inventing new claims, writing cover letters, or building a resume from a job posting alone.
license: Apache-2.0
compatibility: None beyond a text-capable agent.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Resume plain-text restructure

Rearranges one pasted resume into a plain-text version with four standard headings. It only reorders and reformats facts that already appear in the source. Every output line traces to one row of the fact ledger. The procedure does not check how a particular applicant tracking system parses the file.

## Workflow

1. **Intake check.** Required: the resume text, with at least three facts (see step 2). Optional: full name, city and state, email, phone. If the required input is missing, set status to blocked and return the numbered question list in "Refuse / stop when". Output: the line `Intake: ok` or `Intake: blocked`.

2. **Split the source into facts.** One fact is one of: the name line; a contact line; a summary sentence group; a job header with its dates; one bullet; one degree or certificate with its date; one skill list line or one skill item. Rejoin text that wraps across lines or columns, and show each join as ` / ` in the Source line column. Drop bullet glyphs. Assign IDs F01, F02, and so on in reading order: read each line band left column first, then right column. Output: the fact list with ID and source line.

3. **Map each fact to a section.** Use the table below. Anything without a matching row goes to UNPLACED with a reason. Output: the Section value for every ID.

| Source content | Target |
|---|---|
| Name at the top of the page | Name line (above the headings) |
| Email, phone, city and state | Contact line (above the headings) |
| Profile, objective, about, professional summary | SUMMARY |
| Job header with employer and title, plus its bullets (dates may be missing) | EXPERIENCE |
| Degree, school, bootcamp, certificate or license | EDUCATION |
| Skill list, tools, software, languages | SKILLS |
| Hobbies, interests, awards, publications, references, photos, undated volunteer work | UNPLACED |

4. **Normalize dates.** Every date in the output is MMM YYYY with a three-letter English month (Jan 2020, Sep 2021). Ranges use ` - ` (space, hyphen, space).

| Source form | Output | Rule |
|---|---|---|
| January 2020, Jan 2020, 2020-01, 01/2020 | Jan 2020 | Convert and log DATE |
| Present, Current, Now | Present | Allowed only as the end of a range |
| 2020 alone | 2020 | Not converted; add an open question |
| Job header with no date | DATE NEEDED in place of the date | Keep the job; add an open question |

5. **Order, format and trim.**
   - EXPERIENCE: reverse-chronological by end date, Present first. Ties are broken by start date, newer first.
   - EDUCATION: reverse-chronological by date.
   - SKILLS: source order, one comma-separated line.
   - Bullets: one column, each starting with a verb. The current role uses the base form (Lead, Cut, Maintain). Earlier roles use the past form (Handled). Filler words may be removed; numbers and nouns stay.

   Working values (not a published spec):

| Check | Working value | On breach |
|---|---|---|
| Bullets per job | 6 | Keep the 6 most specific; move the rest to UNPLACED with reason "over bullet cap" |
| Words per bullet | 25 | Remove filler words only (code TRIM); if still longer, add an open question |
| Sentences in SUMMARY | 3 | Keep the first 3; move the rest to UNPLACED |

6. **Trace check.** Every number, percentage, year, employer, title, school and skill in the output must match a ledger row word for word, apart from DATE changes. Remove any token that does not trace and log it as REMOVED. Output: `Trace: all traced` or `Trace: N removed`, where N is the count of removed tokens.

7. **Write the deliverable and set status.** Use the output contract below. Status values:

| Status | Use when |
|---|---|
| complete | Every fact is placed or unplaced with a reason, and there are no open questions |
| partial | Output is written and at least one open question exists (undated job, year-only date, empty section, refused clause) |
| blocked | No output; the numbered question list is returned instead |

## Output contract

Section A is the resume. It is plain text: no Markdown symbols, no bold, no tables, no columns, no graphics. Blank lines separate sections.

```
JORDAN ELLIS
Austin, TX, jordan.ellis@example.com

SUMMARY
One to three sentences from the source.

EXPERIENCE
Title, Employer | Mon YYYY - Mon YYYY
- Bullet one
- Bullet two

EDUCATION
Credential, Institution | Mon YYYY
Credential | Mon YYYY

SKILLS
Skill, Skill, Skill
```

Use `Credential | Mon YYYY` when the source gives no institution. A section with no source facts keeps its heading and reads `Not in source.`

Section B is `LEDGER`: a table with the columns Fact ID, Source line, Section, Output line or UNPLACED, Edit. Every fact ID appears exactly once, in source order. Edit codes:

| Code | Meaning |
|---|---|
| NONE | Line unchanged |
| TENSE | Lead verb put in the form the role needs |
| TRIM | Filler words removed |
| DATE | Date changed to MMM YYYY |
| REDACT | Sensitive identifier removed; Source line shows `[redacted]` |
| REMOVED | Untraceable token removed |

Section C is `UNPLACED`: a table with the columns Fact ID and Reason. Write `None` if empty.

Section D is `OPEN QUESTIONS`: a numbered list. Write `None` if empty.

Section E is the last two lines: `Trace: ...` and `Status: complete`, `Status: partial` or `Status: blocked`.

Sensitive identifiers (national ID numbers, bank or card numbers, date of birth, full home street address) are never written into the output, the ledger or the open questions. Replace them with `[redacted]` and code the row REDACT. A REDACT row has Section = the section it would have gone to, Output line = `[redacted]`, Edit = REDACT, and is not counted as UNPLACED.

## Refuse / stop when

- **Blocked, with a numbered question list.** No resume text; fewer than three facts; or the text is a job posting, cover letter or other non-resume. Return status blocked and this list, dropping any question already answered:
  1. Paste the full resume text, including every job, degree and skill.
  2. Confirm this is a resume, not a job posting or a cover letter.
  3. Give the start and end months for each job that has no dates.
- **Refuse one clause only.** A request to add an employer, title, date, number, skill, certification, degree or award that is not in the source; a request to raise a title or move dates to hide a gap. Refuse that clause, keep the rest of the deliverable, set status partial, and list the refused item under OPEN QUESTIONS.
- **Refuse one clause only.** A request to add a metric, scope or outcome to a bullet that the source does not state. Keep the bullet as sourced.
- **Refuse one clause only.** A request to keep a multi-column layout, tables, icons, graphics or colored text in the output. The output stays plain text; set status partial.
- **Never pad.** A short source gives a short output. Do not write filler to reach a length.
- **No silent stop.** Every stop returns either the deliverable or the numbered list above.

Files in this folder: [SKILL.md](SKILL.md) (this procedure) and [LICENSE.txt](LICENSE.txt) (Apache-2.0 license text).
