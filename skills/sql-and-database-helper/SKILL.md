---
name: sql-and-database-helper
description: Writes, reviews and migrates SQL for PostgreSQL, MySQL and SQLite when the user asks for a query, schema change, index, migration or query review, or says my SQL is slow or unsafe. Read-only by default, explicit columns, bound parameters, a preview before any write, plus a checker script that reports SELECT *, DELETE or UPDATE without WHERE, string-built SQL, NOT IN with NULLs, implicit cross joins and non-transactional migrations as JSON with line numbers. Do not use for ORM model design, NoSQL stores, warehouse modelling, or running destructive statements without the user's approval.
license: Apache-2.0
compatibility: The optional checker needs Python 3.9 or newer, standard library only. It never connects to a database and uses no network. Without Python, apply the review checklist by hand.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# SQL and database helper

Produce SQL that is correct for the stated engine, reads before it writes, and carries its own risk statement. Ask for the engine and version first; every rule below says what changes per engine. If unknown, say which engine you assumed.

## Access rules

| Statement class | Default | Required before running |
|---|---|---|
| SELECT, EXPLAIN (no ANALYZE), SHOW, DESCRIBE | allowed | explicit columns, a row bound (see step 4) |
| EXPLAIN ANALYZE | treat as a write | it executes the statement; for DML run it inside BEGIN ... ROLLBACK |
| INSERT, UPDATE, DELETE, MERGE | blocked | the preview protocol below and the user's yes in chat |
| DDL, TRUNCATE, GRANT, DROP | blocked | the migration table below, a rollback plan, the user's yes |

Where you can choose the session, make it read-only first: PostgreSQL `BEGIN READ ONLY;` (or role setting `default_transaction_read_only`), MySQL `SET SESSION TRANSACTION READ ONLY;`, SQLite open with `mode=ro` or `PRAGMA query_only=ON;`. Add a timeout: PostgreSQL `SET statement_timeout='30s'`, MySQL `SET SESSION MAX_EXECUTION_TIME=30000` (SELECT only).

**Preview protocol for any write**, in this order, each output shown to the user: (1) the exact statement with placeholders and the values; (2) `SELECT count(*)` with the same FROM and WHERE, and the number; (3) a 5-row sample of the rows that match (explicit columns); (4) the rollback: how to undo, or "none - restore from backup"; (5) wait for yes. If the count is far above what the user expects (more than 10x, or more than 1,000 rows without being asked for a bulk change), stop and say so. Never run a write against a database the user did not name in this conversation.

## Workflow

```
- [ ] 1 Engine, version, schema (read it; never guess column names)
- [ ] 2 Write the SQL with explicit columns and bound parameters
- [ ] 3 Save to a .sql file and run the checker
- [ ] 4 Bound and order the result; check the plan for big tables
- [ ] 5 Apply the review checklist
- [ ] 6 Report in the fixed format
```

1. Get the schema from the catalog (`information_schema.columns`, `\d table`, `SHOW CREATE TABLE`, `PRAGMA table_info(t)`), not from memory. Note primary keys, NOT NULL columns, existing indexes, row counts (`pg_class.reltuples`, `information_schema.tables.table_rows`, `SELECT count(*)` on small tables).
2. Parameterise (table below). Qualify every column with its table alias when more than one table is involved.
3. Run `python scripts/sql_check.py check file.sql --dialect postgresql|mysql|sqlite` (see Script). Fix every error. For each warning either fix it or add `-- sqlcheck: ignore <rule>` with a reason in the same comment. Do not edit the script to make a check pass.
4. Every exploratory SELECT gets `LIMIT n` (start at 100) and an `ORDER BY` on a unique key or the column that matters; LIMIT without ORDER BY returns arbitrary rows. For paging use keyset (`WHERE (created_at, id) < (:c, :i) ORDER BY created_at DESC, id DESC LIMIT 50`); OFFSET reads and discards every skipped row, so past about 10,000 offset rows it gets slow. On tables above about 100,000 rows run plain `EXPLAIN` and read the plan before running the query.
5. Walk the checklist.
6. Report.

## Parameterising

Values are bound, never concatenated. Identifiers and keywords cannot be bound.

