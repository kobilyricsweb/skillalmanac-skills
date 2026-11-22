---
name: business-proposal-writer
description: Writes a client business proposal from a brief, a scope and a price, using a fixed section order, a deliverables table, scope-boundary clauses and TO-CONFIRM markers for every missing input. Use when a user has a client problem, an intended scope and a price and needs a proposal draft, a bid reply or a short statement of work for a consulting, agency or freelance engagement. Do not use for legal contracts, invoices, grant applications, cold sales emails or investment advice.
license: Apache-2.0
compatibility: Requires nothing beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Business proposal writer

Turn a brief into a proposal that states the client's problem before anything else. The output follows one fixed section order. Anything the user did not supply is written as TO-CONFIRM, never guessed. This skill does not give legal advice and does not write binding terms.

## Inputs the user must supply

| Field | Accepted form | If missing |
|---|---|---|
| Client problem | The client's own words, quoted or paraphrased from the user | Stop (see Refuse / stop when) |
| Desired outcome | One measurable statement, such as "lower checkout drop-off" | Write TO-CONFIRM in Summary |
| Scope in | Bullet list of work items | Write TO-CONFIRM in Deliverables |
| Scope out | Bullet list of excluded items | Use the default clauses in step 5, marked TO-CONFIRM |
| Timeline | Number of weeks and start condition | Write TO-CONFIRM in Timeline |
| Price | Amount, currency and basis (fixed, hourly, retainer) | Write TO-CONFIRM in Price and terms |
| Proof | Named case, credential or client quote the user owns | Omit the proof line; never invent one |

## Workflow

1. Intake check. Output: the intake table above with each field marked OK or TO-CONFIRM. Confirm the client problem is present before going further.
2. Win themes. Choose 2 or 3 win themes. Each theme must cite one sentence from the client problem or the user's brief. Output: a list of "theme | source sentence". A theme with no source sentence is dropped.
3. Draft the eight sections in the order given in the output contract. Respect the word limits in the decision table.
4. Apply the claim rules. Every factual claim must trace to the brief. Output: a count of claims checked and the number removed.
5. Scope boundaries. Add 3 to 6 clauses from the list in the scope clause table. Replace any clause the user contradicted. Output: the numbered clause list.
6. Open items sweep. Collect every TO-CONFIRM marker into the Open items table. Output: the table, one row per marker.
7. Final check against the threshold table. Output: the proposal, followed by the Open items table, and nothing else.

## Decision table and word limits (working values)

| Section | Word limit | Rule |
|---|---|---|
| 1 Summary | 60 to 90 | First sentence states the client outcome in 25 words or fewer |
| 2 The problem | 80 to 150 | Uses the client's own nouns; no solution language |
| 3 Our approach | 100 to 200 | One paragraph per deliverable group, no more than 4 groups |
| 4 Deliverables | table | 3 to 8 rows; every row has an acceptance check |
| 5 Timeline | table | One row per week; total rows equal the stated timeline |
| 6 Price and terms | table | Five rows: fee, currency, payment schedule, validity, expenses |
| 7 Scope boundaries | 3 to 6 numbered clauses | Each clause names one exclusion or one client duty |
| 8 Next step | 1 to 3 sentences | Ends with one dated action for the client |
| Open items | table | Last element; one row per TO-CONFIRM marker, or one row reading "none" |

Win-theme limits: 2 or 3 themes; a theme name is 2 to 4 words; a theme is not repeated in more than 2 sections.

Payment schedule rule: a fixed fee with no schedule given is written as "TO-CONFIRM: payment schedule". Do not default to 50/50.

Validity default: 30 days when the user gives no value, marked TO-CONFIRM.

Missing-week rule: if the timeline is 6 weeks and no weekly split is given, the timeline table has 6 rows marked "TO-CONFIRM activity" in each row.

## Claim rules

- No superlatives: "best", "leading", "world-class", "unmatched" are removed.
- No numbers that the brief does not contain. A result percentage needs a user-supplied source, otherwise it is TO-CONFIRM.
- No names of clients, staff, certifications or awards unless the user supplied them.
- No testimonial text. A quote appears only if the user pasted it.
- Competitors are not named or criticized.

## Scope clause table

| Clause | Use when |
|---|---|
| Changes after sign-off are priced by a written change request | Any scope is fixed-fee |
| Work outside the listed deliverables needs a signed change request | Always |
| Client supplies access and content within 5 working days; each day of delay moves the timeline by one day | Work depends on client materials |
| Third-party tools, hosting, paid licenses and domain costs are excluded unless listed | Tools are involved |
| Implementation of recommendations is excluded from this engagement | Audit or review work |
| Quote valid for 30 days from issue date | Always (value TO-CONFIRM if the user sets another) |

## Output contract

Return one Markdown document with these headings in this order, and nothing before or after it:

```
# Proposal: <client name or TO-CONFIRM>

## 1. Summary
## 2. The problem
## 3. Our approach
## 4. Deliverables
| # | Deliverable | What the client gets | Week due | Acceptance check |
## 5. Timeline
| Week | Activity | Output |
## 6. Price and terms
| Item | Value |
## 7. Scope boundaries
1. ...
## 8. Next step

## Open items
| Marker | Section | Why it is needed | Owner |
```

The Open items table is the last element. If there are no TO-CONFIRM markers, the table has one row reading "none".

## Example of the expected shape

Brief: a 6-week website audit for a regional clinic group. Client problem: "patients cannot find the booking page on mobile." Price not given.

The skill writes section 6 as:

| Item | Value |
|---|---|
| Fee | TO-CONFIRM |
| Currency | TO-CONFIRM |
| Payment schedule | TO-CONFIRM |
| Validity | 30 days (default, TO-CONFIRM) |
| Expenses | TO-CONFIRM |

and lists "TO-CONFIRM | 6 Price and terms | Fee not supplied | user" in Open items.

## Refuse / stop when

- The brief contains no client problem in any form. Stop and ask for one sentence from the client.
- The user asks for invented client names, references, case studies, testimonials, credentials, certifications, team bios, awards or prices. Refuse those lines and write TO-CONFIRM.
- The user asks for a contract, indemnity, liability cap, warranty or binding term. Output a note that counsel must draft those; do not draft them.
- The user asks for a guaranteed result or a return figure without a user-supplied source. Refuse the guarantee; write TO-CONFIRM.
- The user asks for a price, discount or rate that does not appear in the brief. Write TO-CONFIRM; do not compute one.

## Package files

- SKILL.md: this procedure.
- LICENSE.txt: Apache License 2.0 text.

There are no scripts and no evals folder in this package.
