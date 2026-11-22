# Listing page content: sql-and-database-helper

**One line:** Safe SQL and schema changes for PostgreSQL, MySQL and SQLite: read-only by default, with a static checker.

## What it does

The skill gives an agent a fixed procedure for SQL work: read the schema from the catalog, write with explicit columns and bound parameters, save the SQL to a file, run a checker, bound and order the result, walk a 12-item review checklist, and report impact and rollback. Writes are blocked until a preview protocol (the statement, a row count, a 5-row sample, a rollback line) is shown and the user says yes. Decision tables cover indexes and migrations with the behaviour of each engine stated per row, and a reference lists the syntax and locking differences that change the SQL. `scripts/sql_check.py` reads one `.sql` file, never connects to a database, and prints strict JSON with line numbers for 15 rules.

## Capabilities

- `scripts/sql_check.py check FILE.sql --dialect postgresql|mysql|sqlite|generic`: JSON findings with line, column, rule, severity, message, fix and the source line; verdict clean, review or fail; exit 1 on error-level findings
- Rules: `SELECT *`, `DELETE`/`UPDATE` without `WHERE`, always-true `WHERE`, string-built SQL, quoted placeholders, missing `LIMIT`, implicit cross joins, `NOT IN` with a nullable subquery, multi-statement files outside a transaction, `INSERT` without a column list, `= NULL`, `CONCURRENTLY` inside a transaction, MySQL DDL inside a transaction, unclosed transaction
- Inline and file-wide suppression comments, so a judged exception stays visible in the file
- Migration recipes with full SQL (NOT NULL column, concurrent index, foreign key, rename, batched backfill, SQLite rebuild)

## When to use

You ask for a query, an index, a schema change, a migration or a review of a `.sql` file, or say your SQL is slow, unsafe, or returns no rows with `NOT IN`.

## When not to use

ORM model design, NoSQL stores, data-warehouse or dimensional modelling, infrastructure provisioning, or any request to run destructive statements without your approval. Other engines (SQL Server, Oracle) are not covered.

How it differs from the other data skills in this catalogue: `dataset-field-profiler` measures the contents of data files; `join-cardinality-audit` checks join fan-out in data. This skill writes and checks SQL text and schema changes.

## Requirements

Python 3.9 or newer for the checker (standard library only). No network, no database connection. Without Python the agent applies the checklist by hand and says the script was not run.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent output. What exists is the checker on saved fixtures (`python evals/run_fixtures.py`, 13/13 cases):

1. `python scripts/sql_check.py check evals/fixtures/migration_pg_bad.sql --dialect postgresql`: 6 statements, verdict `fail`, exit 1. Findings: line 2 SQL009 (three changes outside a transaction), line 5 SQL015 (`BEGIN;` never committed), line 6 SQL013 (`CREATE INDEX CONCURRENTLY` inside a transaction, error).
2. `python scripts/sql_check.py check evals/files/t1-report/report.sql --dialect postgresql`: verdict `fail`, 1 error and 4 warnings: line 2 SQL001 and SQL007 (`SELECT *` over a comma join), line 5 SQL008 (`NOT IN` subquery), line 7 SQL009, line 8 SQL003 (`UPDATE customers SET segment = 'lapsed'` with no `WHERE`).

## Limits

- Token- and regex-based on one file, not a SQL parser; it misses some problems and flags some legitimate SQL.
- Bodies of triggers, procedures and dollar-quoted functions are not analysed.
- Row counts and column nullability are unknown to it, so `LIMIT`, comma-join and `NOT IN` findings are judged from the text only.
- Engine version numbers in the tables were recalled by the author from release notes; thresholds are working values.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN; 13 script fixture cases pass with expected values read by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, a real database, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a slow report query with `SELECT *` and a comma join; the agent saves it to a file and runs the checker: verdict fail, line numbers shown.
2. The agent rewrites it with explicit columns, `JOIN ... ON`, `NOT EXISTS`, bound parameters and `LIMIT`, and re-runs the checker: clean.
3. A request to deactivate old accounts: the agent shows the count and a 5-row sample and waits for yes.
4. A migration request on a 40-million-row table: three files, index built concurrently outside a transaction.

## FAQ seeds

- Does it connect to my database? No. The script reads a file; running statements is done with your own tools and your approval.
- Does it need network access? No.
- Which databases? PostgreSQL, MySQL (InnoDB, 8.x) and SQLite. The tables state the difference per engine.
- Will it block me from running a delete? It refuses to run writes before showing a count and sample and getting your yes in chat; it does not stop you from running them yourself.
- My migration runner already wraps files in a transaction; the checker complains. Add `-- sqlcheck: ignore-file non-transactional-migration`.
- How is it different from asking an agent to "write safe SQL"? It adds a preview protocol, engine-specific migration and index tables and a repeatable file check. No comparison run has been done yet.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet. Accountable editor: Global Media Holdings.
