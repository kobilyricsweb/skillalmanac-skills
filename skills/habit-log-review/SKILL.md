---
name: habit-log-review
description: Reviews a habit, study, workout or focus log (date, habit, done flag or minutes) with a script that computes current and longest streak, completion rate over 7 and 28 days, goal adherence, best and worst weekday, gaps and trend, as strict JSON plus a plain read-out. Use when the user shares a habit tracker, streak or practice log and asks how they are doing, whether they are slipping, or what their streak is. Do not use for planning or breaking down tasks, setting goals from nothing, scheduling, or interpreting health, mood or nutrition data.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual arithmetic in the fallback section.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Habit log review

Turn a user's own behaviour log into counts, percentages and one small suggestion. The script does the arithmetic; you ask the right questions first and explain the result after. You describe the log. You never diagnose the person or explain why they did or did not do something.

## Never invent inputs

- The goal per habit comes from the user: "daily", or "N days a week", optionally with a minimum per day (for example 20 minutes). If the user has none, run the review without one: the verdict will be `no_goal` and you ask what would count as success before judging pace.
- Ask once whether a day with no row means "not done" or "not logged". Default to not logged (`unknown`). Use `--blank-means-no` only on the user's yes.
- Always pass today's date as `--as-of`, so a typo in the future is caught and an unlogged today is not a miss.

## Workflow

```
- [ ] 1 Get the log and a goal per habit
- [ ] 2 Settle blank days, date order, today's date
- [ ] 3 Run the script
- [ ] 4 Read warnings before numbers
- [ ] 5 Write the read-out
- [ ] 6 Give one change per habit
```

1. **Log and goals.** Save pasted text to a file first. Each line is `date,habit,value`; a header row is optional; a two-column `date,habit` log counts every row as done. Value is a flag (yes, no, true, false, x, done, y, n, 1, 0) or a number with an optional unit (`30`, `30 min`, `1.5h`; hours become minutes).
2. **Settle.** Dates like `03/04/2026` are refused unless you pass `--date-order dmy` or `mdy`; ask the user, do not guess. ISO dates and `Nov 8 2026` need nothing.
3. **Run:**

```bash
python scripts/habit_review.py log.csv --as-of 2026-11-21 --goal "Reading=daily>=20" --goal "Run=3/week" [--blank-means-no] [--date-order dmy]
```

   Goal grammar: `Name=daily` or `Name=N/week` (N 1 to 7), optionally ending `>=M` (a day counts only at value M or more). Names match ignoring case. Run the script; do not edit it to change a number.
4. **Warnings first.** Exit 1 means data-quality warnings, not a bad habit. Say each one in plain words before any number: `duplicate_rows`, `day_conflict`, `mixed_units`, `unknown_days`, `skipped_rows`, `future_dates`, `goal_unmatched`, `no_value_column`. Exit 2 means the input could not be read; relay the stderr sentence and fix the input.
5. **Read-out** in the fixed shape below, using the JSON fields, not your own recount.
6. **One change** per habit from the table below, matched on `pattern`.

## How the numbers are defined

| Term | Rule |
|---|---|
| Day state | `done`; `missed` (explicit no, or under the minimum); `unknown` (no row, blank not read as no); `pending` (no row on the as-of day: the day is not over, so it neither adds to nor breaks a streak) |
| Daily streak | Consecutive done days. A missed or unknown day resets it. Unknown days make it a lower bound |
| Weekly goal | Weeks run Monday to Sunday. A closed week is met at N done days. The week containing the as-of date stays open: it adds to the streak once met, and never breaks it. A partial first week is not scored. Blank days are rest days and count as not done |
| Rates | `rate_7`, `rate_28`, `rate_all` = done days / evaluable days (done + missed) in the window. Days before the habit's first row are excluded |
| `adherence_28` | Daily goal: done / evaluable in 28 days. Weekly goal: done / (N x evaluable days / 7), capped at 100 |
| Trend | Last 28 days against the 28 before. Needs 14 evaluable days in each, else `insufficient`. Up or down at 10 points or more, otherwise flat |
| Weekday profile | Done / evaluable per weekday. Best and worst only among weekdays with 4 or more observed days, and only when they differ |
| Gaps | Runs of not-done days: 2 or more days for daily or no-goal habits, 7 or more for weekly goals |

## Script output (strict JSON on stdout, `schema_version` 1)

