## Contents

- Core loop
- Pillars
- Mechanics and feedback
- Economy
- Scope
- Playtest questions
- Sources

# Reasoning behind the rules

Numbers marked (working) are defaults chosen for small teams, not measured optima. Replace them with the team's own data when it exists.

## Core loop

- The loop is what the player repeats within one session. State it as actions the player takes, not outcomes ("sell the catch", not "earn money").
- Cycle time sets everything downstream: with a 6-minute loop, a 30-minute session holds about 5 passes, which is how many chances the player gets to feel progress. If the user cannot give a cycle time, give an estimate and mark it as an assumption to test.
- A longer loop (a run, a day, a chapter) is the meta loop. Keep it under Progression, because its currency is tiers and unlocks.
- Test for a bad loop: remove any one step; if the loop still works, the step is decoration. If it breaks and the player cannot tell why, the step lacks feedback.

## Pillars

- A pillar is a decision rule used in arguments: "does this feature serve pillar X?". Write each as a name plus what it forbids. Examples of vetoes: "no timers longer than 30 seconds", "no text the player must read to act".
- Three is the limit because a team under time pressure cannot hold a fourth; the checker errors above 3.
- Reject pillars that every game would claim ("fun", "polished", "immersive"). The test is whether a real feature was cut or changed because of it.

## Mechanics and feedback

- A mechanic is a rule that turns player input into a state change. Writing Inputs, Outputs and Feedback separately exposes the common gaps: the input is unclear (which control, how long held), the output is invisible (state changes the UI never shows), or the feedback arrives late.
- Feedback channels: visual (animation, particles, bar), audio, haptic, UI number or text. Use at least two channels for the mechanic that is the core of the loop, one for secondary ones.
- Timing (working): a response inside about 100 ms feels like a direct result of the input; slower feels like a separate event, which is fine for outcomes (a sale completing) and wrong for controls (a jump).
- Do not write balance numbers (damage values) in the mechanic; they belong in a table so they can change without editing prose.

## Economy

- Vocabulary: a source adds a resource (drops, rewards, income), a sink removes it (repairs, upkeep, consumables, fees, one-time unlock costs). Some designers say faucet and drain.
- Recurring sinks keep a resource meaningful after the last unlock. A one-time tier cost is a sink only until the last tier is bought, so the checker does not count it as a recurring sink.
- Sink types by player attitude: forced (upkeep, repair), chosen for power (upgrades, consumables), chosen for expression (cosmetics). A healthy currency has at least one forced or power sink; cosmetics alone leave most players with a pile.
- Progress points (XP) often have no sink on purpose. Use `--exempt-resource xp` and write the reason in the Economy section.
- Net rate for tier N uses only flows active before N, because a player cannot use income from a feature they have not reached. This catches the usual error: balancing tier 3 with tier 4 income.
- Ratio rule (working): sources above 2x sinks at full unlock gives a pile of unspent currency within a few sessions; below 1x the player slowly runs dry. Sources between 1.1x and 1.9x sinks is a comfortable band for a progression currency.
- Target hours per tier usually grow tier over tier (a doubling to tripling is common) so early tiers land inside the first sessions; a flat series is acceptable for a short game.
- The model is linear and deterministic. Randomised drops are entered as their expected value per hour; variance is a playtest question, not a table row.

## Scope

- Capacity (working): people x calendar weeks x 0.6. Raise the factor only after the team has tracked real velocity for a month.
- Must-have work at or below 80% of capacity leaves a fifth for the bugs and rework every build produces.
- First-time features get a 1.5x multiplier (working) because the estimate hides learning time.
- The should/could rows are written in cut order, first cut at the bottom. A scope budget without a cut list is a wish list.

## Playtest questions

- A question is worth asking if the answer changes what the team builds next. Source each question from a pillar ("does the player feel progress in the harbor?") or a risk ("can players find the sell button?").
- Metric: something observed or logged (completion without help, time to first sale, count of deaths at one spot), not a rating of enjoyment alone. If a rating is used, pair it with an observed behaviour.
- Threshold: a number fixed before the test. Use x-of-n phrasing for small samples ("at least 8 of 10") and medians for times.
- Sample (working): 5 players expose most usability problems in a build; 10 or more are needed to say a rate is above a threshold; split by experience level if the audience is mixed.
- Procedure per round: write the questions and thresholds, run the build, record the metric, compare, then decide keep, change or cut. Record the decision next to the row.

## Sources

Facts and terms above are common design practice; these are starting points to read, written from memory and not re-fetched while authoring this skill.

- Daniel Cook, "Loops and Arcs", on the Lost Garden site (lostgarden.com): the idea of nested loops that motivates the core loop versus meta loop split.
- Machinations (machinations.io): diagramming tool for resource sources, sinks and converters; the source of the faucet and drain vocabulary for game economies.
- Jakob Nielsen's usability writing on small test samples (nngroup.com): origin of the "five users" rule of thumb used for usability rounds.
