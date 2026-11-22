---
name: story-structure-planner
description: Plans a fiction story as a beat sheet scaled to a word target with a scene card per scene. Use when the user wants to outline a novel, novella or short story, plan scenes or chapters, fix a saggy middle or check plot holes and continuity. A script checks the outline JSON for missing beats, scenes with no conflict or change, POV and tense drift, timeline contradictions, setups without payoffs and arcs without turning points. Do not use for writing the prose itself, line editing, blog or nonfiction structure, game design documents, or continuing a copyrighted work.
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
compatibility: The checker needs Python 3.9 or newer, standard library only. No network access. Without Python, run the manual pass in step 6.
---

# Story structure planner

Turn a premise into a scaled beat sheet and a set of scene cards, then check the plan mechanically before any chapter is written. The script finds gaps in the plan; it does not judge quality. The writer decides what a flagged scene should become.

## Original-text rule

Everything planned and drafted here is original to the user. Do not reproduce passages from published books, scripts or songs, do not imitate a living author's sentences closely, and for fan fiction use the user's own characters' actions and wording: never copy source text, and plan new events rather than retyping canon scenes. If asked to continue or paste a protected work, decline that part and offer an original outline in the same genre.

## Workflow

```
- [ ] 1 Capture the premise sheet
- [ ] 2 Pick a structure and get budgets
- [ ] 3 Write the characters and arcs
- [ ] 4 Write scene cards into outline.json
- [ ] 5 Run the checker, fix, re-run
- [ ] 6 Report
```

1. **Premise sheet.** Ask for, or infer and state: genre, target length in words, protagonist, what they want (external goal), what they need (internal lesson), what happens if they fail (stakes), antagonistic force, POV mode (`single`, `multiple`, `omniscient`), narrative tense and person. Missing items become explicit assumptions in the report. Do not invent the user's themes.
2. **Structure and budgets.** Default `three-act` (25 / 50 / 25 percent). Use `save-the-cat` for commercial genre plots, `heros-journey` for quest or journey plots, `seven-point` when the user starts from the ending. Run `python scripts/check_outline.py budget <structure> <word_target>` for per-beat word budgets. Three-act turns fall at about 10, 25, 50, 75 and 90 percent. Read the beat meanings in [references/structure_templates.md](references/structure_templates.md) only for the chosen structure.
3. **Characters and arcs.** One entry per character who matters: id, role, `introduced_in`, and for protagonist and antagonist an arc (want, need, at least two turning-point scenes). An arc with no scene where the belief or choice changes is a description, not an arc.
4. **Scene cards.** Fill the outline using [assets/outline-skeleton.json](assets/outline-skeleton.json) and the field list in [references/outline_schema.md](references/outline_schema.md). Every scene needs goal, conflict, outcome, `change` (from, to), POV, a planned word count (a planning guide for prose scenes is 1,000 to 3,000 words; the script does not check this), and a `beat`. Rules for good cards:
   - Goal is what the POV character wants in this scene, in one concrete sentence. Conflict is who or what stops them. Outcome says whether they get it: `yes`, `no`, `yes-but` or `no-and`. Three plain `yes` in a row means nothing opposes the hero.
   - `change.from` and `change.to` name the value that moves (safe to hunted, trusting to suspicious). If it does not move, merge or cut the scene.
   - In the middle third every scene should change a stake (`stakes_change: true`): raise it, lower it or reveal it.
   - Plant a fact, object or promise in `plants` and pay it off in a later scene's `pays_off`. A payoff with no plant is an unearned twist.
   - Change POV or tense only at a chapter change or with `pov_marked` or `tense_marked` set. Dates are ISO; use `flashback: true` for out-of-order scenes.
5. **Check.** Run `python scripts/check_outline.py check outline.json`, fix defects in the outline (never edit the script or loosen the file to pass), and re-run until `"ok": true`. Warnings are questions: fix them or record why they stay. Exit code 1 means error-level defects; exit 2 means the file is not strict JSON (the message names the line).
6. **Report** in this shape, then give the outline:

```
Structure: <name>, <word_target> words, <n> scenes
Checker: ok <true/false>; errors <n>, warnings <n> (codes: ...)
Fixed: <defect codes resolved and how>
Kept on purpose: <warnings left, with the author's reason>
Assumptions: <premise items the user did not give>
Not checked: quality of scenes, prose, originality, genre fit
```

## Defect codes (summary)

Error level: `MISSING_BEAT`, `MISSING_FIELD`, `NO_CHANGE`, `POV_DRIFT`, `TENSE_DRIFT`, `PERSON_DRIFT`, `TIMELINE_CONTRADICTION`, `PAYOFF_NO_SETUP`, `PAYOFF_BEFORE_SETUP`, `CHAR_BEFORE_INTRO`, `CHAR_AFTER_DEATH`, `ARC_MISSING`, `ARC_NO_TURNING_POINT`, `SCHEMA`, plus unknown-id codes. Warning level: `BEAT_DRIFT`, `BEAT_BUDGET`, `BEAT_ORDER`, `TARGET_MISMATCH`, `MIDDLE_NO_STAKE_CHANGE`, `RUN_OF_SUCCESS`, `SETUP_NO_PAYOFF`, `CHAR_VANISHES`, `ARC_FEW_TURNS`, `ARC_INCOMPLETE`, `TIMELINE_BACKWARDS`, `REQUIRES_ORDER`. Meanings and fixes: [references/outline_schema.md](references/outline_schema.md).

## Output contract

`check` prints one JSON object: `command`, `file`, `ok`, `summary` (structure, word_target, planned_words, scenes, errors, warnings), `beat_budgets[]` (beat, span_pct, budget_words, planned_words, status, scene_ids), `counts_by_code`, and `defects[]`, each with `code`, `severity` (`error`, `warn`, `info`), `scene_id` (null for outline-level defects), `ref`, `message`, `fix`. Stdout is JSON only; problems with the file go to stderr.

## Continuity bible

Keep one running file next to the outline from the template in [assets/continuity-bible-template.md](assets/continuity-bible-template.md): characters (age, look, speech habit, knowledge at each point), places, objects, rules of the world, and a dated timeline. Update it whenever a scene card changes; the outline JSON holds structure, the bible holds facts.

## Scripts

- `scripts/check_outline.py check <outline.json>`: run it. Reads the file only; writes nothing.
- `scripts/check_outline.py budget <structure> <word_target>`: run it for beat word budgets.
- `scripts/check_outline.py structures`: lists beat names per structure.

Run, do not edit. Manual fallback without Python: for each scene confirm goal, conflict, outcome and change are filled, compare POV, tense and dates with the scene before, match every plant to a later payoff, and tick each beat of the template.

## Limits

- Mechanical checks only: the script cannot tell a good scene from a bad one, or a real turning point from a labelled one.
- Template spans and the thresholds (beat start within 10 points, budget between 0.5 and 1.5 times, three yeses in a row, middle third as 33 to 67 percent, character gone before 75 percent) are working values for planning, not laws; many good stories break them.
- The outline is in narrative order; dates carry chronology. Time zones are not supported.
- Names are matched by id, never by spelling, so a typo in an id is reported as an unknown character.
- Not for nonfiction, screenplays with page budgets, or interactive fiction with branches.
