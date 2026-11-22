---
name: rubric-feedback-writer
description: Writes criterion-by-criterion feedback on one student answer from a supplied rubric. Parses the rubric into criteria and point levels, quotes the answer for each criterion, assigns a level only from the rubric wording, gives one strength and one next step per criterion, and computes the total. Use when a teacher has a rubric and a student answer and needs consistent per-criterion comments, a scored breakdown, or a points total. Do not use for a final course grade, grading without a rubric, writing or changing rubrics, or judging whether AI wrote an answer.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Rubric Feedback Writer

Type B skill. Works only from the text the teacher supplies. No script, no network.

Smoke inputs shipped with this skill: [fixtures/rubric.txt](fixtures/rubric.txt) (four criteria, four levels each) and [fixtures/answer.txt](fixtures/answer.txt) (120 words).

## Input format

Rubric, one block per criterion:

```
Criterion 1: NAME (max M)
Label (points): descriptor
Label (points): descriptor
```

Levels run from highest points to lowest. Points are whole numbers from 0 to 10 (working value). The answer is one block of plain text.

## Workflow

1. Intake check. Confirm the rubric has 2 to 10 criteria (working value), each with 2 or more levels, and the answer is present. Output: the intake result, which decides between the blocked output and steps 2 to 7. Apply the decision table below before any other step.
2. Parse the rubric. Output one row per criterion: number, name, highest level points as Max. Total max is the sum of all Max values. The stated (max M) must equal the highest level points; if not, stop.
3. Quote. For each criterion, copy one contiguous passage from the answer that addresses it, character for character, 5 to 40 words. Output: the quote, or "none" if nothing in the answer addresses the criterion.
4. Assign a level. Start at the highest level and move down. Choose the first level whose every element (the items named in its descriptor) appears in the quote or elsewhere in the answer. Output: the level label and its points. Do not use wording the rubric does not contain. An element counts as present only if the answer states it in terms the descriptor names. A partly stated element counts as absent; say which part is missing in the Next step.
5. Write strength and next step. Strength: one sentence, 25 words or fewer, that cites part of the quote. Next step: one sentence, 25 words or fewer, that names the missing element of the next level up. At the top level, name one specific extension instead. An extension at the top level must come from the rubric or the answer, not from outside knowledge.
6. Total. Sum the points of all judged criteria. Output: "X / Y" where Y is total max. If any criterion is not judged, add "(Z criteria not judged)" and set status to partial.
7. Self-check. Re-add the points column and compare with the total. Confirm each quote is a verbatim substring of the answer and each label matches the rubric. On a mismatch, correct the row and repeat this check once. A second mismatch is a stop condition.

## Decision table

| Situation | Action | Status | Flag code |
|---|---|---|---|
| Fewer than 2 criteria, or more than 10 | Stop, return the question list | blocked | none |
| A criterion has fewer than 2 levels, or points are not whole numbers from 0 to 10 (working value), or levels are not in descending order | Stop, return the question list | blocked | none |
| (max M) does not equal the highest level points | Stop, return the question list | blocked | none |
| Answer missing, or under 20 words | Stop, return the question list | blocked | MISSING_INPUT |
| Answer over 1,500 words (working value) | Stop, ask the teacher which part to score | blocked | none |
| Answer of 20 to 39 words | Continue | complete or partial | SHORT_ANSWER |
| No passage addresses a criterion | Do not assign a level | partial | NOT_JUDGEABLE |
| Quote under 5 words (working value) | Do not assign a level | partial | SHORT_QUOTE |
| Two levels are equally supported by the answer | Choose the lower level | complete or partial | LEVEL_TIE |

Status values: complete (every criterion judged), partial (one or more criteria not judged), blocked (no scores given). Flag codes are listed in the output contract.

## Output contract

Blocked case:

```
## Status
Status: blocked
Reason: one sentence

## Questions
1. First missing fact, as a question
2. Second missing fact, as a question

## Flags
- FLAG_CODE: one sentence, or none
```

Scored case, in this order and with these headings:

```
## Status
Status: complete | partial
Reason: one sentence

## Criteria
| # | Criterion | Level | Points | Max | Quote | Strength | Next step |
|---|---|---|---|---|---|---|---|

## Total
X / Y

## Flags
- FLAG_CODE: criterion number or answer: one sentence
```

Flag codes allowed: MISSING_INPUT, SHORT_ANSWER, NOT_JUDGEABLE, SHORT_QUOTE, LEVEL_TIE. Write "none" under Flags when no code applies.

## Refuse or stop when

- No rubric is supplied, or the "rubric" is one overall instruction with no criteria.
- The teacher asks for a final course grade, a letter grade, a pass or fail for the course, or a GPA value. Give the criterion points only and say the teacher sets the course grade.
- The teacher asks you to write, change, or invent criteria or levels.
- The teacher asks you to score a criterion the rubric does not contain.
- The teacher asks whether the student or an AI wrote the answer. Say this skill does not make that judgment.
- The input includes a student ID, date of birth, or similar personal data. Leave it out of the output and use the teacher's own label for the answer.
- Any of the blocked rows in the decision table apply.

## Notes for the agent

- Quote text exactly, including spelling errors. Never correct the student's wording inside a quote.
- Level labels and points come only from the rubric. Do not add a level, change a point value, or rename a label.
- Do not carry a level from one criterion to another.
