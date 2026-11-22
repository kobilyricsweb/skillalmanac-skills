# Consolidating Windsurf and Copilot rules into AGENTS.md plus skills (plan only, nothing changed)

Sources reviewed in `data-platform/`: `.windsurfrules`, `.windsurf/rules/{general,python-style,incident-runbook}.md`, `.github/copilot-instructions.md`. There is no `.claude/skills/` in the workspace, so no existing skill applied.

## Proposed split

### AGENTS.md (always-loaded, short, repo-wide facts)

| Rule | Source(s) | Note |
|---|---|---|
| Python 3.12, managed with uv, run with `uv run` | general.md, Copilot | Merged. `pyproject.toml` confirms `>=3.12`. |
| Docs site in `docs-site/` uses **pnpm** | general.md (Copilot says yarn) | Conflict, see below. |
| DAG files live in `dags/` and must not import from `notebooks/` | general.md | |
| Secrets come from the vault client `platform/secrets.py`; never read env vars for credentials | general.md | |
| Keep DAGs idempotent: a rerun for the same date gives the same output | `.windsurfrules`, Copilot | Merged. Keep the `.windsurfrules` wording, which is the more precise one. |
| Use polars, not pandas (in new code) | `.windsurfrules`, python-style.md | Merged. |
| Type hints on public functions | python-style.md, Copilot | Merged. |
| Use `pathlib`, not `os.path` | python-style.md | |
| SQL in `sql/` is formatted with sqlfluff | Copilot | See "Needs your decision". |
| Pointer: "For failed production DAG runs, use the `dag-failure-triage` skill" | new | One line, so the skill is discoverable. |

The three style rules (type hints, pathlib, polars) are short, so they go in AGENTS.md as a "Python style" section rather than a skill. A skill adds a loading step, and these should apply every time.

### Skill: `dag-failure-triage` (e.g. `.claude/skills/dag-failure-triage/SKILL.md`)

- Source: `incident-runbook.md` (a `model_decision` rule, which is already the same idea as a skill).
- The `description` comes from the rule's own description: use when a DAG run has failed in production and needs triage.
- The body is the 5-step runbook, unchanged: read the task log, check upstream freshness with `platform/freshness.py --dataset <name>`, do not rerun on an upstream schema change (open a ticket), rerun only the failed task with `airflow tasks clear`, record the incident in `docs/incidents/`.

### Nothing else needs a skill
The other rules are always-on conventions, not task-specific procedures.

## Conflicts and items needing your decision

1. **pnpm vs yarn.** general.md says pnpm and Copilot says yarn. The repo supports pnpm: `docs-site/package.json` has `"packageManager": "pnpm@9.12.0"` and there is a `pnpm-lock.yaml`. Plan: AGENTS.md says pnpm and the yarn line is dropped. Please confirm yarn is stale.
2. **sqlfluff / `sql/`.** Only Copilot mentions it, and there is no `sql/` directory in this checkout. Plan: keep it in AGENTS.md, but confirm it is still true. Otherwise it is a stale rule.
3. **Unverifiable references.** `platform/freshness.py` and `docs/incidents/` do not exist in this checkout. The runbook will be copied as-is, but they may be stale or live elsewhere.
4. **Scope of "polars not pandas".** `.windsurfrules` states it for everything, and python-style.md says "in new code" for `**/*.py`. Plan: use "in new code", which is the less ambiguous form.

## What we would lose

1. **Windsurf activation modes.** `always_on`, `glob` (`**/*.py`) and `model_decision` do not exist in AGENTS.md.
   - The Python style rules were glob-scoped to `.py` files. In AGENTS.md they become always loaded. This costs a few tokens on non-Python work and is otherwise harmless.
   - The runbook was model-decided. As a skill it is still loaded on demand, based on its description, so this is roughly equivalent.
2. **Tool-specific behaviour, if the tools are still used.** Windsurf only reads `.windsurf/rules` and `.windsurfrules`, and Copilot reads `.github/copilot-instructions.md` (and recent versions also read `AGENTS.md`). If anyone still uses Windsurf, check that their version reads `AGENTS.md`. Deleting the old files before checking would leave those users with no rules. Skills (`SKILL.md`) are not read by Windsurf or Copilot, so the triage runbook would be invisible to them. Option: keep a thin `.github/copilot-instructions.md` and `.windsurf/rules` stub that points to AGENTS.md and the runbook path.
3. **Duplicates collapse.** Idempotent DAGs, type hints, polars and uv each appear in two places and become one line. No information is lost, but the exact wording differs and we would pick one.
4. **Frontmatter metadata.** Only the trigger and glob fields go away. Nothing else is stored there.
5. **Per-tool wording quirks.** Nothing material, since the files contain no tool-specific instructions.

No rule content is lost outright if the decisions above are resolved. The yarn line is the only deliberate deletion, and the sqlfluff line is kept pending your confirmation.

## Suggested execution order (when you approve)
1. Create AGENTS.md with the merged rules.
2. Create the `dag-failure-triage` skill.
3. Decide on stubs or deletion for `.windsurfrules`, `.windsurf/rules/*` and `.github/copilot-instructions.md`, depending on whether Windsurf and Copilot are still in use.
