## תקציר

- זהו תוכן עמוד ה-skill באתר: מה הוא עושה, מתי להשתמש, דוגמאות, מגבלות, תסריט הדגמה ושאלות נפוצות.
- ה-skill כותב, מבקר ומארגן מחדש קובצי הוראות לסוכן (AGENTS.md, CLAUDE.md) כך שנשארות רק הוראות ספציפיות לפרויקט שאומתו מול הקבצים.
- כולל script שמאתר נתיבים ופקודות שאינם קיימים, מנהל חבילות שגוי, import שבור, מחרוזת שנראית כסוד, שורות כלליות וגודל חריג.
- זו התוצאה החלשה בסדרה: כל 16 הבדיקות האוטומטיות עברו גם בלי ה-skill. מדרג עיוור העדיף את ה-skill בשתיים מתוך שלוש בהפרש של נקודה (8 מול 7).
- הדוגמאות והמספרים לקוחים מריצות שמורות; טיוטה, לא לפרסום לפני סקירה אנושית והשלמת הבדיקות.

---

# Listing page content: agent-instruction-files

**One line:** Instruction files where every line is project-specific, verified against the repo, and worth loading on every session.

## What it does

The skill applies two tests to every line (would the agent get it wrong without it; is it true today and checkable in the repo), reads manifests, CI files and configs before writing, settles contradictions from the file the tools execute, and places rules at the right level (root, nested, on-demand procedure, or a hook when it must always happen). A bundled script audits a file against the repo. A reference explains how Claude Code, Codex and Cursor load instruction files, including the import syntax and size limits, for a one-source setup.

## Capabilities

- `scripts/instruction_file_audit.py`: missing paths, missing package scripts and make targets, package manager that contradicts the lockfile, broken imports, credential-like strings, vague lines, exact duplicates, emphasis overuse, size
- What to keep and what to cut, in order of value
- Layouts for one shared source across tools, for small repos and monorepos
- A fixed report: fixed, conflicts settled and by which file, removed, kept, needs the owner

## When to use

You want an AGENTS.md or CLAUDE.md written or improved, the agent ignores its instructions, the file is long or stale, or several tools should share one file.

## When not to use

README or onboarding docs for people, chatbot system prompts, converting rule files into skills.

## Requirements

Python 3.9+ for the audit script. No network. Loading details verified for Claude Code, Codex and Cursor on 2026-11-20.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples (from saved runs)

1. Prompt: "The CLAUDE.md in web-dashboard/ has grown and the agent keeps ignoring parts of it. Audit it and replace it with a fixed version." Result: `evals/runs/i1-audit-bloated/with_skill/reply.md`: wrong package manager, a script and two paths that do not exist, a tabs-versus-spaces contradiction settled from `.prettierrc`, a committed staging key flagged for rotation, and unverifiable facts kept as TODO lines. The run without the skill fixed the same errors; the blind grader scored 8 against 7.
2. Prompt: "Write an AGENTS.md for the repo in geo-pipeline/." Result: `evals/runs/i2-write-from-scratch/with_skill/geo-pipeline/AGENTS.md`: 12 lines with the real make targets, the database-before-tests trap, the generated-file rule and the coordinate order; no README overview.

## Limits

- The audit checks that paths and commands exist, not that they do what the file says; it cannot see contradictions.
- Loading behaviour was read from documentation and can change with a tool update.
- In testing, the same model without the skill already did most of this well; the measured benefit is small.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Assertions passed: 23/24 with the skill against 23/24 without. A blind grader preferred the with-skill result in 2 of 3 tasks. Average token overhead 9,816 per run (+13%). Blinding was imperfect and each cell ran once. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Open an 83-line CLAUDE.md. Run the audit: two missing paths, a missing script, npm against a pnpm lockfile, a credential-like line, 20 vague lines.
2. The agent reads `.prettierrc` and `package.json` and settles the contradiction.
3. The new file: about 25 lines. The report lists what was removed and what the owner must rotate.
4. Audit again: zero problems.

## FAQ seeds

- Does it invent rules for my repo? It is told not to: facts come from files or from you, and gaps become TODO lines.
- Can one file serve Claude Code, Cursor and Codex? Yes: shared rules in AGENTS.md and a CLAUDE.md that imports it. The reference gives the loading rules it relies on.
- How long should the file be? Under about 100 lines at the root is the skill's aim; the documented target for one tool is under 200.
- Does the audit script send anything anywhere? No. It only reads files under the folder you give it.
- What about secrets found in the file? It removes them, tells you to rotate them, and does not repeat the value.
- Is it better than just asking the agent? In our three tests the difference was small: all scripted checks passed either way, and a blind grader preferred the skill's result in two of three by one point.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