Top level: `as_of`, `blank_means` (`unknown` or `not_done`), `rows_read`, `rows_used`, `habits[]`, `warnings[]` (strings starting `code:`), `summary` (count per verdict). Each habit: `name`, `goal` (`raw`, `kind`, `target`, `min_value`, or null), `value_type` (`flag`, `number`, `mixed`), `first_date`, `last_done_date`, `span_days`, `days_done`, `days_missed`, `days_unknown`, `streak_current`, `streak_longest`, `streak_unit` (`days` or `weeks`), `rate_7`, `rate_28`, `rate_all`, `adherence_28`, `weeks` (`closed`, `met`, `pct`, `open`; weekly goals only), `weekday_profile` (Mon to Sun: `done`, `days`, `rate`), `best_weekday`, `worst_weekday`, `gaps_total`, `gaps[]` (`start`, `end`, `days`, `kind`), `trend` (`recent_rate`, `prior_rate`, `delta_pts`, `direction`), `days_since_last_done`, `verdict`, `pattern`, `warnings[]`, `notes[]`, `readout`. Rates are percents with one decimal, or null when nothing can be evaluated. Exit 0 clean, 1 warnings, 2 bad input. The script reads only the log and writes nothing.

## Verdict ladder

Checked in this order, on the last 28 days:

| Verdict | Condition |
|---|---|
| `too_early` | Fewer than 14 days from first row to as-of date, or fewer than 7 evaluable days in the window |
| `no_goal` | No goal given |
| `stalled` | No done day for 14 days or more, or adherence under 40% |
| `slipping` | Adherence from 40% up to 80% |
| `on_pace` | Adherence 80% or more |

Never write "failing", "lazy" or "disciplined"; use the verdict word. A `too_early` habit gets counts and no judgement.

## One change per habit

| `pattern` (from the script) | Meaning | Suggest |
|---|---|---|
| `steady` | On pace, no strong dip, no long pause | Change nothing. Say so |
| `uneven` | Slipping, no single cause visible | Anchor it: attach it to one existing daily event so the cue is fixed |
| `weekday_gap` | Best and worst weekday differ by 40 points or more | Move the time on the worst weekday, or make that weekday a planned rest day and say so in the goal |
| `fading` | Trend down 10 points or more and not on pace | Lower the bar to about half (20 minutes to 10, 5 a week to 3) for two weeks, then review again |
| `stop_start` | A pause of 7 days or more, followed by a done day | Anchor it, and agree the smallest version to do on the first day after any miss |
| `never_took_off` | Under 30% of days done overall and not on pace | Lower the bar to a version the user would do on a bad day. Offer once to drop it if the user no longer wants it; that call is theirs |
| `null` | `too_early` or `no_goal` | No suggestion; ask for the missing goal or more days |

## Read-out format

```
Habit: <name>, goal <as given, or none>
Verdict: <verdict>; streak <current> now, <longest> longest (<unit>)
Last 28 days: <rate_28>% of days done, <adherence_28>% of goal; trend <direction> (<delta_pts> points)
Pattern: <weekday, gap or trend facts from the JSON, one sentence>
One change: <row from the table>
Data notes: <each warning in plain words, or "none">
Not checked: <e.g. why days were missed; whether the goal is the right one>
```

Several habits: one block each, then one line naming the habit with the lowest adherence.

## Limits

- Counts only what was logged. A logged "yes" is trusted; the script cannot tell a skipped entry from a skipped day when blank means unknown.
- Weekly goals count days, not weekly totals; a "150 minutes a week" goal is not supported.
- The thresholds (14 days, 80%, 40%, 10 points, 4 weekday days) are working values, not measured optima.
- A weekday gap from fewer than 8 weeks of data can be chance.
- English flag words and dates only; other languages need the values translated first.
- This is a description of a log. It says nothing about health, mood, sleep or diet. If the log is about those, report the counts and stop; interpretation belongs to the person and, where relevant, a professional.

## Fallback without Python

Per habit: list each day as done, missed or blank from the user's rows. Streak = done days counted back from the latest day, skipping a not-yet-logged today. Rate = done days / days with a row in the last 28 days. Adherence for "N a week" = done / (N x days / 7), capped at 100. Compare the last 28 days with the 28 before for the trend, and apply the ladder above. State that the arithmetic was done by hand and nothing else was checked.
