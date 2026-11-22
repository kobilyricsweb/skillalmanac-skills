# Essay Outline Builder

## One line

Turns a writing prompt, a word target and three to five of the writer's own points into a thesis-tested outline with exact word budgets.

## What it does

The skill takes four intake facts: the prompt, a target length between 300 and 3000 words, three to five points in the writer's words, and the writer's stance. It first checks that all four are present. Then it runs a four-part thesis test on the stance, covering whether the thesis is arguable, specific, answers the prompt and fits in one sentence of 8 to 35 words. If the stance fails, it offers up to two rewrites built only from the writer's own wording.

Each writer point becomes one body section, in the writer's order. The introduction and conclusion each get 10 percent of the target. The remaining words are split evenly across the body sections, and any rounding remainder goes to the last body section, so the budget always sums to the target. Each body section is checked for evidence the writer supplied. A section with no supplied example, observation or quotation is flagged EVIDENCE-NEEDED instead of being filled with invented material.

The result is a short outline table with a claim, evidence and counterpoint per section, a budget check line and a status of READY, PARTIAL or BLOCKED. A BLOCKED result lists numbered questions for the missing facts and produces no outline.

## When to use

Use it when a student or writer has a prompt, a length and a set of their own ideas, and needs a structure before drafting. It fits a 500 to 1500 word assignment with a clear position, where the main risk is a vague thesis or an uneven split of words across sections.

## When not to use

Do not use it to write essay text, to find sources or statistics, to grade a finished essay, or to decide whether a text was produced with AI. It does not handle creative writing, poetry or fiction plots, where a claim-and-evidence layout does not apply.

## Requirements

A text-capable agent. No scripts, no network access and no files beyond the prompt, the length and the writer's points.

## Example

The example below is a complete run on the offline smoke input: the prompt asks whether schools should start later, the target is 800 words, and the writer gives three points, the third of which has no supplied evidence.

```text
## Prompt
Should schools start later? Target 800 words, three writer points.

## Thesis
Schools should start later because early first bells cost teenagers sleep they cannot make up, and that lost sleep hurts learning and safety.
Tests: arguable PASS; specific PASS; answers prompt PASS; one sentence PASS (23 words)

## Outline
| Section | Words | Claim | Evidence (writer point) | Counterpoint | Flag |
|---|---|---|---|---|---|
| Introduction | 80 | Set up the late-bell question and state the thesis | n/a | n/a | OK |
| Body 1 | 213 | Early bells clash with the adolescent sleep clock | Writer point 1: teens' sleep clocks shift later; observation: first bell at 7:20 and half the class slept through first period | Parents' work schedules depend on the morning bell | OK |
| Body 2 | 213 | Drowsy first-period students miss lessons that later lessons build on | Writer point 2; observation: a chemistry unit was re-taught twice after most of the class missed the first lesson | NONE GIVEN | OK |
| Body 3 | 214 | A later start makes the drive to school safer for teens who drive in the dark | EVIDENCE-NEEDED (claim given, no example supplied) | NONE GIVEN | EVIDENCE-NEEDED |
| Conclusion | 80 | Restate the thesis and the three points | n/a | n/a | OK |

## Budget check
Target 800. Sum 800. Result PASS.

## Status
PARTIAL
```

## Limits

- The 300 to 3000 word range, the 10 percent introduction and conclusion shares, and the 8 to 35 word thesis band are working values, not a published standard.
- It only uses evidence the writer supplies. A thin or missing example produces an EVIDENCE-NEEDED flag, not a fix.
- It checks the thesis wording, not whether the position is correct.
- It cannot judge whether the writer's points are true.
- Three to five body sections is the supported range.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
