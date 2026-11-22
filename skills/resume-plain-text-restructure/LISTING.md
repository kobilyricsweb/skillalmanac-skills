# Resume plain-text restructure

## One line

Turns a pasted resume, including two-column or designed layouts, into a plain-text version with Summary, Experience, Education and Skills headings, plus a ledger that traces every line to its source.

## What it does

The skill takes the text of one resume and splits it into individual facts: the name, the contact line, the summary sentences, each job header with its dates, each bullet, each degree or certificate, and each skill. Text that a PDF or template scrambled across columns is rejoined before splitting, and each joined fact is shown with a slash in the ledger so a reviewer can see where the join happened.

Each fact is then placed under one of the four headings or listed as unplaced with a reason. Dates are rewritten in one format, MMM YYYY. Experience and education are sorted newest first. Bullets are kept to one column and start with a verb in the form the role needs. A trace check removes any number, employer, title or skill that does not appear in the source.

The output has four parts: the plain-text resume, a ledger with one row per fact, an unplaced list, and open questions with a status of complete, partial or blocked.

## When to use

Use it when a candidate has a resume that an applicant tracking system is likely to misread, such as a template with a sidebar, a header band, icons or a two-column grid. It also fits a resume pasted from a PDF where the columns have merged into one run of text.

## When not to use

Do not use it to write new achievements, to strengthen weak bullets, to tailor the resume to a posting, or to produce a cover letter. It will not invent a metric, a job, a date or a skill, and it will not raise a title. For a resume built from a job posting alone, there are no source facts to restructure.

## Requirements

Nothing beyond a text-capable agent. No scripts, no network, no files to install. The input is the resume text itself. Optional facts such as the full name, city and state, email and phone are used when present.

## Example

Input: a two-column resume copied from a PDF. The sidebar text is interleaved with the main column, one volunteer line has no dates, and the hobbies line sits at the bottom. The run record is in VERIFICATION.md under "Smoke run".

```
JORDAN ELLIS                         EXPERIENCE
Austin, TX, jordan.ellis@example.com    Operations Coordinator, Parkside Freight
                                     Mar 2022 - Present
PROFILE                              • Led weekly carrier scheduling for 40 routes
Operations professional with         • Cut invoice errors by 18% with a new checklist
experience in freight logistics.     • Maintain vendor master data in NetSuite
SKILLS
SQL, Excel, Tableau                  Dispatch Clerk, Lakeshore Logistics
Project management                   Jun 2019 - Feb 2022
                                     • Handled 120 inbound calls per shift
EDUCATION                            Volunteer coach, youth soccer
B.S. Business Administration,
State University, May 2019
Certified Six Sigma Yellow Belt,
Jul 2021
Hobbies: hiking, chess
```

Output:

```
JORDAN ELLIS
Austin, TX, jordan.ellis@example.com

SUMMARY
Operations professional with experience in freight logistics.

EXPERIENCE
Operations Coordinator, Parkside Freight | Mar 2022 - Present
- Lead weekly carrier scheduling for 40 routes
- Cut invoice errors by 18% with a new checklist
- Maintain vendor master data in NetSuite

Dispatch Clerk, Lakeshore Logistics | Jun 2019 - Feb 2022
- Handled 120 inbound calls per shift

EDUCATION
Certified Six Sigma Yellow Belt | Jul 2021
B.S. Business Administration, State University | May 2019

SKILLS
SQL, Excel, Tableau, Project management
```

LEDGER

| Fact ID | Source line | Section | Output line or UNPLACED | Edit |
|---|---|---|---|---|
| F01 | JORDAN ELLIS | Name | JORDAN ELLIS | NONE |
| F02 | Austin, TX, jordan.ellis@example.com | Contact | Austin, TX, jordan.ellis@example.com | NONE |
| F03 | Operations Coordinator, Parkside Freight / Mar 2022 - Present | EXPERIENCE | Operations Coordinator, Parkside Freight \| Mar 2022 - Present | NONE |
| F04 | Led weekly carrier scheduling for 40 routes | EXPERIENCE | - Lead weekly carrier scheduling for 40 routes | TENSE |
| F05 | Operations professional with / experience in freight logistics. | SUMMARY | Operations professional with experience in freight logistics. | NONE |
| F06 | Cut invoice errors by 18% with a new checklist | EXPERIENCE | - Cut invoice errors by 18% with a new checklist | NONE |
| F07 | Maintain vendor master data in NetSuite | EXPERIENCE | - Maintain vendor master data in NetSuite | NONE |
| F08 | SQL, Excel, Tableau | SKILLS | SQL, Excel, Tableau | NONE |
| F09 | Dispatch Clerk, Lakeshore Logistics / Jun 2019 - Feb 2022 | EXPERIENCE | Dispatch Clerk, Lakeshore Logistics \| Jun 2019 - Feb 2022 | NONE |
| F10 | Project management | SKILLS | Project management | NONE |
| F11 | Handled 120 inbound calls per shift | EXPERIENCE | - Handled 120 inbound calls per shift | NONE |
| F12 | B.S. Business Administration, / State University, May 2019 | EDUCATION | B.S. Business Administration, State University \| May 2019 | NONE |
| F13 | Volunteer coach, youth soccer | UNPLACED | UNPLACED | NONE |
| F14 | Certified Six Sigma Yellow Belt, / Jul 2021 | EDUCATION | Certified Six Sigma Yellow Belt \| Jul 2021 | NONE |
| F15 | Hobbies: hiking, chess | UNPLACED | UNPLACED | NONE |

UNPLACED

| Fact ID | Reason |
|---|---|
| F13 | No dates, and undated volunteer work is not a job entry |
| F15 | Interests are not one of the four headings |

OPEN QUESTIONS

1. F13 (volunteer coach): give the start and end months to place it under EXPERIENCE. Otherwise it stays unplaced.

Trace: all traced
Status: partial

## Limits

The skill checks the structure of its own output against the source it was given. It does not check the source itself, so a wrong date or title in the original is carried through faithfully. It does not verify how any particular applicant tracking system parses the result, does not compare the output visually with the original layout, and does not judge whether the resume will persuade a reader. Date-order rules assume the source dates are correct. Non-English resumes, and dates written in day-first or numeric forms with unclear months, are handled by open questions rather than by a conversion rule. Working thresholds, such as six bullets per job, are working values chosen for this skill and are not an industry standard.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
