---
name: agency-client-onboarding-checklist
description: Builds a client onboarding checklist for an agency project, with an access and asset list that gives each item one owner and a due day, a 45-minute kickoff agenda, an approval path with turnaround in working days, communication rules, a risk table with a mitigation for each risk, and a first-two-weeks timeline. Use when an agency is starting a client project and missing access, late assets or unclear approvers are likely to stall the work. Do not use for ongoing project management, contract drafting, or technical setup of client systems.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Agency client onboarding checklist

Writes one onboarding checklist for a new client project. The output is one Markdown document with eight numbered sections. Every table row has an owner, a due day or a turnaround, and a status, so that stalled work can be traced to a named person.

## Working values

The values below are working values chosen for agency projects of 2 to 12 weeks. They are not published standards. Change a value only when the user states a different one, and record the change in section 8.

| Item | Working value | Change it when |
|---|---|---|
| Kickoff length | 45 minutes (fixed) | Never |
| Access item due day | Day 3 | The client names a different date in writing |
| Asset item due day | Day 5 | The project is under 3 weeks; then use Day 3 |
| Turnaround, scope change | 3 working days | The contract sets a different period |
| Turnaround, creative or content draft | 3 working days | The contract sets a different period |
| Turnaround, final launch sign-off | 2 working days | The launch date is fewer than 3 working days away |
| Turnaround, invoice or legal term | 5 working days | The client finance team sets a different period |
| First escalation | 1 working day after turnaround ends, to the client sponsor | Never |
| Second escalation | 2 working days later, agency lead calls the sponsor | Never |
| Escalation when the approver is the client sponsor | First escalation to the agency lead; second to the agency's named executive, or "name needed" | Never |
| Question response time | 1 working day | The user states a different response time |
| Status update | Every Thursday, email | The user names another day |
| Decision log entry | Within 1 working day of the decision | Never |
| Minimum access or asset rows | 6 | The client has fewer than 6 systems or assets |

Day numbers count working days from Day 0, the kickoff day.

## Workflow

1. **Confirm intake.** Check five facts: client name, project name, length in weeks, agency lead, and client sponsor. Kickoff date is optional; if none is given, use "Day 0". Output: section 1 with each fact and its value or the word "missing".
2. **Build the access and asset list.** Start from these eight categories: domain registrar, hosting or CMS admin, analytics account, brand files (logo, fonts, colors), copy and content, product or service data, existing search or ad accounts, and approved contacts. Keep each category that applies and write "not applicable" for the rest. Output at least six rows (the minimum in the working values table). Give every row one owner: a named client person or a named agency person. Output: section 2 table, with IDs A-01 upward, the type "access" or "asset", and status "open".
3. **Set the kickoff agenda.** Use exactly these five items, which total 45 minutes. Output: section 3 table.
4. **Set the approval path.** List each approval type the project needs, with one approver role, the turnaround from the table above, and the escalation step. Output: section 4 table.
5. **Write the communication rules.** Output exactly five bullet rules in section 5. Each rule must name a channel, a time, or a person.
6. **Build the risk table.** Output exactly three risks in section 6: late assets, scope creep, and unclear owner. Each row has an early signal, a mitigation, and an owner. Add a fourth row only when the user supplies one.
7. **Build the first-two-weeks timeline.** Output section 7 with one row per action, using Day numbers from the working-day count. Cover Day 0 through Day 10. Each row has one owner.
8. **Record status and open questions.** Set the status line in section 1 to "complete", "partial", or "needs_input". List every unknown or changed working value as a numbered item in section 8.

## Kickoff agenda (fixed, 45 minutes)

| Minutes | Item | Lead |
|---|---|---|
| 10 | Goals and scope in one sentence each | Agency lead |
| 10 | Roles, owners, and sponsor | Client sponsor |
| 10 | Access and asset walkthrough, row by row | Agency lead |
| 10 | Approval path and turnaround | Agency lead |
| 5 | Communication rules and next steps | Agency lead |

## Field rules

- **Owner:** one person per row. Write a person's role and name, for example "Client marketing lead (name needed)". Do not write "team", "everyone", or "TBD" as an owner. If the name is unknown, keep the role and list the name as an open question.
- **Due day:** the word "Day" followed by a whole number of working days from Day 0, for example "Day 3". Rows for later weeks use the same form. Never write a calendar date unless the user gave one.
- **Status:** "open" at creation. Only the user can change a row to "done", so the skill never writes "done".
- **Turnaround:** a whole number of working days. Weekends and public holidays are not counted.
- **Escalation:** name the person who receives it, not the role alone.
- **Timeline:** keep Day 0 to Day 10 in order. Each row shows one action, not a list of actions.

## Output contract

The document starts with the line `# Onboarding checklist: <client> / <project>`, then the status line `Status: complete`, `Status: partial`, or `Status: needs_input`. Use these eight headings, in this order:

1. `## 1. Intake and status`. Table: Fact | Value.
2. `## 2. Access and asset list`. Table: ID | Item | Type | Owner | Due day | Status.
3. `## 3. Kickoff agenda (45 minutes)`. Table: Minutes | Item | Lead. Minutes must sum to 45.
4. `## 4. Approval path`. Table: Approval | Approver | Turnaround (working days) | Escalate after.
5. `## 5. Communication rules`. Exactly five bullets.
6. `## 6. Risk table`. Table: Risk | Early signal | Mitigation | Owner.
7. `## 7. First two weeks`. Table: Day | Action | Owner.
8. `## 8. Open questions`. Numbered list. Write "None" if empty.

## Refuse / stop when

- **Needs input:** any of client name, project name, length in weeks, or agency lead is missing. Stop. Return section 1 with status `needs_input` and a numbered list of the questions needed. Do not write sections 2 to 7.
- **Partial:** a required fact such as the client sponsor is missing, but the rest can be written. Write all eight sections with status `partial`, put "to confirm" in the affected cells, and list each gap in section 8.
- **Passwords or keys requested:** do not write any password, API key, or login in plain text, in the checklist, or in a reply. In the access row, write the item name and the owner only. Say that access is to be shared through the agency's password vault, with a grant to each named person.
- **Payment or bank details requested:** do not write card numbers, bank accounts, or tax IDs. Add an access row that says the client finance contact will share these through the client's own secure channel.
- **Verification requested:** this skill cannot check whether access works or whether an asset exists. Say so in section 8 and do not mark any row "done".

## Files shipped

- `SKILL.md`: this file, the only instructions the agent needs.
- `LICENSE.txt`: Apache License 2.0 text.
