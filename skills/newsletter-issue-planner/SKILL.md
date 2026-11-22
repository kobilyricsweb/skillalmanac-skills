---
name: newsletter-issue-planner
description: Plans one marketing newsletter issue with an angle, a section blueprint with word budgets, five subject lines with preview text, a link audit and a pre-send checklist. Use when a single newsletter issue must be assembled quickly from three user-supplied source items, a stated audience, one goal and one call to action. Do not use for multi-issue sequences, drip campaigns, automation setup, or writing the full issue body.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Newsletter Issue Planner

This skill plans one newsletter issue before any copy is written. The output is a plan: an angle, a section blueprint with word budgets, five subject-line options with preview text, a link and image audit, and a pre-send checklist. It does not write the issue body. Work only from facts the user supplies.

## Inputs the user must supply

- Audience: one sentence naming who reads the list and what they already care about.
- Goal: exactly one of `inform`, `convert`, `retain`, `announce`.
- Three source items: each with a title, a link the user will test themselves, and one fact stated in the user's own words.
- Call to action (CTA): one action and one destination link.
- Send date (optional): used only by the seasonal subject-line option.
- Most-used item (required only for the `retain` goal): the number of the source item the audience uses most, as the user states it.

If the user gives a fact that is not in the three items, leave it out of the plan.

## Workflow

**Step 1. Intake.** Check each input above.
Required output: an `Intake` block that lists every input as `GIVEN` or `MISSING`.
If the audience, goal, or CTA is `MISSING`, or fewer than three source items are given, follow the stop list below and do not continue.

**Step 2. Angle.** Pick one angle from the table using the goal.
Required output: the angle name, one sentence naming the reader benefit, and the number of the source item that leads.

| Goal | Angle | Lead item rule |
|---|---|---|
| inform | Explain: what changed and why it matters | the item the user marks as most time-sensitive |
| convert | Offer: the one item the reader can act on now | the item whose fact names a concrete action |
| retain | Routine: a habit or task the reader repeats | the item the audience uses most, as the user states |
| announce | News: one new thing and when it applies | the announcement item |

If two items tie for lead, use source item 1.

**Step 3. Section blueprint.** Use this fixed order. Budgets count body words only (not subject, preview, or footer).

| Section | Word budget | Content rule |
|---|---|---|
| Opening | 40-60 | One paragraph that names the angle |
| Item 1 | 90-130 | Uses only the fact supplied for item 1 |
| Item 2 | 90-130 | Uses only the fact supplied for item 2 |
| Item 3 | 90-130 | Uses only the fact supplied for item 3 |
| CTA block | 25-40 | The CTA sentence and its link, once |
| Total | 335-490 | If the sum is outside this range, shorten or lengthen the item furthest from its range |

Required output: a Blueprint table with columns `Section | Budget | Source item | Purpose`, and a `Total` row with the planned sum.

**Step 4. Subject lines.** Write exactly five options in this order: `curiosity`, `specific benefit`, `direct`, `question`, `seasonal`.
If no send date was supplied, the seasonal option uses a season named in the audience sentence; if none is named, write `NEEDS SEASON` in the subject cell.

Working values (chosen for this skill, not published standards):

| Field | Budget in characters |
|---|---|
| Subject | 30-50 |
| Preview text | 40-90 |

Rules: no word in all capitals; at most one exclamation mark across all five subjects; no emoji; no claim that is not in the source items.
Required output: a Subject lines table with columns `# | Type | Subject | Subject chars | Preview | Preview chars`. Count characters including spaces and write the exact count.

**Step 5. Link and image audit.** The plan has four links: one per source item plus the CTA link. Flag any link that is missing, duplicated, or shortened.
Images: none unless the user supplies them. A supplied image needs alt text of 5-15 words taken from the user's description of it.
Required output: a table with columns `Link | Where | Status`, where `Status` is one of `OK`, `MISSING`, `DUPLICATE`, `SHORTENED`, or `IMAGE OK` / `IMAGE NO ALT`.

**Step 6. Pre-send checklist.** Use exactly these rows. Status is `PASS`, `FAIL`, or `USER-CONFIRM`.

| Check | Status rule |
|---|---|
| Every link tested by the user in a live preview | Always `USER-CONFIRM`; this skill cannot open links |
| Unsubscribe link in footer | Always `USER-CONFIRM` |
| Sender name and postal address in footer | Always `USER-CONFIRM` |
| Plain-text version drafted | `PASS` when the plan says the plain-text version keeps the blueprint order, drops images, and repeats the four links; otherwise `FAIL` |
| All five subjects within budget | `PASS` when every count from Step 4 is inside its range; otherwise `FAIL` |
| Every number and quote traces to a supplied item | `PASS` when true; otherwise `FAIL` |
| CTA appears once in the blueprint | `PASS` when the CTA block is the only CTA; otherwise `FAIL` |

Required output: a Pre-send checklist table with columns `Check | Status | Note`.

**Step 7. Open items.** List every `FAIL` and `USER-CONFIRM` row as a numbered line. If there are none, write `None`.

## Output contract

The plan has exactly these top-level headings, in this order:

```
## Issue plan
### Intake
### Angle
### Blueprint
### Subject lines
### Link and image audit
### Pre-send checklist
### Open items
```

Each heading holds the table or list named in its step. Do not add other headings. Put `[SOURCE NEEDED]` in place of any figure, quote, or date the user did not supply.

## Refuse or stop when

- Audience, goal, or CTA is missing. Ask for it once and stop.
- Fewer than three source items are supplied, or an item has no fact stated by the user.
- The user asks for statistics, quotes, prices, testimonials, or dates that they did not supply. Refuse to invent them; mark them `[SOURCE NEEDED]`.
- The request is a multi-issue sequence, drip campaign, or automation setup. State that this skill plans one issue.
- The user asks for the full issue body. Deliver the plan only and say that the body is out of scope.

## Working rules

- Use only facts the user supplied. Do not add background, statistics, or quotes from memory.
- Every budget and character limit in this file is a working value chosen for this skill. Do not describe any of them as an industry standard.
- Keep the plan in the order the output contract lists it.

The package is licensed under Apache-2.0; see [LICENSE.txt](LICENSE.txt).
