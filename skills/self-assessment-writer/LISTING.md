# Self-assessment writer

## One line

Turns a list of five to eight real accomplishments into a 350-to-500-word performance self-assessment, grouped by goal, with a growth area and a next-period goal.

## What it does

Many people undersell their year because they remember the work but not the outcomes. This skill takes the employee's own list of accomplishments, each with a month and what was done, and drafts a self-review. Each accomplishment becomes one paragraph in situation, action, result order, capped at 45 words. Work is grouped under up to three goals, using the goal list if the user supplies one and otherwise grouping by theme.

Result numbers are used only when the user supplies them, and then exactly as given. When no number is supplied, the paragraph states the outcome in plain words. The skill never rounds, scales or estimates a figure, and it bans a short working list of inflated phrasing such as "results-driven" and "leveraged".

A stop rule governs intake. The skill asks for missing period dates, fewer than five accomplishments, or more than eight, and returns a numbered question list instead of a guessed draft. It also refuses requests to invent figures or to describe a named colleague negatively.

The Summary, growth area and next-period goal each have word ranges, so the whole draft lands in the same length band from one run to the next.

## When to use

- An employee has a list of work done and must write a year-end or mid-year self-review.
- The work has dates and the employee can say what changed for the team or the customer.
- The employee wants a first draft to edit, not a final submission.

## When not to use

- Writing a manager review of another person, or rating or ranking staff.
- Turning a thin list of two or three items into a full review. The skill stops and asks for more.
- Adding results the employee cannot support with a source.

## Requirements

A text-capable agent. No network access, no files beyond the skill itself, and no scripts.

## Example

Smoke input (six accomplishments, two with supplied numbers) and the complete draft it produced follow.

Status: complete

# Self-assessment: January 1, 2026 to November 15, 2026

## Summary
This year I worked on three goals: support quality, reporting accuracy, and team growth. The six accomplishments below are grouped by goal. Each paragraph follows the same order: what was happening, what I did, and what changed. Two carry a measured result, and the other four describe outcomes in plain terms.

## Goal: Support quality
Tier-one tickets were sent to the wrong queue, which slowed every handoff. In March I built a triage checklist and trained the team to apply it at intake. Misrouted tickets fell from 14% to 6% of weekly volume.

The aged-ticket queue had to be cleared before quarter close. In April I led the weekend shifts and coordinated cover with two colleagues. The queue was cleared on time.

Escalations had no written path for the hardest cases. In July I wrote an escalation guide with named owners and response steps. The team lead adopted the guide as the standard for every shift.

## Goal: Reporting accuracy
The monthly reconciliation workbook did not match the finance ledger. In June I rebuilt it with checked totals and a separate reconciliation tab. Reconciliation errors fell from 5 per month to 0 over the last 4 months.

Refreshing the weekly report was a manual task that delayed the start of each Monday. In August I automated the refresh so the report is ready before the team begins. The team now starts Monday with current data and no manual copy steps.

## Goal: Team growth
Two new hires needed to learn the triage checklist and the escalation path. In October I trained both on live queues and reviewed their early work each day. Both reached independent queue work before their onboarding period ended.

## Growth area
My growth area is delegation. The reconciliation workbook ran only through my own steps until I rebuilt it, so no one else could run it. Next period I will document each recurring report, name a backup for each, and hand one report per month to that backup. Progress will show as completed handoffs, not as hours I spend on reports myself.

## Next-period goal
By March 31, 2027, I will name a backup for every recurring report and complete one full handoff per month. I will track each handoff in the team tracker and review the list with my manager at each one-on-one.

## Limits

- Draft only. The employee must check every fact, date and figure before submitting.
- Works from the input given. It does not verify outcomes against company records.
- Group and goal names come from the user's list or from the content. The skill does not know the company's own goal framework.
- Word ranges, the 45-word paragraph cap and the 350-to-500-word total are working values, not a published standard.
- Written for English. US spelling and conventions are assumed.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
