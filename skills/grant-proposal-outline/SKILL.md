---
name: grant-proposal-outline
description: Outlines a nonprofit grant proposal against a funder's stated criteria by mapping each criterion to a section, splitting the word limit into budgets that sum to the limit, and drafting need, outcomes and budget skeletons. Use when the user pastes funder guidelines with criteria and a word limit and needs an outline before drafting, or when a draft misses criteria. Do not use for writing final prose, finding funders, donor letters, or inventing statistics, partners or past results.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B); no scripts, no network.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Grant proposal outline

Produces a six-part outline for one grant proposal from pasted funder guidelines and the applicant's own material. The output maps each funder criterion to one of seven proposal sections, sets word budgets that add up to the limit, and marks every missing fact as TO-CONFIRM. Skeleton sentences only; no finished prose.

Shipped files: [LICENSE.txt](LICENSE.txt). No scripts.

## Workflow

Run the steps in order. Stop at the first stop condition.

1. **Intake check.** Output: the intake table below with each fact marked present or missing.

| Fact | Required | If missing |
|---|---|---|
| Funder guidelines text with at least 3 criteria | yes | stop |
| Word limit as a number of words | yes | stop |
| Program name | yes | partial |
| At least 1 outcome figure with its source | yes | partial |
| Requested total amount | no | budget row shows TO-CONFIRM |

   On a stop, write `Status: stopped` and a numbered list of up to 5 questions, one per missing fact. Write no outline.

2. **Extract criteria.** Output: list C1, C2, ... in the order the guidelines state them, each with its guideline heading. Quote at most 15 words of any criterion; paraphrase the rest.

| Criteria found | Action |
|---|---|
| 0 to 2 | stop; ask for the full guidelines |
| 3 to 12 | proceed |
| 13 or more | stop; ask the user to choose 12 (working value) |

3. **Set word budgets.** Output: the budget table in output section 2. Start from the default shares (working values). The seven proposal sections are fixed.

| Proposal section | Default share | Words at a 1,500-word limit |
|---|---|---|
| 1 Summary | 8% | 120 |
| 2 Need | 18% | 270 |
| 3 Program | 22% | 330 |
| 4 Outcomes and measures | 15% | 225 |
| 5 Organizational capacity | 12% | 180 |
| 6 Evaluation | 13% | 195 |
| 7 Budget narrative | 12% | 180 |

   Rules: round sections 1 to 6 to the nearest 5 words. Section 7 takes the rounding difference so the total equals the limit exactly. If the guidelines set a per-section limit, use it and spread the remaining words over the other sections in proportion to their default shares. If section 7 differs from its default by more than 3 percentage points of the limit, stop and ask.

4. **Map criteria to sections.** Output: the criteria map in output section 1. Assign each criterion to exactly one primary section using this guide.

| Criterion is about | Primary section |
|---|---|
| Summary, fit with the funder's mission | 1 Summary |
| Community problem, population, gap | 2 Need |
| Activities, staffing, schedule, design | 3 Program |
| Results, change, participants reached | 4 Outcomes and measures |
| Board, staff, history, partners, reserves | 5 Organizational capacity |
| Data collection, reporting, learning | 6 Evaluation |
| Cost, match, cost per participant | 7 Budget narrative |

   A section may hold zero criteria and is still kept. A criterion that fits no section goes to open items. A section holding more than 4 criteria is flagged as overloaded in open items (working value).

5. **Draft the need statement and outcomes.** Output: output sections 3 and 4.
   - Need claims: one row per claim with its value and a source tag. Allowed tags are `USER-DATA: <document, year>` for figures the user supplied, `PUBLIC: <named source, date>` for public figures the user supplied with a citation, and `TO-CONFIRM` for anything else. Every number in the need paragraph carries a tag. An untagged number is removed.
   - Outcomes: 2 to 5 rows (working value; more than 5 means ask the user to trim, and fewer than 2 means partial). Columns: Outcome, Measure, Target, Timeframe, Source. Target and timeframe the user did not supply are TO-CONFIRM.

6. **Draft the budget skeleton and open items.** Output: output sections 5 and 6. Each line item shows its amount and source tag. Close the budget table with two fixed rows: `Line-item sum` (the computed sum of the line items; Basis `computed`, Status `n/a`) and `Requested total` (as supplied; Status `supplied` if it equals the sum, `mismatch: <difference>` if not). If the user gave no requested total, the Requested total row shows TO-CONFIRM. Never adjust either figure. Section 6 (Evaluation) gets a word budget only; no evaluation skeleton is drafted. Open items are numbered in the order they appear in sections 3 to 5, followed by any unmapped criteria and overload flags.

Status rule:

| Status | Condition |
|---|---|
| complete | all intake facts present; no TO-CONFIRM, mismatch, or unmapped criterion remains |
| partial | outline produced; at least one TO-CONFIRM, mismatch, or unmapped criterion remains |
| stopped | a required intake fact is missing or a stop threshold was hit; no outline |

## Output contract

The reply is Markdown in this order. Use the exact headings.

```
# Grant outline: <program name>
Status: <complete | partial | stopped>
Limit: <N> words

## 1. Criteria map
| ID | Criterion (at most 15 words) | Guideline heading | Section |

## 2. Word budgets
| Section | Words |
(7 rows, then a Total row equal to the limit)

## 3. Need statement
| Claim | Value | Source tag |
(then one paragraph no longer than the section 2 budget)

## 4. Outcomes and measures
| Outcome | Measure | Target | Timeframe | Source |

## 5. Budget narrative skeleton (proposal section 7)
| Line item | Amount | Basis | Status |
(line items, then the Line-item sum row and the Requested total row from step 6; Status is supplied, TO-CONFIRM, or mismatch, and n/a on the Line-item sum row)

## 6. Open items
(numbered list; each item names its section and what is missing)
```

## Refuse or stop when

1. The word limit is missing, or it is given in pages with no words-per-page figure in the guidelines.
2. The criteria count is outside 3 to 12 (step 2).
3. Section 7 is more than 3 percentage points off its default (step 3).
4. The user asks for a statistic, partner name, past result, award, testimonial, or quotation that the user did not supply. Write TO-CONFIRM and do not estimate.
5. A user figure has no source. Do not use it; list it under open items.
6. The requested total differs from the line-item sum. Report the difference; change neither figure.
7. The funder asks for a section outside the seven. Ask for its word budget; do not add it silently.
