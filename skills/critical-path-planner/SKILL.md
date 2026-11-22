---
name: critical-path-planner
description: Computes a project schedule from a list of tasks with durations and predecessors, giving the critical path, slack per task, dependency cycles, dangling predecessors, finish date against a deadline and owners booked on too many tasks at once, as strict JSON from a bundled script. Use when the user asks for a critical path, which tasks have slack, whether a deadline is realistic, or says "what is holding up my plan", "check my dependencies", "who is double-booked". Do not use for breaking a goal into tasks, writing tickets, estimating durations, resource levelling or probabilistic risk simulation.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, do the forward and backward pass by hand as in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Critical path planner

Turn a dependency list into a schedule you can defend. The script does the arithmetic; you supply the user's numbers unchanged and read the result. Durations are the user's: never estimate, round or "fix" them to make a deadline fit.

## Workflow

```
- [ ] 1 Collect tasks, durations, predecessors, owners, calendar, deadline
- [ ] 2 Write the plan JSON
- [ ] 3 Run the script
- [ ] 4 Resolve errors before reading any dates
- [ ] 5 Read slack, paths, deadline gap, overloads
- [ ] 6 Report
```

1. **Collect.** Each task needs an id, a duration in whole units and its predecessors (tasks that must finish first). Ask for owner only if the user wants a workload check. Confirm the unit and the calendar: working weekdays (default Monday to Friday), holidays, start date, deadline. A task with duration 0 is a milestone. If durations arrive as ranges or hours, ask for one number per task and a single unit; use a smaller unit (hours) rather than fractions.
2. **Write the plan** to a file (never edit the user's file in place). Keys:

| Key | Meaning |
|---|---|
| `unit` | `"days"` for working days with real dates; any other word (`"hours"`, `"weeks"`) gives offsets only, no dates |
| `start_date` | `YYYY-MM-DD`, only with unit `days`; a non-working start moves to the next working day |
| `working_days` | ISO weekdays, default `[1,2,3,4,5]` |
| `holidays` | list of dates that are not worked |
| `deadline` or `deadline_days` | a date (needs `start_date`) or a count of units from the start; not both |
| `capacity`, `default_capacity` | simultaneous tasks allowed per owner (default 1) |
| `tasks[]` | `id`, `duration` (whole number, 0 to 3650), optional `name`, `owner`, `predecessors` (list, or comma-separated text) |

3. **Run:** `python scripts/critical_path.py plan.json`. Add `--out report.json` to keep the report; it refuses an existing file unless `--force`, and never writes over the plan. Exit 0 clean, 1 findings, 2 bad input (the JSON says what to fix).
4. **Resolve structural errors first.** `cycles` and `dangling` make the numbers meaningless. With a cycle the script computes no schedule (`scheduled: false`): ask the user which link is wrong and cut that one, do not pick for them. A dangling predecessor is ignored by the script: ask whether the id is a typo or a missing task. `isolated_task` usually means a forgotten link. Re-run after each fix. By hand (no Python): earliest start = latest earliest-finish among predecessors (0 if none), finish = start + duration, project length = largest finish; backward, latest finish = smallest latest-start among successors (project length if none); slack = latest start minus earliest start.
5. **Read the result** with the tables below. Slack is shared along a chain: two tasks that each show 3 days of slack on one path do not both have 3 days. `free_slack` is what a task can slip without moving any successor; use it for "can this one slip?".
6. **Report** in this fixed shape:

```
Schedule: <project length in unit>, start <date>, finish <date or n/a>
Critical path(s): <ids in order>, <n> critical tasks of <total>
Deadline: <gap: +n spare or -n late, or none given>
At risk: <ids with slack at most 10 percent of length>
Problems: <cycles, dangling, isolated, overloads with owner and days>
Options: <only if late or overloaded, in the order of the compression table>
Not checked: <estimates, dependency types other than finish-to-start, holidays not supplied>
```

## Reading the numbers

| Field | Rule | Say |
|---|---|---|
| `slack` = 0 | critical | any slip moves the finish one for one |
| `slack` 1 up to 10 percent of length (minimum 1) | `at_risk` | one bad week eats the buffer |
| `slack` above that | comfortable | still shared with the rest of its path |
| `deadline_slack` < 0 | late against deadline | the amount is the shortfall, on every task of that path |
| `deadline_gap` > 0 | spare time | it is buffer for the whole project, not per task |
| `critical_count` above half of tasks | fragile plan | tell the user most of the plan has no room |

Several paths in `paths` means the finish date depends on all of them: shortening one does nothing until every one is shortened.

## If the finish is later than the deadline

Work down this order and stop at the first that closes the gap; each option is a suggestion to the user, not a change you make.

| Order | Option | Check |
|---|---|---|
| 1 | Cut or defer scope on critical tasks | Remove the task from the plan, re-run, confirm the gap |
| 2 | Run critical tasks in parallel (split, or drop a link the user confirms is soft) | A dropped link must be confirmed as not real; never drop one to make numbers work |
| 3 | Add people to critical tasks | Helps only tasks that divide cleanly; late knowledge-work tasks usually do not speed up and often slow down |
| 4 | Move the deadline | Give the user the gap in units and dates |

Compress only the critical path: shortening a task with slack changes nothing. After each change, re-run, because a new path can become critical.

## Padding

Pad the path, not the task. Add one buffer task (name it Buffer) at the end of the critical path, or before a fixed external date, sized by the user. Per-task padding hides slack and is used up by the task that owns it. Never add a buffer silently; show the length with and without it.

## Overloads

`overloads` counts, per owner and per working-day offset, how many tasks are in progress on the earliest-start schedule, against capacity. It is a count, not levelling: it moves nothing. For each range read the `slack` map: a clashing task clears the overlap only if it can be moved, within its own slack, to start after the other task's `ef` or finish before the other's `es`; check that against the numbers, since a long task overlaps anything moved a short way. If every clashing task is critical, or no move within slack clears it, it is a real conflict to raise with the user (second person, longer duration, or a later finish). First ask whether the task needs the owner's own time: waiting, ordering, delivery and curing tasks do not, and should have no owner.

## Scripts

- `scripts/critical_path.py`: run it, do not edit it to make a check pass. Prints one JSON report; keys `schema_version`, `ok`, `scheduled`, `project_duration`, `start_date`, `finish_date`, `deadline_days`, `deadline_gap`, `critical_count`, `tasks[]` (`es ef ls lf slack free_slack deadline_slack critical at_risk start_date finish_date`), `paths[]`, `cycles[]`, `dangling[]`, `overloads[]`, `warnings[]` (`rule`, `severity`, `message`). Read [references/scheduling_rules.md](references/scheduling_rules.md) for the offset-to-date convention, milestone dates, a worked example and the sources; read it only when a date or slack figure surprises you.

## Limits

- Finish-to-start links only; no lags, leads, start-to-start or fixed-date constraints. Say so when the user describes them.
- One duration per task; no uncertainty, no probability of meeting the date.
- Overload counting uses the earliest-start schedule and one owner per task; it does not level or reassign.
- Dates need unit `days` and a start date; the calendar is weekdays plus the listed holidays.
- A schedule is only as good as the durations and links given. A missing dependency makes the path look shorter than it is.
