# Listing page content: game-design-docs

**One line:** Writes a game design document a small team can build from, then checks it and its economy table with a script.

## What it does

The skill gives an agent a fixed GDD layout with a test for every section: a one-line core loop with cycle time, at most 3 pillars that each veto something, mechanics written as inputs, outputs and feedback, a tier table, a scope budget with a cut list, and a playtest plan whose pass thresholds are numbers. Economy numbers live in a CSV of sources, sinks and tier costs. A checker script reads the Markdown and the CSV and prints strict JSON: missing or empty sections, more than 3 pillars, mechanics without feedback, resources with a source and no sink (or the reverse), tiers the player can never afford or would take too many hours to afford, scope that leaves no buffer, and playtest rows without a number.

## Capabilities

- `scripts/gdd_check.py --gdd F --economy F`: JSON report with `ok`, error and warning counts, and one finding per problem (code, location, message)
- Net-income arithmetic per tier using only flows active before that tier, compared with the GDD's target hours
- Cross-check that the GDD tier table and the CSV define the same number of tiers
- A GDD template and an economy CSV template
- A fixed closing report: checker result, assumptions, open questions, cut list, what was not checked

## When to use

An indie developer says write my GDD, turn these notes into a design doc, check my economy, how many pillars, make a playtest plan, or what should we cut.

## When not to use

Story, lore or level writing; art direction; publisher pitch decks; engine code; legal terms for purchases. It does not judge whether a game is fun.

How it differs from other jobs in the catalogue: `prd-writer` and `spec-driven-build` cover software product requirements; this skill is specific to game design, with the economy and scope arithmetic that a PRD has no place for.

## Requirements

Python 3.9 or newer for the checker (standard library only). No network. Without Python the agent follows the manual checklist in the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so no saved generated GDD is shown. What exists is the checker run on saved fixtures (real output):

1. `python scripts/gdd_check.py --economy evals/fixtures/economy_bad.csv` returns `ok: false`, 4 errors and 1 warning:
   - `source-without-sink`: 'gems' enters the game (5 per hour) but nothing recurring removes it
   - `sink-without-source`: 'salt' is spent (10 per hour) but nothing produces it
   - `tier-too-slow`: tier 3 needs 450.0 hours of play to afford 90000 (net 200 per hour); limit 20.0
   - `tier-unreachable`: tier 4: 'coins' nets -200 per hour (sources 300, sinks 500); the player can never afford 5000
   - warning `tier-cost-decreases`: tier 4 costs less than the previous tier
2. `python scripts/gdd_check.py --gdd evals/fixtures/gdd_missing_sections.md` returns `ok: false` with `section-missing` for Progression and Scope Budget, `section-empty` for Economy and one warning.
3. `python scripts/gdd_check.py --gdd evals/fixtures/gdd_good.md --economy evals/fixtures/economy_good.csv` returns `ok: true`, 0 findings, and tiers 2, 3, 4 reachable in 3.0, 4.36 and 12.0 hours.

## Limits

- Checks structure and arithmetic only; fun and balance beyond net income are not judged.
- The economy model is linear with flows switched on by tier.
- Thresholds (100 ms, 2x inflation, 0.6 focus factor, 80% must share, 1.5x tolerance, 20 default hours) are working values.
- Feedback-channel detection is a keyword match.
- The Markdown must use the exact headings.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN; 10 of 10 fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds, to be recorded from a real run)

1. Prompt: "Turn these notes into a GDD and an economy table" with the Moss & Mortar notes attached.
2. The agent asks nothing extra, states two assumptions (cycle time, token income) and writes `design.md` and `economy.csv`.
3. The checker runs and reports a tier the player cannot afford; the agent changes one sink and re-runs.
4. The checker prints `ok: true`; the agent ends with the fixed report listing assumptions and the cut list.

This storyboard has not been recorded; use a saved real run when one exists.

## FAQ seeds

- Does it need network access? No.
- Does it work in tool X? The layout is plain Markdown; the checker needs Python 3.9+. Only a Claude-family run is planned for verification; other tools are not tested.
- Can I use my own headings? The checker matches the seven headings by name; other layouts are reported as missing sections.
- Why a maximum of 3 pillars? The rule is stated in the skill; the checker errors above 3.
- Why does my XP resource fail the sink check? Pass `--exempt-resource xp` and write the reason in the Economy section.
- What data leaves my machine? None from the script; it reads the two files you give it.
- How do I uninstall? Delete the skill folder.

## Changelog

- 0.1.0 (2026-11-21): first draft; static lint and fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings. Drafted by an AI model (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
