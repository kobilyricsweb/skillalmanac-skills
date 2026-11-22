---
name: daily-plan-timeboxer
description: Plans one working day by placing prioritised tasks with minute estimates into the free time around fixed meetings, adding a buffer, inserting breaks, and listing the tasks that do not fit. Use when a to-do list has minute estimates but the day plan ignores transitions, when someone needs a realistic timeboxed schedule around fixed meetings, or when a person prefers fixed time blocks to an open list. Do not use for medical or diagnostic advice, for syncing with a calendar service, for tasks without minute estimates, or for days that run past midnight.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Daily Plan Timeboxer

This skill turns minute estimates into a fixed-time schedule for one day. It is a planning aid. It does not predict whether anyone will follow the plan, and it gives no medical or treatment advice.

## Files

- `scripts/timebox.py`: the scheduler. Reads one JSON file and prints a JSON result.
- `fixtures/smoke_day.json`: the 6-task, 2-meeting, 8-hour input used for the smoke test.
- `LICENSE.txt`: Apache-2.0 license text.

## Inputs

| Key | Type | Default | Allowed | Notes |
|---|---|---|---|---|
| `day_start` | "HH:MM" string | required | 00:00 to 23:59 | 24-hour clock |
| `day_end` | "HH:MM" string | required | later than `day_start` | overnight days are refused |
| `fixed` | list | `[]` | up to 50 objects with `title`, `start`, `end` | must lie inside the day, must not overlap |
| `tasks` | list | required | 1 to 200 objects with `title`, `minutes`, `priority` | titles 1 to 200 characters |
| `tasks[].minutes` | integer | required | 1 to 480 | raw estimate, before buffer |
| `tasks[].priority` | integer | 3 | 1 to 5 | 1 is highest |
| `buffer_pct` | integer | 25 | 0 to 100 | working value |
| `break_every` | integer | 90 | 15 to 240 | minutes of task work before a break is due; working value |
| `break_minutes` | integer | 10 | 1 to 60 | length of one break; working value |

Any key not in the table is refused with exit 2.

## Settings decision table

| Situation | `buffer_pct` | `break_every` | `break_minutes` |
|---|---|---|---|
| Estimates in the user's own words, no history | 25 | 90 | 10 |
| User says past estimates were usually too short | 50 | 90 | 10 |
| User says the estimates already include padding | 0 | 90 | 10 |
| Three or more fixed events in the day | 25 | 60 | 10 |
| Day shorter than 240 minutes | 25 | 90 | 5 |

Every value in this table is a working value chosen for this skill. None is a published standard.

## Priority scale

| Value | Meaning | Placement |
|---|---|---|
| 1 | Must finish today | placed first |
| 2 | Should finish today | placed after all 1s |
| 3 | Default | placed after all 2s |
| 4 | Only if time remains | placed after all 3s |
| 5 | Last to be placed | placed last; first to appear in `not_fitting` |

## Workflow

1. Collect the day and the tasks. Output: `day_start`, `day_end`, the fixed events as start and end times, and each task with a whole-number minute estimate. Stop if any estimate is missing (see the refusal list).
2. Choose settings from the decision table. Output: the three settings and the row that justified any value other than the defaults.
3. Write the input JSON into the working folder. Output: the absolute path of that file.
4. Run the command in the Command section. Output: the exit code and the JSON printed to stdout.
5. Branch on the exit code. 0 means every task is placed. 1 means `not_fitting` has entries; continue to step 6 anyway. 2 means stop and report the error line.
6. Render the result using the Output contract. Output: the Plan, Does not fit, Totals and Settings sections.
7. For each entry in `not_fitting`, offer the user exactly three options: shorten the estimate, move the task to another day, or drop it. Output: one line per task with those three options.

## Placement rules (what the script does)

- Free time is the day minus the fixed events. Each free stretch is a window, in chronological order.
- Tasks are placed in priority order. Ties keep input order.
- Block length is `minutes` multiplied by `(100 + buffer_pct)` divided by 100, rounded up to a whole minute. Tasks are never split.
- A task goes into the first window where it fits, starting from that window's current cursor.
- When a window has had `break_every` minutes of task work since its start or its last break, a break of `break_minutes` is placed before the next task in that window. The task is placed there only if the break and the task both fit; otherwise the window is skipped.
- Breaks never overlap fixed events.

## Command

Run from the skill folder:

```
python -I scripts/timebox.py fixtures/smoke_day.json
```

For a user file, pass its absolute path in place of the fixture path. Redirect stdout to a file in the working folder if the result must be kept.

## Script contract

- Arguments: exactly one, the path to the input JSON. The file must be 2 MB or smaller, valid UTF-8, valid JSON, and nested no deeper than 6 levels.
- Exit 0: every task placed. Stdout holds the JSON result.
- Exit 1: at least one task is in `not_fitting`. Stdout still holds a complete, valid JSON result.
- Exit 2: usage or input error. Stdout is empty. Stderr holds one line such as `{"error": "tasks[0].minutes must be an integer"}`.
- Result keys: `day`, `settings`, `schedule`, `not_fitting`, `totals`.
- `schedule` items have `type` (fixed, task or break), `title`, `start`, `end` (HH:MM). Task items also have `priority`, `minutes` (raw) and `block_minutes` (with buffer).
- `not_fitting` items have `title`, `priority`, `minutes`, `block_minutes`.
- `totals` keys: `free_minutes`, `task_minutes_scheduled`, `block_minutes_scheduled`, `break_minutes`, `unused_free_minutes`, `task_minutes_not_fitting`.

## Output contract (rendered plan)

Use these headings in this order:

1. `## Plan for HH:MM to HH:MM`, where the times are `day.start` and `day.end`. Table with columns `Start | End | Type | Item | Minutes`. Type is fixed, task or break. For tasks, Minutes reads `raw (block)`, for example `45 (57)`. Breaks and fixed events show their own length.
2. `## Does not fit`. Table with columns `Item | Priority | Minutes | Block minutes`, or the single line `None.` when the list is empty.
3. `## Totals`. Bulleted list of all six `totals` keys with their values, using the exact key names.
4. `## Settings used`. One line each for `buffer_pct`, `break_every` and `break_minutes`.

Do not add any other section. Do not state that the plan will be followed.

## Refuse / stop when

- A task has no `minutes` value, or the value is not a whole number from 1 to 480. Stop and ask for the estimate. Do not guess one.
- The script exits 2. Stop, quote the error line, and ask for corrected input. Do not change values just to make the run pass.
- `day_end` is not later than `day_start`. Stop and ask whether the day really ends after midnight; this skill cannot plan that.
- The user asks for medical, diagnostic or treatment advice about attention, focus or any condition. Decline that part and offer only the scheduling.
- The user asks to create calendar events, send invitations, or sync with a calendar. This is out of scope and the script has no network access. Offer the rendered plan as text instead.
- The user asks for a promise that the schedule will be kept. Do not promise it. Say the schedule is an estimate built from the numbers given.
