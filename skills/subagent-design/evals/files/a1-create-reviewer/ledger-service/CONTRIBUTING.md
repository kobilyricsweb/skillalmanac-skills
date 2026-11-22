# Contributing

## Database migrations

Rules the reviewers enforce (two incidents in 2025 came from breaking them):

1. Every `NNN_name.up.sql` has a matching `NNN_name.down.sql` that really reverses it.
2. Each migration starts with `SET lock_timeout = '5s';`. A migration that waits on a lock took the API down in March.
3. `ledger_entries` has more than 50 million rows. Indexes on it are created with `CREATE INDEX CONCURRENTLY`, in a migration of their own, outside a transaction.
4. Expand and contract: never drop or rename a column in the same release that stops using it. Drop in a later migration, after the code that reads it has shipped.
5. No data backfills inside schema migrations. Backfills go in `db/backfills/` and run as jobs.

## Tests

`npm test`. Migration files are not covered by tests.
