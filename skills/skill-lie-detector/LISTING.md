# Listing page content: skill-lie-detector

**One line:** Tests whether a skill actually helps on your own tasks: same tasks with and without it, graded blind, with a verdict and a 95% interval.

## What it does

The skill gives an agent a seven-step procedure for a paired test.
1. Pick 6 to 10 of your real tasks and write pass/fail checks for each, before any run.
2. Run every task in fresh sessions, with the skill and without it, on the same model.
3. Shuffle the outputs under random ids, flag and redact lines that reveal the arm, and grade each task in an isolated copy so the grader cannot tell which arm produced an answer.
4. Grade each output in a fresh session that sees only the task, the checks and the anonymized answers, and must quote evidence for every pass.
5. Compute the result with a script: the pass-rate difference per task, the mean, a 95% bootstrap interval and an exact two-sided sign-flip test over tasks, wins and losses, and output length in each arm.

## Capabilities

- `scripts/blind.py`: copies the outputs to shuffled random ids and writes the key; refuses to re-blind a graded folder
- `scripts/verdict.py`: joins grades with the key and prints JSON with the verdict (LIFT, LIFT_UNCONFIRMED, NO_LIFT, HARMED or INCONCLUSIVE), the mean difference, the interval, per-task results and length; a pass whose quote is empty or not found in the output counts as a fail
- `references/grader_prompt.md`: the exact blind-grader instructions
- `references/formats.md`: tasks.json, key.json and grades.json formats

## When to use

You ask: does this skill help, is it worth installing or keeping, test or benchmark a skill, compare with and without, prune skills that do nothing.

## When not to use

Writing or fixing a skill (`skill-authoring-and-evals`), checking a package for malware (`skill-safety-audit`), choosing between skills without running them (`verified-skill-finder`).

## Requirements

An agent that can start fresh subagents or headless sessions (Claude Code: Task tool or `claude -p`). Python 3.9 or newer, standard library only. The two Python scripts run offline. The executor and grader runs use your configured model provider, so they need network access and may cost money.

## Tested

- Eight new-author synthetic transfer tasks, written by a Codex collaborator and frozen before the runs (2 runs per arm, Haiku executor): no improvement detected with either grader. The plain model reached full marks on 8 of 8 tasks with Sonnet and 7 of 8 with Opus.
- Self-test by the author (8 tasks, 2 runs per arm, Haiku executor, partially blinded):
  - Sonnet grader: LIFT, +15.6 points.
  - Opus grader: LIFT_UNCONFIRMED, +10.9 points.
  - No task lost with either grader.
  - The graders agree on 94.5% of the check results, but not on the verdict.
- Fixture tests: 17/17.
- Two separate reviews (an agent and a Codex collaborator); all the issues they found are fixed.
- Real-user and full-workflow efficacy remain untested.
- A real run on `json-records-to-csv` reproduced its published NO_LIFT and found a task where that skill made results worse.

Details and every file are in `VERIFICATION.md` and `evals/`.

## Limits

- Few tasks give wide intervals. LIFT or HARMED needs at least 6 tasks and a sign-flip p of 0.05 or less; with 5 tasks or fewer the best result is LIFT_UNCONFIRMED.
- It tests the skill's content when read, not whether the skill triggers by itself.
- A model grades a model; checks that a script or a person can confirm are more reliable.
