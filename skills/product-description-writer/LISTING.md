# Product Description Writer

## One line

Turns a physical product's spec sheet into an 80 to 120 word description in which every benefit line points back to a given fact. When the supplied facts cannot reach 80 words, it returns a shorter description marked SHORT with a missing-facts list, rather than padding.

## What it does

The skill takes a spec sheet for one physical good and checks it for five facts: the product name, the materials, the dimensions with units, the care instructions, and the box contents. It records each fact as given or missing in a fact table. If the name, materials, or dimensions are missing, or if two values for one fact disagree, it stops and returns a numbered list of questions instead of a description. If only the care instructions or box contents are missing, it writes the description and marks each gap with a TO-CONFIRM tag at the place the fact belongs.

The description is one paragraph. It opens with the product name and material, then states the dimensions, three benefit lines, the care method, and the box contents. Each benefit line is listed in a benefit map next to the fact ID it restates. A banned-claim table catches words such as best, guaranteed, eco-friendly, and medical terms, and gives a fix rule for each one. The output ends with a Checks block that reports the word count, the number of banned-claim replacements, and the number of TO-CONFIRM tags.

## When to use

Use it when a store owner has a spec sheet for a mug, bag, candle, or similar physical product and needs a product page description that does not go beyond the sheet. It fits the case where the owner has the facts but no time to write copy that stays inside them.

## When not to use

Do not use it for ad copy that promises performance, health effects, or results. Do not use it for supplements, medical devices, or any text that makes a clinical claim. It cannot add certifications, awards, reviews, origin statements, or test results that the sheet does not contain. Services and digital goods are outside its scope.

## Requirements

A text-capable agent. No network access, no scripts, and no files beyond the spec sheet pasted into the conversation.

## Example

Input spec sheet, pasted as text: name "Glazed Stoneware Mug"; materials "stoneware body, glossy glaze"; dimensions "12 oz (355 ml) capacity, 4.2 in (10.7 cm) tall, 3.3 in (8.4 cm) diameter"; care "hand wash"; box contents not stated.

Output:

## Status
partial

## Facts
| ID | Fact | Value | Source |
|---|---|---|---|
| F1 | Name | Glazed Stoneware Mug | given |
| F2 | Materials | Stoneware body, glossy glaze | given |
| F3 | Dimensions | 12 oz (355 ml) capacity; 4.2 in (10.7 cm) tall; 3.3 in (8.4 cm) diameter | given |
| F4 | Care | Hand wash | given |
| F5 | Box contents | | missing |

## Description
Glazed Stoneware Mug has a stoneware body and a glossy glaze. It holds 12 oz (355 ml) of liquid. It stands 4.2 in (10.7 cm) tall with a 3.3 in (8.4 cm) diameter. Care: hand wash. Box contents: [TO-CONFIRM: box contents].

## Benefit map
| Benefit line | Fact ID |
|---|---|
| Holds 12 oz (355 ml) of liquid. | F3 |
| Stands 4.2 in (10.7 cm) tall with a 3.3 in (8.4 cm) diameter. | F3 |
| A stoneware body with a glossy glaze. | F2 |

## Checks
- Words: 38 (SHORT, below 80: the supplied facts cannot reach 80 without repeating facts, so none were added)
- Banned-claim hits replaced: 0
- TO-CONFIRM tags: 1
- Missing facts: F5 box contents
- Facts needed for requested claims: none

## Limits

The skill cannot check whether a fact on the sheet is true. It repeats what the sheet says and flags what the sheet leaves out. It does not measure the product, test the glaze, or confirm care instructions with a manufacturer. The word range of 80 to 120 and the three-line benefit rule are working values chosen for this skill, not a published standard. The banned-claim table covers common overclaims only and is not a legal review of advertising rules in any market.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
