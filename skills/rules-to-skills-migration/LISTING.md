## תקציר

- זהו תוכן עמוד ה-skill באתר: מה הוא עושה, מתי להשתמש, דוגמאות, מגבלות, תסריט הדגמה ושאלות נפוצות.
- ה-skill מעביר קובצי rules של עורכים (Cursor, Windsurf, Copilot) למבנה נייד: AGENTS.md להוראות קבועות ו-skills לנהלים לפי דרישה.
- הרעיון המרכזי: לסווג קודם לפי אופן ההפעלה של כל rule (תמיד, לפי תבנית קבצים, לפי החלטת המודל, ידני) ורק אז להעביר טקסט.
- ההבדל הגדול נמדד בהמרת rule יחיד ל-skill: 8 מתוך 8 מול 4 מתוך 8 (תיאור עם גבול, תהליך ממוספר, היסטוריית תקלות שנחתכה).
- הדוגמאות והמספרים לקוחים מריצות שמורות; טיוטה, לא לפרסום לפני סקירה אנושית והשלמת הבדיקות.

---

# Listing page content: rules-to-skills-migration

**One line:** Move editor rule files to AGENTS.md plus portable skills without losing how each rule was switched on.

## What it does

The skill inventories every rule file with a script that reads the activation fields, decides each rule's destination by what it is (convention, path-scoped convention, occasional procedure, reference, personal preference), corrects misfiled rules such as a long procedure marked always-on, settles duplicates and conflicts from the repo, rewrites procedures as real skills with trigger descriptions and only open-standard frontmatter, installs them where each tool looks, and reports per source file what went where and what was lost.

## Capabilities

- `scripts/rules_inventory.py`: Cursor `.mdc` rules, `.cursorrules`, Windsurf rules, Copilot instructions, Claude rule files and instruction files, with activation, size, suggested destination, misfiled procedures and lines repeated across sources
- Destination table and the cases where the source's activation is wrong
- A skill skeleton and the rules for turning rule prose into a skill
- Reference: activation fields per tool, where skills are read from, what does not carry over
- Plan-only mode that changes nothing

## When to use

You ask to convert, migrate, port or consolidate cursor rules or other rule files, turn a rule into a SKILL.md, or decide which rules stay always-on.

## When not to use

Writing a new skill or instruction file from scratch; explaining how one tool's rules work.

## Requirements

Python 3.9+ for the inventory script. No network. Source formats checked on 2026-11-20.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples (from saved runs)

1. Prompt: "Turn payments/.cursor/rules/refund-handling.mdc into a proper agent skill that also works outside Cursor." Result: `evals/runs/m2-single-rule-to-skill/with_skill/`: a `refund-handling` skill with a description built from user words (refund, double refund, chargeback) and a boundary, a numbered workflow, the incident history cut, copies in both skill folders. Independent checker 5 of 5 against 3 of 5 without the skill; blind grader 9 against 5.
2. Prompt: "We're moving crm-web/ off Cursor-only rules so that Claude Code and Codex users get the same guidance." Result: `evals/runs/m1-full-migration/with_skill/reply.md`: seven sources mapped, the always-on hotfix procedure moved to a skill with a pointer, a nested AGENTS.md for the component rules, a per-tool check of what was loaded.

## Limits

- The script classifies by frontmatter and size; convention versus procedure is a judgement.
- Exact glob scoping and manual attach have no exact portable equivalent; the report says what was lost.
- Whether a migrated skill triggers in a given tool was not tested.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Assertions passed: 23/24 with the skill against 18/24 without. A blind grader preferred the with-skill result in 3 of 3 tasks. Average token overhead 10,415 per run (+14%). Blinding was imperfect and each cell ran once. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Show a `.cursor/rules` folder with six files. Run the inventory: a table with activation and suggested destination; one row flagged 'procedure filed as always-on'.
2. The agent writes AGENTS.md (short) and four skills; show one description before and after.
3. The report table: source, activation there, destination, why, what changed.
4. Close on the 'what is lost' paragraph.

## FAQ seeds

- Does Cursor not already have a migrate command? Yes, for some rule types. It leaves always-on rules, glob rules and user rules alone; those are what this skill handles.
- Will it delete my old rule files? Not unless you ask. It tells you what to do with each.
- Where do the skills go? `.agents/skills/` and `.claude/skills/`, identical copies, so the common coding tools find them.
- What about rules stored in the editor's settings? They are not on disk; the skill asks you for them.
- Does it need network? No.
- Can it only plan? Yes. Say 'don't change anything yet'.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
