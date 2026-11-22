---
name: product-description-writer
description: Writes an 80 to 120 word product description from a supplied spec sheet, tying each benefit line to a given fact and marking missing facts TO-CONFIRM. Use when a store owner needs a product page description for a physical good such as a mug, bag, or candle and the sheet gives the name, materials, dimensions, care instructions, and box contents. Use when every claim must stay within the supplied specs. Do not use for ad copy with performance or health claims, for invented certifications or reviews, for services or digital goods, or for supplement and medical product text.
license: Apache-2.0
compatibility: Requires nothing beyond a text-capable agent (type B), with no network access and no scripts.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Product Description Writer

Writes one product description from a supplied spec sheet. Every claim must trace to a given fact. Missing facts are marked TO-CONFIRM and never filled in.

## Workflow

1. **Intake check.** Read the spec sheet and look for five required facts: F1 name, F2 materials, F3 dimensions (each value with a unit), F4 care instructions, F5 box contents. Mark each fact "given" or "missing". Output: the five-row fact table.
2. **Apply the decision table** below to pick a status. If the status is `needs-facts`, stop and output the question list under Output contract. Do not write a description.
3. **Map the benefits.** Write exactly three benefit lines. Each line restates one given fact in buyer terms (for example, "Holds 12 oz (355 ml) of liquid" from F3). Output: the benefit map. Delete any line that has no fact ID.
4. **Draft the description** in this order: product name and material in the first sentence, dimensions, the benefit lines, care, box contents. Use one paragraph. A missing F4 or F5 is written as `[TO-CONFIRM: care]` or `[TO-CONFIRM: box contents]` at the spot where the fact belongs.
5. **Scan the draft** against the banned-claim table. Replace each hit with its fix rule and count the hits. Output: the count, in Checks.
6. **Count the words** in the description, excluding the TO-CONFIRM tags. If the count is below 80, state the count and mark Words SHORT; do not repeat facts or add filler. List the missing facts in Checks. If above 120, delete the least specific sentence. Repeat the above check at most two times. If the count is still above 120, set Words to FAIL and return the draft.

## Decision table

| Condition | Status | Action |
|---|---|---|
| F1, F2, or F3 is missing | needs-facts | Stop. Output the question list. No description. |
| Two values for the same fact conflict | needs-facts | Stop. Ask which value is correct. No description. |
| F1, F2, and F3 given; F4 or F5 missing | partial | Write the description with one or two TO-CONFIRM tags. |
| F1 to F5 all given | complete | Write the description. Zero TO-CONFIRM tags. |
| Description word count | pass | 80 to 120 words (working value) |
| Benefit lines | pass | Exactly 3 (working value), each with a fact ID |

## Banned-claim table

| Banned term or pattern | Fix rule |
|---|---|
| best, best-in-class, number one, top-rated | Delete. Replace with the fact it was standing in for. |
| guaranteed, lifetime, forever, warranty | Delete unless the sheet gives the exact warranty terms; then quote those terms. |
| eco-friendly, sustainable, green, non-toxic, recyclable | Delete unless the sheet gives a certification fact; otherwise name the material only. |
| medical, heals, cures, relieves, therapeutic, clinically proven | Delete. If the product is medical, stop and refuse. |
| dishwasher safe, microwave safe, oven safe | Keep only if F4 states it; otherwise replace with `[TO-CONFIRM: dishwasher or microwave use]`. |
| 5-star, rated, customers love, award-winning | Delete. The sheet holds no review or award data. |
| unbreakable, indestructible, waterproof, leak-proof | Delete unless the sheet gives a test result; otherwise state the material. |
| handmade, made in (country), artisan | Delete unless the sheet gives the production fact. |

## Output contract

Status complete, partial, or needs-facts, as the first heading. Then:

```
## Status
complete | partial | needs-facts

## Facts
| ID | Fact | Value | Source |
|---|---|---|---|
| F1 | Name | <value or blank> | given or missing |
| F2 | Materials | <value or blank> | given or missing |
| F3 | Dimensions | <value with unit or blank> | given or missing |
| F4 | Care | <value or blank> | given or missing |
| F5 | Box contents | <value or blank> | given or missing |

## Description
<one paragraph, 80 to 120 words, or shorter with Words SHORT in Checks when the facts run out (Step 6); TO-CONFIRM tags allowed when status is partial>

## Benefit map
| Benefit line | Fact ID |
|---|---|
| <line 1> | <F1 to F5> |
| <line 2> | <F1 to F5> |
| <line 3> | <F1 to F5> |

## Checks
- Words: <count, with SHORT or FAIL if outside 80 to 120>
- Banned-claim hits replaced: <count>
- TO-CONFIRM tags: <count>
- Missing facts: <fact IDs and names, or none>
- Facts needed for requested claims: <sheet item that would allow each banned claim the user asked for, or none>
```

For `needs-facts`, output only `## Status` followed by `needs-facts`, then `## Questions` with one numbered question per missing or conflicting fact. Each question names the fact ID and asks for the value.

## Refuse / stop when

- The request asks for specs, certifications, awards, reviews, origin, or test results that the spec sheet does not contain. Write only from the sheet.
- The request asks for health, medical, or supplement claims. Refuse.
- F1, F2, or F3 is missing, or two values for one fact conflict. Stop with `needs-facts`.
- The product is a service or a digital good. Stop and say the skill covers physical goods only.
- The request asks for a comparison with a named competitor.
- The request asks for a banned claim (for example, "eco-friendly" or "waterproof"). Keep it out of the description and name in Checks the sheet item that would be needed to allow it.
- The sheet gives no product name at all, even after the user is asked for it once.

## Shipped files

- `SKILL.md` (this file): the workflow, decision table, and output contract.
- `LICENSE.txt`: the Apache-2.0 license text.
