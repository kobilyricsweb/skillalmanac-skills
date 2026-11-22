# Reply

I created one project subagent: `.claude/agents/migration-reviewer.md`.

- **What it does:** reviews changes under `ledger-service/db/migrations/` before merge. It checks the five migration rules in `ledger-service/CONTRIBUTING.md`: matching up/down pairs, `SET lock_timeout = '5s';` first, `CREATE INDEX CONCURRENTLY` in its own non-transactional migration for `ledger_entries`, expand-and-contract for column drops/renames, and no backfills in schema migrations. It returns APPROVE / APPROVE WITH NITS / BLOCK with file:line findings.
- **Automatic pickup:** the `description` field says to use it proactively whenever migration files (or `db/backfills/`) are added, changed or deleted, or when a migration review or merge is requested. Claude Code delegates based on that description.
- **Why read-only:** its tools are limited to Read, Grep, Glob and Bash, so it reports problems and never edits migrations. The migration rules caused two incidents in 2025, and migrations have no test coverage, so review is the only safety net.
- **Why the rules are repeated in the agent:** it is told to re-read CONTRIBUTING.md first, so that file stays the source of truth if the rules change.

Note: a description cannot guarantee delegation every time. For a hard guarantee, add a CI check or a hook.
