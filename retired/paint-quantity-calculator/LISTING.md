# Paint Quantity Calculator

## One line

Estimates the gallons of wall paint one room needs, with each step of the arithmetic printed.

## What it does

The skill takes the measurements of one rectangular room: length, width, height, the number of doors and windows, and the number of coats. It runs a small Python script that computes gross wall area, subtracts the openings, multiplies the remaining area by the coat count, adds a 10 percent waste allowance, and divides by coverage per gallon. The result is rounded up to the next half gallon, or to the next whole gallon when the user asks for that. Every intermediate figure appears in the report, so a painter or homeowner can check the work line by line.

Door and window sizes default to a 3 by 7 ft door and a 3 by 5 ft window. Coverage defaults to 350 square feet per gallon. Each default is labelled as a working value in the output, and the user can replace any of them with a figure from a tape measure or a product label. The script also flags two conditions for review: openings covering more than half the wall area, and wall heights outside a 6 to 20 foot range. Either flag makes the skill ask the user to confirm the measurements before a purchase amount is given.

## When to use

Use it when someone is about to buy paint for a single interior room and wants a number they can audit. It suits a first-time painter comparing a rough estimate against a store calculator, or a contractor who needs the same arithmetic written out for a client.

## When not to use

Do not use it for ceilings, trim, cabinets, or exterior siding. It does not handle several rooms in one run, mixed finishes, primer-only jobs, or texture. It does not recommend colors, brands, or sheens.

## Requirements

Python 3.9 or later, standard library only. No network access and no installed packages. The script reads one JSON file of at most 2 MB and writes only to standard output or standard error.

## Example

Input file with a 12 by 10 by 8 ft room, one door, two windows, and two coats, run as `python -I scripts/paint.py fixtures/sample-room.json`. The output below is verbatim from the run.

```
paint-quantity-calculator 0.1.0
units: ft
gross_wall_area: 2 x (12.00 + 10.00) x 8.00 = 352.00 sq ft
door_area_each: 21.00 sq ft (working default)
window_area_each: 15.00 sq ft (working default)
openings: doors 1 x 21.00 = 21.00; windows 2 x 15.00 = 30.00; total 51.00 sq ft
net_wall_area: 352.00 - 51.00 = 301.00 sq ft
coats: 2
coated_area: 301.00 x 2 = 602.00 sq ft
waste: 10.00 percent (working value); 602.00 x 1.1000 = 662.20 sq ft
coverage: 350.00 sq ft per gallon (working default)
gallons_exact: 662.20 / 350.00 = 1.8920 gallons
gallons_to_buy: 2.00 gallons (rounding: half)
status: ok
```

## Limits

Walls only. The ceiling is not counted, and the script has no input for it. Gallons are US gallons. Metric users give dimensions in meters and coverage in square meters per gallon, which the script does not convert to liters. Openings are subtracted at their full stated area, so a user who has measured the frame size rather than the glass size may overstate the openings. Dimensions are capped at 200 units, and at most 50 doors and 50 windows are accepted. The waste allowance and default coverage are working values, not published specifications.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
