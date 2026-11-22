# Listing page content: habit-log-review

**One line:** Computes streaks, adherence, weekday pattern and trend from your own habit log, then suggests one small change.

## What it does

The agent asks for the log and a goal per habit, never inventing one, then runs `scripts/habit_review.py`. The script reads `date,habit,value` lines (flags or minutes), merges duplicate days, ignores future dates, and returns strict JSON: current and longest streak, completion rate over 7 and 28 days, adherence to the goal, weekday profile with best and worst day, gaps, and the last 28 days against the 28 before. A verdict ladder (on pace, slipping, stalled, too early, no goal) uses stated thresholds, and a pattern code maps to one change: anchor it, lower the bar, move the time, or drop it.

## Capabilities

- Daily goals and weekly goals (N days a week, Monday to Sunday), each with an optional per-day minimum such as 20 minutes
- Day states done, missed, unknown and pending, so an unlogged today never breaks a streak
- Warnings for duplicates, mixed units, unreadable rows, future dates and unlogged days, reported before any number
- A fixed read-out format with a "Not checked" line

## When to use

You share a habit, study, workout or focus log and ask how you are doing, what your streak is, whether you are slipping, or which weekday you miss.

## When not to use

Planning or breaking down tasks, choosing a goal from nothing, scheduling, or reading health, mood, sleep or diet data for meaning. Weekly totals such as "150 minutes a week" are not supported.

How it differs from `task-breakdown-coach`: that skill turns a goal into steps to do next. This one looks backwards at a behaviour log that already exists and does the arithmetic (streaks, adherence percent, best and worst weekday, trend) with a script and a fixed JSON contract; it plans nothing and never invents a goal.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the manual arithmetic in the skill. Not tested in any agent tool yet.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from the saved fixture run (`evals/fixtures/RESULTS.txt`), not from an agent session.

1. `python scripts/habit_review.py evals/fixtures/log_fading.csv --as-of 2026-11-21 --goal "Stretch=daily"` (55 days of a daily stretch log): verdict `stalled`, pattern `fading`; 32 of 55 days done; last 28 days 28.6% against 88.9% in the 28 before (down 60.3 points); current streak 0, longest 11; best weekday Tue, worst Sat (1 of 8); 4 gaps of 4 to 6 days; exit 0. The suggested change is to lower the bar to about half for two weeks.
2. `python scripts/habit_review.py evals/fixtures/log_two_habits.csv --as-of 2026-11-21 --goal "Reading=daily>=20" --goal "Run=3/week" --goal "Journal=daily"`: Reading is on pace with a 10-day streak (90.0% of days, 2 days under 20 minutes); Run, 3 a week, is on pace with a 3-week streak (2 of 2 closed weeks met, this week already met); Journal is slipping at 70.0% with 3 two-day gaps; exit 0. The unlogged 21 November is `pending` and breaks nothing.

## Limits

- Counts only what was logged; a blank day is unknown unless the user says blank means no.
- Weekly goals count days, not weekly totals.
- Thresholds (14 days, 80%, 40%, 10 points, 4 weekday days) are working values, not measured optima.
- A weekday gap from under 8 weeks of data can be chance.
- English flag words and dates only.
- It describes a log. It says nothing about health, mood or why days were missed.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN, and 9 script fixture cases pass with expected values worked out by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

1. Prompt: "Here is my stretch log, I stopped and don't know why. Goal was every day. Today is 21 Nov."
2. The agent asks nothing it can read from the log, notes the goal is daily, and runs the script with `--as-of 2026-11-21`.
3. Read-out: stalled; 28.6% of the last 28 days against 88.9% the month before; longest streak 11 days; Saturday done 1 time in 8.
4. One change: lower the bar to about half for two weeks, then review. "Not checked: why the days were missed."

## FAQ seeds

- Does it need network access? No.
- What file formats? CSV, tab or semicolon separated lines; paste text is saved to a file first.
- What if I only logged the days I did it? Say blank means "not done" and it passes `--blank-means-no`; otherwise blank days are unknown.
- Does it give health advice? No. It reports counts and one habit-design change, and stops there.
- How is it different from task-breakdown-coach? See above: it analyses a past log, it does not plan.
- What leaves my machine? Nothing; the script reads one file and prints to the terminal.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft, static and fixture checks only.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
