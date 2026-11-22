# data-platform: consolidation plan (nothing changed)

Inventory found 5 source files, 594 bytes always loaded today. Paths below are relative to `data-platform/`.

## Table

| Source | Activation there | Destination | Why | Changed or dropped |
|---|---|---|---|---|
| `.windsurfrules` | always (legacy format) | root `AGENTS.md` | Two short conventions | Both lines are duplicates of lines elsewhere (polars, idempotent DAGs); merged, file contributes nothing new |
| `.github/copilot-instructions.md` | always | root `AGENTS.md` | Short conventions | Python/uv, type hints, idempotent DAGs merged as duplicates; yarn line dropped (conflict, see below); sqlfluff line kept with a caveat |
| `.windsurf/rules/general.md` | always | root `AGENTS.md` | Core conventions | Kept: uv run, pnpm, dags must not import `notebooks/`, secrets via `platform/secrets.py` |
| `.windsurf/rules/python-style.md` | glob `**/*.py` | root `AGENTS.md` (or `AGENTS.md` nested only if a Python dir is chosen) | Glob covers essentially the whole Python repo | Type hints (dup), pathlib not `os.path`, polars in new code (dup, wording merged). Glob scoping is lost |
| `.windsurf/rules/incident-runbook.md` | model-decision, has description | skill `dag-failure-triage` | A 5-step procedure used only during incidents | Rewritten as a skill; one-line pointer in `AGENTS.md` optional |

## Proposed root AGENTS.md (about 10 lines)

- Python 3.12, managed with uv; run things with `uv run`.
- Docs site in `docs-site/` uses pnpm (pinned `pnpm@9.12.0`).
- DAGs in `dags/` are idempotent (a rerun for the same date gives the same output) and must not import from `notebooks/`.
- Credentials come from the vault client in `platform/secrets.py`; never read env vars for them.
- Type hints on every public function; `pathlib`, not `os.path`.
- DataFrames: polars, not pandas (existing pandas code may stay; new code uses polars).
- SQL in `sql/` is formatted with sqlfluff (see verification note).
- DAG failed in production: use the `dag-failure-triage` skill.

## Proposed skill: `dag-failure-triage`

- Install in `.agents/skills/dag-failure-triage/SKILL.md` (source) and `.claude/skills/dag-failure-triage/SKILL.md` (identical copy).
- Frontmatter: only `name` and `description`. Suggested description: "Guides triage of a failed production Airflow DAG run: read the failed task log, check upstream data freshness, decide between a task rerun and a ticket, and record the incident. Use when a DAG run has failed, a pipeline is red, or someone asks to debug or rerun a failed task. Do not use for writing new DAGs or for local test failures."
- Body: the five steps in the same order, keeping exact strings: `platform/freshness.py --dataset <name>`, `airflow tasks clear`, `docs/incidents/`. Hard rules stay next to their steps: on an upstream schema change do not rerun and open a ticket for the owning team; rerun only the failed task, never the whole DAG.
- The windsurf `trigger: model_decision` and its description map directly onto the skill description, so little is lost here.

## Conflicts and evidence

1. **yarn vs pnpm for `docs-site/`.** Copilot says yarn, Windsurf general says pnpm. Repo evidence: `docs-site/package.json` has `"packageManager": "pnpm@9.12.0"` and `docs-site/pnpm-lock.yaml` exists; there is no yarn.lock. Settled on pnpm; the Copilot yarn line is dropped and should be reported to the team as a stale rule.
2. **polars vs pandas.** Not a real conflict: `.windsurfrules` says "not pandas" without qualification, `python-style.md` limits it to new code. Plan uses the narrower, more precise wording. Please confirm that existing pandas code is acceptable.
3. **Duplicates merged:** idempotent DAGs (3 sources), polars (2), type hints (2), Python 3.12 + uv (2).

## Verification notes (referenced paths missing from this checkout)

These could not be confirmed in the repo, so they should be checked before they go into always-on text or the skill: `platform/freshness.py` (not present), `docs/incidents/` (not present), `sql/` (not present, so the sqlfluff rule has nothing to apply to here), `notebooks/` (not present). `dags/daily_sales.py`, `platform/secrets.py`, `pyproject.toml` (requires-python >=3.12) do exist. The `uv run` claim has no uv.lock to confirm it; I found none.

## What we lose or weaken

- **Path scoping:** `python-style.md` applied only to `**/*.py` in Windsurf. In AGENTS.md those rules load for every task, including non-Python work. The cost is tiny (3 lines). If scoping matters, use a nested `AGENTS.md` in a Python directory, but the glob spans the repo so root is simpler.
- **Windsurf activation modes:** always / glob / model-decision become always-on (AGENTS.md) or description-triggered (skill). Whether the skill triggers depends on each tool and on the description wording; test with real requests such as "the daily_sales DAG failed".
- **Tool-specific loading:** Copilot and Windsurf have their own always-loaded files. Check each tool's current support for AGENTS.md and skills (see the skill's source-formats reference); where a tool does not read AGENTS.md, keep a thin pointer in its own file.
- **Dropped:** the yarn line, and the redundant duplicates. No facts are otherwise lost; the incident runbook keeps all five steps and every command.

## Old files

Do not delete in the same step. Recommended: after the team confirms the new setup loads in Windsurf and Copilot, remove `.windsurfrules` (legacy format), `.windsurf/rules/general.md`, `python-style.md`, `incident-runbook.md`, and `.github/copilot-instructions.md`, or reduce the last one to a pointer to AGENTS.md. If they stay as they are, any tool that reads both loads the always-on content twice and the stale yarn line keeps misleading Copilot, so the copies will drift.

## Per-tool check

In each of Windsurf, Copilot and Claude Code, ask: "Which instruction files and skills did you load? Which package manager does docs-site use?" Expected: AGENTS.md loaded, answer pnpm. Then say "a DAG run failed in production" and confirm `dag-failure-triage` is picked up.
