---
name: floor-plan-clearance-check
description: Checks a furniture layout in a rectangular room against working-value walkway clearances, door swing zones and item overlaps. Use when a user gives the room width and length, item positions and door positions and asks whether furniture blocks a door, a path or another piece. Do not use for building-code, fire-egress or accessibility compliance, for generating a floor plan from a prompt or photo, or for rooms with curved or irregular walls.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Floor plan clearance check

This skill runs [scripts/clearance.py](scripts/clearance.py) on a JSON description of one rectangular room. It reports items outside the room, overlapping items, items inside a door swing zone, items inside a 36 in main-path corridor, and gaps below the minimums. The 36 in and 24 in values are working values chosen for this skill. The result is a layout geometry check, not a building-code check, and every report must say so.

## Coordinate rules

- The origin is the north-west corner. x grows east and y grows south.
- Walls: north is y = 0, south is y = length, west is x = 0, east is x = width.
- An item is its north-west corner (x, y) plus w along x and d along y.
- A door offset counts from the start of its wall: from the west end on north and south walls, from the north end on east and west walls.

Input shape:

```
{"room": {"width": 144, "length": 120},
 "items": [{"name": "sofa", "x": 30, "y": 10, "w": 84, "d": 36}],
 "doors": [{"wall": "north", "offset": 20, "width": 32}]}
```

Input limits: file at most 2 MB, at most 300 items, at most 20 doors, item name 1 to 80 characters, room width and length above 0, item w and d above 0, door width above 0, and offset plus width no more than the wall length. Item x and y may be negative; the script then reports out_of_bounds.

## Workflow

1. **Collect intake.** Required facts: room width and length in inches; for each item a name, x, y, w and d; for each door a wall, an offset and a width. Output: the list of facts received and the list of facts missing. If any are missing, stop (see Refuse / stop when).
2. **Write the input file.** Save the facts as JSON with the keys `room`, `items` and `doors` to `<input-file>`, a file name that does not exist yet. Output: the path of the input file.
3. **Run the script.** Command: `python -I scripts/clearance.py <input-file>`. Output: the exit code, plus the findings JSON on standard output or the error JSON on standard error.
4. **Branch on the exit code.** 0 means no violations, so report a clean layout. 1 means findings, so go to step 5. 2 means an input or usage error: fix the input from step 2, rerun once, and if it fails again report the error and stop. Output: one status line.
5. **Describe each violation.** Make one table row per entry in `violations`, copying code, items, door, distance and required values exactly. Do not recompute them. Output: the report table.
6. **Propose one fix per violation** using the fix rule table below. Output: the fixes listed under the table. A fix that is not rechecked is marked "rerun to confirm".

## Check rules and working values

| Code | Rule | Required (in) | Basis |
|---|---|---|---|
| `out_of_bounds` | Any part of an item lies outside the room | 0 | geometry |
| `overlap` | Two items share positive area | 0 | geometry |
| `door_swing_blocked` | An item enters a door swing zone: the opening span times a depth equal to the door width | 0 | rule of this skill |
| `main_path_blocked` | An item enters the 36 in corridor centered on a door opening and running from the wall to the far wall | 36 | working value |
| `main_path_narrow` | A gap between two items lies inside a main-path corridor and is under 36 in | 36 | working value |
| `secondary_gap_narrow` | A gap between two items lies outside every main-path corridor and is under 24 in | 24 | working value |

Gaps are measured only between two items that overlap in one axis and face each other across the other axis. Diagonal pairs are not measured. Items are not measured against walls; only items inside a door corridor or swing zone are reported against a door.

## Fix rule table

| Code | Fix to propose |
|---|---|
| `out_of_bounds` | Move the item inward by `distance_in`. |
| `overlap` | Move one item by `depth_in` along the axis with the smaller overlap. |
| `door_swing_blocked` | Move the item so it clears the opening span, or move it so its near edge is at least the door width from the door wall. |
| `main_path_blocked` | Move the item sideways out of the corridor by `depth_in`. |
| `main_path_narrow` | Move one item away from the other by 36 minus `distance_in`. |
| `secondary_gap_narrow` | Move one item away from the other by 24 minus `distance_in`. |

## Output contract

Standard output (exit 0 or 1) is one JSON object with these keys:

- `scope`: fixed text, "working-value layout check, not a building-code check".
- `status`: `ok` or `findings`.
- `room`: `width` and `length` as floats.
- `violation_count`: the length of `violations`.
- `violations`: a list. Each entry has `code`, `items` (a list of names), `door` (1-based door number, or null), `distance_in`, `required_in`, `depth_in` (set for overlap, door and corridor codes, else null) and `message`.

Standard error (exit 2) is one JSON object: `{"status": "error", "error": "<one line>"}`.

The report to the user is a Markdown table with the columns `#`, `Code`, `Items`, `Door`, `Distance (in)`, `Required (in)` and `Fix`, followed by the scope line and the violation count.

## Command and exit codes

Command: `python -I scripts/clearance.py <input-file>`

| Exit | Meaning |
|---|---|
| 0 | No violations |
| 1 | One or more violations |
| 2 | Usage error, missing file, file over 2 MB, invalid UTF-8, invalid JSON, or a field outside the input rules |

## Refuse / stop when

- Any intake fact is missing: stop and return a numbered question list that covers only the missing facts.
- The user asks whether the layout meets a building, fire, egress or accessibility code. Refuse: this check does not decide code compliance.
- Dimensions are in centimeters or meters: stop and ask the user to confirm the figures in inches before converting.
- The room is not rectangular, a wall is not straight, or a door is not on one of the four walls: stop, because the script cannot model it.
- The input exceeds 2 MB, 300 items or 20 doors: stop and ask the user to split the room or remove items.
- The user asks to overwrite an existing input or output file: refuse. The script never writes files.
- The script exits 2 twice on the same input: report the error and stop.

## Shipped files

- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
- [scripts/clearance.py](scripts/clearance.py): the checker.
- [fixtures/smoke_room.json](fixtures/smoke_room.json): a 144 by 120 in room with a sofa over a north door and an overlapping table. Expected: 5 violations, exit 1.
- [fixtures/clean_room.json](fixtures/clean_room.json): a room with no violations. Expected: exit 0.
- [fixtures/bad_door_input.json](fixtures/bad_door_input.json): a door that does not fit its wall. Expected: exit 2.
