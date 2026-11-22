## תקציר

- ה-skill כותב או סוקר בריף קמפיין בעמוד אחד: יעד מדיד עם בסיס ותאריך, קהל אחד, הצעה, תוכנית ערוצים שסכומה שווה לתקציב, מדידה וכלל החלטה.
- כל מספר מתויג [given] / [assumption] / [calc], וכל ההנחות מרוכזות לאישור הבעלים.
- כולל script לא מקוון שבודק שלמות, חשבון תקציב ומספרים לא מתויגים.
- טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: marketing-campaign-brief

**One line:** Write or review a one-page campaign brief whose objective is measurable, whose budget adds up and whose every figure is tagged given, assumed or calculated.

## What it does

Seven ground rules (one primary objective, every figure tagged, ask before inventing, the money adds up, a KPI needs a data source, targets not promises, product claims must be supportable) and a five-step workflow: extract what is given, close the gaps, write the brief in a fixed nine-section layout, check, deliver. The script checks the sections, that the objective has a number, a deadline and a baseline, that channel budgets equal the stated total, that every money amount, percentage and channel target carries a tag, and that assumptions are listed for the owner.

## Capabilities

- `brief_check.py`: sections, objective, channel table, budget arithmetic, tags, assumptions list, measurement, outcome-promise words.
- A nine-section brief layout.
- A reasoning reference: objective patterns, channel roles, funnel arithmetic, budget split, decision rules, ten review questions.
- A delivery note: confirm first, check result, not covered.

## When to use

Turning kickoff notes into a brief; reviewing a brief before sign-off; a first draft from thin input with the questions that matter.

## When not to use

Writing the ads, posts or emails; keyword research; long-range brand strategy; legal review of claims.

## Requirements

Python 3.9+ (standard library). No network. Tested in one tool only (see Evidence).

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved runs)

1. Prompt: "Review this brief before I send it to the CEO." Saved run: `evals/runs/c2-review-brief/with_skill/reply.md` (8 of 8): budgets add up to $30,500 against a stated $28,000, and the brief's own numbers give 60 leads from search, not 300. The baseline (7 of 8) brought in outside benchmarks as fact.
2. Prompt: "Need a campaign brief for our spring promo for the bakery. Budget is $1,500. I'm in a rush." Saved run: `evals/runs/c3-thin-input/with_skill/` (7 of 7 against 5 of 7): a draft with every supplied figure tagged as an assumption and five questions.

## Limits

- The script checks structure and arithmetic, not whether the plan is wise.
- Tags make the brief dense to read; one grader note says so.
- In one run the agent read 'never run TikTok' as a ban and offered no test.
- No benchmarks are supplied; with no data from the user the numbers are assumptions.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model (haiku alias), one tool, 2026-11-20. Blind grading: 3 of 3 preferred with the skill, 0 tie, 0 preferred without. Static lint 0 FAIL. Token overhead about +25% per run. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Show the messy kickoff notes with two budgets and no target.
2. Show the brief: objective from 310 a month, each figure tagged, the $18k against $20k question listed.
3. Run the script: 0 FAIL, channel budgets 18,000 equal the total.
4. Run it on the flawed brief: 'channel budgets add up to 30,500 but the stated total is 28,000'.

## FAQ seeds

- Does it invent benchmarks? It is instructed not to; anything it supplies is tagged as an assumption.
- Does it write the ads? No.
- Can it review a brief in another layout? Yes by hand; the script expects the skill's headings.
- Is this legal review? No.
- Does it need network? No.
- What leaves my machine? Nothing.
- Other currencies? The script reads dollar, euro, pound and shekel signs.

## Changelog

- 0.1.0 (2026-11-20): first batch version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
