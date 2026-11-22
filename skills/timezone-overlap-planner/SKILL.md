---
name: timezone-overlap-planner
description: Finds meeting times across time zones. Use when the user asks for overlap hours, the best time for a call with people in several countries, who should take the early or late slot, or whether daylight saving breaks a recurring meeting. Converts each person's IANA-zone working hours per date, ranks windows by who is inside hours and by fairness, warns of DST changes in a date range, plans a rotation, and prints strict JSON from a script. Do not use for calendar booking, sending invites, availability polls, or converting one single time.
license: Apache-2.0
compatibility: Needs Python 3.9 or newer, standard library only, no network. IANA zone data comes from the tz database; on Windows that needs the PyPI package tzdata installed by the user. Without it the script runs only on fixed utc_offset values and says DST is not tracked.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Timezone overlap planner

Turn a list of people, their zones and working hours into ranked meeting windows for each date, with DST warnings and a rotation. The arithmetic is done by `scripts/overlap_windows.py`; do not do it by hand, because the common errors (DST gap weeks, shifts that cross midnight, weekends that differ by country) are exactly the ones mental conversion gets wrong.

## Workflow

```
- [ ] 1 Collect and clean the inputs
- [ ] 2 Check zone names
- [ ] 3 Write the input file
- [ ] 4 Run the planner
- [ ] 5 Read the findings in order
- [ ] 6 Report
```

1. **Collect.** For every person: a name, an IANA zone (`Area/City`), working hours, days off, and holidays that fall in the range. Also the date range, the meeting length, and whether it is one meeting or a recurring one. Ask only for what is missing. Do not guess a zone from a country; a country with several zones needs a city.
2. **Check zones.** Abbreviations are refused until the user names a city. Run `python scripts/overlap_windows.py check-zones <names...> --date <a date in the range>`; it returns `ok`, `ambiguous_zone`, `unknown_zone` or `no_tz_database` per name. Candidates for common abbreviations (IST, CST, BST, PST, EST and others) are in [references/zones-and-dst.md](references/zones-and-dst.md), section 1; read it only when a name is rejected or ambiguous.
3. **Write the input** to a new JSON file (never over a user file):

