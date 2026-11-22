---
name: onboarding-checklist-builder
description: Builds a role-specific onboarding checklist with owners, due dates, done-evidence, an access and equipment list, and day-30, day-60 and day-90 outcomes that the manager must confirm. Use when a manager or team lead needs ad hoc onboarding turned into a dated checklist for a named role and start date, or when a new hire plan must say who does what before day 1 and in week 1. Do not use for HR or legal compliance content such as policy acknowledgements, tax or visa steps, background checks or labor-law wording, which HR owns, and do not use for offboarding or performance reviews.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B); no network.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Onboarding checklist builder

Build one checklist for one new hire. The output is a Markdown document with the sections in step 6. Run the steps in order. Do not skip the intake.

## 1. Intake (required first)

Collect these fields. If a required field is missing, or the start date is not a real ISO date (YYYY-MM-DD), stop and ask for that field only.

| Field | Required | Rule |
|---|---|---|
| Role title | yes | Use the title as given. Do not invent a seniority level. |
| Team | yes | Team name as given. |
| Manager | yes | Role title of the manager, for example "Analytics Manager". A personal name is optional. |
| Start date | yes | ISO date. Day 1 is this date. |
| Team tools | yes | List of tools. If there are more than 8, group them into access bundles in step 3. |
| Location | no | "remote" or a site name. Used only for the equipment row. |
| Buddy | no | If blank, the manager assigns one (item BD1-01). |

Output: the Intake table (section 6, item 2).

## 2. Compute the period dates

- Day 1 = start date.
- Day 30, day 60 and day 90 = start date plus 30, 60 and 90 calendar days.
- Week 1 = start date through day 5, counted in business days (Monday to Friday).
- Before day 1 = the business days immediately before the start date.
- Business-day due dates ignore public holidays because no holiday calendar is applied. Note this in Open questions when the start date falls within two weeks of a known holiday.

Output: the three dates in the document header line are the start date only. Each section header carries its own dates in the Due column.

## 3. Assign owners and due dates

Use this decision table for every item. Values are working values, not standards.

| Item type | Default owner | Due rule |
|---|---|---|
| Account or access request | IT administrator | start date minus 3 business days |
| Equipment hand-over | IT administrator | start date minus 5 business days |
| Buddy named and introduced | Manager | start date minus 2 business days |
| Team tool first-login check | Manager | day 1 |
| Reading of team documents | New hire | day 5 |
| Meeting with a data consumer or adjacent team | New hire; manager sends the invite | day 5 |
| Walk-through of current dashboards or reports | Buddy | day 5 |
| Outcome confirmation at day N | Manager | day N |

Every item needs five fields: ID, item text, owner (a role title unless a person name was given), due date in YYYY-MM-DD, and done-evidence. Done-evidence must be something a third party can check: a ticket number, a link, a saved log, or a filed note. The word "done" alone is not evidence.

## 4. Count thresholds

| Section | Items | ID prefix |
|---|---|---|
| Access and equipment | 3 to 6 | ACC- |
| Before day 1 | 2 to 4 | BD1- |
| Week 1 | 4 to 7 | W1- |
| Day 30 | 2 to 3 | D30- |
| Day 60 | 2 to 3 | D60- |
| Day 90 | 2 to 3 | D90- |

Total must be 15 to 26 items. If the total is below 15, add a line to Open questions naming the thinnest section. If a section would exceed its maximum, merge items that share one owner instead of adding rows.

## 5. Success outcomes

Write one outcome per day-30, day-60 and day-90 period.

- The measure must be something the manager can observe in a single check, for example "manager watches one run of the query set".
- Confirmed by is the manager role title. The new hire never confirms their own outcome.
- Confirm date equals that period's due date.

## 6. Output contract

Produce exactly these parts, in this order, as Markdown:

1. Heading `# Onboarding checklist: {role title}`, then one line: `Start: YYYY-MM-DD | Team: {team} | Manager: {manager}`
2. `## Intake`, table with columns `Field | Value`, one row per intake field.
3. `## Access and equipment`, table with columns `ID | Item | Owner | Due (YYYY-MM-DD) | Done evidence`.
4. `## Before day 1`, `## Week 1`, `## Day 30`, `## Day 60`, `## Day 90`. Each uses the same five columns as part 3.
5. `## Success outcomes`, table with columns `Period | Outcome | Measure | Confirmed by | Confirm date`.
6. `## Routed to HR`, bullet list. Write "None from intake." when empty.
7. `## Open questions`, bullet list. Write "None." when empty.

No other headings. No compliance wording in any cell.

## 7. Self-check before returning

Fix the table and re-check until every line passes:

- Every item has an owner, a YYYY-MM-DD due date, and non-empty done-evidence.
- Every ACC- row and the equipment row are due on or before the business day before the start date.
- No due date is later than start date plus 90 calendar days.
- Each section's item count matches the table in step 4.
- Each day-N outcome has Confirmed by set to the manager role title.
- No cell contains policy acknowledgement, legal, tax, visa, benefits-eligibility or background-check wording.

## Refuse or stop when

- Role title, team, manager or start date is missing, or the start date is not a real ISO date. Stop and ask for that one field.
- The request asks for HR or legal compliance content (policy acknowledgements, legal obligations, tax, visa, background checks, benefits rules). Do not write it. Add the topic to Routed to HR as "HR to own".
- The request asks for personal data about the new hire, such as salary, national ID, health or family details. Refuse and leave it out.
- The request asks you to send messages, open tickets, or change accounts. This skill writes the document only.
- The request asks you to mark an item done. Leave done-evidence as "to be filed" and let the owner fill it in.
