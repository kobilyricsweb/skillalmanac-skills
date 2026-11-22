## תקציר

- זהו תוכן עמוד ה-skill באתר: מה הוא עושה, מתי להשתמש, דוגמאות, מגבלות, תסריט הדגמה ושאלות נפוצות.
- ה-skill מחליט מה להאציל לתת-סוכן ומה להשאיר בשיחה הראשית, כותב קובצי הגדרה ו-briefs עצמאיים עם פורמט דוח קבוע, ומתקן סוכנים שלא נבחרים או שמחזירים קיר טקסט.
- כללי ההאצלה ניטרליים לכלי; פורמט הקובץ ו-script הבדיקה מיועדים ל-Claude Code בלבד.
- ההבדל הגדול נמדד במשימת ה-briefs: בלי ה-skill הסוכן האציל גם את כתיבת התוכנית ולא קבע איך לבדוק את התוצאות (3 מתוך 7 מול 7 מתוך 7).
- הדוגמאות והמספרים לקוחים מריצות שמורות; טיוטה, לא לפרסום לפני סקירה אנושית והשלמת הבדיקות.

---

# Listing page content: subagent-design

**One line:** Decide what to delegate, then write subagent definitions and briefs that work without the conversation.

## What it does

The skill starts from the two handoffs that break delegation: the subagent starts with none of the conversation, and only its last message comes back. It gives a decision table for what to delegate and what to keep (the synthesis stays with the caller), the anatomy of a definition file (trigger description, least-privilege tools, how to find its input, project rules copied in with reasons, report format, what to do when stuck), a brief template for one-off delegation, and a rule that returned work is spot-checked before it is relied on.

## Capabilities

- Delegate-or-keep table and the subagent-versus-skill distinction
- Definition template and brief template (`assets/`)
- `scripts/agent_def_lint.py`: thin descriptions, missing tool list on read-only roles, wording that assumes the conversation or tells the agent to ask the user, missing report format or length bound
- A symptom table for agents that are never picked, return too much, or edit files
- Field reference for Claude Code agent files, with the date it was checked

## When to use

You ask for a subagent, a custom agent, an agent team, prompts for parallel agents, or a brief to hand to another agent; or an existing agent is never picked, returns walls of text or changes files it should not.

## When not to use

Building multi-agent applications with an SDK or framework; writing skills or hooks.

## Requirements

Python 3.9+ for the lint script. No network. Definition format: Claude Code (`.claude/agents`). Other tools' agent files were not checked.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples (from saved runs)

1. Prompt: "In storefront/ I need three things: find every place that reads the LEGACY_BILLING flag, check which npm dependencies are unused, and write the removal plan. Use subagents where it makes sense; show me the prompts first." Result: `evals/runs/a2-delegation-brief/with_skill/reply.md`: two briefs (flag reads, unused dependencies), the plan kept with the main agent, fixed return formats with file and line, and a check of the results. Blind grader: 7 of 7 assertions against 3 of 7 without the skill.
2. Prompt: "Create a subagent that reviews database migration files and is picked up automatically." Result: `evals/runs/a1-create-reviewer/with_skill/ledger-service/_dot_claude/agents/migration-reviewer.md`: read-only tools, the five project rules with reasons, commands to find the change, a capped report with NOT CHECKED and ASSUMPTIONS lines.

## Limits

- Automatic selection depends on the harness and the other agents installed; a good description raises the odds only.
- The lint checks form, not whether the agent does good work.
- Field names are for one tool. No created agent was run in a live session during testing.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Assertions passed: 21/21 with the skill against 16/21 without. A blind grader preferred the with-skill result in 3 of 3 tasks. Average token overhead 8,257 per run (+11%). Blinding was imperfect and each cell ran once. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Show a vague agent file ('Helps with code') and the complaint: never picked, wall of text, edits files.
2. Run the lint: six findings, each tied to a symptom.
3. The rewritten file: trigger description, Read/Grep/Glob, a 30-line report format.
4. Second beat: a three-part task split into two briefs, with the plan kept by the main agent.

## FAQ seeds

- Subagent or skill? A skill adds instructions to the current context; a subagent moves work out of it.
- Will my agent now be picked automatically? More likely, not guaranteed. Try two or three real requests.
- Does it work for Cursor or Codex agents? The delegation and brief rules do. The file format and lint are for Claude Code; others were not checked.
- Why does it refuse to delegate the plan? A plan written by an agent that has not seen the conversation answers a different problem.
- Does it run the agents? No. It writes definitions and briefs; you decide when to run them.
- What leaves my machine? Nothing.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
