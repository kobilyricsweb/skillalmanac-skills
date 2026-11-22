# Lantern Harbor

A cozy harbor-management game for PC. Solo developer, 20 weeks.

## Core Loop

Loop: Sail out -> haul catch -> sell at the dock -> repair and upgrade the boat
Cycle time: 6 minutes

## Pillars

- Every trip is short enough to finish before a kettle boils.
- Progress is always visible in the harbor itself, never in a menu.
- Nothing can be permanently lost, so the player is never punished for stopping.

## Mechanics

### Cast and haul

- Inputs: hold and release the action button to set cast distance; tap to reel
- Outputs: one fish item per successful haul, 0 to 3 per trip leg
- Feedback: line tension bar on the HUD, splash particles on the water, a rising pitch sound while reeling

### Dock market

- Inputs: select a catch stack and confirm the sale
- Outputs: coins added to the wallet, stack removed
- Feedback: coin count animates upward with a short chime and a floating +N number

### Boat repair

- Inputs: choose a damaged part and confirm
- Outputs: part health restored to 100%, coins deducted
- Feedback: the part flashes green, a hammer sound plays, the repair icon disappears from the boat

## Progression

| Tier | Unlock | Target hours |
|---|---|---|
| 1 | Rowboat, shallow reef | 0 |
| 2 | Sailboat, open water | 3 |
| 3 | Trawler, deep trench | 5 |
| 4 | Lighthouse and night fishing | 12 |

## Economy

Table: economy_good.csv

Coins come from selling catch; repairs and upkeep drain them. Shells are crafted into bait.

## Scope Budget

Capacity: 20 weeks

| Feature | Weeks | Priority |
|---|---|---|
| Cast and haul | 4 | must |
| Dock market | 3 | must |
| Boat repair | 2 | must |
| Four progression tiers | 5 | must |
| Night fishing | 3 | should |
| Photo mode | 2 | could |

## Playtest Plan

| Question | Metric | Pass threshold | Sample |
|---|---|---|---|
| Do new players finish a first trip unaided? | share completing trip 1 without help | at least 8 of 10 | 10 players |
| Is a trip as short as intended? | median trip length from logs | between 4 and 8 minutes | 10 players |
| Does tier 2 arrive on time? | median hours of play to unlock tier 2 | at most 4.5 hours | 6 players |
