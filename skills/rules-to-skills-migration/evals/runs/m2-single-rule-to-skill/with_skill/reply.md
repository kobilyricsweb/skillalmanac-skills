# Refund handling migration

Used the `rules-to-skills-migration` skill. Inventory: one rule, `payments/.cursor/rules/refund-handling.mdc`, activation "model decides" (`alwaysApply: false`, has a description), 27 lines, a procedure with a decision table and a done-checklist. Destination: a skill. No always-on content, so no AGENTS.md was written.

| Source | Activation there | Destination | Why | Changed or dropped |
|---|---|---|---|---|
| payments/.cursor/rules/refund-handling.mdc | model-decision | skill `refund-handling` | multi-step procedure used only when touching refund code | Rewritten as numbered workflow; frontmatter reduced to name, description, metadata.source; background/incident history cut to one clause |

## Created
- `payments/.agents/skills/refund-handling/SKILL.md` (source copy, read by most tools)
- `payments/.claude/skills/refund-handling/SKILL.md` (identical copy for Claude Code). Keep the two identical; `.agents` is the source.

## Facts kept
Table rows with `refund_full`, `refund_partial`, `credit_issued`, `REFUND_EXCEEDS_CAPTURE`, `CHARGE_DISPUTED`; 90-day limit; key `refund:<charge_id>:<request_id>`; `ledger_adjustments` and `refunds` in one transaction; `reconcile_refund` job; integer cents, currency match; all six checks; the SQL query.

## Dropped
- "Four incidents Jan to June, three double refunds" and "please read all of it" (history). Kept only the reason (money bugs, nightly reconciliation pages on-call).
- Cursor keys: `alwaysApply`.

## Notes
- Paths are under `payments/`, so tools pick it up when working in that service; a tool opened only at the repo root may need the skill at the root instead.
- The "integer cents, same currency" rule could also go in a `payments/AGENTS.md` if you want it always-on; I left it in the skill only.
- Old file: not deleted. Remove it after the team confirms the skill triggers; if kept for Cursor, the two copies can drift (Cursor still reads the .mdc as a model-decided rule).
- Verification: the description is under 700 characters, the name equals the folder, only allowed frontmatter keys. The inventory script only scans rule formats, so it still lists the .mdc.
- Per-tool check: ask each tool "which skills and instruction files did you load?" then "add a partial refund endpoint" and see that `refund-handling` loads.
