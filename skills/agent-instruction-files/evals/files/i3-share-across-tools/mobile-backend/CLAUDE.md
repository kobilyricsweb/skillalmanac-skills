# mobile-backend

## Commands

- Build: `make build`
- Test: `make test` (needs `make db-up` first)
- Lint: `make lint`
- Regenerate queries after editing `internal/db/queries/*.sql`: `make sqlc`

## Rules

- Go 1.22. Do not use features from later versions.
- Handlers live in `internal/api/`; they call services in `internal/service/`, never the DB package directly.
- SQL lives only in `internal/db/queries/`. Generated code in `internal/db/gen/` is never edited by hand.
- Errors are wrapped with `fmt.Errorf("...: %w", err)`; no bare returns of driver errors.
- Every new endpoint gets an entry in `docs/openapi.yaml` in the same change.
- Money is integer cents (`int64`). No floats for money anywhere.

## Claude Code only

- Use the `db-reviewer` subagent for anything under `migrations/`.
- A PostToolUse hook already runs gofmt on edited files. Do not run gofmt yourself.