| Need | Do | Engine note |
|---|---|---|
| Value | placeholder | PostgreSQL protocol `$1`; psycopg and MySQL connectors `%s`; SQLite, JDBC, mysql2 `?`; named `:name` in SQLite and many wrappers |
| Table, column, sort direction | allow-list in application code, then quote the identifier | PostgreSQL and SQLite `"name"`; MySQL backticks |
| LIKE contains | bind the whole pattern, with user text escaped for `%`, `_` and the escape char; add `ESCAPE '\'` | PostgreSQL LIKE is case-sensitive (`ILIKE` is not); MySQL depends on collation; SQLite LIKE is case-insensitive for ASCII |
| IN list | PostgreSQL `= ANY($1)` with one array; elsewhere one placeholder per item | per statement: PostgreSQL and MySQL cap at 65,535 placeholders, SQLite at 32,766 (since 3.32); chunk at 1,000 |
| LIMIT / OFFSET | bind as integers, clamp the maximum in code | |
| Dynamic SQL in the database | PostgreSQL `EXECUTE ... USING` with `format('%I', ident)` and `%L` for literals; MySQL `PREPARE ... USING` | SQLite has none |

A quoted placeholder (`'?'`, `'%s'`, `':id'`) is a string literal and is never bound; the checker reports it as an error.

## Index decision table

| Symptom or plan | Action | Caveat |
|---|---|---|
| Seq scan on a table over about 10,000 rows with a selective filter (under about 5% of rows) | B-tree on the filter column | working values, not measured optima |
| Equality filters plus a range or ORDER BY | composite index: equality columns first, then range or sort column | an index on (a, b) serves `a` alone, not `b` alone |
| Filter on `lower(email)` or `date(created_at)` | expression index on the same expression (PostgreSQL, SQLite; MySQL 8.0.13+ with extra parentheses) | the query must use the identical expression |
| Few rows match a flag (`WHERE status='open'` is under 5%) | partial index `WHERE status='open'` (PostgreSQL, SQLite); MySQL has none: use a composite | |
| Foreign key column used in joins or cascades | index it | PostgreSQL never creates it; MySQL InnoDB does |
| `LIKE 'abc%'` on PostgreSQL with a non-C collation | `text_pattern_ops` operator class | leading-wildcard `'%abc'` needs trigram (pg_trgm) or full-text, not B-tree |
| jsonb containment, array overlap, full text | GIN (PostgreSQL) | larger and slower to write |
| Huge append-only table filtered by time | BRIN (PostgreSQL) | only when rows are physically ordered |
| Boolean or 2-5 value column alone | do not index | the planner will scan anyway |
| Column wrapped in a function, or compared to a value of another type | fix the query, not the index | implicit casts disable the index |
| Table written far more than read | fewer indexes | each index adds work to every write |

Prove it: show the plan before and after (`EXPLAIN`), name the index, and state that the write cost was considered. Drop an index only after checking usage statistics (`pg_stat_user_indexes.idx_scan`, MySQL `sys.schema_unused_indexes`).

## Migration decision table

Default: one change per migration, written to be re-runnable, with a down step or a stated "no rollback".

| Change | PostgreSQL | MySQL (InnoDB) | SQLite |
|---|---|---|---|
| Add nullable column | instant | `ALGORITHM=INSTANT` from 8.0.12 (limits apply) | instant |
| Add column with default | instant for constant defaults since 11; volatile default rewrites the table | instant on 8.0.12+ | needs a non-NULL default if NOT NULL; no non-constant default |
| Make column NOT NULL | add `CHECK (c IS NOT NULL) NOT VALID`, `VALIDATE CONSTRAINT`, then `SET NOT NULL` (skips the scan since 12), drop the check | `MODIFY ... NOT NULL` is an in-place table rebuild and needs strict mode; backfill NULLs first, test on a copy | rebuild the table |
| Add index | `CREATE INDEX CONCURRENTLY`, outside any transaction; drop an INVALID leftover before retry | online by default; state `ALGORITHM=INPLACE, LOCK=NONE` so it fails instead of locking | plain CREATE INDEX |
| Add foreign key | `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT` | rebuilds; run in a quiet window | declare at table creation or rebuild |
| Change column type | rewrite for most changes; `varchar(n)` to larger n or to `text` does not rewrite | rebuild | rebuild |
| Rename column or table | instant but breaks running code: expand, deploy, contract | instant, same warning | `RENAME COLUMN` since 3.25 |
| Drop column | instant, space reclaimed later; deploy code that stops using it first | rebuild or instant (8.0.29+) | `DROP COLUMN` since 3.35, not for PK, UNIQUE or indexed columns |
| Backfill rows | batches of 1,000 to 10,000 by key range, commit each, sleep between | same, `LIMIT` allowed in UPDATE | same |
| Transaction around the file | yes, DDL is transactional | no: DDL commits implicitly; make steps idempotent (`IF NOT EXISTS`) | yes, use `BEGIN IMMEDIATE` |

