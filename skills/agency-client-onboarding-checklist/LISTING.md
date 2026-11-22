# agency-client-onboarding-checklist

## One line

Writes a client onboarding checklist for an agency project: owned access and asset rows with due days, a fixed 45-minute kickoff agenda, approval turnaround in working days, communication rules, a three-risk table, and a first-two-weeks timeline.

## What it does

The skill turns a short intake (client, project, length in weeks, agency lead, client sponsor) into one Markdown checklist with eight numbered sections. The access and asset list gives every row a single owner, a due day counted in working days from kickoff, and an open status. The kickoff agenda is fixed at five items that add up to 45 minutes. The approval path lists each approval type with an approver role, a turnaround in working days, and the person who receives the escalation. The risk table covers late assets, scope creep, and unclear owner, and each risk has an early signal and a mitigation. The timeline runs from Day 0 to Day 10.

The working values (for example Day 3 for access items, Day 5 for assets, 3 working days for scope change approvals) are stated in one table so that a user can see which numbers are defaults and which came from them. The skill refuses to write passwords, keys, or payment details into the checklist and points the user to a password vault or the client's own secure channel.

## When to use

- An agency is starting a website, SEO, or content project and expects access or assets to arrive late.
- The project has several client-side approvers and nobody has written down who approves what.
- The agency lead wants a checklist to walk through at kickoff, with owners and dates already filled in.

## When not to use

- Ongoing project tracking after the first two weeks. The skill writes one checklist, not a status log.
- Drafting a contract, statement of work, or payment terms. Turnaround values in the table are working values, not contract terms.
- Setting up client systems, DNS, or accounts. The skill lists access, it does not perform or verify it.

## Requirements

A text-capable agent. No Python, no network access, no files beyond the skill folder. The user supplies the five intake facts in the request; any fact that is missing produces a numbered question list instead of a checklist.

## Example

The example below is the complete output for a 6-week website rebuild with fictional names, produced by following SKILL.md.

# Onboarding checklist: Example Client Co. / Website rebuild

Status: complete

## 1. Intake and status

| Fact | Value |
|---|---|
| Client name | Example Client Co. |
| Project name | Website rebuild |
| Length in weeks | 6 |
| Agency lead | Dana Morales |
| Client sponsor | Sam Okafor |
| Kickoff date | Not given; Day 0 used |

## 2. Access and asset list

| ID | Item | Type | Owner | Due day | Status |
|---|---|---|---|---|---|
| A-01 | Domain registrar login, shared through the agency password vault | access | Lee Park (client IT) | Day 3 | open |
| A-02 | Current CMS admin account, shared through the agency password vault | access | Lee Park (client IT) | Day 3 | open |
| A-03 | Analytics property editor access for the agency | access | Jordan Ellis (client marketing lead) | Day 3 | open |
| A-04 | Brand files: logo, fonts, color codes | asset | Jordan Ellis (client marketing lead) | Day 5 | open |
| A-05 | Current product list and prices, as a spreadsheet | asset | Riley Chen (client operations) | Day 5 | open |
| A-06 | Approved copy for home, about, and contact pages | asset | Jordan Ellis (client marketing lead) | Day 5 | open |
| A-07 | Approved contacts list for review sign-off | asset | Sam Okafor (client sponsor) | Day 5 | open |

Not applicable: existing search or ad accounts (no paid search in scope).

## 3. Kickoff agenda (45 minutes)

| Minutes | Item | Lead |
|---|---|---|
| 10 | Goals and scope in one sentence each | Agency lead |
| 10 | Roles, owners, and sponsor | Client sponsor |
| 10 | Access and asset walkthrough, row by row | Agency lead |
| 10 | Approval path and turnaround | Agency lead |
| 5 | Communication rules and next steps | Agency lead |

## 4. Approval path

| Approval | Approver | Turnaround (working days) | Escalate after |
|---|---|---|---|
| Scope change | Sam Okafor (client sponsor) | 3 | 1 working day past turnaround, to Dana Morales (agency lead); 2 working days later, agency executive (name needed, see section 8) |
| Homepage and key page drafts | Jordan Ellis (client marketing lead) | 3 | 1 working day past turnaround, to Sam Okafor; 2 working days later, Dana Morales calls Sam Okafor |
| Final launch sign-off | Sam Okafor (client sponsor) | 2 | 1 working day past turnaround, to Dana Morales (agency lead); 2 working days later, agency executive (name needed, see section 8) |
| Invoice or legal term | Client finance contact (name needed, see section 8) | 5 | 1 working day past turnaround, to Sam Okafor; 2 working days later, Dana Morales calls Sam Okafor |

## 5. Communication rules

- All decisions go in one shared project email thread. Chat messages are not decisions.
- The agency project lead answers every question within 1 working day.
- Dana Morales sends a status email every Thursday listing the open rows from section 2 and the next due day.
- Every decision is written into the decision log within 1 working day, with the approver's name.
- Each side names one point of contact; requests from other staff go to that contact first.

## 6. Risk table

| Risk | Early signal | Mitigation | Owner |
|---|---|---|---|
| Late assets | A section 2 row is open after its due day | Send a reminder on the due day; escalate under section 4 the next working day; move dependent tasks in section 7 | Dana Morales |
| Scope creep | A request is not in the scope sentence agreed at kickoff | Log it in the decision log; price it or defer it through the scope change approval (3 working days) | Dana Morales |
| Unclear owner | A row owner still reads "name needed" after Day 3 | Sam Okafor names the person within 1 working day; the row stays open until a name is entered | Sam Okafor |

## 7. First two weeks

| Day | Action | Owner |
|---|---|---|
| Day 0 | Kickoff meeting, 45 minutes, agenda in section 3 | Dana Morales |
| Day 1 | Send the section 2 list to the client and confirm each owner | Dana Morales |
| Day 2 | Client confirms the name for each row that still reads "name needed" | Sam Okafor |
| Day 3 | Access row A-01 due | Lee Park |
| Day 3 | Access row A-02 due | Lee Park |
| Day 3 | Access row A-03 due | Jordan Ellis |
| Day 4 | Agency lead tests the access received for A-01 to A-03 with the client | Dana Morales |
| Day 5 | Asset rows A-04 to A-07 due | Jordan Ellis |
| Day 5 | Week 2 starts: sitemap draft sent to Jordan Ellis for review, 3-day turnaround | Dana Morales |
| Day 8 | Sitemap approval turnaround ends | Jordan Ellis |
| Day 9 | First escalation if the sitemap is unapproved, to Sam Okafor | Dana Morales |
| Day 10 | Decision log reviewed | Dana Morales |

## 8. Open questions

1. Name the client finance contact who approves invoice and legal terms (section 4).
2. Client to confirm the Day 3 access and Day 5 asset due days, which are working values.
3. Client to confirm whether the contract sets any turnaround that differs from the section 4 values.
4. Name the agency executive who receives second escalations on client-sponsor approvals (section 4).

The example was written for this LISTING file. It is not a real client engagement.

## Limits

- Working values are not published standards. A contract or the client's own calendar overrides them.
- The skill cannot check whether access works or whether an asset exists. Its output is a plan, not a verification.
- Working days are counted as Monday to Friday. The skill does not know public holidays unless the user names them.
- The checklist holds names and roles. It does not hold passwords, keys, or payment details, and it does not replace the agency's password vault.
- The timeline covers two weeks. Projects longer than that need a second pass for the later weeks.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
