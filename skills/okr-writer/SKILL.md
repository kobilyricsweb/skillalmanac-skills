---
name: okr-writer
description: Rewrites draft OKRs for one period into measurable objectives and key results, flagging tasks, output counts, vanity totals and sandbagged targets, and leaving unknown baselines as TO-CONFIRM. Use when draft OKRs read like a to-do list, when key results have no baseline, unit or source of measure, or when a target needs a sandbagging check before scoring. Do not use for personal habit lists, dated project plans with owners, live KPI dashboards, or for inventing baselines or actual results.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# OKR writer

Use this procedure to review and rewrite draft OKRs for a single period. Work only from the drafts and the numbers the user supplies. Never supply a number that was not given to you.

This package is procedure only. It has no scripts.

## Inputs

- Draft objectives with their key results (KRs), as plain text.
- A period label, for example "Q3 2026" or "FY2027". If it is missing, ask once and stop until it is given.
- Baseline values and dates, only where the user has them.

## Workflow

1. Inventory the drafts. Assign IDs: objectives O1, O2, and so on; key results O1-KR1, O1-KR2, and so on. Required output: a list of IDs with the draft text copied verbatim.
2. Check each objective against the objective rules below. Required output: PASS or REWRITE for each objective, with one reason.
3. Classify each KR with the anti-pattern table. A KR gets one code or PASS. Required output: one code per KR.
4. Check each KR against the KR field rules. Required output: which of the five fields (Metric, Baseline, Target, Source, Owner) are present or missing.
5. Check each target against the threshold table. Required output: OK or a named flag per target.
6. Rewrite every KR that has a code other than PASS or is missing a field. Required output: a before and after pair for each rewritten KR.
7. Turn every baseline you could not take from the input into an open item marked TO-CONFIRM, naming the role that should supply it. Required output: the open items list.
8. Assemble the output contract below. Required output: every section present, in the stated order.

### Objective rules

- Qualitative and inspiring: a direction a person can say aloud in one sentence.
- No digits in the objective text. Numbers belong in KRs.
- 6 to 20 words.
- Owned and achievable within the one period. A dated deliverable is not an objective; classify it as TASK.

### KR field rules

- Metric: one measurable quantity with a unit (count, percent, minutes, currency, score).
- Baseline: the current value with its date. If unknown, write TO-CONFIRM. Never estimate it.
- Target: a value that differs from the baseline in the stated direction.
- Source: the named report, export or system where the number is read. An empty source is a NO-SOURCE flag.
- Owner: a role. Use a person's name only if the user gave one.
- Length: 8 to 25 words.

### Anti-pattern table

| Code | What it looks like | Test | Fix |
|---|---|---|---|
| TASK | A deliverable verb: "Launch", "Build", "Migrate", "Hire" | Would the KR be complete the day the thing ships, even if no metric moved? | State the change the deliverable should cause, with its metric |
| OUTPUT | A count of what was produced: "Publish 12 guides" | The number measures effort, not result | Measure the result of the output, such as the share of readers who finish a guide |
| VANITY | A total that can grow while the business does not: raw page views, total sign-ups, follower count | No quality or conversion rate sits beside it | Pair it with the rate that shows quality, or replace it |
| SANDBAG | Target equals or is below the baseline, or is already met | Target minus baseline is zero or has the wrong sign | Apply the threshold table, or mark the target TO-CONFIRM |
| MULTI | Two metrics joined by "and" or "or" | Count the metrics in the sentence | Split into two KRs and keep the one that matters |
| VAGUE | No number: "improve", "better", "increase engagement" | No unit can be found | Add metric, unit, baseline and target |
| NO-SOURCE | No system named for reading the number | Source field is empty | Name the export; if none exists, list the KR as an open item |

When more than one code applies, report only the first in this order: TASK, OUTPUT, VANITY, SANDBAG, MULTI, VAGUE, NO-SOURCE.

### Threshold table (working values, not industry standards)

| Check | Working value | If outside |
|---|---|---|
| Objectives per period | 2 to 4 | 1 or 5 or more: flag and ask which to keep |
| KRs per objective | 2 to 4 | Flag |
| Required change from baseline in one period | 10% to 100% relative, or points for a percent metric | Under 10%: SANDBAG review. Over 100%: feasibility check, mark TO-CONFIRM |
| Baseline age | Measured within 90 days before period start | Older: keep the value, add its date, mark TO-CONFIRM |
| Words per objective | 6 to 20 | Rewrite |
| Words per KR | 8 to 25 | Rewrite |

### Scoring convention

State this as a convention in the output, never as a standard: 0.0 means no movement; 0.3 means some movement, far from target; 0.7 means the target was reached, which is the aim for a well-set KR; 1.0 means fully reached, which suggests the target was too easy. Each KR is scored on its own metric.

## Output contract

Use these headings, in this order, and nothing else at the top level.

## Summary
Lines in this exact form: `Period:`, `Objectives:` (count), `KRs reviewed:` (count), `PASS:` (count), `REWRITTEN:` (count), `TO-CONFIRM baselines:` (count).

## Findings
A table with the columns: ID | Draft text | Code | Result | Reason. Result is PASS or REWRITE. One row per objective and one row per KR.

## Rewrites
One block per rewritten KR, in this form:

### O1-KR2 (OUTPUT)
- Before: draft text, verbatim
- After: the rewritten KR, one sentence
- Metric: unit
- Baseline: value and date, or TO-CONFIRM
- Target: value, or TO-CONFIRM (set after baseline)
- Source: named report or export
- Owner: role

## Open items
Bulleted lines in this form: `- TO-CONFIRM: <item> - ask <role>`. If there are none, write `None.`

## Scoring
One line stating the scoring convention above.

## Refuse or stop when

- No key results are in the input: stop and ask for the drafts.
- The user asks for a baseline, actual result or target that was not given: write TO-CONFIRM and do not supply a figure.
- The user asks you to backfill actual results for a period that has ended: refuse to fabricate actuals and offer to set the next period's KRs instead.
- The draft mixes two or more periods: stop and ask which period to rewrite.
- A KR measures one named person's rating, pay or discipline: stop and offer a team-level metric instead.
- The user asks for targets the team cannot miss, or targets that hide a decline: refuse the SANDBAG target and show the threshold table.
- More than 20 KR drafts are supplied at once: ask for batches of 20 or fewer.

## Worked rule

A KR that reads "Launch the onboarding checklist by March 31" is TASK. The rewrite names the change the checklist should cause, for example the share of new accounts that finish setup in the first week, with that baseline marked TO-CONFIRM and the source named by the user. Never keep the launch date as the measure.
