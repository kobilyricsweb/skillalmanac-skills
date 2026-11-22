---
name: self-assessment-writer
description: Writes a performance self-assessment from the employee's own accomplishments. Use when an employee must draft a year-end or mid-year self-review from a list of work done. Output is grouped by goal, with each accomplishment as a situation-action-result paragraph of at most 45 words, plus a growth area and a next-period goal. Do not use for manager reviews of other people, rating or ranking staff, or adding results that were not supplied.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Self-assessment writer

Shipped files: this SKILL.md and [LICENSE.txt](LICENSE.txt). No scripts.

## Workflow

1. **Intake.** Collect the review period (start and end dates), 5 to 8 accomplishments, and optionally a goal list and any result numbers. Output: intake record with period, goal list (or "none"), accomplishment count, and count of results supplied with a number.
2. **Check the decision table** below before writing anything. A stop condition ends the run here with a numbered question list.
3. **Validate each accomplishment.** It needs a month, an action the employee took (not only what the team did), and an outcome in words. Output: accepted list with a month label, and rejected items with the reason.
4. **Group by goal.** Use the supplied goal list in its order. If none is supplied, group by theme and name each group from its content. Maximum 3 groups (working value). Output: group map.
5. **Write each accomplishment** as one paragraph in situation, action, result order, at most 45 words (working value). Apply the result rules below. Output: paragraphs, each checked against 45 words.
6. **Write the Summary**, 40 to 60 words (working value). It states the accomplishment count and how many carry a supplied number. Output: summary paragraph.
7. **Write the Growth area**, 50 to 90 words (working value). Name one real gap that the input shows, such as work done alone or a skill no accomplishment demonstrates. A strength written as a weakness is a failure. Output: one paragraph.
8. **Write the Next-period goal**, 30 to 70 words (working value). One goal, one measurable check, one date. Output: one paragraph.
9. **Count and fit.** Count words in Summary through Next-period goal, excluding headings and the status line. Target 350 to 500 words (working value). If under 350, lengthen the Summary and Growth area first, never an accomplishment past 45 words. If over 500, shorten the Growth area, then the Summary. Output: total word count.

## Intake fields

| Field | Required | Rule |
|---|---|---|
| Period start and end | yes | Dates as Month D, YYYY. Missing either one is a stop. |
| Accomplishments | yes | 5 to 8 items. Each has a month, one action, and one outcome. |
| Goal list | no | Ordered. If absent, group by theme. |
| Result number | no | Only as supplied, with its unit. |
| Employee name | no | Not written into the draft. Used only to address questions. |
| Colleague names | no | Named only as people the employee worked with. Never assessed. |
| Other people's personal data | no | Not written into the draft. See the refusal list. |

## Decision table

| Condition | Action | Status |
|---|---|---|
| Period start or end date missing | Stop. Return a numbered question list. | partial |
| Fewer than 5 accomplishments | Stop. Ask for more, using the three prompts: what changed, who it helped, what was measured. | partial |
| More than 8 accomplishments | Stop. Ask the user to choose 8. Do not drop items silently. | partial |
| 5 to 8 accomplishments with dates | Draft the self-assessment. | complete |
| Request to state a number that was not supplied, or to describe a named colleague negatively | Write no draft. Explain the limit in one sentence. | refused |

## Result rules

| Input | Written as |
|---|---|
| Number supplied with its unit | The exact number and unit as supplied, for example "from 14% to 6%". |
| Outcome described, no number | Plain outcome words with no digits and no scale words such as "most" or "half". |
| Number implied but not supplied | Do not add it. Use plain outcome words. |

Team results count only as the employee's part: "as part of the team, I ..." Never credit a colleague's work to the employee.

Counts of the employee's own items (accomplishments, goals) may be spelled out; counts of people or events not in the input may not.

## Banned words (working list)

passionate, synergy, results-driven, go-getter, rockstar, leveraged, best-in-class, "responsible for". Replace each with the plain verb for what the employee did.

## Output contract

The reply starts with one status line: `Status: complete`, `Status: partial`, or `Status: refused`.

For `complete`, the reply has exactly these headings, in this order:

- `# Self-assessment: <Month D, YYYY> to <Month D, YYYY>`
- `## Summary`
- `## Goal: <goal name>`, one heading per group, in group order. Each accomplishment is one paragraph with no bullets and no labels.
- `## Growth area`
- `## Next-period goal`

No tables and no other headings appear in a complete reply.

For `partial`, the reply has the status line, then `## Questions`, then a numbered list of 1 to 5 questions. No draft.

For `refused`, the reply has the status line, then one sentence giving the reason and what the user can supply instead.

## Final check before the reply

1. Every accomplishment paragraph is 45 words or fewer.
2. The draft counts 350 to 500 words, excluding headings and the status line.
3. Every result number in the draft appears in the input, with the same unit. Dates in the period heading and the next-period goal are the only other numbers allowed.
4. No word from the banned list appears.
5. The headings match the output contract for the status value.

## Refuse or stop when

- The input asks for a figure, percentage, or currency amount that the user did not supply.
- The input asks for a claim about a named colleague's shortcomings, or asks to take credit for a colleague's work.
- The request is a manager review, a rating, or a ranking of staff.
- The input includes another person's salary, medical, or disciplinary details. Leave them out of the draft and do not repeat them in the reply.
- The user declines to add the period dates. Keep the partial status and repeat the question.
