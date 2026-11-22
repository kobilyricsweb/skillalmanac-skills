# Listing page content: task-breakdown-coach

**One line:** Turns a goal you cannot start into a first physical action and a checked 15 to 45 minute step plan.

## What it does

The skill gives an agent a fixed procedure: ask at most three questions, write a done-line, write a first action of 10 minutes or less that needs no decision, then a sequence of 15 to 45 minute steps each tagged with energy (low, medium, high) and context. It adds a next-action rule and a daily plan contract (capacity, at most 3 steps, stop time, a minimum version for a bad day). A script then reads the plan file, JSON or Markdown, and prints strict JSON listing steps over the time limit, titles without a concrete verb and object, a missing or oversized first action and days booked past the stated capacity. It makes no medical claims and does not diagnose.

## Capabilities

- `scripts/plan_check.py`: strict JSON report with `ok`, error and warning counts, per-day minute totals and coded findings; exit 0, 1 or 2
- A table of fixed limits (10-minute first action, 15 to 45 minute steps, 3 steps a day, 70% day-load target)
- A verb-swap table and splitting patterns for steps that will not shrink
- A stuck rule for a step skipped twice
- A fixed report: done-line, first action, plan, next action, contract, check result, assumptions, not checked

## When to use

You say I can't get started, break this down, I'm overwhelmed, too big to start, what is my first step, or plan my week, including when ADHD is part of why starting is hard. Or you have a plan file and want to know whether it can be followed.

## When not to use

Team project management, writing tickets, a stress test of a plan's assumptions, medical or therapy advice, and any diagnosis. Difference from the ticket-writing and plan-stress-test skills in this catalogue: this skill plans one person's own tasks down to a first physical action and checks the plan against numeric limits; it does not write tickets or challenge strategy.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent applies the hand checklist in step 7.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from the saved fixture run (`evals/fixtures/RESULTS.txt`); no with-skill agent run exists yet, so there is no saved agent conversation to show.

1. `python scripts/plan_check.py evals/fixtures/good.json`: 4 steps, `ok` true, 0 errors, 0 warnings, day totals `mon` 45 and `tue` 55 against a capacity of 180, exit 0.
2. `python scripts/plan_check.py evals/fixtures/bad.json`: `ok` false, 9 errors and 3 warnings, exit 1. Excerpt of the real output:

```
first_action_not_concrete: ... status: vague.
first_action_too_long: First action is 30 minutes; the limit is 10. Shrink it.
step_over_limit (s2): 90 minutes is over the 45-minute limit. Split it.
day_overbooked: Day 'mon' holds 160 minutes against a capacity of 120.
```

## Limits

- The script is lexical: it checks verbs against a fixed English list and minutes against numbers; it cannot judge whether a step is doable.
- The numeric limits are working values, not measured optima.
- Dates are free labels; no calendar or deadline check.
- Energy tags are self-reported.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and 6 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds, storyboard only, not yet recorded)

Prompt: "I have to file my taxes, I keep avoiding it, 90 minutes on weekdays." Beat 1: the agent asks one question (deadline). Beat 2: it names the first action, "Open the tax folder on the desk" (5 minutes). Beat 3: it saves `plan.json` and runs `plan_check.py`; a first run shows `step_over_limit`. Beat 4: it splits the step, re-runs, `ok` true. Before: "gather documents". After: a first action, four tagged steps and a daily contract. To be recorded from a saved real run.

## FAQ seeds

- Does it need network access? No.
- Does it diagnose ADHD or treat anything? No; it makes no medical claims and sends health questions to a professional.
- How is it different from a ticket-writing or plan-review skill? It plans one person's tasks to a first physical action; it does not write tickets or challenge strategy.
- Can I set my own step limit? Yes, `limits.max_step_minutes` in JSON or `Max step:` in Markdown.
- What data leaves my machine? None from the script; the agent's normal chat applies.
- How do I uninstall? Delete the skill folder.

## Changelog

- 0.1.0, 2026-11-21: first draft; static and fixture checks only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5); accountable publisher Global Media Holdings; no human review has taken place yet.
