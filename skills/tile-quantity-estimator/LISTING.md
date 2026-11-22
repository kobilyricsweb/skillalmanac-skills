# Tile quantity estimator

## One line

Counts the tiles, boxes and leftover tiles for one rectangular floor, with grout gap and a waste allowance that depends on straight or diagonal layout.

## What it does

The skill takes the room length and width in feet, the tile length and width in inches, the grout gap, the layout, and the number of tiles in a box. It converts the room to inches, works out how many tiles fit along each side including the gap, and multiplies the two counts to get the base tile number. It then adds a waste allowance, rounds the order up to whole boxes, and reports how many tiles are left over after the last box. A small script does the arithmetic, so the same input always returns the same numbers, and it prints each calculation step so the figures can be checked by hand.

When the waste percent is lower than the working minimum for the layout, the script flags it. That is the most common reason a tile job runs short partway through the floor.

## When to use

Use it when someone is about to buy tile for a rectangular floor and needs a box count before ordering. It also fits the moment after a measurement, when the user has the room size but has not yet decided how much waste to allow. Diagonal layouts get a larger default allowance because the cuts at the walls consume more tile.

## When not to use

Do not use it for wall tile, countertops, backsplashes, or mosaic sheets, where the counting rules differ. It does not handle rooms with cutouts, alcoves, or irregular outlines, and it does not price tile. Setting, grout, and substrate advice are outside its scope.

## Requirements

Python 3.9 or later, standard library only. No network access and no packages to install. The script reads one JSON file of at most 2 MB and writes nothing.

## Example

Input file with a 10 by 8 foot room, 12 by 12 inch tiles, diagonal layout, eight tiles per box, and the default waste. Command: `python -I scripts/tiles.py <input-file>`. Exit code 0.

```json
{
  "status": "ok",
  "layout": "diagonal",
  "columns": 10,
  "rows": 8,
  "base_tiles": 80,
  "waste_pct": "15",
  "waste_tiles": 12,
  "order_tiles": 92,
  "tiles_per_box": 8,
  "boxes": 12,
  "leftover_tiles": 4,
  "arithmetic": [
    "Room 10 ft = 120 in long; 8 ft = 96 in wide",
    "Columns = ceil((120 + 0) / (12 + 0)) = 10",
    "Rows = ceil((96 + 0) / (12 + 0)) = 8",
    "Base tiles = 10 x 8 = 80",
    "Waste tiles = ceil(80 x 15 / 100) = 12",
    "Order tiles = 80 + 12 = 92",
    "Boxes = ceil(92 / 8) = 12",
    "Leftover tiles = 12 x 8 - 92 = 4"
  ],
  "findings": []
}
```

## Limits

Rectangles only. Room and tile dimensions must be positive, and the waste percent must be between 0 and 100. The waste minimums of 10 percent for straight and 15 percent for diagonal are working values chosen for this skill, not a published standard. Diagonal layout changes only the default waste percent (15 vs 10). The count itself is the same grid count with no diagonal cut allowance; treat 15 percent as a working value and ask the installer. The gap is treated as the same width in both directions. The script does not account for tiles cut to fit a border or for a pattern that must be centered, so the user should add a margin when a centered layout is required.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
