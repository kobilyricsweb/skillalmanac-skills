# timezone-overlap-planner: listing

**One-line summary:** Ranked meeting windows, DST warnings and a fair rotation for people working in different time zones.

## What it does

The user (or the agent for them) lists people with IANA zones, working hours, days off and holidays, plus a date range and meeting length. `scripts/overlap_windows.py` tries every start time in steps across each date, converts the meeting into every person's own wall clock with `zoneinfo`, and judges it against their shift (shifts that cross midnight are supported). Slots are grouped into windows, ranked by how many people are inside hours and how big the worst cost is, and a greedy rotation spreads the cost of the awkward slot across the dates. It also lists the dates on which a person's UTC offset changes and the pairs whose gap changes, which is what breaks a recurring meeting.

## Capabilities

- Per-date windows with the person-by-person local start, end, margin and cost, as strict JSON.
- Quality tiers: all inside, edge, one outside, several outside, day off.
- DST drift: `dst_changes` per person and `relative_offset_shifts` per pair.
- Rotation plan with running cost per person and a fairness score.
- Rejects abbreviations (IST, CST, PST and similar) with the candidate cities; reports unknown zones and a missing tz database.
- `check-zones` to validate names before collecting hours.

## When to use

- A team or a freelancer pair in two or more countries needs a recurring slot.
- Someone asks "is our call still fine after the clocks change".
- There is no common working time and the team wants the least bad slot with the cost shown.

## When not to use

- Booking a room, sending invites or polling availability (nothing here touches a calendar).
- Converting one clock time: use a plain converter.
- Scheduling shifts for a support rota: that is capacity work, not window finding.

Differences from nearby skills: `ask-to-slot`, `capacity-slot-allocation-table` and `meeting-agenda-timebox-check` do not model time zones; this skill's whole job is the zone and DST arithmetic.

## Requirements

Python 3.9 or newer, standard library only, no network. IANA zone names need the tz database: Linux and macOS have it; on Windows the user installs the PyPI package `tzdata` in their own environment (the skill never installs anything). Without it the script runs only when every person has a fixed `utc_offset`, and warns that DST is not tracked.

## Install

Copy the folder to `.claude/skills/timezone-overlap-planner/` or `.agents/skills/timezone-overlap-planner/`. Pinned version and commit: to be set at publication.

## Example 1: no common working time

Prompt: "Ana is in New York and Ken is in Tokyo, both 09:00 to 17:00. A 60 minute call on Monday 2 February 2026: what is the least bad slot, and who pays?"

Real output (`evals/fixtures/ny_tokyo.json`, first date, abridged to the fields that matter):

```
best_quality: one_outside
window 1: best start 2026-02-02T21:00:00Z   Ana 16:00-17:00 New York (edge, cost 15)   Ken 06:00-07:00 next day Tokyo (outside, cost 180)
window 2: best start 2026-02-03T00:00:00Z   Ana 19:00-20:00 New York (outside, cost 180)   Ken 09:00-10:00 Tokyo (edge, cost 15)
rotation over Mon-Thu: slot 1, slot 2, slot 1, slot 2 -> total cost Ana 390, Ken 390, fairness_score 1.0
```

## Example 2: a DST change in the range

Prompt: "Ana (New York) and Liam (London), both 09:00 to 17:00, 60 minutes, 2 to 13 March 2026. Is a fixed time safe?"

Real output (`evals/fixtures/ny_london_dst.json`): the only all-inside start on 2 March is 10:00 New York (15:00Z); from 9 March the window is 10:00 to 11:00 New York (14:00Z to 15:00Z); `dst_changes` shows New York moving from -05:00 to -04:00 on 2026-03-08, and `relative_offset_shifts` shows the Ana/Liam gap changing from -300 to -240 minutes that day. Exit code 1 (finding). London's own change on 29 March is outside this range.

## Limits

- Public holidays and weekends come only from the user; no holiday data is shipped.
- A DST change inside a single meeting is not adjusted.
- Preferences are not modelled; they must be turned into days off or narrower hours.
- Costs are working values, not measured preferences. The tz data may lag a very recent government change.
- One meeting length per run, at most 20 people and 366 days.

## Evidence

| Stage | Result |
|---|---|
| Static lint | 0 FAIL, 0 WARN (see VERIFICATION.md) |
| Script fixtures | 11 of 11 pass; expected values worked out by hand |
| Trigger test, task evals, cross-tool, human review | not run |

## Demo script (about 75 seconds)

1. Prompt: "Team in Berlin, Chicago and Bengaluru, weekly 45 minute sync, week of 13 April 2026."
2. The agent checks zones, writes the input file and runs `plan`.
3. It reports that Bengaluru and Chicago share no working time (best quality one_outside every day) and shows the two least bad slots with minutes of cost.
4. It shows the rotation: the awkward slot alternates between Priya and Carla; Jonas in Berlin is never outside hours.
5. It asks the user to confirm weekends and holidays, since none were supplied.

## FAQ seeds

1. Does it need network? No.
2. Does it work on Windows? Yes, if the `tzdata` package is installed; otherwise only with fixed offsets and without DST tracking.
3. Why does it refuse "IST"? Because it names three different rule sets.
4. Does it read my calendar? No; it only reads the JSON you give it.
5. How is it different from a time converter? It judges whole working days per date and warns when DST moves the overlap.
6. How do I uninstall? Delete the folder.
7. What if someone works Friday to Sunday? Set `days_off` for that person.

## Changelog

0.1.0, 2026-11-21: first draft; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
