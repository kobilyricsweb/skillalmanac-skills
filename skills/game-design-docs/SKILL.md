---
name: game-design-docs
description: Writes a game design document (GDD) a small team can build from, in a fixed Markdown layout, and validates it plus an economy CSV with a script that prints strict JSON. Use when an indie developer asks for a GDD, game design doc, core loop, pillars, mechanics, economy balance, scope budget or playtest plan. The script flags missing sections, more than 3 pillars, mechanics without feedback, economy sources without sinks and unreachable progression tiers. Do not use for story or level writing, art direction, publisher pitch decks, engine code or purchase legal terms.
license: Apache-2.0
compatibility: The checker needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the manual checklist in step 8.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Game design docs

Produce a design document a small team can build from without asking the author what a section means. Every section has a test it must pass; a section that cannot pass the test is marked as an open question, not filled with prose.

## Intake

Ask for these five facts, or state the assumption you used for each one you did not get: platform; team size and calendar weeks; target session length in minutes; one or two reference games and what to borrow from each; revenue model (premium, free with ads, free with purchases, none). If the user already has notes, build from them and do not ask again.

## Workflow

```
- [ ] 1 Copy the layout from assets/gdd-template.md and the CSV header from assets/economy-template.csv
- [ ] 2 Core loop: one line, 3 to 6 steps, plus cycle time
- [ ] 3 Pillars: at most 3, each with a veto
- [ ] 4 Mechanics: inputs, outputs, feedback for every one
- [ ] 5 Progression and economy: tier table in the GDD, flows in the CSV
- [ ] 6 Scope budget
- [ ] 7 Playtest plan
- [ ] 8 Run the checker, fix, re-run
- [ ] 9 Report
```

Exact headings, field names and table columns are in [references/gdd-format.md](references/gdd-format.md); read it before step 1 if you have not used this layout. The reasoning and numbers behind each rule are in [references/design-rules.md](references/design-rules.md); read only the section for the step you are on.

1. **Layout.** Use the H2 headings exactly: `Core Loop`, `Pillars`, `Mechanics`, `Progression`, `Economy`, `Scope Budget`, `Playtest Plan`. The checker matches them by name.
2. **Core loop.** One line `Loop: a -> b -> c`, with `Cycle time: <n> <unit>` under it. Test: a stranger can name the player's action in each step. A loop of 2 steps is an action, a loop of 7 or more is two loops: split it into a core loop and a meta loop and put the meta loop under Progression.
3. **Pillars.** Maximum 3, each written as `**Name**: what it forbids`. Test: for each pillar, name one tempting feature it vetoes; if none exists, the pillar decides nothing, so delete it.
4. **Mechanics.** One `###` per mechanic with `Inputs:`, `Outputs:`, `Feedback:`. Feedback names a channel (visual, audio, haptic, UI) and what the player perceives; direct input should respond within about 100 ms. A mechanic whose result the player cannot perceive is not finished. Link each mechanic to a pillar in your head; if it serves none, flag it for cutting.
5. **Progression and economy.** The GDD holds a table of tiers with target hours of play. All numbers that move resources go in the CSV, one row per flow: `source` (units per hour of average play), `sink` (units per hour), `tier` (one-time cost to reach tier N). Decision rules:

| Situation | Action |
|---|---|
| A resource has a source and no recurring sink | Add a sink (repair, upkeep, consumable, fee) or exempt it with a written reason (progress points that are never spent) |
| A resource is spent but nothing makes it | Add the source or delete the spending |
| Sources exceed 2x sinks at full unlock | Raise sinks or cut a source; currency will pile up |
| A tier's net income is zero or negative before that tier | Raise a source active earlier or lower the cost; the tier is unreachable |
| A tier takes over 1.5x its target hours | Lower the cost or raise early income, or change the target and say so |

6. **Scope budget.** `Capacity: <weeks>` is people x calendar weeks x 0.6 unless the team has measured velocity (0.6 allows for bugs, builds, meetings and non-dev work; replace it with a measured figure). List features with weeks and `must`, `should` or `could`. Must-have work stays at or under 80% of capacity. The `could` rows are the cut list; say what is cut first. Estimates for a feature the team has never built are multiplied by 1.5.
7. **Playtest plan.** 3 to 7 rows `Question | Metric | Pass threshold | Sample`. Each question comes from a pillar or a named risk. Thresholds are written before any test and contain a number ("at least 8 of 10", "median under 6 minutes"). Five players find most usability problems but cannot measure a rate; for rates use 10 or more and phrase the threshold as "x of n".
8. **Verify.** Save the GDD and the CSV, then run:

```bash
python scripts/gdd_check.py --gdd design.md --economy economy.csv
```

Fix every `error` finding and re-run until `"ok": true`. Warnings are judgement calls: fix them or explain them in the report. If the script cannot run, check by hand: 7 headings present and non-empty; 3 pillars or fewer; every mechanic has all three fields filled in; every resource has a source and a sink; for each tier cost / (sources - sinks active before it) is under the target hours; must-have weeks at most 80% of capacity; every playtest row has a number.
9. **Report** in this fixed shape, after the document:

```
Checker: <ok true/false, errors, warnings, or "not run: why">
Assumptions: <intake answers you guessed>
Open questions: <sections that could not pass their test and why>
Cut first: <the could/should rows>
Not checked: <fun, balance beyond the net-income arithmetic, feasibility of estimates>
```

## Script

`scripts/gdd_check.py` (run it, do not edit it to make a check pass). Options: `--gdd FILE`, `--economy FILE`, `--max-hours N` (default 20, used when the GDD has no target for a tier), `--exempt-resource NAME` (repeatable). Prints one JSON object: `schema_version`, `ok`, `summary` (errors, warnings), `findings` (each with `severity`, `code`, `where`, `message`), `gdd` and `economy` summaries. Exit 0 no errors, 1 errors, 2 usage problem (missing or empty file; JSON with `error` is still printed). With both files it also checks that the GDD tier count equals the CSV tier count. Finding codes are listed in [references/gdd-format.md](references/gdd-format.md).

## Limits

- The script checks structure and arithmetic. It cannot judge whether the loop is fun or the pillars are good.
- The economy model is linear: flat per-hour rates, flows switched on at a tier, no stock decay and no player skill spread. It will miss exponential or randomised economies.
- Heuristics (100 ms, 2x inflation ratio, 0.6 focus factor, 80% must share, 1.5x tolerance, 20 default hours) are working values, not measured optima.
- Feedback-channel detection is a keyword match and gives warnings only.
- Markdown must follow the exact headings; other layouts are reported as missing sections.
- Not for multiplayer netcode, live-ops calendars or legal terms for purchases.
