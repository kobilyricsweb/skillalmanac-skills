---
name: landing-page-wireframe-brief
description: Writes a section-by-section wireframe brief for one landing page, covering the goal, one primary action, six ordered sections with purpose, content, word budget and element type, mobile order notes, and a TO-SUPPLY list of missing content. Use when a landing page must be planned before design starts, when a service or product page has no content plan, or when a designer needs section order and placeholders for proof. Do not use for writing final marketing copy, designing visuals, building the page in code, or inventing testimonials, numbers or logos.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Landing page wireframe brief

This skill turns a short intake into a content plan for one landing page. The output tells a designer what each section must do, what content it needs, how many words it may use and how it stacks on a phone. It contains no final copy and no invented proof.

License text: [LICENSE.txt](LICENSE.txt).

## Intake

Required fields. If any one is missing, stop (see the stop rule below).

- Offer: what is sold, in one sentence.
- Audience: who it is for, in one sentence.
- Primary action: exactly one action as a verb phrase, for example "Book a free trial lesson".
- Benefits: three or more, each in the user's own words.

Optional fields. A missing optional item becomes a TO-SUPPLY row; it never stops the work.

- Proof items: reviews, customer counts, logos, awards or press names, each with its source and date.
- FAQ facts: price, lesson or session length, cancellation or refund terms, location, schedule, and similar facts.
- Brand name.

## Workflow

1. Check intake. Output: the "Intake check" table with Present or Missing for each required field and the count of benefits. If any required field is Missing, set Status to blocked and follow the stop rule.
2. Set the goal and primary action. Output: the "Goal and primary action" lines. The goal is one sentence that starts with "Visitors leave having". The primary action is the single action from intake. It appears as a button in Hero and Final call only. Any other action is a text link.
3. Order the six sections in this fixed order: Hero, Proof, Benefits, How it works, FAQ, Final call. Do not add, drop or reorder a section. Output: six rows in the "Section order" table.
4. Fill "Content needed" from intake only. Benefits are used exactly as written, one card each. Anything that intake does not supply goes to TO-SUPPLY. Output: one content list per row.
5. Set "Element type" and "Word budget" from the budget table below. Output: both cells in each row.
6. Write "Mobile note" from the mobile table below. Output: one note per row.
7. Build the TO-SUPPLY table. Give one row per missing item, numbered TS-01 upward in section order. Output: the table, or the word "None." when empty.
8. Set Status. complete means the TO-SUPPLY table is empty. partial means one or more TO-SUPPLY rows exist and a brief was produced. blocked means no brief was produced.

## Decision and threshold table

| Check | Threshold (working value) | Result when not met |
|---|---|---|
| Required intake fields | 4 of 4 Present | blocked, with one question per missing field |
| Primary actions named | exactly 1 | blocked, asking which action is primary |
| Benefits supplied | 3 or 4 | fewer than 3: blocked; 3: three cards only; 4: four cards |
| Proof items supplied | 0 to 6 real items | 0 items: one TO-SUPPLY row per missing proof type (reviews; customer count or result; logos), with no placeholders |
| FAQ questions with answers | 4 to 6 rows | the 4 default questions each keep a row; a default question with no supplied answer becomes one TO-SUPPLY row |
| How it works steps supplied | 3 | any step not supplied becomes a TO-SUPPLY row |

FAQ question set. The default questions, in this order, are: price; lesson length or duration; cancellation or refund terms; schedule or location. A fifth or sixth question is added only when the intake supplies a fact for another topic. The FAQ has fewer than four rows only when the user removes a default topic. Never invent a question or an answer.

## Word budget and element table

| Section | Word budget, total (working value) | Element type |
|---|---|---|
| Hero | 40 | headline of 6 to 12 words, subhead, primary button, one image slot |
| Proof | 30 | logo row or quote cards, real items only |
| Benefits | 100 | three or four cards, each with an icon slot, a heading and one line |
| How it works | 60 | three numbered steps |
| FAQ | 250 | accordion with 4 to 6 questions |
| Final call | 30 | headline and primary button |

## Mobile order table

| Rule | Value (working value) |
|---|---|
| Layout below 768 px | one column |
| Benefit cards | same order as desktop, stacked |
| Proof logos | grid of two per row |
| Hero button | placed directly below the subhead, above the image slot |
| Final call button | directly below the headline |
| How it works steps | stacked vertically, numbered |
| FAQ | accordion, all questions collapsed on load |
| Touch target height | at least 44 px |

## Output contract

A complete brief uses exactly these headings, in this order.

    # Wireframe brief: <offer name>

    Status: complete | partial | blocked

    ## Goal and primary action
    Goal: <one sentence starting with "Visitors leave having">
    Primary action: <one verb phrase>

    ## Intake check
    | Field | Status |
    |---|---|
    | Offer | Present or Missing |
    | Audience | Present or Missing |
    | Primary action | Present or Missing |
    | Benefits | Present (count) or Missing |

    ## Section order
    | # | Section | Purpose | Content needed | Element type | Word budget | Mobile note |
    |---|---|---|---|---|---|---|
    (six rows, Hero through Final call)

    ## TO-SUPPLY
    | ID | Section | Item needed | Why it blocks the page |
    |---|---|---|---|
    (TS-01 upward, or the word None.)

A blocked result uses only the title, the Status line, the Intake check table and this heading:

    ## Questions
    1. <one question per missing required field, in intake order>

## Refuse or stop when

1. A required intake field is missing. Set Status to blocked, produce the Questions list, and produce no section table.
2. Two or more primary actions are named and the user does not rank them. Set Status to blocked and ask which one is primary.
3. The user asks for testimonials, quotes, star ratings, customer or user counts, percentages, logos, awards or press names that were not supplied. Write a TO-SUPPLY row. Never write a placeholder that looks like a real item.
4. The user asks for a benefit that is not in intake. Do not add it. Ask whether to include it, and leave it out until the user confirms.
5. The user asks for final marketing copy, visual design, page code, or a plan for many pages. Say that this skill covers one page's brief only, and stop.
