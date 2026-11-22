# Kitchen layout brief

## One line

Turns measured room sizes and fixed sink, cooktop, and refrigerator positions into a written kitchen layout brief with work triangle legs, zone checks, a walkway check, and open questions for the installer.

## What it does

The skill takes a rectangular room with an optional corner notch, the center points of three fixed items, and the number of cooks who work at once. It places each item on a grid whose origin is the southwest corner, checks that every point sits inside the room and outside the notch, and then measures the three straight-line legs of the work triangle. Each leg and the total perimeter are compared with working values of 4 to 9 feet per leg and 13 to 26 feet for the perimeter.

Optional counter frontage, dishwasher distance, and a refrigerator landing feed four zone checks. A narrowest walkway measurement feeds a walkway check that uses 42 inches for one cook and 48 inches for two. Any required fact that is missing turns the brief into a partial brief, with the affected rows marked NOT GIVEN and each gap written as a numbered question. The output is always the same eight sections, so an installer can read two briefs side by side.

## When to use

Use it before a remodel designer or installer sees the room, when the homeowner has a tape measure and a rough sketch, and when the team needs the triangle legs in numbers rather than impressions. It suits a single kitchen with one sink, one cooktop, and one refrigerator on two walls.

## When not to use

Do not use it for load-bearing walls, gas lines, venting, circuit sizing, or wiring. Those items need a licensed professional and the local building department, and the skill refuses them. It also does not price work, choose a contractor, file for a permit, or design cabinets. Kitchens with two islands or several sinks fall outside the three-point model.

## Requirements

Text-capable agent only. No scripts, no network, and no files beyond the intake the user provides. The user must supply measurements in feet and inches, with the origin at the southwest corner of the room.

## Example

The example below is a complete brief produced by following the skill's workflow for a 10 by 12 foot L-shaped room with a 4 by 5 foot notch at the southeast corner. The refrigerator front center is at (1.0, 9.0), the sink bowl center at (5.0, 11.0), and the cooktop center at (9.5, 11.0). One cook works at a time. Every leg and the perimeter fall inside the working values. The walkway is 40 inches, which fails the 42 inch working value, and two zone rows lack intake facts.

# Kitchen layout brief

## 1. Status

Status: complete

Layout brief for a 10 ft by 12 ft L-shaped kitchen. It is not a construction or permit plan.

## 2. Room

| Item | Value |
|---|---|
| Bounding box | 10.0 ft wide by 12.0 ft long |
| Notch | Southeast corner, 4.0 ft wide by 5.0 ft deep (x 6.0 to 10.0, y 0.0 to 5.0) |
| Cooks at once | 1 |
| Origin | Southwest corner; x runs east, y runs north |

## 3. Fixed positions

| Item | x (ft) | y (ft) | Bounds |
|---|---|---|---|
| Refrigerator front center | 1.0 | 9.0 | IN |
| Sink bowl center | 5.0 | 11.0 | IN |
| Cooktop center | 9.5 | 11.0 | IN |

## 4. Work triangle

| Leg | Calculation | Unrounded (ft) | Rounded (ft) | Result |
|---|---|---|---|---|
| Refrigerator to sink | dx 4.0, dy 2.0 | 4.47 | 4.5 | IN |
| Sink to cooktop | dx 4.5, dy 0.0 | 4.50 | 4.5 | IN |
| Cooktop to refrigerator | dx 8.5, dy 2.0 | 8.73 | 8.7 | IN |
| Perimeter | 4.5 + 4.5 + 8.7 | n/a | 17.7 | IN |

## 5. Zones

| Zone | Anchor | Given | Result |
|---|---|---|---|
| Prep | Sink | West 42 in, east 18 in | PASS |
| Cook | Cooktop | West 24 in, east 6 in | PASS |
| Clean | Sink | NOT GIVEN | NOT GIVEN |
| Storage | Refrigerator | NOT GIVEN | NOT GIVEN |

## 6. Walkway

| Check | Required (in) | Given (in) | Result |
|---|---|---|---|
| Walkway, cooks at once = 1 | 42 | 40 | FAIL |

## 7. Keep and wishlist

**Must keep:**

- Window above the sink

**Wishlist:**

- Built-in microwave, position not given

## 8. Open questions and referrals

1. The narrowest walkway is 40 in, below the 42 in working value for one cook. Can the refrigerator or the notch wall move by 2 in or more?
2. What is the dishwasher distance from the sink center, in inches? The working value is 36 in or less.
3. What is the landing on the handle side of the refrigerator, in inches? The working value is 15 in or more.

Structural, gas, and electrical items are outside this brief. Confirm them with a licensed contractor, plumber, or electrician and the local building department.

## Limits

- Three fixed points only. The model does not place islands, peninsulas, or a second sink.
- Straight-line leg distances. The skill does not check whether a cabinet or door blocks a leg.
- Working values only. Local codes, appliance dimensions, and the installer's field measurements override them.
- Feet to 0.1 ft is the precision used. Inches are used only for counter, landing, and walkway checks.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
