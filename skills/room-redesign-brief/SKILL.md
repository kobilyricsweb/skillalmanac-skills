---
name: room-redesign-brief
description: Writes a room redesign brief, three image-tool prompts and a measure-before-you-buy checklist from measured dimensions, window and door positions, fixed items, budget, light and style words. Use when someone wants to redesign or decorate a room with an AI image tool and the results must respect real measurements, or when a cozy-room request keeps producing unusable images. Do not use for structural, electrical or plumbing plans, contractor quotes, or any output presented as a measured floor plan.
license: Apache-2.0
compatibility: Requires none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Room Redesign Brief

Use this procedure to turn a room description into a written brief that an image tool can be asked to follow. The brief is text only. It is not a plan a builder can use. Image tools often ignore dimensions, so every number in the output must come from the user's intake or be marked as assumed.

## Workflow

Run the steps in order. Do not start step 6 until steps 1 to 5 have written their outputs.

1. Intake. Record each field in a table. Accept metric or imperial units; convert imperial to metres with two decimals and show both values.
   - Room length and width (required, to 0.05 m)
   - Ceiling height (optional; if missing, use 2.40 m and mark it assumed)
   - Each window: wall (N, E, S or W), width, sill height, head height
   - Each door: wall, width, hinge side, swing direction (in or out)
   - Fixed items: radiator, fireplace, built-in shelves, sockets and switches with height above floor
   - Budget: one total with currency
   - Light: direct sun hours per window per day, or "unknown"
   - Style: up to three style words or short descriptions in plain words
   Output: "Intake table" with columns Field | Value | Status (given, assumed or missing).

2. Check the intake. Stop under the refusal list if length, width or any window wall is missing. If no door is given, write "no door placed" and add it to Assumptions. Compute floor area as length x width, to 0.1 m2.

3. Constraints. Apply Decision table A to every fixed item and opening. Output "Constraints table" with columns Constraint | Working value | Source (given, derived or assumed) | Confirm (yes or no).

4. Layout zones. Split the floor into a walkway, a seating zone, a storage zone and, if space allows, a work or display zone. Each zone is named by wall and has an area in m2 to one decimal. Check that no zone sits in a door swing or blocks a radiator. Output "Layout zones" table with columns Zone | Location | Area m2 | Notes.

5. Light and style. Use Decision table B to choose the light line from the window wall and sun hours. Write at most three style words and one palette sentence of 25 words or fewer. Output one "Light" line and one "Style" line.

6. Brief. Write the brief under the headings in the Output contract. Copy numbers from the Constraints table without rounding.

7. Image prompts. Write exactly three variants, A, B and C. Each variant copies the room dimensions and clearance values verbatim. The variants differ only in style and palette, never in dimensions. Each prompt is 60 to 120 words.

8. Checklist. Write the measure-before-you-buy checklist from Decision table C, one row per item the user plans to buy.

9. Assumptions. List every value with status "assumed" or "missing" and ask the user to confirm each one. Stop after this step.

## Decision table A: clearances (working values)

These are working values chosen for this procedure. They are not published standards.

| Constraint | Working value | If not met |
|---|---|---|
| Main walkway width | 0.90 m minimum | Move the nearest piece 0.10 m or remove it |
| Door swing zone | Keep clear of furniture for the full swing arc (door width) | Move furniture out of the arc |
| Sofa to coffee table | 0.40 m to 0.50 m | Shrink the table or move the sofa |
| Seating to focal wall | 2.00 m to 3.00 m | Choose a smaller focal piece |
| Rug edge to wall | 0.15 m minimum | Use a smaller rug |
| Furniture to radiator | 0.10 m minimum | Mark the radiator blocked and do not place a piece |
| Top of piece under a window | 0.10 m below sill height | Choose a lower piece |
| Wall art centerline | 1.45 m to 1.55 m above floor | Change the hanging height |
| Clear height above tallest piece | 0.30 m below ceiling | Choose a lower piece |

## Decision table B: light (Northern Hemisphere compass)

| Window wall | Direct sun hours | Light line for the brief |
|---|---|---|
| N | under 1 h | Soft, even daylight; no hard sun patches; cooler white tones |
| N | 1 h or more | Soft daylight with one short direct patch; plan a warm lamp for evenings |
| S | any | Strong direct light; plan sun-filtering textiles |
| E | any | Warm morning light, dimmer afternoon |
| W | any | Warm late-afternoon light; plan glare control after mid-afternoon |
| any | unknown | Light: unconfirmed; ask the user, do not guess |

If the user lives in the Southern Hemisphere, swap N and S and write that swap in Assumptions.

## Decision table C: measure before you buy

| Item | Measure | Pass rule |
|---|---|---|
| Sofa | Length, depth, back height | Leaves 0.90 m walkway |
| Door | Leaf width, swing direction | Nothing inside the swing arc |
| Window piece | Sill height, piece top height | Top sits 0.10 m below sill |
| Rug | Target length and width | 0.15 m off every wall; edge not under the door |
| Radiator | Depth from wall, height | 0.10 m clear of any piece |
| Sockets | Height above floor | Reachable; not behind a piece |
| Delivery route | Narrowest door or hall | Piece passes with 0.05 m spare (working value) |

## Output contract

The brief is one Markdown file with these H2 headings in this order:

1. Room summary (area, ceiling height, one-sentence purpose)
2. Intake (the Intake table)
3. Constraints (the Constraints table)
4. Layout zones (the Layout zones table)
5. Light and style (the Light line and Style line)
6. Image prompts (three H3 sections: Variant A, Variant B, Variant C)
7. Measure-before-you-buy (the checklist table)
8. Assumptions to confirm (a bullet list, one item per assumed or missing value)

Each image prompt section has these lines in this order: Dimensions, Fixed items, Light, Style, Avoid, Prompt. The Avoid line is always: "Avoid: furniture in the door swing, clutter in the walkway, pieces blocking radiators or sockets."

Under "Image prompts" write this sentence once: "Image tools can ignore dimensions; treat any rendering as mood, not as a plan."

## Refuse or stop when

- Room length, room width, or the wall of any window is missing: stop and ask.
- Intake values contradict each other (for example, a door wider than the wall it sits on): stop and ask.
- The user wants structural work (walls, beams, loads), electrical work (new circuits or sockets) or gas or plumbing work: decline and recommend a licensed professional. Do not write a substitute plan.
- The user asks for a measured floor plan, a to-scale image or a contractor quote: decline. The brief is not a plan and carries no guarantee of dimensions.
- The budget was not given: write "missing" in the Intake table. Do not invent a figure.
- The user asks for a named real person, a copied photograph or a brand logo in a prompt: leave that item out and keep the style words general.

## Package files

- SKILL.md: this procedure (the only file the agent follows).
- LICENSE.txt: Apache-2.0 license text.
- evals/trigger_queries.json: queries that should or should not trigger this skill.
- evals/evals.json: two task prompts with expected outputs and assertions.
