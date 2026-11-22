# Listing page content: plan-stress-test

**One line:** Attacks a written plan before execution and returns a ranked, validated risk register.

## What it does

The skill gives an agent a fixed eight-step procedure for stress-testing a plan: save it as Markdown, scan it, state goal and assumptions, run six attack passes (done criteria, hidden assumptions, dependencies, ownership and single points of failure, schedule, failure and reversal), run a pre-mortem, score each risk from 1 to 5 on likelihood and impact, and write a register. A script parses headings, checklist items, numbered items and step tables, and reports steps with no owner, date or done criterion, dependencies that no step defines, circular waits, steps dated before what they depend on, owner concentration and plan-level gaps (no success criteria, no rollback). A second command validates the agent's register: score arithmetic, rank order, categories, and that every quoted piece of evidence really occurs in the plan.

## Capabilities

- `scripts/plan_scan.py scan`: strict JSON report of structural gaps with line numbers and severity; exit 1 when a high-severity gap exists
- `scripts/plan_scan.py register`: strict JSON check of the risk register against the contract in `SKILL.md`; rejects invented quotes
- Question bank for each attack pass, and scoring anchors so likelihood and impact stay comparable
- A fixed report: verdict, top risks, hidden assumptions, questions for the author, what was not checked

## When to use

You have a written plan (project, launch, migration, rollout, office move) and say stress test this, poke holes, red team it, run a pre-mortem, what could go wrong, or is this plan solid.

## When not to use

Writing a plan from scratch, effort estimates, code or contract review, security threat modelling of a system. How it differs from nearby skills in this catalogue: `scope-change-brief` assesses a requested change to an agreed scope, `handover-readiness-check` checks a handover pack, and `prd-writer` writes requirements. This one attacks an existing plan's structure and assumptions.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual structural pass in step 2 of the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both outputs below are from the saved fixtures (`evals/fixtures/RESULTS.txt`), not invented.

1. `python scripts/plan_scan.py scan evals/fixtures/plan_bad.md` on a seven-step database migration plan: verdict `weak`, 12 findings, exit code 1. The high-severity ones: line 11 `date_before_dependency` (A3 is dated 2026-03-03 but depends on A2 dated 2026-03-04), line 13 `no_owner` (A5, the application switch), line 15 `no_owner` (A6). Medium ones include `undefined_dependency` on A2 ("the network team opens the firewall ports" is never defined as a step) and `no_rollback`.
2. `python scripts/plan_scan.py register evals/fixtures/plan_bad.md evals/fixtures/register_bad.json`: `ok` false with 6 errors, among them `risks[1] score 25 is not likelihood x impact = 20` and `risks[2] evidence.quote does not occur in the plan`, plus a warning that high-severity findings on lines 11 and 15 are cited by no risk. The same plan with `register_good.json` returns `ok` true with 5 risks.

No with-skill agent run exists yet, so there is no saved final report to show.

## Limits

- The scan is lexical: owners must be written as `@name` or `owner: name`, done criteria need words such as verify, done when, accept, pass, or a threshold.
- Dependency matching compares words, so it can resolve to the wrong step or miss a rephrased one.
- Dates are compared only when the year is written; no holidays, time zones or working days.
- Thresholds are working values, not measured optima.
- Ranking depends on the agent's likelihood and impact estimates, which no script checks.
- English only for the parsing.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 10 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

Copyright 2026 Global Media Holdings (skillalmanac.com)

## Differentiators and limits (fix round 2026-11-21)

- `decision-council` chooses between options; this skill attacks one existing plan. It owns the phrase pre-mortem; `decision-council` no longer lists it as a trigger.
- Owners written in prose ("Dana to freeze the schema") are not read as owners. Write `owner: Dana` or `@dana`, or the step is reported as unowned.
- A dependency list such as "staff training and the sandbox UAT" is now split into two dependencies.
