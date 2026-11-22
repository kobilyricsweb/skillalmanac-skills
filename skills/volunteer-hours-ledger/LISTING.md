# Listing page content: volunteer-hours-ledger

**One line:** Totals a volunteer hour log and flags the rows a coordinator must check, with strict JSON output.

## What it does

The skill gives an agent a fixed procedure for a volunteer sign-in sheet or hour log: collect the organisation's own rules, run a script, resolve rejected rows with the user, then draft a monthly report from the script's figures. The script parses CSV or plain lines, rounds each shift to a stated unit with integer minutes, and totals per person, activity, project and month. It rejects rows that cannot be counted (end before start, zero duration, impossible dates, blank names, duplicate sign-ins within 15 minutes) and flags overlapping shifts, over-cap days, missing sign-offs, outlier shifts, names missing from a roster, near-duplicate names, threshold crossings and inactive volunteers. It never says what hours count for in tax, law or benefits.

## Capabilities

- `scripts/volunteer_ledger.py`: one JSON report (`people[]`, `totals`, `monthly_report[]`, `near_name_matches[]`, `inactive[]`, `rejected_rows[]`, `verdict`); exit 0 clean, 1 findings, 2 bad input
- Rounding per shift: nearest, up or down, to any minute unit
- Name merging only when exact after casefolding, spacing and punctuation; every other pair is listed for a human
- Optional `--output` report file that refuses to overwrite the log or the roster, even with `--force`
- A fixed report shape ending in what was not checked

## When to use

You have a sign-in sheet, timesheet or hour log for volunteers and want totals per person, activity, project or month, a monthly report, milestone dates (for example 50 or 100 hours), a list of quiet volunteers, or a check for overlaps, duplicates and missing sign-offs.

## When not to use

Tax, legal, insurance, benefit or school-credit questions about what hours count for; payroll for paid staff; planning future rotas or slots; sending messages to volunteers. Planning future coverage is the job of the rota and capacity-planning skills; this one only totals and checks hours already logged.

## Requirements

Python 3.9 or newer, standard library only. No network. Input must be UTF-8 with ISO dates.

## Example 1: monthly totals

Prompt: "Here is our pantry's volunteer log for March and April. Give me per-person totals and a monthly report."

Command: `python scripts/volunteer_ledger.py evals/fixtures/good.csv`

Real output (abridged): `verdict: clean`, `totals.hours: 15.0`, `totals.shifts: 5`, Ana Lopez 8.0 h, Ben Cohen 7.0 h, `by_month: {"2026-03": 10.5, "2026-04": 4.5}`, `by_activity: {"Events": 1.5, "Food bank": 6.5, "Tutoring": 7.0}`.

## Example 2: a dirty log

Command: `python scripts/volunteer_ledger.py evals/fixtures/bad.csv --daily-cap 8 --roster evals/fixtures/roster.txt`

Real output (abridged): `verdict: findings`, 6 rows accepted and 6 rejected (duplicate_signin, end_before_start, zero_duration, impossible_date, missing_name, bad_time), 22.5 h counted; flags `overlapping_shifts` (Eli Park, rows 5 and 6, 60 minutes), `over_daily_cap` (Fay Nunez, 11.5 h on 2026-03-06), `missing_signoff` (row 5), `unmatched_name` (Dan Ruiz); one near-name pair, Dan Ruiz and Dana Ruiz, ratio 0.941, left unmerged. Exit code 1.

## Limits

The script trusts the log: it checks that rows agree with each other and with your stated rules, not that anyone attended. Overlap and duplicate checks need start and end times. Nicknames and distant spellings are not matched. The 15-minute duplicate window and the outlier rule are working values.

## Evidence

Static lint and 16 script fixture cases passed (see VERIFICATION.md). Not tested: with and without skill efficacy, trigger rates, native discovery in any tool, cross-tool runs, human review.

## Demo script (60 to 90 seconds)

1. Prompt: "Total our March volunteer hours and tell me what looks wrong" with the dirty log attached.
2. The agent asks one question: any rounding, daily cap or roster? The user answers 8 hours a day and gives the roster.
3. The script runs; the agent shows 22.5 hours counted and 6 rows left out, each with its reason.
4. The agent asks about the overnight shelter shift, the Dan and Dana pair and the missing sign-off, and does not change any of them.
5. After the user's answers it re-runs on a corrected copy and gives the monthly report with a "Not checked" line.

## FAQ seeds

- Does it need network access? No.
- Does it tell me whether volunteer hours are deductible or count for a benefit? No, by design.
- Will it merge "Dan Ruiz" and "Dana Ruiz"? No; it lists them and you decide.
- Does it change my file? No; it reads the log and writes only a report file you name, never over your input.
- How is it different from a rota or capacity-planning skill? Those plan future coverage; this totals and checks past hours.
- What format must the log have? CSV or comma lines, ISO dates, 24-hour or AM/PM times.

## Changelog

0.1.0, 2026-11-21: first draft, script fixtures run, not otherwise verified.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
