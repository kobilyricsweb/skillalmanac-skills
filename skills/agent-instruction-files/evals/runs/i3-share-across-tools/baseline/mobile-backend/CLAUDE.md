@AGENTS.md

## Claude Code only

- Use the `db-reviewer` subagent for anything under `migrations/`.
- A PostToolUse hook already runs gofmt on edited files. Do not run gofmt yourself.