```json
{
  "start_date": "2026-03-02", "end_date": "2026-03-13",
  "meeting_minutes": 60, "step_minutes": 30,
  "holidays": ["2026-03-05"],
  "participants": [
    {"name": "Ana", "zone": "America/New_York", "work_start": "09:00", "work_end": "17:00",
     "days_off": ["sat", "sun"], "holidays": []},
    {"name": "Ravi", "zone": "Asia/Kolkata", "work_start": "22:00", "work_end": "06:00"}
  ]
}
```

   Optional keys: `anchor_zone` (a participant's zone; dates and candidate start times follow it, default the first person), `meeting_dates` (restrict the rotation to these dates), `rotation_slack_minutes` (default 120), `utc_offset` per person (only for the no-database fallback), `holidays` at top level for company-wide days. A shift with `work_end` earlier than `work_start` wraps past midnight; `24:00` is allowed as an end. If hours are omitted the script assumes 09:00 to 17:00 and warns; say so in the report. Use `step_minutes` 15 when anyone is in a :45 zone.
4. **Run.** `python scripts/overlap_windows.py plan input.json` (add `--out report.json` to save; it never overwrites the input and refuses an existing output without `--force`). Exit 0 clean, 1 findings, 2 bad input (the JSON says why: `ambiguous_zone`, `unknown_zone`, `no_tz_database`, `bad_time`, `bad_date`, `output_is_input`, ...). Fix the input; never edit the script to get a pass.
5. **Read in this order**: `warnings`, `relative_offset_shifts` and `dst_changes`, then each `dates[].windows[]`, then `rotation_plan`.
6. **Report** in the shape at the end.

## Output contract (strict JSON on stdout, `schema_version` 1)

| Key | Content |
|---|---|
| `inputs` | echo of the cleaned participants, `tz_database` (`available` or `missing`), `edge_minutes` |
| `warnings[]` | `code` and message: `default_hours_used`, `fixed_offset_no_dst_tracking`, `etc_gmt_sign_inverted` |
| `dates[]` | per anchor-zone date: `status` (`all_working`, `some_off`, `everyone_off`), `best_quality`, `windows[]` (top 3), `dst_changes_today[]` |
| `windows[]` | `quality`, `least_bad`, `earliest_start_utc`, `latest_start_utc` (the run of acceptable starts), `best_start_utc`, `best_end_utc`, `people_inside`, `pain_by_person`, `local_times_by_person` (start, end, status, margin, shortfall) |
| `dst_changes[]` | the date each person's UTC offset changes, from, to, minutes |
| `relative_offset_shifts[]` | pairs whose gap changes on a date: the DST-drift warning that matters |
| `rotation_plan` | `slots[]` per eligible date, running `cumulative_pain_by_person`, `total_pain_by_person`, `fairness_score`, `skipped_dates[]` |

## Decision tables

Window quality (the best slot of a run, in rank order; a person is inside if the whole meeting fits in a working shift):

| Quality | Rule | What to tell the user |
|---|---|---|
| `all_inside` | everyone inside and at least 60 minutes from both edges of their day | Offer first |
| `edge` | everyone inside, someone has under 60 minutes of margin (first or last hour) | Fine, mention who is on the edge |
| `one_outside` | exactly one person outside hours | Name them and the minutes; this is the person to rotate |
| `several_outside` | two or more outside | Say there is no fair slot; show the cost per person |
| `day_off` | someone is on a day off or holiday, or inside an off-day shift | Never offer silently; move the date |

Cost per person ("pain", minutes): 0 when inside with 60 or more minutes of margin; a quarter minute per missing margin minute when inside but under 60 (`edge`); otherwise the minutes the meeting would have to move to fit a shift; 1440 on a day off or holiday. The numbers are working values, not measured preferences.

Fairness: across the dates, each date picks, among slots of its best quality whose worst cost is within `rotation_slack_minutes` of the best, the one that keeps the largest running total lowest. When two people alternate, expect the slot to switch sides each date. `fairness_score` is 1.0 when everyone who bears any cost bears the same, lower as the gap grows; one person bearing everything scores 0. People who never pay (usually the middle zone) are not counted as unfairness, but name them in the report.

Dates in the plan are anchor-zone calendar dates; each local time in `local_times_by_person` is exact. A recurring meeting fixed at one UTC time is not what the plan gives: it gives a local-clock slot, and the offset shifts show when a fixed UTC time moves.

## Report format

```
Windows: <per date or pattern: best window in each person's local time, quality>
Awkward slot: <who, how many minutes outside, and the rotation>
DST: <dates where a gap changes, in the participants' own zones, and what moves>
Assumptions: <default hours, weekends, holidays supplied, fixed offsets used>
Not checked: <public holidays not supplied, personal preferences, real calendars, daylight changes after the tz data was issued>
```

Give times as `Mon 10 Mar 09:00 America/New_York`, not as an abbreviation.

## Scripts

- `scripts/overlap_windows.py plan`: run it. Reads one input file; writes only the `--out` file if asked.
- `scripts/overlap_windows.py check-zones`: run it before collecting hours.
- Testing hook `--simulate-no-tzdb` (before the sub-command) forces the missing-database path; users never need it.

If Python cannot run, do the manual fallback: get each person's UTC offset for the specific dates from a trusted source, convert both ends of the working hours to UTC, intersect, and check the dates around each spring and autumn change from [references/zones-and-dst.md](references/zones-and-dst.md), section 2. Say that the result is unchecked by script.

## Limits

- Public holidays and weekends are not in any database; only what the user supplies is used.
- Local time during a DST change inside a single meeting is not adjusted; meetings at 02:00 on a change night are skipped or approximate.
- Preferences (no calls on Friday afternoon, school runs, religious observance) are not modelled; ask, and turn them into `days_off` or narrower hours.
- The tz database in use may be older than a government's latest decision; if a result looks odd for a recently changed zone, say which data was used.
- It plans one meeting length per run, scans anchor-zone start times in `step_minutes` steps, and handles at most 20 people and 366 days.
