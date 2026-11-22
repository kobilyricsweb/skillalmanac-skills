# Notes to Prose Paragraph

## One line

Turns bulleted notes into one to three prose paragraphs and returns a coverage table that maps every bullet to its sentence.

## What it does

The procedure takes a short list of notes, such as eight bullets about a product launch, and rewrites them as connected paragraphs. Each bullet is numbered first, so nothing can disappear silently. The paragraph count follows a fixed threshold table, and every paragraph is capped at five sentences. Connectors are limited to a short allowed list that adds no cause, conclusion, or judgment. A forbidden word such as "therefore" or "significant" may appear only when the note itself contains it.

The output is a Status line, the paragraphs, a Coverage table with one row per numbered item, an Unplaced section, and an Open questions list. A bullet that cannot become a sentence without inventing a fact is marked UNPLACED with a reason, and the status drops to partial. A request to add a cause or a judgment is refused for that clause only, and the rest of the paragraphs are still delivered.

## When to use

Use it when notes read as fragments and a reader needs paragraph form: a launch summary, a meeting recap, or a project update drafted from bullets. It fits best when the notes already contain every fact and the work is only arrangement and wording.

## When not to use

Do not use it to draft prose from a topic with no notes, because the procedure stops when fewer than two items are supplied. Do not use it to summarize a long document, since it expects discrete claims and has a ceiling of twelve numbered items. Do not use it to edit a paragraph that is already written. It also does not check whether the notes are true or consistent with each other.

## Requirements

A text-capable agent that can follow a numbered procedure and produce markdown tables. No script, no network access, and no files beyond the notes and the skill folder.

## Example

Input notes, eight items, subject "Harbor Lamp launch":

1. Launch date is March 4.
2. Pre-orders opened January 12 and sold 6,200 units in the first week.
3. Price is $89 for the base model and $119 for the model with the dimmable charging base.
4. Ships in three finishes: oak, graphite, and sand.
5. Battery lasts about 10 hours on a single charge.
6. Available at 40 retail partners and on the company website.
7. Support hours extended to 8 a.m. through 8 p.m. Eastern during launch month.
8. Next product review is scheduled for June.

Numbering after step 2: bullet 1 is N1; bullet 2 is N2a (pre-orders opened January 12) and N2b (6,200 units sold in the first week); bullet 3 is N3a (base price) and N3b (dimmable-base price); bullets 4 to 6 are N4 to N6; bullet 7 is N7a (support hours) and N7b (launch-month window); bullet 8 is N8. That makes 11 numbered items, the 10-to-12 row, so 3 paragraphs.

Output:

```
Status: complete
Subject: Harbor Lamp launch

## Paragraphs
P1. The Harbor Lamp launches on March 4. Pre-orders opened on January 12 and sold 6,200 units in the first week.
P2. The base model costs $89, and the version with a dimmable charging base costs $119. It ships in three finishes: oak, graphite, and sand. Battery life is about 10 hours on a single charge.
P3. The lamp is available at 40 retail partners and on the company website. Separately, support hours extend from 8 a.m. to 8 p.m. Eastern during launch month. Finally, the next product review is scheduled for June.

## Coverage
| Item | Paragraph | Sentence | Placement |
|---|---|---|---|
| N1 | P1 | 1.1 | PLACED |
| N2a | P1 | 1.2 | PLACED |
| N2b | P1 | 1.2 | PLACED |
| N3a | P2 | 2.1 | PLACED |
| N3b | P2 | 2.1 | PLACED |
| N4 | P2 | 2.2 | PLACED |
| N5 | P2 | 2.3 | PLACED |
| N6 | P3 | 3.1 | PLACED |
| N7a | P3 | 3.2 | PLACED |
| N7b | P3 | 3.2 | PLACED |
| N8 | P3 | 3.3 | PLACED |

## Unplaced
None

## Open questions
None
```

## Limits

The procedure copies numbers, names, dates, and prices exactly as the notes write them, but it does not verify them against any source. It does not check whether two notes conflict, grammar beyond sentence level, tone, or formatting inside the paragraphs. It adds nothing from outside the notes, so a reader may find the result terse. The threshold table and the connector list are working values chosen by the author, not a published style standard.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
