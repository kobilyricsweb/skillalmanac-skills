# Daily Plan Timeboxer

## One line

Places prioritised tasks with minute estimates into the free time left around fixed meetings, then reports which tasks do not fit.

## What it does

The skill takes one working day, a list of fixed events such as meetings, and a list of tasks, each with a whole-number minute estimate and a priority from 1 (highest) to 5. A bundled Python script removes the fixed events from the day, leaves the free stretches as windows, and places tasks in priority order into the first window where each one fits. Each task receives a buffer percentage on top of its estimate, rounded up to the whole minute, and the script inserts a short break before a task whenever the window has already gone a set number of minutes without one. Tasks are never split across windows. The output is a chronological schedule with the fixed events, the tasks and the breaks, a list of tasks that did not fit, and totals that show how much free time was left over. The agent then renders this as a plain table and offers the user three choices for each task that did not fit.

## When to use

Use it when a to-do list already has minute estimates but the day plan ignores the gaps between meetings. It is most useful for a single day with two or three fixed events, where the question is which tasks realistically fit before end of day. It also suits a user who prefers a day broken into fixed time blocks over an open list, because the output is a set of start and end times rather than a ranking.

## When not to use

Do not use it for medical, diagnostic or treatment questions about attention or focus; the skill is a scheduling aid and says so. Do not use it for tasks that have no minute estimate, since the script refuses them rather than guessing. It does not sync with calendar services and cannot create invitations. It does not plan days that run past midnight, and it does not plan several days at once.

## Requirements

Python 3.9 or newer, standard library only. No network access, no third-party packages and no write access to anything except the standard output stream. The package holds one script under `scripts/`, one input file under `fixtures/` and the license text.

## Example

Command: `python -I scripts/timebox.py fixtures/smoke_day.json`, exit code 1. The output below is verbatim from that run.

```json
{
  "day": {
    "start": "08:00",
    "end": "16:00",
    "minutes": 480
  },
  "settings": {
    "buffer_pct": 25,
    "break_every": 90,
    "break_minutes": 10
  },
  "schedule": [
    {
      "type": "task",
      "title": "Review pull requests",
      "priority": 2,
      "minutes": 45,
      "block_minutes": 57,
      "start": "08:00",
      "end": "08:57"
    },
    {
      "type": "fixed",
      "title": "Team sync",
      "start": "09:00",
      "end": "09:30"
    },
    {
      "type": "task",
      "title": "Draft budget memo",
      "priority": 1,
      "minutes": 60,
      "block_minutes": 75,
      "start": "09:30",
      "end": "10:45"
    },
    {
      "type": "task",
      "title": "Write status update",
      "priority": 2,
      "minutes": 30,
      "block_minutes": 38,
      "start": "10:45",
      "end": "11:23"
    },
    {
      "type": "break",
      "title": "Break",
      "start": "11:23",
      "end": "11:33"
    },
    {
      "type": "task",
      "title": "Clean up inbox",
      "priority": 4,
      "minutes": 40,
      "block_minutes": 50,
      "start": "11:33",
      "end": "12:23"
    },
    {
      "type": "fixed",
      "title": "Client call",
      "start": "13:00",
      "end": "14:00"
    },
    {
      "type": "task",
      "title": "Plan next sprint",
      "priority": 3,
      "minutes": 90,
      "block_minutes": 113,
      "start": "14:00",
      "end": "15:53"
    }
  ],
  "not_fitting": [
    {
      "title": "Prepare slides",
      "priority": 3,
      "minutes": 120,
      "block_minutes": 150
    }
  ],
  "totals": {
    "free_minutes": 390,
    "task_minutes_scheduled": 265,
    "block_minutes_scheduled": 333,
    "break_minutes": 10,
    "unused_free_minutes": 47,
    "task_minutes_not_fitting": 120
  }
}
```

## Limits

Each task is placed whole, so a 120-minute task cannot use two separate 60-minute gaps. Placement is greedy in priority order, which is predictable but not optimal: a lower-priority task can take room that a later, larger task would have used better. Buffer percentages and break intervals are working values and are not drawn from any published guideline. Inputs are capped at 2 MB, 200 tasks, 50 fixed events and 6 levels of nesting. Times are 24-hour clock values and days cannot cross midnight.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
