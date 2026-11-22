# Garden bed planting plan

## One line

Turns a bed's length, width and sun hours into a plant count per band, a water-need grouping and a text grid of where each band sits.

## What it does

The skill takes one garden bed and a list of up to eight plants. It converts the bed to inches, maps the sun hours to full, part or shade, and checks each plant's sun need against that class. Spacing comes from the user when given; otherwise the skill uses a category working value and marks it for local confirmation. Each plant gets one or more bands across the bed width. The plant count in a band is the bed length divided by the spacing, rounded down. Bands that do not fit are dropped from the end of the list, and each drop is named. Tall bands go to the north edge, then medium, then low, so that shorter plants are not shaded. The output has seven fixed sections: inputs, a plant table, band order, a text grid, totals, flags and status. The status is complete, partial or needs-input.

## When to use

Use it when a bed looks overcrowded or when the plant mix looks mismatched, and you need a count per plant before buying seedlings. It is also useful for checking whether a planned mix fits a bed of a given size and sun exposure, and for grouping plants that need similar watering so they can share a line or a schedule.

## When not to use

Do not use it for pest control, disease diagnosis, soil testing, fertilizer rates or hardiness claims. The skill has no location data and will not say a plant is safe to eat, non-toxic or hardy where you live. It does not plan structures, paths, raised-bed construction or irrigation hardware.

## Requirements

A text-capable agent only. No scripts, no network access and no files beyond the user's own intake. The user supplies bed length and width in feet, sun hours per day, and the plant list. Spacing, sun need, water group and height class are optional per plant; when absent, the category table supplies working values and the output says so.

## Example

Complete output for a 4 ft by 8 ft bed with 6 sun hours and tomato, basil and lettuce. Spacing values are working values, so the status is partial.

```
## Inputs

| Item | Value | Source |
|---|---|---|
| Bed length | 8 ft (96 in) | user |
| Bed width | 4 ft (48 in) | user |
| Sun hours per day | 6 | user |
| Plant list | tomato, basil, lettuce | user |

## Plant table

| Plant | Category | Sun need | Sun class | Spacing (in) | Spacing source | Water group | Height class | Bands | Plants |
|---|---|---|---|---|---|---|---|---|---|
| Tomato | Fruiting vegetable | full | full | 24 | working value, VERIFY-LOCALLY | High | tall | 1 | 4 |
| Basil | Annual herb | full | full | 8 | working value, VERIFY-LOCALLY | Moderate | medium | 1 | 12 |
| Lettuce | Leafy green | part | full | 8 | working value, VERIFY-LOCALLY | Moderate | low | 1 | 12 |

## Band order

1. Band 1 (north edge): Tomato, depth 24 in, 4 plants
2. Band 2: Basil, depth 8 in, 12 plants
3. Band 3 (south edge): Lettuce, depth 8 in, 12 plants

## Text grid

Legend: T tomato, B basil, L lettuce. One letter per plant, north at top.

```
North
T T T T
B B B B B B B B B B B B
L L L L L L L L L L L L
(8 in unused at south edge)
South
```

## Totals

- Plants: 28
- Used depth: 40 in of 48 in
- Unused depth: 8 in
- Water groups: High: tomato 4; Moderate: basil 12, lettuce 12

## Flags

- VERIFY-LOCALLY: tomato: spacing 24 in is a working value
- VERIFY-LOCALLY: basil: spacing 8 in is a working value
- VERIFY-LOCALLY: lettuce: spacing 8 in is a working value
- UNUSED-DEPTH: bed: 8 in unused at south edge

## Status

partial. A plan was produced, but all three spacing values are working values to confirm locally.
```

## Limits

The category table holds working values, not published spacing specifications. Sun classes use a 6-hour and 3-hour cut-off that the skill applies as working values. The count assumes square spacing within a band and one row per band; plants that need staggered or wide spacing need the user's own spacing value. The grid shows one letter per plant, so a bed with more than about 40 plants per band becomes hard to read. The skill plans only the bed it is given and does not check neighboring beds for shade.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
