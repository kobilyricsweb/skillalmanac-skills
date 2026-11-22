---
name: kitchen-layout-brief
description: Writes a kitchen layout brief from measured room sizes and fixed sink, cooktop, and refrigerator positions, computing work triangle legs, zone checks, a walkway check, and open questions for the installer. Use when a kitchen project needs a written brief before design or installation, when measurements must be turned into triangle leg lengths, or when a homeowner needs a must-keep and wishlist list. Do not use for structural, gas, or electrical advice, cabinet pricing, or permit filings.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Kitchen layout brief

This skill writes one kitchen layout brief from intake measurements. It computes the work triangle, checks four zones and the walkway, and lists open questions for the installer. It does not design cabinets, price work, or give structural, gas, or electrical advice.

## Coordinate frame

- The origin is the southwest corner of the room. x runs east and y runs north. Distances are in feet to 0.1 ft unless a value is marked in inches.
- Each fixed item is a center point: the sink bowl center, the cooktop center, and the refrigerator front center.
- The notch is a rectangle removed from one corner. Give its width and depth in feet, and its corner.

## Workflow

1. Collect intake. Required facts: room width (ft), room length (ft), notch (none, or width and depth with its corner), refrigerator x and y, sink x and y, cooktop x and y, and cooks at once (1 or 2). Optional facts: counter frontage west and east of the sink (in), counter frontage west and east of the cooktop (in), dishwasher distance from sink center (in), refrigerator handle-side landing (in), narrowest walkway (in), must-keep items, and wishlist items. Output: held internally; NOT GIVEN facts surface in sections 2 to 6 and section 8.
2. Apply the stop rule for missing required facts. If any required fact is NOT GIVEN, do not compute the rows that depend on it and do not estimate it. Set status to partial, write NOT GIVEN in those rows, and carry the missing facts into section 8 as numbered questions.
3. Check bounds. A fixed point is IN when x is between 0 and the room width (inclusive), y is between 0 and the room length (inclusive), and the point is not inside the notch. Otherwise it is OUT. An OUT point makes the status partial.
4. Compute the three legs as straight-line distances between centers: the square root of (dx times dx plus dy times dy). No scripts are shipped; compute each leg by hand. Keep the unrounded value to 2 decimals, then round the leg to 0.1 ft with half-up rounding. The perimeter is the sum of the three rounded legs.
5. Apply the leg and perimeter thresholds in the first table below.
6. Run the four zone checks in the second table. A missing optional fact gives NOT GIVEN, never FAIL.
7. Run the walkway check. The required walkway depends on cooks at once.
8. Copy must-keep and wishlist items word for word. Write "none given" for an empty list.
9. Write the open questions: one numbered item for each OUT point, FAIL row, and NOT GIVEN row, plus the referral line. Combine related items and cap the list at 10 questions.
10. Set the status, then assemble the brief using the output contract. Do not add sections.

## Thresholds

Every value below is a working value for planning. None is a published code requirement. The installer and the local building department decide final dimensions.

| Check | Working value | Result when outside |
|---|---|---|
| Work triangle leg | 4.0 to 9.0 ft, inclusive | OUT |
| Work triangle perimeter | 13.0 to 26.0 ft, inclusive | OUT |
| Walkway, cooks at once = 1 | 42 in or more | FAIL |
| Walkway, cooks at once = 2 | 48 in or more | FAIL |

## Zone rules

| Zone | Anchor | Working rule | Intake fact used | Result |
|---|---|---|---|---|
| Prep | Sink | 36 in or more of counter on at least one side | Counter frontage west and east of sink | PASS or FAIL |
| Cook | Cooktop | 12 in or more of landing on at least one side | Counter frontage west and east of cooktop | PASS or FAIL |
| Clean | Sink | Dishwasher center 36 in or less from sink center | Dishwasher distance | PASS or FAIL |
| Storage | Refrigerator | 15 in or more on the handle side | Refrigerator handle-side landing | PASS or FAIL |

Result codes are IN, OUT, PASS, FAIL, and NOT GIVEN. No other code appears in the brief.

## Output contract

The brief has exactly eight sections, in this order, with these headings:

1. `## 1. Status`: one line reading `Status: complete`, `Status: partial`, or `Status: refused`, then one sentence of scope.
   - complete: every required fact is given and every fixed point is IN. Rows may still read FAIL or NOT GIVEN.
   - partial: at least one required fact is NOT GIVEN, or one fixed point is OUT. Affected rows read NOT GIVEN or OUT.
   - refused: the request is for structural, gas, or electrical design. Keep all eight headings, write "Not produced." under sections 2 to 7, and put only the referral line in section 8.
2. `## 2. Room`: table with columns `| Item | Value |`, rows Bounding box, Notch, Cooks at once, Origin.
3. `## 3. Fixed positions`: table with columns `| Item | x (ft) | y (ft) | Bounds |`, rows Refrigerator front center, Sink bowl center, Cooktop center.
4. `## 4. Work triangle`: table with columns `| Leg | Calculation | Unrounded (ft) | Rounded (ft) | Result |`, rows Refrigerator to sink, Sink to cooktop, Cooktop to refrigerator, Perimeter. The perimeter row shows the sum of rounded legs and "n/a" in the unrounded column.
5. `## 5. Zones`: table with columns `| Zone | Anchor | Given | Result |`, one row per zone in the zone table above.
6. `## 6. Walkway`: table with columns `| Check | Required (in) | Given (in) | Result |`, one row.
7. `## 7. Keep and wishlist`: two bold labels, `**Must keep:**` and `**Wishlist:**`, each followed by a bullet list.
8. `## 8. Open questions and referrals`: a numbered list of questions, then this exact line: "Structural, gas, and electrical items are outside this brief. Confirm them with a licensed contractor, plumber, or electrician and the local building department."

## Refuse or stop when

Set status to refused, and stop, when the request asks for:

- advice on load-bearing walls, beams, headers, or removing a wall;
- gas line routing, gas appliance connections, or venting;
- circuit sizing, outlet counts, panel work, or wiring code compliance.

Stop without refusing, and return a partial brief, when:

- a required fact is still NOT GIVEN after the numbered question list has been returned;
- a fixed point is still OUT after the user has been asked to correct it.

Do not give prices, permit filings, or advice on choosing a contractor. Say that these are outside this brief.

## Shipped files

- `LICENSE.txt`: the Apache-2.0 license text that covers this skill.
- `SKILL.md`: this file.
