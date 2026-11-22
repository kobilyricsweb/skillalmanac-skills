# Listing page content: schedule-conflict-check

**One line:** Finds clashes, buffer and rest-gap breaches and unassigned slots in a booking list, roster or .ics file, and proposes the nearest free slot.

## What it does

A bundled script reads a CSV or an iCalendar subset plus an optional rules file, sorts bookings per provider, room and client, and finds overlaps with an interval sweep that also handles capacity (summed headcount against a listed limit). It then checks turnover buffers, a minimum rest between working days, a daily maximum, opening hours, daily breaks, unknown resource or room names and missing assignments. Each finding has a class and a severity (hard, soft, info). For the later booking in each fixable clash it searches the nearest slot of the same length that passes every check, working through the schedule one move at a time on a working copy. Nothing is written, sent or booked.

## Capabilities

- `scripts/schedule_conflicts.py`: strict JSON with conflicts, rejected rows, unassigned slots, ordered move suggestions, what remains after the moves, and free slots per resource
- Reads CSV (flexible headers) and `.ics` (`UID`, `DTSTART`, `DTEND`/`DURATION`, `RESOURCES`, `LOCATION`, `STATUS`, `RRULE` flagged)
- Rules file with strict key checking, so a typo cannot silently turn a rule off
- A conflict-class table with severity and fix order, and a fixed report shape that ends with what was not checked

## How it differs from nearby skills

`timezone-overlap-planner` finds a good meeting time across zones and `critical-path-planner` computes task timing from dependencies; this skill takes bookings that already exist and finds where they collide: people, rooms and clients, buffers, rest rules, capacity, unassigned slots.

## When to use

You have a booking list, shift roster, room timetable or calendar export and say check it for clashes, who is double-booked, does it break our rest rule, which slots are unassigned.

## When not to use

Picking a time for people in several time zones, planning tasks and dependencies, building a rota from nothing, booking or inviting anyone, or deciding whether a rest or hours rule is legally required.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the manual pass in the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both outputs are from `python scripts/schedule_conflicts.py` on the saved fixtures.

1. `schedule_conflicts.py evals/fixtures/roster.csv --rules evals/fixtures/roster_rules.json` (exit 1): `room_over_capacity` for s1, s3 and s4 from 2026-03-02T15:00 to 21:00 (360 min, Ward limit 2); `rest_gap` for Ana between s1 and s2 (480 min against 660, 180 short); `max_daily_exceeded` for Dee (120 min over); s5 listed as having no room. Moves: s4 to 08:00 on 2 March, then s2 to 10:00 on 3 March.
2. `schedule_conflicts.py evals/fixtures/clinic.csv --rules evals/fixtures/clinic_rules.json` (exit 1): 8 hard and 2 soft conflicts, b8 unassigned, b10 rejected (end before start); five moves proposed (for example b11, a Saturday booking, to Monday 2026-03-09T09:00); b7 (fixed) and b9 (unknown provider) remain, so `remaining_after_moves` is 2 hard, 0 soft.

## Limits

- Only the supplied file and rules are checked; recurring events are not expanded and daylight saving is not tracked (clock-change dates can be listed to flag bookings).
- Suggestions are greedy, local and not optimal; the daily maximum has no automatic move.
- Seconds in times are refused; names are matched exactly.
- Admin checking only; no clinical, legal or labour-law advice.

## Evidence

See `VERIFICATION.md`. Static lint passed with 0 FAIL and 0 WARN and 10 of 10 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Drop in a clinic CSV and say the opening hours and the 10 minute turnover.
2. The script runs: 8 hard, 2 soft, one unassigned, one rejected row.
3. The agent walks the hard clashes first and lists the moves in order, with the caveat that move 2 assumes move 1.
4. The agent ends with what it did not check: recurring bookings, daylight saving, rules not stated.

## FAQ seeds

- Does it change my calendar or send anything? No; it only reads files and prints a report.
- Do I have to give client names? No; use codes. It asks for no reasons for visits.
- Does it handle recurring events? Only the first instance; it says so.
- What about time zones and daylight saving? One zone per file; clock-change dates you list are flagged, nothing is adjusted.
- Does it work in other tools? It is plain Markdown and Python; no cross-tool run has been done yet.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
