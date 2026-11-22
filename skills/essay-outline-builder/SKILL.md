---
name: essay-outline-builder
description: Builds a thesis-first essay outline from a writing prompt, a target word count and the writer's own points. Use when a student or writer needs a section plan with exact word budgets, a four-part thesis test and a check that each body section rests on evidence the writer supplied. Do not use for writing essay text, inventing sources or quotes, grading a finished essay, or judging whether a text was written by AI.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Essay Outline Builder

This skill plans an essay. It does not draft one. The writer supplies the position and the points; the skill turns them into a thesis test, a section plan, a word budget and an evidence check.

Shipped files: `SKILL.md` (this file) and `LICENSE.txt` (Apache-2.0 license text). No scripts are shipped.

## Intake (required facts)

Four facts are needed before any work starts.

| Fact | Accepted value |
|---|---|
| Prompt | The assignment or question, one to three sentences |
| Target length | Whole number of words, 300 to 3000 (working value) |
| Writer points | 3 to 5 points, each a claim in the writer's own words |
| Thesis position | The writer's stance on the prompt, in the writer's words |

Each writer point may also carry an evidence item (an example, observation or quotation the writer supplies) and a counterpoint. Both are optional. Missing evidence is flagged, not filled in.

## Workflow

1. Check intake. Output: the four facts as a checklist with OK or MISSING beside each. Any MISSING or out-of-range fact stops the run (see Stop rules).
2. Restate the prompt in one line. Add no new claims. Output: the Prompt line.
3. Run the thesis test on the writer's position. Output: one thesis sentence and the four test results (arguable, specific, answers the prompt, one sentence with 8 to 35 words). If a test fails, write up to two alternative theses that reuse only the writer's words. If neither alternative passes all four tests, stop with BLOCKED and ask for a position.
4. Map points to body sections. One writer point per body section, in the writer's order. Output: a list named Body 1 through Body N, where N is the number of points.
5. Compute word budgets with the rules below. Output: a Words value for every row. The sum must equal the target before you continue.
6. Check evidence for each body section. Output: a Flag of OK or EVIDENCE-NEEDED.
7. Assemble the output contract below. Output: the final result with its Status.

## Decision and threshold table

| Rule | Value | Action when broken |
|---|---|---|
| Target length | 300 to 3000 words (working value) | BLOCKED; ask for the length |
| Writer points | 3 to 5 | Fewer than 3: BLOCKED. More than 5: ask the writer to choose 5 |
| Thesis sentence | One sentence, 8 to 35 words (working value) | Two alternatives, then BLOCKED |
| Introduction words | 10 percent of target, rounded to the nearest whole word (working value) | None |
| Conclusion words | 10 percent of target, rounded to the nearest whole word (working value) | None |
| Body words per section | (Target minus Introduction minus Conclusion), divided by the number of body sections, rounded down; the last body section takes the remainder | None |
| Evidence present | Writer point names a specific example, observation or quotation the writer supplied | Flag EVIDENCE-NEEDED |
| Claim cell length | 25 words or fewer | Shorten the claim |
| Status READY | Thesis passes and no EVIDENCE-NEEDED flags | Not applicable |
| Status PARTIAL | Thesis passes and one or more EVIDENCE-NEEDED flags | Not applicable |

Worked check for a target of 800 with three writer points: Introduction 80, Conclusion 80, body total 640, so 640 divided by 3 is 213 with remainder 1; Body 1 gets 213, Body 2 gets 213, Body 3 gets 214. Sum 80 + 213 + 213 + 214 + 80 = 800.

## Output contract

When Status is READY or PARTIAL, the output has exactly five headings, in this order:

```
## Prompt
<one line>

## Thesis
<one thesis sentence>
Tests: arguable <PASS|FAIL>; specific <PASS|FAIL>; answers prompt <PASS|FAIL>; one sentence <PASS|FAIL> (<n> words)

## Outline
| Section | Words | Claim | Evidence (writer point) | Counterpoint | Flag |
|---|---|---|---|---|---|
| Introduction | <n> | <claim> | n/a | n/a | OK |
| Body 1 | <n> | <claim> | <evidence or EVIDENCE-NEEDED> | <writer counterpoint or NONE GIVEN> | OK or EVIDENCE-NEEDED |
| ... one row per body section ... |
| Conclusion | <n> | <claim> | n/a | n/a | OK |

## Budget check
Target <T>. Sum <S>. Result PASS or FAIL.

## Status
READY or PARTIAL
```

When Status is BLOCKED, the output has exactly three headings: Prompt, Questions, Status. Under Questions, list at most five numbered questions, one for each MISSING or out-of-range fact. Status is BLOCKED.

## Refuse or stop when

- The request asks for essay paragraphs, a full draft, or finished prose. Offer the outline only.
- The request asks for sources, citations, statistics, study names, URLs or quotations the writer did not supply. Refuse, and flag the section EVIDENCE-NEEDED.
- The request asks the skill to pick evidence from memory or from the web.
- The request asks for a grade, a plagiarism check, or a judgment on whether the writer used AI.
- Any intake fact is MISSING or out of range. Do not guess a length or a point. Stop and return BLOCKED with numbered questions.
- Fewer than 3 writer points, or a thesis that fails both alternatives. Return BLOCKED.
- More than 5 writer points. Ask the writer to choose 5 before any budget is computed.