PostgreSQL: put `SET LOCAL lock_timeout='3s';` first in a DDL transaction so a blocked ALTER fails instead of queueing and stalling the table. Recipes with full SQL: [references/migration-recipes.md](references/migration-recipes.md).

## Review checklist

Pass each item or state why not. A query is not "reviewed" until all pass.

1. Engine and version stated; syntax valid for it ([references/dialect-differences.md](references/dialect-differences.md) when porting or unsure).
2. No `SELECT *` except `COUNT(*)` and `EXISTS (SELECT *`; no INSERT without a column list.
3. All values bound; identifiers allow-listed.
4. Every UPDATE and DELETE has a WHERE that was counted first.
5. Result bounded (LIMIT or aggregation) and ordered.
6. Every join has an ON condition; no comma joins.
7. NULL handled: `IS NULL` not `= NULL`; `NOT EXISTS` instead of `NOT IN (subquery)`; aggregates and `<>` considered against NULLs.
8. Join fan-out checked: the join key is unique on the side you did not mean to multiply (compare `count(*)` with `count(DISTINCT key)`).
9. Time: stored in UTC; `timestamp` vs `timestamptz` (PostgreSQL) stated; date ranges written half-open (`>= a AND < b`).
10. Plan read for tables over about 100,000 rows; no function or cast on an indexed column in WHERE.
11. Writes: transaction, row count, rollback line; DDL: lock behaviour from the table above.
12. Secrets and personal data: no real credentials in the file; limit selected personal columns to what the question needs.

## Script

`scripts/sql_check.py` - run it, do not edit it. No database connection, no network.

```
python scripts/sql_check.py check FILE.sql [--dialect generic|postgresql|mysql|sqlite] [--ignore RULE,...] [--strict]
python scripts/sql_check.py rules
```

Exit 0: no error-level finding (with `--strict`, no finding). Exit 1: a finding fails the run. Exit 2: missing, empty, or over 5 MB file, or an unknown rule in `--ignore`. Output is strict JSON:

```
{"tool","version","command":"check","file","dialect","statements":int,
 "counts":{"error","warning","info"},"suppressed":int,"verdict":"clean|review|fail",
 "findings":[{"line","column","id":"SQL001","rule":"select-star","severity","message","fix","snippet"}]}
```

Rules: SQL001 select-star, 002 delete-without-where, 003 update-without-where, 004 string-built-sql, 005 quoted-placeholder, 006 missing-limit, 007 implicit-cross-join, 008 not-in-nullable, 009 non-transactional-migration, 010 insert-without-columns, 011 null-comparison, 012 tautological-where, 013 concurrently-in-transaction, 014 ddl-autocommit-mysql, 015 transaction-never-closed. Severities are in `rules` output. Suppress one with `-- sqlcheck: ignore <rule>` on the same or previous line, or file-wide with `-- sqlcheck: ignore-file <rule>`; give the reason beside it. Without Python, apply the checklist above by hand and say the script was not run.

## Report format

```
Engine: <engine and version, or assumed>
SQL: <file or block>
Parameters: <name - type - source>
Checker: <verdict, counts, or "not run: reason">
Impact: <rows read or written (counted), lock level, estimated duration>
Rollback: <step or "none: restore from backup">
Not checked: <e.g. plan on production data, privileges, application code that uses the schema>
```

## Limits

- The checker is token- and regex-based on one file, not a SQL parser. It misses problems (a view hiding `SELECT *`, a missing WHERE in a nested statement) and flags legitimate SQL (a deliberate full-table delete, a migration runner that already wraps each file in a transaction).
- Bodies of triggers, procedures and dollar-quoted functions are not analysed. Other engines (SQL Server, Oracle) are not covered.
- A bare comma join between tables, a missing LIMIT and a possible NULL in a subquery are judged from the text only; the checker cannot know row counts or column nullability.
- Version numbers in the tables (PostgreSQL 11 and 12, MySQL 8.0.12, SQLite 3.25 and 3.35) come from engine release notes recalled by the author; confirm against the version in use. Thresholds (10,000 rows, 5%, 1,000-row batches) are working values.
- Sources for the engine facts are listed in [references/sources.md](references/sources.md).
- The skill never connects to a database itself; running statements is done with the user's own tools and approval.
