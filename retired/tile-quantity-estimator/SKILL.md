---
name: tile-quantity-estimator
description: Estimates floor tile count, order count, box count and leftover tiles from room length and width, tile size, grout gap, layout and waste percent. Use when someone is planning a rectangular floor tile job and needs to know how many tiles and boxes to buy, for straight or diagonal layouts, or when a tile order must be checked against a waste allowance before purchase. Do not use for wall tile, countertops, mosaic or irregular rooms with cutouts, tile cost or pricing, or advice on setting, grout or substrate preparation.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Tile quantity estimator

Use `scripts/tiles.py` to compute tiles and boxes for one rectangular floor. Do the arithmetic only in the script. Do not estimate tile counts by hand.

## Workflow

1. **Collect intake.** Required: room length (ft), room width (ft), tile length (in), tile width (in), layout (`straight` or `diagonal`), tiles per box (integer). Optional: grout gap (in, default 0) and waste percent (default 10 straight, 15 diagonal). Output: an intake table with one row per value and its unit.
2. **Check the intake against the decision table below.** If a required value is missing, stop and follow the stop rule. Output: a pass or a stop.
3. **Write the input file.** Save a JSON object with the keys in the next section to `<input-file>`. Do not edit `fixtures/` files. Output: the path of the saved file.
4. **Run the script.** Command: `python -I scripts/tiles.py <input-file>`. Output: the JSON result on stdout, and the exit code.
5. **Branch on the exit code.** Exit 0 means report. Exit 1 means report and show the finding. Exit 2 means stop and fix the input file. Output: one of the three outcomes in the exit table.
6. **Write the answer in the output contract.** Output: the four sections in the contract, with the numbers copied from the JSON without rounding.

## Input file keys

| Key | Type | Rule | Default |
|---|---|---|---|
| `room_length_ft` | number | greater than 0 | none, required |
| `room_width_ft` | number | greater than 0 | none, required |
| `tile_length_in` | number | greater than 0 | none, required |
| `tile_width_in` | number | greater than 0 | none, required |
| `layout` | string | `straight` or `diagonal` | none, required |
| `tiles_per_box` | integer | 1 or more | none, required |
| `gap_in` | number | 0 or more | 0 |
| `waste_pct` | number | 0 to 100 | 10 straight, 15 diagonal |

Any other key makes the script exit 2. Keep the key names exact.

## Decision and threshold table

| Item | Value | Status |
|---|---|---|
| Straight-layout waste minimum | 10 percent | working value |
| Diagonal-layout waste minimum | 15 percent | working value |
| Waste below the minimum for the layout | finding `WASTE_BELOW_MINIMUM`, exit 1 | working value |
| Waste above 100 or below 0 | exit 2 | rule |
| Gap below 0 | exit 2 | rule |
| Tiles per box below 1, or not an integer | exit 2 | rule |
| Room side used in the count | feet times 12, to inches | rule |
| Waste tiles | ceiling of base tiles times waste percent, divided by 100 | rule |
| Boxes | ceiling of order tiles divided by tiles per box | rule |

Diagonal layout changes only the default waste percent (15 vs 10). The count itself is the same grid count with no diagonal cut allowance; treat 15 percent as a working value and ask the installer.

## Exit codes and findings

| Exit | Meaning | Action |
|---|---|---|
| 0 | Result with no findings. `status` is `ok`. | Report the result. |
| 1 | Result with findings. `status` is `findings`. | Report the result and show each finding. Recommend the layout default. |
| 2 | Usage or input error. A one-line JSON object `{"error": "..."}` is on stderr. | Stop. Name the error and ask the user for a corrected input. Do not estimate by hand. |

| Finding code | Trigger | Action |
|---|---|---|
| `WASTE_BELOW_MINIMUM` | `waste_pct` is below 10 for straight or below 15 for diagonal | Say the order may run short. Offer to rerun with the default waste. |

## Output contract

Use exactly these four headings, in this order.

**## Quantity** - a table with columns `Item` and `Value`. Rows, in this order: Columns, Rows, Base tiles, Waste percent, Waste tiles, Order tiles, Tiles per box, Boxes, Leftover tiles. Copy each value from the JSON keys `columns`, `rows`, `base_tiles`, `waste_pct`, `waste_tiles`, `order_tiles`, `tiles_per_box`, `boxes`, `leftover_tiles`.

**## Arithmetic** - the eight lines of the `arithmetic` array, verbatim, as a bulleted list.

**## Findings** - one bullet per entry in `findings`, as `CODE: detail`. Write `None` if the array is empty.

**## Assumptions** - three bullets: grout gap in inches, waste percent and its source (default or user value), and the layout.

## Refuse or stop when

- Any required key is missing. Stop. Return a numbered list of the missing items, for example "1. Room length in feet", and wait for the answer.
- The room is not a rectangle, or has a cutout or an alcove. Stop. This script covers one rectangle only.
- The user gives units other than feet for the room or inches for the tile. Stop and ask for a conversion to feet and inches.
- The script exits 2. Stop and report the error message.
- The user asks for tile prices, delivery, or setting advice. Decline and state that this skill only counts tiles and boxes.

## Script contract

- Command: `python -I scripts/tiles.py <input-file>`
- Argument: one path to a UTF-8 JSON file of at most 2 MB, containing one JSON object.
- Stdout on exit 0 or 1: one JSON object with keys `status`, `layout`, `columns`, `rows`, `base_tiles`, `waste_pct` (a string), `waste_tiles`, `order_tiles`, `tiles_per_box`, `boxes`, `leftover_tiles`, `arithmetic`, `findings`.
- Exit 0: no findings. Exit 1: at least one finding. Exit 2: usage, read, encoding or JSON error, or a validation error.
- The script only reads the input file. It writes nothing, opens no network connection, and runs no subprocess.

## Shipped files

- `scripts/tiles.py`: the estimator script described above.
- `fixtures/smoke_diagonal.json`: a 10 by 8 ft floor with 12 by 12 in tiles, 8 per box, diagonal layout, default waste. Exit 0.
- `fixtures/short_waste_straight.json`: the same floor with a 0.125 in gap, straight layout, and 5 percent waste. Exit 1 with `WASTE_BELOW_MINIMUM`.
- `LICENSE.txt`: the Apache-2.0 license text.
