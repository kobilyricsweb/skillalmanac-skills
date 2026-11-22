# Listing page content: story-structure-planner

**One line:** Plans a story as scaled beats and scene cards, then checks the outline for holes.

## What it does

The skill walks an agent through a premise sheet, picks one of four beat structures, scales it to the word target (three-act: 25 / 50 / 25 with turns at about 10, 25, 50, 75 and 90 percent) and builds a scene card for every scene: goal, conflict, outcome, what changes, POV, tense, date, planned words, plants and payoffs. A script then reads the outline JSON and reports missing beats, per-beat word budgets, scenes without goal, conflict, outcome or change, unmarked POV and tense changes, scene dates that contradict their prerequisites, setups with no payoff and payoffs with no setup, characters appearing before introduction or after death, and arcs with no turning points. A continuity-bible template keeps facts beside the structure.

## Capabilities

- `scripts/check_outline.py check`: strict-JSON defect report with `scene_id`, severity and a suggested fix per defect
- `scripts/check_outline.py budget`: word budget per beat for any word target
- Four structure templates (three-act, save-the-cat, heros-journey, seven-point) with beat meanings
- Outline skeleton and continuity-bible template
- A fixed report: assumptions, defects fixed, warnings kept, what was not checked

## When to use / when not to

Use it to outline a novel, novella or short story, to plan scenes or chapters, to find a saggy middle, or to check a plan for plot holes and continuity. Not for writing the prose itself, line editing, blog or nonfiction structure (see blog-article-writer), game design documents (see game-design-docs), or continuing a copyrighted work. It carries a rule to write original text and to decline close imitation of a living author or reproduction of source text in fan fiction.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the manual pass in `SKILL.md`.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet. What exists is the script on saved fixtures.

1. `python scripts/check_outline.py check evals/fixtures/good_outline.json`: `ok` true, 12 scenes, 20,000 planned words against a 20,000 target, 0 errors, 0 warnings, exit 0.
2. `python scripts/check_outline.py check evals/fixtures/bad_outline.json`: `ok` false, 13 errors and 7 warnings, exit 1. Excerpt of `defects[]`: b03 `POV_DRIFT` (viewpoint moves from mara to joss inside a chapter with no marker); b04 `TIMELINE_CONTRADICTION` (dated 2026-03-10 but needs b06, dated 2026-03-15); b06 `PAYOFF_NO_SETUP` (payoff 'ghost_debt' has no earlier setup); b08 `CHAR_AFTER_DEATH`; outline-level `MISSING_BEAT` for climax and resolution and `ARC_NO_TURNING_POINT` for mara.
3. `python scripts/check_outline.py budget three-act 20000`: hook 2000, inciting_incident 3000, first_plot_point 5000, midpoint 5000, second_plot_point 3000, climax 1600, resolution 400.

## Limits

- Mechanical checks only; cannot judge whether a scene is good.
- Template spans and thresholds are planning values, not rules of fiction.
- Narrative order is array order; time zones are not supported.
- Ids are matched exactly; a typo shows up as an unknown character.
- Not for nonfiction, page-budgeted screenplays or branching interactive fiction.

## Evidence

See `VERIFICATION.md`. Static lint passes with 0 FAIL and 0 WARN and the 7 fixture cases pass. Not tested: with/without efficacy, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats: (1) paste a one-paragraph premise; (2) the agent runs `budget` and shows the beat sheet; (3) it fills scene cards and runs `check`, which reports a missing payoff and an unmarked POV change; (4) it fixes both, the check returns `ok: true`, and the report lists assumptions and what was not checked.

## FAQ seeds

- Does it write my story? No; it plans and checks the plan. Writing prose is a separate job.
- Does it need network access? No.
- Will it copy from books or imitate an author? No; it writes original plans and declines close imitation or reproducing source text.
- Can I use my own structure? Not in the script yet; pick the nearest of the four, or treat unknown-beat warnings as expected.
- How is it different from blog-article-writer or game-design-docs? Those structure articles and game documents; this checks fiction continuity (setups, arcs, POV, dates).
- Does it handle series or multiple timelines? One outline per book; use `flashback` for out-of-order scenes.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; lint and script fixtures run; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
