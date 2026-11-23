---
name: service-package-description
description: Writes a fixed-scope service package description with a package name, outcome, quantified deliverables, exclusions, client responsibilities, working-day timeline, revision count, acceptance criteria and price as supplied. Use when a freelancer or small agency must define exactly what a client receives for a package, when a quote lists vague deliverables, or when an existing package is missing terms. Do not use for setting or discounting prices, promising results or guarantees, drafting legal contracts, or giving regulated professional advice.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B), with no network access and no tools other than reading the intake facts supplied in the conversation.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Service package description

This skill turns seller-supplied intake facts into one package description that a client can read without a follow-up call. It never invents a price, quantity, duration or client name. A complete or partial package always has the ten sections shown in the output contract, in that order.

Shipped files: this `SKILL.md` and [LICENSE.txt](LICENSE.txt) (Apache-2.0).

## Required and optional intake facts

| ID | Fact | Required | If absent |
|----|------|----------|-----------|
| R1 | Each deliverable with its quantity and file format | Yes | status `needs_input` |
| R2 | Working days for each phase (concept, feedback, revision, final) | Yes | status `needs_input` |
| R3 | Number of revision rounds included | Yes | status `needs_input` |
| O1 | Price as supplied, with amount and unit (for example, flat fee) | No | status `partial`, Price reads "Not supplied" |
| O2 | Client responsibilities the seller wants stated | No | use the default list in the Client responsibilities table |

## Workflow

1. **Check intake.** Confirm R1, R2 and R3 are present. If any is missing, stop and follow the stop rule below. Required output: the status line and nothing else.
2. **Check refusal triggers.** Match each clause of the request against the refusal table. If the whole request is only for a legal contract, trademark clearance or regulated advice, set status `refused` and output the Refused block described in the output contract. Otherwise refuse only each matched clause: write its replacement wording in place of the clause, keep the rest of the package, and record the refused clause for Open questions. The status then follows the status table.
3. **Write the package name and outcome.** The name is 2 to 4 words and names no vendor or brand. The outcome is one sentence of 30 words or fewer that names the deliverables and the revision count. It must not contain the words "guarantee", "guaranteed", "ensures", "best" or "100%".
4. **Build the deliverables table.** One row per R1 item. Files per row equal quantity multiplied by the number of formats. Required output: the table plus a "Total files" row that sums the file counts.
5. **Write exclusions.** Start from the default list for the service type (exclusions table). Add the seller's own out-of-scope items from intake. Required output: at least 3 bullets.
6. **Build the timeline.** List phases in order, each with its working days from R2 and a cumulative total. Required output: the timeline table with a Total row. If the total exceeds 20 working days, add a milestone row every 10 working days.
7. **Write acceptance criteria.** One row per deliverable row from step 4, using the criteria table. Required output: the criteria table with columns Deliverable, Criterion.
8. **Copy the price.** Copy O1 exactly as supplied. Do not convert currency, round, compute discounts or add taxes. If O1 is absent, write "Not supplied" and set status `partial`.
9. **Self-check before output.** Recompute the Total files row and the timeline Total. Count the ## headings and confirm there are exactly 10. Search the text for each banned word from step 3. Fix any mismatch once, then output.

## Decision tables

### Status

| Condition | Status |
|-----------|--------|
| R1, R2 or R3 missing | `needs_input` |
| The whole request is for a legal contract, trademark clearance or regulated advice | `refused` |
| R1, R2, R3 present and O1 absent, or a clause was refused | `partial` |
| R1, R2, R3 present, O1 present and no clause was refused | `complete` |

### Refusal triggers

| The request asks for | Response |
|----------------------|----------|
| A guaranteed result: sales, rankings, traffic, conversion rate, or approval by a third party | Refuse this clause only. Replace it with the wording "The seller delivers the items listed; the seller does not control outcomes." Status `partial`; list the refused clause under Open questions. |
| Trademark registration or legal clearance, as one clause of a package | Refuse this clause only. Write it only as an exclusion. Status `partial`; list the refused clause under Open questions. |
| Unlimited revision rounds | Refuse this clause only. Write the R3 count instead. Status `partial`; list the refused clause under Open questions. |
| A price, discount or currency conversion the seller did not supply | Not refused. Do not compute it. Status follows the status table. |
| A legal contract, trademark clearance or regulated professional advice, as the whole request | `refused`. Out of scope for this skill. |

### Default exclusions (working value, by service type)

| Service type | Default exclusions |
|--------------|--------------------|
| Logo design | Trademark search or registration; print production and physical proofs; animation or motion versions; stationery or brand guidelines; purchased font or stock image licenses |
| Any other type | Take at least 3 exclusions from the seller's out-of-scope list; none are added by default |

### Acceptance criteria (working value)

| Deliverable kind | Criterion written in the table |
|------------------|--------------------------------|
| Raster preview (PNG, JPG) | Long edge 1500 px or more |
| Raster final (PNG, JPG) | Long edge 3000 px or more; transparent background when the item says so |
| Vector (SVG, PDF) | Opens without error in a vector editor and in a PDF viewer |
| Any item | Delivered count equals the R1 quantity |
| Feedback | Due within 2 working days of delivery; one consolidated list per round |

### Client responsibilities (defaults, used when O2 is absent)

| Responsibility | Default wording |
|----------------|-----------------|
| Feedback | Send one consolidated feedback list per round, within 2 working days of delivery |
| Materials | Supply brand or reference files before the first phase starts |
| Approval | Confirm the selected concept in writing before the final phase starts |

## Output contract

The output is a Markdown document with a status line first, then the ten sections below. Headings are exact.

```
Status: complete | partial
## 1. Package name
## 2. Outcome
## 3. Included deliverables     (table: Item | Quantity | Format | Files)  + "Total files" row
## 4. Exclusions                (bullets, at least 3)
## 5. Client responsibilities   (bullets)
## 6. Timeline                  (table: Phase | Working days | Cumulative)  + Total row
## 7. Revisions                 (one sentence: round count, days per round, feedback window)
## 8. Acceptance criteria       (table: Deliverable | Criterion)
## 9. Price                     (the O1 text as supplied, or "Not supplied")
## 10. Open questions           ("None." for complete; one bullet per missing optional fact and one per refused clause for partial)
```

Refused output (whole request only): the line `Status: refused`, then one bullet per matched trigger quoting the replacement wording from the refusal table. No other sections.

Needs-input output: the line `Status: needs_input`, then a numbered list of at most 5 questions, one per missing required fact (R1, R2 or R3). No other sections.

## Refuse or stop when

- R1, R2 or R3 is missing: stop with `needs_input` and the numbered question list. Do not guess quantities, durations or revision counts.
- The request asks for a guaranteed result, guaranteed approval, or unlimited revisions: refuse that clause only, write the replacement wording in its place, keep the package and set `partial`.
- The whole request is for a legal contract, trademark clearance or regulated advice: set `refused`. As one clause of a package, refuse the clause only, as above.
- The request asks for a price, discount or currency conversion that was not supplied: write "Not supplied" and set `partial`. Do not compute a figure.
- A deliverable has no format in R1: stop with `needs_input` and ask for the format.
