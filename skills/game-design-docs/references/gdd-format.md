## Contents

- Layout
- Core Loop
- Pillars
- Mechanics
- Progression
- Economy and the CSV
- Scope Budget
- Playtest Plan
- Finding codes

# GDD layout the checker reads

## Layout

One H1 title, then these H2 headings in any order, spelled exactly (case ignored): `Core Loop`, `Pillars`, `Mechanics`, `Progression`, `Economy`, `Scope Budget`, `Playtest Plan`. Extra H2 sections (Audience, Art, Audio) are allowed and ignored. Text inside code fences is ignored. A value that is empty, `TBD`, `TODO`, `n/a`, `none`, `-`, `?` or an `<angle-bracket prompt>` counts as a placeholder.

## Core Loop

```
Loop: sail out -> haul catch -> sell at the dock -> repair and upgrade
Cycle time: 6 minutes
```

3 to 6 steps joined by `->`. Cycle time is a number and a unit (seconds, minutes, hours).

## Pillars

A list of `-` or `1.` items directly under the heading. More than 3 is an error. An item under 4 words is a warning (a bare adjective decides nothing). Suggested shape: `**Short by design**: no trip needs more than one kettle-boil of attention`.

## Mechanics

One `### Name` per mechanic, each with three lines (bullet or plain, bold labels allowed):

```
### Cast and haul
- Inputs: what the player does, with which control
- Outputs: what changes in the game state
- Feedback: what the player sees, hears or feels, and when
```

Missing line or placeholder value is an error. A feedback line that names none of visual, audio, sound, haptic, UI, HUD, animation, particle, shake, flash, popup, text, number, icon, bar, voice, color, screen is a warning.

## Progression

A table with a `Tier` column (numbers 1..N without gaps) and a `Target hours` column (hours of play to reach that tier from the previous one; tier 1 is 0).

```
| Tier | Unlock | Target hours |
|---|---|---|
| 1 | Rowboat | 0 |
| 2 | Sailboat | 3 |
```

## Economy and the CSV

In the GDD: prose plus a `Table: economy.csv` line (missing line is a warning). In the CSV:

```
id,type,resource,amount,tier
coin_sell,source,coins,300,1
coin_repair,sink,coins,100,1
tier_2,tier,coins,600,2
```

| Column | Meaning |
|---|---|
| `id` | Unique per row |
| `type` | `source`, `sink` or `tier` |
| `resource` | Name of the currency or material (compared case-insensitively) |
| `amount` | Source and sink: units per hour of average play, above 0. Tier: one-time cost to reach that tier |
| `tier` | Optional. Source and sink: first tier at which the flow is active (default 1). Tier row: the tier being bought, numbered 2, 3, ... |

Tier N is reachable when, counting only flows with `tier` at most N-1 on the tier's resource, sources minus sinks is above 0. Hours to afford = cost / that net rate. The limit is 1.5 times the GDD target hours for that tier, or `--max-hours` when the GDD gives none. A tier row's cost is a one-time spend and does not count as a sink.

## Scope Budget

```
Capacity: 20 weeks

| Feature | Weeks | Priority |
|---|---|---|
| Cast and haul | 4 | must |
```

Priority is `must`, `should` or `could`. Weeks are positive numbers.

## Playtest Plan

```
| Question | Metric | Pass threshold | Sample |
|---|---|---|---|
| Do new players finish trip 1 unaided? | share finishing without help | at least 8 of 10 | 10 players |
```

A row needs a metric that is not a placeholder and a threshold containing a digit. At least 3 such rows. A table with no Sample column is a warning.

## Finding codes

Errors: `section-missing`, `section-empty`, `core-loop-no-statement`, `core-loop-steps`, `core-loop-no-cycle-time`, `pillars-none`, `pillars-too-many`, `mechanics-none`, `mechanic-missing-inputs`, `mechanic-missing-outputs`, `mechanic-missing-feedback`, `mechanic-placeholder-inputs`, `mechanic-placeholder-outputs`, `mechanic-placeholder-feedback`, `progression-no-table`, `progression-columns`, `progression-bad-tier`, `progression-bad-hours`, `progression-too-few`, `progression-tier-gap`, `scope-no-capacity`, `scope-no-table`, `scope-columns`, `scope-bad-weeks`, `scope-bad-priority`, `scope-must-over-limit`, `playtest-no-table`, `playtest-columns`, `playtest-no-metric`, `playtest-no-threshold`, `playtest-too-few`, `economy-columns`, `economy-duplicate-id`, `economy-bad-type`, `economy-bad-row`, `economy-bad-from-tier`, `source-without-sink`, `sink-without-source`, `tier-gap`, `tier-unreachable`, `tier-too-slow`, `tier-count-mismatch`.

Warnings: `title-missing`, `section-duplicate`, `pillar-thin`, `mechanic-feedback-no-channel`, `economy-no-table-line`, `scope-total-over-capacity`, `playtest-no-sample`, `inflation-risk`, `tier-cost-decreases`.
