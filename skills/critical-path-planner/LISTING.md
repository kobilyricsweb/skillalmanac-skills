# Listing page content: critical-path-planner

**One line:** Computes critical path, slack, cycles and owner overload from a task list with durations and dependencies.

## What it does

The user gives tasks, whole-number durations and what each task needs first. The agent writes a small plan file and runs `scripts/critical_path.py`, which checks the dependency graph (duplicate links, links to tasks that do not exist, cycles, tasks connected to nothing), then runs a forward and a backward pass. It reports earliest and latest start and finish, total and free slack, every critical path, the finish date on a working-day calendar with holidays, the gap to a deadline, and owners with more tasks in progress on a day than their capacity. The agent then reads the figures with fixed tables (what slack means, what to compress first, why padding goes on the path) and answers in a fixed report. Durations are always the user's own.

## Capabilities

- Strict JSON report with `tasks[]` (`es ef ls lf slack free_slack deadline_slack critical at_risk` and dates), `paths[]`, `cycles[]`, `dangling[]`, `overloads[]`, `warnings[]`
- Cycle detection that names one concrete loop per knot, and no schedule until it is fixed
- Working-day dates with weekends, custom working weekdays and holidays; deadline as a date or a count
- Overload ranges per owner with each task's slack, so the agent can check whether a clash can be moved within slack or is a real conflict
- Optional `--out` file that can never overwrite the plan

## When to use

You have a list of tasks with durations and dependencies and ask for the critical path, which tasks have slack, whether a deadline is realistic, what is holding the plan up, whether the dependency list is consistent, or who is double-booked.

## When not to use

- Breaking a goal into tasks: use task-breakdown-coach. This skill needs the tasks and links already.
- Writing tickets or user stories: use project-tickets-writer.
- Challenging a plan's assumptions in words: use plan-stress-test. This skill only does the arithmetic of the schedule.
- Estimating durations, resource levelling, or probability of finishing on time. It does none of these.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent does the forward and backward pass by hand, as described in the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Prompt: "Here is my kitchen renovation plan (8 tasks, start 2026-03-02, deadline 2026-03-27). What is the critical path, which tasks can slip, and is anyone double-booked?"

Real output from the fixture run (`python scripts/critical_path.py evals/fixtures/kitchen_renovation.json`, trimmed):

```
project_duration: 14   start_date: 2026-03-02   finish_date: 2026-03-19
deadline_days: 20      deadline_gap: 6          critical_count: 3
paths: [["E", "F", "H"]]
A es 0 ef 2  ls 1  lf 3   slack 1     D es 5 ef 9  ls 6  lf 10  slack 1
E es 0 ef 10 ls 0  lf 10  slack 0     G es 9 ef 11 ls 11 lf 13  slack 2
overloads: Cara on days 2-3 (C, E) = 2026-03-04..03-05, and day 9 (E, G) = 2026-03-13
exit code: 1
```

Prompt: "Work out the schedule for this CSV" with a loop (1 needs 4, 4 needs 3, 3 needs 2, 2 needs 1) and a link to a task 9 that does not exist.

Real output (`evals/fixtures/bad_cycle.json`, same shape): `scheduled: false`, `cycles: [["A","B","C","A"], ["E","E"]]`, `dangling: [{"task":"D","predecessor":"X"}]`, warnings duplicate_predecessor, dangling_predecessor, cycle, cycle; exit 1. No dates are produced until the loop is cut.

## Limits

Finish-to-start links only, one duration per task, no lags or fixed-date constraints, no levelling, no probability. A missing dependency makes the path look shorter than it is.

## Evidence

Script fixtures only: 9 of 9 pass (see `VERIFICATION.md`). No efficacy, trigger or cross-tool testing yet.

## Demo script

Beat 1: paste the kitchen table; the agent writes the plan JSON. Beat 2: it runs the script and shows the exit code 1 and the three critical tasks. Beat 3: it explains that Plaster has 1 day of slack shared with its chain, and that the deadline has 6 spare days. Beat 4: it reports Cara's two clashes and asks whether ordering and receiving cabinets really needs her own time, since a long wait would explain both clashes. Result: a one-screen report instead of a hand-drawn network.

## FAQ seeds

- Does it need network? No.
- Can I give durations in hours? Yes, use a unit other than days; you get offsets, not dates.
- Does it level resources? No, it counts clashes and shows the slack of the tasks involved.
- Does it support lags or start-to-start links? No; the agent tells you if your plan needs them.
- How is it different from plan-stress-test or task-breakdown-coach? Those challenge or create the plan; this computes the schedule from it.
- What if my plan has a cycle? You get the loop named and no schedule until you decide which link to cut.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings; no human review has taken place yet.
