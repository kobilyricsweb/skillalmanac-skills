# Reply

Created `ledger-service/.claude/agents/migration-reviewer.md`, a read-only subagent (tools: Read, Grep, Glob, Bash limited to read-only git commands) that reviews migration files in `ledger-service/db/migrations/`.

Why:
- **Auto-pickup:** the description says "Use proactively" and names the paths and file types (`db/migrations/`, `*.up.sql`, `*.down.sql`) and the merge/PR moment, so the main agent delegates when migrations are touched. Delegation still depends on the harness; try it on two or three real changes.
- **Placed inside `ledger-service/`**, the project you named, so it travels with that project in version control.
- **Applies the five rules from `CONTRIBUTING.md`** (up/down pair, `lock_timeout`, `CREATE INDEX CONCURRENTLY` on `ledger_entries` in its own migration, expand and contract, no backfills), each with its reason, since migrations have no test coverage and these rules came from real incidents.
- **Fixed short report** (PASS/BLOCK/NEEDS-INFO, file:line plus quoted line, not-checked list, at most 30 lines) so the caller can verify findings without redoing the review.
- It cannot ask questions, so it states assumptions instead. It never edits files. Model is `inherit` because the review needs judgement.

The definition passes the bundled lint script. Spot-check its first few findings against the files.
