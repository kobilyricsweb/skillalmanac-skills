## תקציר

- זהו תוכן עמוד ה-skill באתר: מה הוא עושה, מתי להשתמש, דוגמאות, מגבלות, תסריט הדגמה ושאלות נפוצות.
- ה-skill מלווה כתיבת skill מהכשלים של סוכן בלי skill, דרך בדיקת צורה, שאילתות trigger והשוואת משימות עם ובלי.
- כולל שני scripts: בודק צורה לתיקיית skill, ומדרג תוצאות trigger ומשימות לפי תקן 90%/10%.
- הדוגמאות מבוססות על fixtures שמורים בלבד. לא נעשתה בדיקת יעילות עם/בלי, ולא נבדק ב-Claude Code, Codex או Cursor בפועל.
- סטטוס: DRAFT. אין סקירה אנושית.

---

# Listing page content: skill-authoring-and-evals

**One line:** Write a SKILL.md from what a plain agent gets wrong, then prove it works with trigger and with-versus-without evals.

## How it differs from Anthropic's skill-creator

Anthropic's skill-creator is a vendor tool tied to its own environment and a model-driven eval loop. This skill is tool-neutral and offline: two standard-library Python scripts, no network, no model calls, works in any agent that loads SKILL.md folders. It does not run your agent; you save which sessions loaded the skill and the outputs, and the scripts score the files. It adds a decision table that maps trigger-test numbers to a specific description change, the exact `evals.json` contract, a table of the house checks with thresholds, a fixed 60/40 held-out split and a `NOT-MEASURING` detector. No head-to-head comparison with skill-creator was run.

## What it does

The skill orders the work so a skill is measured before it is trusted: decide skill, instruction file or script; record what the agent does wrong without help; draft the trigger queries and task assertions first; write the smallest SKILL.md that closes those gaps; check the form; score triggers; score paired task runs. Two bundled Python scripts do the counting. One checks a skill folder against the open layout rules; the other scores trigger runs (with a fixed held-out 40%) and scripted task checks, and names the checks that cannot tell the skill from no skill.

## Capabilities

- Decision table: skill, always-on instruction file, script, or nothing
- Description recipe: what, `Use when` with user wording, `Do not use for`
- `scripts/skill_check.py`: frontmatter, name, description length and wording, body size, broken or orphan files, reference depth, hidden comments, stale wording
- `scripts/eval_score.py triggers`: trigger and false-trigger rates, held-out slice, missed queries
- `scripts/eval_score.py tasks`: scripted checks on with-skill and baseline outputs, plus the list of checks that do not separate them
- Templates for a SKILL.md and an eval file; a fixed report format that ends with what was not tested

## When to use

You want to create or improve a SKILL.md, a skill never loads or gets ignored, you want evals or a benchmark for a skill, or you are unsure whether something is a skill or belongs in an instruction file.

## When not to use

Writing the instruction file (AGENTS.md or similar) itself, subagent definitions, hooks, or MCP servers.

## Requirements

Python 3.9 or newer for the scripts (standard library only). No network. No other tools needed to read the instructions.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output of the shipped scripts on the saved fixtures (not a run of an agent):

1. `python scripts/skill_check.py evals/fixtures/bad-skill` reports 9 errors and 9 warnings, including a name that does not match the folder, a description with no `Use when` clause and in the first person, an HTML tag, a hidden comment and a backslash path. The good fixture reports none.
2. `python scripts/eval_score.py tasks evals/evals.json t1-runbook-to-skill evals/fixtures/out_with evals/fixtures/out_baseline` shows 7/7 checks with and 4/7 without, three separating checks, and four `NOT-MEASURING` checks that both runs pass.

No saved agent run of the skill exists yet, so there is no example of an agent session here.

## Limits

- The scripts judge form and counts, not whether the skill helps; only paired task runs show that.
- Trigger behaviour depends on the agent, model and other installed skills.
- Covers the open SKILL.md layout only; tool-specific extras are outside it.

## Evidence

See `VERIFICATION.md`. Static lint passed with no findings; the nine fixture cases pass. Not done: with-versus-without efficacy evals, trigger tests in any real tool, cross-tool installs, human review.

## Demo script (60 to 90 seconds)

1. Show a skill with the description "I can help with SQL and more" and the complaint that it never loads.
2. Run `skill_check.py`: first-person, no `Use when`, vague wording flagged.
3. Rewrite the description with the recipe; the check is clean.
4. Run `eval_score.py triggers` on a saved result file with misses; the four missed queries are named.
5. Run the paired task score; show the NOT-MEASURING lines and replace one assertion.

(Storyboard built on saved fixtures; replace with a saved agent run before publication.)

## FAQ seeds

- Does it need network? No.
- Does it work in tool X? The rules follow the open layout; only the layout was checked, no tool was run.
- How is it different from a skill-creator skill? It adds a form checker and a scorer that flags assertions that cannot separate the skill from no skill; no comparison was run.
- What data leaves my machine? None.
- Can it run the agent for me? No. You run the sessions and record loaded or not loaded; the scripts score the files.
- How do I uninstall? Delete the folder from the skills directory.

## Changelog

- 0.2.0 (2026-11-21): fix round: generic advice replaced by numeric gates, a trigger-description decision table, the evals.json contract and the house-check table; `skill_check.py` keeps checking the description after a block-scalar error.
- 0.1.0 (2026-11-21): first version; fixtures and lint verified, no efficacy evals.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings (skillalmanac.com). Author: Skill Almanac Editorial. Accountable editor: Global Media Holdings. Drafted by an AI model (claude-sonnet-5-5); no independent human review yet.
