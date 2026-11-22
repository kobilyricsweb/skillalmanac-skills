---
name: schedule-conflict-check
description: Checks a booking list, staff roster, room timetable or .ics export for clashes and proposes the nearest free slot. Use when the user says check my schedule for clashes, who is double-booked, does this roster break our rest rule, or why do these appointments overlap. A script finds overlaps, buffer and rest-gap breaches, over-capacity rooms, bookings outside opening hours, one client in two places and unassigned slots, as strict JSON. Do not use for meeting times across time zones, task dependency plans, or booking and sending invites.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used and nothing is written. Without Python, follow the manual pass in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Schedule conflict check

Find every clash in a list of bookings that already exists, say which are hard and which are soft, and suggest where the loser could go. The user decides; this skill never edits a calendar, sends a message or moves anything.

## Privacy rule

Only ids, resource names, room names, times and a client code are needed. Ask for no clinical content, reasons for a visit, contact details or real client names; offer a pseudonymous id (`c17`) instead. If the file already holds such columns, ignore them and do not repeat them in the report.

## Workflow

```
- [ ] 1 Get the bookings and the rules
- [ ] 2 Run the script
- [ ] 3 Read rejected rows and unassigned first
- [ ] 4 Walk the conflicts, hard before soft
- [ ] 5 Offer the suggested moves as options
- [ ] 6 Report
```

1. **Collect.** Accept a CSV (`id, resource, room, client, start, end` plus optional `buffer_min, units, fixed, title`; `resource` may be headed provider, staff or person; `room` may be headed location) or an `.ics` file. In `.ics`, the resource is read from `RESOURCES` (or `X-RESOURCE`, or with `--resource-from attendee` from the first `ATTENDEE`), the room from `LOCATION`. Ask only for rules the user has: turnover minutes after a booking, opening hours per resource, breaks, a minimum rest between working days, a daily maximum, room capacities, the list of valid resources and rooms. Do not invent rules. All times must be in one zone; ask for the offset if some carry `Z` or `+02:00` and others do not.
2. **Run** `python scripts/schedule_conflicts.py <bookings> --rules <rules.json>`. Write the rules file from what the user said (shape below). Exit 0 clean, 1 findings, 2 unusable input (message on stderr; fix and rerun). Do not edit the script to make a check pass.
3. **Triage inputs.** `rejected_rows` (end before start, zero length, duplicate id, bad time, seconds present) and `unassigned` (no resource, or no room when `require_room` is true) are data problems: list them first and ask, never guess a resource. `skipped` lists cancelled `.ics` events.
4. **Manual pass without Python.** Sort per resource by start; compare each booking only with the next ones until a start is at or after the end plus buffer. Do the same per room and per client code. Then check opening hours, breaks, rest, daily total and capacity per the table below. State plainly that it was done by hand.
5. **Suggestions.** `suggested_moves` are computed one after another on a working copy, so `order` matters: move 2 assumes move 1 happened. The later-starting booking moves, the nearest slot of the same length wins, ties go to the later slot, and a booking marked `fixed` never moves. `unmovable` lists conflicts with no slot inside `--search-days`. `remaining_after_moves` is what is still wrong after all moves. Present moves as options for the booking owner, never as done.
6. **Report** in the fixed shape below.

## Conflict classes

| type | severity | meaning | fix order |
|---|---|---|---|
| `resource_overlap` / `resource_over_capacity` | hard | two bookings at once for one provider or person (over capacity when the resource has a listed capacity and the summed `units` exceed it) | move the later one; else swap resource |
| `room_overlap` / `room_over_capacity` | hard | same, for a room (units are headcount when the room has a listed capacity) | move the later one; else change room |
| `client_double_booked` | hard | one client code in two places at once | ask the client which stays |
| `outside_hours` | hard | not inside one opening interval of that day, or the day has none; overnight bookings always fail this, so omit `opening_hours` for night resources | move into hours |
| `unknown_resource`, `unknown_room` | hard | name not in the user's list; usually a typo | correct the name, do not move |
| `buffer_breach` | soft | next booking starts after the previous ends but inside its buffer; `shortfall_min` says how much | move, or shrink the buffer only if the user allows |
| `rest_gap` | soft | consecutive bookings of one person on different start dates with less than `min_rest_min` between end and start | move the second one |
| `break_overlap` | soft | booking overlaps a declared daily break | move out of the break |
| `max_daily_exceeded` | soft | booked minutes per start date exceed the limit; no automatic move | user chooses what to drop |
| `spans_midnight`, `dst_change_date`, `recurring_not_expanded` | info | check the real duration; only the first instance of a recurring event was checked | tell the user |

