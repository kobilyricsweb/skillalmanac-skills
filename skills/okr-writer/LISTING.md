# OKR writer

## One line

Rewrites draft OKRs for one period into measurable key results and marks every missing baseline TO-CONFIRM instead of guessing it.

## What it does

The skill takes a set of draft objectives and key results for a single period and runs a fixed review. Each objective gets a pass or rewrite decision. Each key result is matched against a table of seven anti-patterns: task, output count, vanity total, sandbagged target, multiple metrics in one line, vague wording and missing source. Each key result is then checked for five fields (metric, baseline, target, source and owner). Targets are checked against a threshold table of working values for objective count, key result count, required change from baseline, baseline age and word counts.

Rewrites appear as before and after pairs. Where the user did not supply a baseline, the rewrite keeps the field as TO-CONFIRM and adds an open item that names the role to ask. The output uses a fixed contract: a summary, a findings table, one block per rewrite, an open items list and a scoring line. Scoring is stated as a convention on a 0.0 to 1.0 scale, not as a standard.

## When to use

Use it when a quarterly or annual draft reads like a task list, when key results have a number but no unit or source, or when a team wants a quick sandbagging check before it commits to scoring. It is most useful on five to twenty drafts at a time, where the same mistakes repeat across key results and a consistent rewrite format saves a review pass.

## When not to use

Do not use it for personal habit trackers, dated project plans with named owners and milestones, live KPI dashboards or reports that already have actual values. It will not invent a baseline, back-fill results for a closed period or write a key result about a named person's rating or pay. For those, a different tool or a manager conversation is the right step.

## Requirements

A text-capable agent. No scripts, no network access and no additional files are needed. The user supplies the draft text, the period label and any baseline values they already know.

## Example

The excerpt below is from the smoke run recorded in VERIFICATION.md, pasted from the produced output.

| ID | Draft text | Code | Result | Reason |
|---|---|---|---|---|
| O1-KR3 | Reach 50,000 total page views this quarter. | VANITY | REWRITE | Total grows without quality; no rate beside it |

### O1-KR3 (VANITY)
- Before: Reach 50,000 total page views this quarter.
- After: Raise the share of unique site visitors who start a free trial in the quarter.
- Metric: percent of unique visitors
- Baseline: TO-CONFIRM
- Target: TO-CONFIRM (set after baseline)
- Source: Web analytics export joined to trial sign-ups
- Owner: Marketing lead (proposed, confirm)

## Limits

The working values in the threshold table are not industry standards and will not fit every team. Targets are only as good as the baseline the user provides, and the skill cannot check the source system. Scores are a team convention and do not measure performance on their own. The skill reviews text; it does not decide strategy, and a rewrite still needs the owner to agree on it.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
