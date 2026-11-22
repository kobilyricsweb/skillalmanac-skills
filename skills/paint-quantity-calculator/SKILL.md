---
name: paint-quantity-calculator
description: Estimates how many gallons of wall paint a room needs from its length, width, height, door and window counts, coat count and coverage per gallon, and prints the arithmetic step by step. Use when a homeowner or painter asks how much paint to buy for one room, or wants to check a paint estimate for openings, coats and waste. Do not use for ceilings, trim, exterior surfaces, multi-room projects with mixed finishes, paint color choice, or product recommendations.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Paint Quantity Calculator

Estimates wall paint for one rectangular room. The script does the arithmetic; the agent collects inputs, runs the script, and reports its output without changing a number.

## Workflow

1. **Confirm the room is a rectangle with flat walls.** Required output: a one-line room description (for example "12 x 10 x 8 ft, walls only"). If the job is a ceiling, trim, an exterior, or a non-rectangular room, stop (see Refuse / stop when).
2. **Collect required intake.** Required fields: `units` (`ft` or `m`), `length`, `width`, `height`, `doors`, `windows`, `coats`. Required output: a list of each value with its unit. Missing any field: stop and return the numbered question list described below.
3. **Collect optional intake.** Fields: `door_area`, `window_area`, `coverage`, `waste_percent`, `rounding`. Use the defaults in the decision table when the user gives no value. Required output: each optional field marked `user` or `default`. Use the product label coverage figure as `coverage` when the user has one.
4. **Write the intake as JSON** to `<input-file>` (one object, UTF-8). Required output: the file path and its keys. Do not add keys the script does not list in the input table.
5. **Run the script** with `python -I scripts/paint.py <input-file>`. Required output: the exit code. Follow the exit code rules in the exit table.
6. **Report the output.** Copy the script report lines verbatim, in order, into the reply. Do not recompute, round, or re-label any value. Required output: the report block, then one sentence naming the gallons to buy.
7. **Handle findings.** If the status line reads `findings (N)`, list each `finding:` line, ask the user to confirm the measurements, and do not state a final purchase amount until they do.

## Decision and threshold table

| Item | Value | Basis |
|---|---|---|
| Default door area | 21 sq ft (1.95 sq m) | working value, 3 ft x 7 ft |
| Default window area | 15 sq ft (1.39 sq m) | working value, 3 ft x 5 ft |
| Default coverage | 350 sq ft per gallon (32.5 sq m per gallon) | working value |
| Default waste | 10 percent | working value |
| Coats | whole number, 1 to 4 | input limit |
| Doors and windows | 0 to 50 each (whole numbers) | input limit |
| Waste percent | 0 to 50 | input limit |
| Length, width, height | greater than 0 up to 200 units | input limit |
| Openings limit (F1) | openings above 50 percent of gross wall area | working value |
| Wall height range (F2) | 6 to 20 ft (about 1.83 to 6.10 m) | working value |
| Rounding `half` (default) | up to the next 0.5 gallon | rule |
| Rounding `whole` | up to the next whole gallon | rule |

Formula, in the order the script applies it:

- gross wall area = 2 x (length + width) x height
- openings = doors x door area + windows x window area
- net wall area = gross wall area - openings (must be greater than 0)
- coated area = net wall area x coats
- total = coated area x (1 + waste_percent / 100)
- gallons exact = total / coverage
- gallons to buy = gallons exact, rounded up per the rounding rule

## Script contract (type A)

Command line: `python -I scripts/paint.py <input-file>`. One argument only. The script reads the file, writes nothing, and never opens a network connection.

Input keys: `units` (required), `length`, `width`, `height`, `doors`, `windows`, `coats` (all required), and optional `door_area`, `window_area`, `coverage`, `waste_percent`, `rounding`. Any other key is an error.

Input limits: file at most 2 MB, UTF-8, one JSON object.

Output on exit 0 or 1 (stdout), in this fixed order: the header line `paint-quantity-calculator 0.1.0`, then `units:`, `gross_wall_area:`, `door_area_each:`, `window_area_each:`, `openings:`, `net_wall_area:`, `coats:`, `coated_area:`, `waste:`, `coverage:`, `gallons_exact:`, `gallons_to_buy:`, one `finding:` line per finding, and finally `status:`.

| Exit code | Meaning | Output |
|---|---|---|
| 0 | Report produced, no findings | stdout report, `status: ok` |
| 1 | Report produced, one or more findings | stdout report, `finding:` lines, `status: findings (N)` |
| 2 | Usage or input error | one JSON line on stderr: `{"error": "<CODE>", "detail": "<text>"}` |

Error codes on exit 2: `E_USAGE` (wrong argument count), `E_MISSING_FILE`, `E_READ`, `E_TOO_LARGE` (over 2 MB), `E_INVALID_UTF8`, `E_INVALID_JSON`, `E_FIELD` (missing, unknown, wrong type, or out-of-range field, including bad `units` or `rounding`), `E_GEOMETRY` (openings equal or exceed gross wall area).

Finding codes on exit 1: `F1 OPENINGS_OVER_HALF`, `F2 HEIGHT_OUT_OF_RANGE`.

## Output contract for the reply

Reply with these headings, in this order:

1. `## Room` with the room description and units.
2. `## Calculation` with the report block copied verbatim inside a code fence.
3. `## Gallons to buy` with one sentence: "Buy N.NN gallons (rounding: half)" using the `gallons_to_buy` value.
4. `## Findings` with the `finding:` lines, or the words "No findings."

## Stop and ask rules

Missing required intake: return a numbered question list, one question per missing field, for example "1. What is the room length, in feet?" Do not run the script with guessed values.

## Refuse / stop when

- The job is a ceiling, trim, exterior wall, cabinet, or any surface other than flat interior walls of one room.
- The room is not rectangular, or the user gives several rooms at once. Run one room per file.
- The script returns `E_GEOMETRY`. Ask the user to re-measure the doors and windows, and do not reduce the openings yourself.
- The script returns `F1` or `F2`. Report the finding and wait for the user to confirm the measurements before stating a final amount.
- The user asks which paint color, brand, or sheen to buy. This skill only computes quantity.
- The user asks for a coverage claim beyond the product label they supply. Use only the figure they give, or the default, and label it.

## Files shipped

- `scripts/paint.py`: the calculator described above.
- `fixtures/sample-room.json`: 12 x 10 x 8 ft room, 1 door, 2 windows, 2 coats. Exit 0.
- `fixtures/tall-room-findings.json`: 20 x 20 x 24 ft room with coverage and whole-gallon rounding. Exit 1 with F2.
- `LICENSE.txt`: Apache License 2.0 text.

Smoke run on the sample fixture: `python -I scripts/paint.py fixtures/sample-room.json`.
