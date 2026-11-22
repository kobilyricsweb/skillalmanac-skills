# Rubric Feedback Writer

## One line

Turns one rubric and one student answer into a criterion-by-criterion table with verbatim quotes, levels, a computed points total, and a short strength and next step for each criterion.

## What it does

The skill reads a rubric as a list of criteria, each with named performance levels and whole-number points. It then searches the student answer for the passage that addresses each criterion and copies that passage exactly, including spelling errors. A level is assigned by starting at the top of the rubric and moving down until every element named in a level's wording is present somewhere in the answer. The skill does not invent wording the rubric lacks, so a teacher can trace every level back to a line in the rubric and a sentence in the answer.

Each criterion receives one strength, one next step, and a points value. The next step names the element that the next level up requires, so the student can see what is missing. The total is the sum of the points column, written as a fraction of the total possible. Criteria the answer does not address are marked as not judged, not scored zero, and the total is then labelled partial.

## When to use

Use it when a teacher has a rubric, has one answer open, and wants comments that match the rubric's own language. It suits short written responses of roughly 20 to 1,500 words, where each criterion can be found in one passage. Teachers who write the same per-criterion comment many times for a class can use the output as a first draft and edit it.

## When not to use

Do not use it to assign a course grade, a letter grade, or a pass or fail decision. It does not write rubrics, does not decide which criteria matter, and does not judge whether a student or an AI model wrote the answer. It does not handle multiple answers in one run, because the table is built for one student at a time.

## Requirements

A text-capable agent. No script, no network access, and no installed packages. The rubric must have 2 to 10 criteria, each with 2 or more levels, and the answer must be at least 20 words.

## Example

Input: the four-criterion rubric and the 120-word answer on photosynthesis shipped in the fixtures folder. Output from one run, pasted unchanged:

```
## Status
Status: complete
Reason: All four criteria were judged from passages in the answer.

## Criteria
| # | Criterion | Level | Points | Max | Quote | Strength | Next step |
|---|---|---|---|---|---|---|---|
| 1 | Light-dependent reactions | Proficient | 3 | 4 | "light energy splits water molecules, releasing oxygen as a byproduct, and the process produces ATP and NADPH" | Correctly states that light splits water, releases oxygen, and produces ATP and NADPH. | Name water as the source of electrons, not only the molecule that is split. |
| 2 | Calvin cycle | Exemplary | 4 | 4 | "The Calvin cycle then uses these molecules to fix carbon dioxide into sugar, with the enzyme RuBisCO catalyzing the first step" | Explains that the Calvin cycle fixes carbon dioxide into sugar and names RuBisCO. | Keep this level; extend it by naming ATP and NADPH in the cycle sentence, in place of these molecules. |
| 3 | Role of chlorophyll | Exemplary | 4 | 4 | "chlorophyll in the thylakoid membranes absorbs light, mostly red and blue wavelengths, while green light is reflected" | Gives the pigment's absorption pattern and its location in the thylakoid membranes. | Keep this level; extend it by linking the absorbed light to the light-dependent reactions named in criterion 1. |
| 4 | Ecosystem significance | Proficient | 3 | 4 | "the oxygen supports animal respiration, and the sugars made by plants start nearly every food chain" | Links photosynthesis to both the oxygen supply and the food chain. | Add one concrete example, such as a forest or ocean ecosystem, to reach the top level. |

## Total
14 / 16

## Flags
- none
```

## Limits

The skill works from the text it is given and does not check facts beyond the rubric's own wording. Level choices depend on how literally the rubric is written; loosely worded descriptors leave more room for disagreement. Quotes are limited to 5 to 40 words, so a criterion that is addressed across several separated sentences may be assigned a lower level than a teacher would give. The 10-criterion and 1,500-word limits are working values, not published limits. Output is text only, so the teacher must paste results into a gradebook.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
