---
name: volunteer-hours-ledger
description: Totals a volunteer hour log per person, activity, project and month, rounds shifts to the organisation's own unit, and flags overlapping shifts, duplicate sign-ins, missing sign-offs, over-cap days, outlier shifts, near-duplicate names and inactive volunteers, with a script that prints strict JSON. Use when a coordinator or charity has a sign-in sheet or hour log and asks for volunteer hour totals, a monthly volunteer report, hours per person, who hit 50 or 100 hours, or to clean up the log. Do not use for tax, legal, benefit or insurance questions about what hours count for, payroll, or planning future rotas.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only, and uses no network. Without Python, follow the manual fallback in the procedure.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Volunteer hours ledger

Turn a messy hour log into totals a coordinator can trust, and list every row that needs a human decision. Arithmetic and consistency only. The skill never says what hours count for (tax, legal, benefits, insurance, grants, school credit); if asked, say the organisation or the receiving body decides that, and give the totals.

## Collect before running

Ask for what is missing, in one message:

1. The log: person, date, start and end times (or an hours value), activity, project (optional), sign-off (optional). Dates must be `YYYY-MM-DD`; times 24-hour `HH:MM` or `1:30 PM`.
2. The organisation's own rules, each optional: rounding unit in minutes and direction, daily cap in hours, hour thresholds to track (for example 50, 100), the days of silence after which a volunteer counts as inactive, whether shifts may run past midnight, an expected-name roster.
3. The report month, if only one month is wanted.

Do not invent a rule the organisation did not state. With no rounding stated, use 1 minute (exact). Ambiguous dates such as `03/04/2026` are not guessed: ask which order, convert the file copy, keep the original.

## Procedure

1. Keep the original log untouched. If it is only in chat, save it to a file first.
2. Run the script (flags only for rules the user stated):

```bash
python scripts/volunteer_ledger.py log.csv --round-unit 15 --round-mode nearest --daily-cap 10 --thresholds 50,100 --inactive-days 60 --roster roster.txt --output ledger.json
```

3. Read `rejected_rows` first. They are in no total. For each reason, use the table below, then ask the user for the corrected value; never repair a row yourself.
4. Read `near_name_matches` and `people[].flags`. Present them as questions, not corrections.
5. Re-run after the user's corrections (on a corrected copy) until `rows_rejected` is 0 or the user accepts the remainder, then report.
6. Draft the monthly report from `monthly_report` and `totals` only (format below).

If Python is unavailable: total by hand per person, never mixing rounded and unrounded figures, list the same checks from the tables below, and say the report was not script-verified.

## What the script decides

| Reason in `rejected_rows` | Meaning | Ask the user |
|---|---|---|
| `end_before_start` | end earlier than start | overnight shift (then re-run with `--allow-overnight`) or a typo |
| `zero_duration` | start equals end | real shift with a typo, or a sign-in with no sign-out |
| `duplicate_signin` | same person and date, start within 15 minutes (`--dup-minutes`) of an earlier row | keep the first; confirm it is one visit |
| `impossible_date`, `bad_date_format`, `date_out_of_range`, `future_date` | not a real date, not ISO, year outside 1990-2100, or after `--as-of` | the correct date |
| `bad_time`, `incomplete_times`, `no_duration`, `bad_hours`, `non_positive_duration`, `over_24_hours` | unreadable or impossible time or hours | the correct values |
| `missing_name` | blank name | who it was; the row stays out until named |

| Flag type (`people[].flags[].type`) | Kind | Rule |
|---|---|---|
| `overlapping_shifts` | quality | two shifts of one person overlap by more than 0 minutes; both stay in the totals, the detail gives the overlap |
| `over_daily_cap` | quality | rounded minutes of one person on one date exceed `--daily-cap` |
| `missing_signoff` | quality | a sign-off column exists and the cell is empty, no, pending, none, n/a or a dash |
| `outlier_shift` | quality | shift at least 3 times the median shift and at least 4 hours, in logs of 10 or more shifts |
| `hours_mismatch` | quality | an hours column differs from start to end by more than 0.01 h; the times win |
| `possible_duplicate_hours` | quality | hours-only rows with the same person, date, activity and hours |
| `unmatched_name` | quality | name not on the roster file (exact after normalising) |
| `overnight_shift` | info | shift past midnight, accepted because `--allow-overnight` was given |
| `threshold_crossed` | info | the date on which a person's running total reached a threshold |