Severity order when listing: hard before soft before info; inside a class, the longest overlap first. A booking that ends exactly when the next starts is not a clash. A boundary exactly equal to the buffer or rest limit passes.

## Rules file

```json
{
  "default_buffer_min": 10,
  "min_rest_min": 660,
  "max_booked_min_per_day": 600,
  "utc_offset": "+02:00",
  "require_room": true,
  "resources": ["DrA", "DrB"],
  "rooms": ["R1", "R2"],
  "capacity": {"rooms": {"Ward": 2}, "resources": {"Van": 3}},
  "opening_hours": {"*": {"mon": [["09:00", "12:00"], ["13:00", "17:00"]]}, "DrB": {"tue": ["10:00", "14:00"]}},
  "breaks": {"*": [["12:00", "13:00"]]},
  "dst_change_dates": ["2026-03-29"]
}
```

Unknown keys are an error, so a typo cannot silently disable a rule. A resource-specific entry replaces `"*"`. A weekday missing from an opening-hours entry means closed. Resources and rooms without a listed capacity hold one booking at a time and ignore `units`. Aware times are converted with the fixed `utc_offset`; real daylight-saving changes are not tracked, so list clock-change dates in `dst_change_dates` and the affected bookings are flagged for a human look.

## Output contract

Strict JSON on stdout, `schema_version` 1: `input_format`, `bookings_used`, `rejected_rows[]` (`row`, `id`, `reason`), `skipped[]`, `conflicts[]` (`type`, `severity`, `ids`, `resource`, `room`, `client`, `start`, `end`, `overlap_min`, `shortfall_min`, `excess_min`, `detail`; fields that do not apply are null), `unassigned[]` (`id`, `missing`), `suggested_moves[]` (`order`, `id`, `from_start`, `to_start`, `to_end`, `shift_min`, `resolves`), `unmovable[]`, `remaining_after_moves` (`hard`, `soft`, or null with `--no-suggest`), `free_slots{}` per resource (only where opening hours apply; slots of `--min-free` minutes or more, computed before any move, each booking blocking its own buffer), `summary` (`hard`, `soft`, `info`, `unassigned`, `rejected`, `verdict`), `notes[]`. Times are local `YYYY-MM-DDTHH:MM`.

## Report shape

```
Checked: <n bookings, format, rules applied>
Hard: <count and each conflict in one line: ids, what, minutes>
Soft: <count and lines>
Data problems: <rejected rows, unassigned, unknown names>
Options: <moves as "booking X could go to ..." with the order caveat>
Still open after moves: <remaining_after_moves, unmovable>
Not checked: <rules not supplied, recurring events, daylight saving, time zones, anything outside the file>
```

## Limits

- Only what is in the file is checked; a rule the user did not state is not applied, and the report says which rules were absent.
- Recurring events are not expanded; exceptions (`EXDATE`) and overrides are ignored.
- Several `TZID` values in one file are refused; convert to one zone first. A `TZID` is read as wall-clock time, with no clock-change logic.
- Suggestions are greedy and local: they respect the same checks except the daily maximum, are not optimal, and ignore preferences such as "keep it before lunch".
- Seconds in a time are refused, not rounded. Names are compared exactly, so `Dr A` and `Dr. A` are different resources; point such cases out instead of merging them.
- This is admin checking only. It gives no clinical, legal or labour-law view on whether a rest or hours rule is the right one; the thresholds come from the user.
