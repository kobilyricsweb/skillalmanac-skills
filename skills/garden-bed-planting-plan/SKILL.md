---
name: garden-bed-planting-plan
description: Plans a garden bed layout from bed size, sun hours and a plant list. Counts plants per band by spacing, groups them by water need, orders bands by height and draws a text grid. Use when a bed looks overcrowded or mismatched, or before buying plants when you need a count. Do not use for pest control, soil testing, hardiness or edibility claims, or structures and hardscape.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B); no scripts and no network access.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Garden bed planting plan

Plans one bed: how many of each plant fit, which plants share a water group, and the north-to-south order of the plant bands. Every number is either supplied by the user or labelled as a working value. This skill does not decide whether a plant is safe to eat, non-toxic, or hardy at a location.

## Intake

Required from the user: bed length (ft), bed width (ft), sun hours per day in the growing season, and a plant list of 1 to 8 plants.

Optional per plant: in-row spacing (in), water group (High, Moderate or Low), sun need (full, part or shade), height class (tall, medium or low).

Convert feet to inches before any arithmetic: length_in = length_ft x 12, width_in = width_ft x 12.

## Workflow

1. Intake. Check the required facts. Record each value with its source ("user" or "working value") in the Inputs table. If a required fact is missing, stop (see Refuse / stop when).
2. Sun class. Map sun hours to a class with the Sun table. Compare with each plant's sun need. Set LOW-SUN if the need is full and the class is not full, or the need is part and the class is shade. Output: the Sun class column in the Plant table.
3. Spacing. Use the user's spacing when given. Otherwise use the category working value and set the source to "working value, VERIFY-LOCALLY". Output: the Spacing columns in the Plant table.
4. Water group. Use the user's group when given, otherwise the category group. Output: the Water group column, and the group lines in Totals.
5. Band count. Each plant gets bands (default 1). Band depth_in = spacing_in. Plants per band = floor(length_in / spacing_in). Plants = bands x plants per band. Sum all band depths. If the sum is more than width_in, drop plants from the last listed plant backward until it fits, and set DROPPED for each one. If plants per band is 0, set DROPPED for that plant. Unused depth = width_in minus the sum of band depths. Output: Band order and Totals.
6. Band order. Tall bands go at the north edge, then medium, then low. Ties keep the user's list order. Output: the Band order list, north first.
7. Text grid and report. Draw one line per band, north band first, one letter per plant. Write the seven output sections in the order given in the output contract. Set the Status.

No script is shipped. Do all arithmetic by hand with whole-number division (floor), and recheck every count before writing the output.

## Tables (working values unless the user supplies the value)

Sun table:

| Sun hours per day | Sun class |
|---|---|
| 6 or more | full |
| 3 to under 6 | part |
| under 3 | shade |

Category table:

| Category | Example plants | Sun need | Spacing (in) | Water group | Height class |
|---|---|---|---|---|---|
| Fruiting vegetable | tomato, eggplant | full | 24 | High | tall |
| Annual herb | basil, cilantro | full | 8 | Moderate | medium |
| Leafy green | lettuce, spinach | part | 8 | Moderate | low |
| Root vegetable | carrot, radish | full | 3 | Moderate | low |
| Other | any plant not listed | user must supply | user must supply | Moderate | medium |

Height class thresholds: tall is over 4 ft, medium is 1 to 4 ft, low is under 1 ft.

Bed limits: length and width 1 to 40 ft each.

## Output contract

Write exactly these seven headings, in this order, with no other top-level headings.

1. `## Inputs`: table with columns Item | Value | Source. Rows: Bed length, Bed width, Sun hours per day, Plant list.
2. `## Plant table`: columns Plant | Category | Sun need | Sun class | Spacing (in) | Spacing source | Water group | Height class | Bands | Plants.
3. `## Band order`: numbered list, one line per band: "Band n (north edge or south edge when applicable): Plant, depth x in, y plants".
4. `## Text grid`: a code block. First line "North", last line "South". One letter per plant, separated by single spaces. Legend line above the block: letter for each plant, for example "T tomato, B basil, L lettuce". Unused depth goes on its own line in the block as "(n in unused at south edge)".
5. `## Totals`: bullets "Plants: n", "Used depth: n in of width_in in", "Unused depth: n in", and "Water groups: High: names with counts; Moderate: names with counts; Low: names with counts" (omit a group with no plants).
6. `## Flags`: one bullet per flag, format "CODE: item: note". Codes:

| Code | Meaning | Effect on status |
|---|---|---|
| VERIFY-LOCALLY | Spacing is a working value | partial |
| LOW-SUN | Sun class is below the plant's sun need | partial |
| DROPPED | Plant removed because depth or length is too small | partial |
| UNUSED-DEPTH | Unused depth is above 0 in | none |

If there are no flags, write "None".

7. `## Status`: one of the values below, then one sentence of reason.

| Status | When |
|---|---|
| complete | Plan produced and no VERIFY-LOCALLY, LOW-SUN or DROPPED flags |
| partial | Plan produced and at least one VERIFY-LOCALLY, LOW-SUN or DROPPED flag |
| needs-input | No plan produced; numbered question list given instead |

## Refuse / stop when

- Bed length, bed width, sun hours or the plant list is missing: status needs-input. Return a numbered question list (Q1, Q2, ...) naming each missing fact. Do not write the other sections.
- An "Other" plant has no spacing or no sun need from the user: status needs-input, with one question for that plant. Do not guess a spacing for it.
- The plant list has more than 8 plants: status needs-input, and ask the user to choose 8.
- Bed length or width is outside 1 to 40 ft: status needs-input, with one question per bad value.
- The user asks whether a plant is safe to eat, non-toxic, or hardy at a location: refuse that claim. State that the plan has no location data and that the user should check local extension guidance.
- The user asks for pest, disease, soil or fertilizer advice: state that it is out of scope and continue with the counts.