Names merge only when identical after casefolding, collapsing spaces and dropping `.` and `,`. Everything else is listed in `near_name_matches` (`similar_spelling` at difflib ratio 0.85 or more, or `same_words_different_order`) and is never merged by the script. If the user confirms a match, edit a copy of the log so the names are identical, then re-run.

Rounding is per shift, before totals: `nearest` (half rounds up), `up` or `down`. Say which was used. A shift that rounds to zero stays in the log as 0 h.

## Output contract

Strict JSON on stdout (also written to `--output`). Top level: `schema_version` ("1"), `command`, `input`, `rows_read`, `rows_accepted`, `rows_rejected`, `settings`, `people[]`, `totals`, `monthly_report[]`, `flag_counts`, `near_name_matches[]`, `inactive[]`, `rejected_rows[]`, `verdict` ("clean" or "findings").

- `people[]`: `name`, `hours`, `shifts`, `first_date`, `last_date`, `months{}`, `activities{}`, `projects{}`, `name_variants[]`, `flags[]` (each with `type`, `kind`, `rows`, `date`, `detail`).
- `totals`: `hours`, `shifts`, `volunteers`, `by_activity{}`, `by_project{}`, `by_month{}`.
- `monthly_report[]`: `month`, `hours`, `shifts`, `volunteers`, `people{}`, `top_activity{name, hours}`.
- `inactive[]`: `name`, `last_date`, `days_since`, only when `--inactive-days` is set; the reference date is `--as-of` or the latest date in the log.
- `rejected_rows[]`: `row` (data row number), `line` (file line), `reason`, `raw`.

Exit code 0 means no data-quality finding, 1 means findings, 2 means bad input or options. Threshold crossings and inactive people are information and do not change the exit code. Row numbers count data rows after the header.

## Report to the user

Give this fixed shape, numbers copied from the JSON:

```
Period and rules: <dates covered; rounding; cap; thresholds>
Totals: <hours, shifts, volunteers; by month; by activity; by project>
Per person: <table: name, hours, shifts>
Needs a human: <rejected rows with reason; overlaps; missing sign-offs; near-name pairs; over-cap days; outliers>
Milestones and quiet volunteers: <threshold crossings with dates; inactive list>
Not checked: <anything the log cannot show: whether hours were worked, accuracy of sign-ins, what the hours count for>
```

Certificates or thank-you notes may be drafted only from `people[]` figures for names the user selects, with the total and period, and with no statement about what the hours qualify for. Use only names in the log; never contact anyone or look anyone up.

## Boundaries

- Hours of minors and personal details stay in the user's workspace; do not add information about anyone that is not in the log.
- Do not use the totals to rank people against each other unless the user asks; the report lists alphabetically.

## Limits

- The script trusts the log. It cannot tell whether a person really attended, only whether the rows agree with each other and with the stated rules.
- Overlap and duplicate checks need start and end times; hours-only rows are checked for the daily cap and for exact repeats only.
- Names that differ by more than the 0.85 ratio, nicknames and married names are not found.
- The 15-minute duplicate window and the outlier rule (3 times the median, 4 hours, 10 shifts) are working values, not measured optima.
- Dates must be ISO; times are 24-hour or with AM/PM. One delimiter per file (`--delimiter`); the file must be UTF-8.
- Future dates are rejected only when `--as-of` is given; without it a mistyped far-future date inside 1990-2100 is accepted.
- Volunteer hours may have rules set by a funder or a regulator; those are outside this skill.
