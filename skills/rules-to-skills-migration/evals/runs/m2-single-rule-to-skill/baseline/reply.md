# Refund handling skill

I converted `payments/.cursor/rules/refund-handling.mdc` into an Agent Skill at `payments/.claude/skills/refund-handling/SKILL.md`.

- **Format:** The file follows the open Agent Skills layout, which is a folder holding a `SKILL.md` with `name` and `description` frontmatter. The `name` matches the folder name. Claude Code reads it from `.claude/skills/`, and other agents that support the format can load the same file. This includes Cursor, which supports skills as well as rules.
- **Description:** The Cursor rule had only a short description and `alwaysApply: false`. I rewrote the description so an agent can decide when to load the skill. It names the triggers: refund code, `src/refunds/`, idempotency keys, `ledger_adjustments`, `reconcile_refund`, disputed charges and account credit.
- **Content:** All rules, error codes, ledger entry names, the SQL query and the done checklist are kept as they were. I only restructured them into three steps (classify, call the processor safely, record it), followed by the checklist and the verification query. I shortened the intro and removed the "please read" filler. The incident background is kept in one sentence.
- **Original file:** I left the `.mdc` in place and unchanged, so Cursor users keep working. The two copies can drift, so if you want a single source of truth, replace the `.mdc` body with a pointer to the skill or delete it.
- **Not tested:** I did not run the skill in any agent. There were no existing skills in the workspace, and I left `src/refunds/service.ts` (a stub) and the README alone.
