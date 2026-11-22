# One source of truth for agent instructions in mobile-backend

## Layout

```
mobile-backend/AGENTS.md   shared rules: the only place they are edited
mobile-backend/CLAUDE.md   "@AGENTS.md" import + Claude-only notes
```

- **Codex** reads `AGENTS.md` directly.
- **Cursor** reads `AGENTS.md` in the project root directly.
- **Claude Code** reads `CLAUDE.md`, which imports `AGENTS.md` with `@AGENTS.md`. Claude Code only falls back to `AGENTS.md` when no `CLAUDE.md` exists, so the import line is required.
- I deleted `.cursor/rules/general.mdc`. It was an always-on rule that duplicated `AGENTS.md`, so Cursor would have loaded every rule twice. Add a `.cursor/rules/*.mdc` file only for something Cursor-specific or glob-scoped.

## Files

- `mobile-backend/AGENTS.md` (new, 14 lines): commands and rules merged from both old files.
- `mobile-backend/CLAUDE.md` (22 lines -> 4 lines): the import plus the Claude-only notes (`db-reviewer` subagent, gofmt hook). Those stay here because the other tools have no subagents or hook.
- `mobile-backend/.cursor/rules/general.mdc`: removed.
- `mobile-backend/.claude/agents/db-reviewer.md`: untouched.

## Conflicts and fixes

- **Go version**: `CLAUDE.md` said 1.22 and the Cursor rule said 1.21. `go.mod` says `go 1.22`, so 1.22 wins. The Cursor copy was stale.
- **No-logging rule**: "Never log request bodies" (PII, logs shipped to a third party) existed only in the Cursor rule, so Claude Code users never saw it. It is now in the shared file.
- **Test failure hint**: I added "a database connection error means the container is not running". It is derived from the `db-up` target, which starts the database container.

All commands were checked against the `Makefile`.

## Audit

I ran `scripts/instruction_file_audit.py` on both files. It reports no missing commands. It flags four paths that do not exist in this checkout: `internal/service/`, `internal/db/queries/`, `internal/db/gen/` and `migrations/`. I left them in because they describe the intended layout, and `gen/` is created by `make sqlc`. If those directories should exist already, check the rules still match the code.

## How to confirm

In a fresh session in `mobile-backend/`, ask each tool: "List the instruction files you loaded and quote the first line of each." In Claude Code, `/memory` also lists loaded files. Each tool should show `# mobile-backend` from `AGENTS.md`.

## Keeping it in sync

Edit shared rules only in `AGENTS.md`. Put tool-only notes in that tool's file. Personal preferences go in each tool's user-level file, not in the repo.

Loading behaviour was taken from the skill's reference file, which was read from each tool's docs on 2026-11-20. A tool update can change it.
