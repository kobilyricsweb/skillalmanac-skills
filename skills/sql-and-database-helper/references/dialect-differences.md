## Contents

- Syntax and behaviour differences
- Type and time handling
- Concurrency and locking
- How to use this file

# Dialect differences that change the SQL

Read the section that matches the job (porting a query, choosing a type, locking). Version numbers are from engine release notes recalled by the author; check the version in use.

## Syntax and behaviour differences

| Topic | PostgreSQL | MySQL 8 (InnoDB) | SQLite |
|---|---|---|---|
| String concatenation | `a \|\| b` | `CONCAT(a, b)`; `\|\|` means OR unless `PIPES_AS_CONCAT` is set | `a \|\| b` |
| Quoting identifiers | `"name"`; unquoted names fold to lower case | backticks; `"x"` is a string unless `ANSI_QUOTES` | `"name"` (backticks and brackets also accepted) |
| Row limit | `LIMIT n`, or standard `FETCH FIRST n ROWS ONLY` | `LIMIT n` | `LIMIT n` |
| Limit on UPDATE or DELETE | none: batch with `WHERE id IN (SELECT id ... LIMIT n)` | `LIMIT n` (single table, optional ORDER BY) | only if built with the option; do not rely on it |
| Upsert | `INSERT ... ON CONFLICT (cols) DO UPDATE SET ...` | `INSERT ... ON DUPLICATE KEY UPDATE ...` | `INSERT ... ON CONFLICT (cols) DO UPDATE` since 3.24 |
| Return changed rows | `RETURNING` | none | `RETURNING` since 3.35 |
| Auto id | `GENERATED ALWAYS AS IDENTITY` | `AUTO_INCREMENT` | `INTEGER PRIMARY KEY` |
| String aggregate | `string_agg(x, ',')` | `GROUP_CONCAT(x SEPARATOR ',')`, truncated at `group_concat_max_len` | `group_concat(x, ',')` |
| FULL OUTER JOIN | yes | no: emulate with UNION of LEFT and RIGHT | since 3.39 |
| INTERSECT / EXCEPT | yes | since 8.0.31 | yes |
| Null-safe equality | `IS NOT DISTINCT FROM` | `<=>` | `IS` |
| Case sensitivity of `=` and LIKE | case-sensitive; `ILIKE` for insensitive | decided by collation, usually insensitive | `=` is case-sensitive; LIKE insensitive for ASCII |
| Division by zero | error | NULL (a warning; an error for strict-mode writes) | NULL |
| Integer division | `7/2` is 3 | `7/2` is 3.5000; `DIV` is integer | `7/2` is 3 |
| Skip locked rows | `FOR UPDATE SKIP LOCKED` (9.5+) | `FOR UPDATE SKIP LOCKED` (8.0+) | none; one writer at a time |
| Unicode text | UTF-8 database encoding | use `utf8mb4`; `utf8` is a 3-byte subset | UTF-8 text by default |
| Foreign keys | enforced | enforced for InnoDB | off unless `PRAGMA foreign_keys=ON` per connection |

## Type and time handling

| Topic | PostgreSQL | MySQL 8 | SQLite |
|---|---|---|---|
| Boolean | `boolean` | `TINYINT(1)` alias | integers 0 and 1 |
| Exact decimals | `numeric(p,s)` | `DECIMAL(p,s)` | stored as integer or float by affinity: keep money as integer cents |
| Time with zone | `timestamptz` stores a UTC instant; `timestamp` has no zone | `TIMESTAMP` converts through the session zone; `DATETIME` does not | no date type: text, real or integer; pick one format (ISO-8601 UTC text) |
| Typing | strict | strict in strict `sql_mode` (default since 5.7), otherwise silent truncation | flexible by affinity; `STRICT` tables since 3.37 |
| Placeholders per statement | 65,535 | 65,535 | 32,766 since 3.32 |

## Concurrency and locking

| Topic | PostgreSQL | MySQL 8 | SQLite |
|---|---|---|---|
| Default isolation | read committed | repeatable read | serializable (one writer) |
| DDL in a transaction | yes, rolls back | no: implicit commit | yes, rolls back |
| Take the write lock up front | `LOCK TABLE` or `SELECT ... FOR UPDATE` | `SELECT ... FOR UPDATE` | `BEGIN IMMEDIATE` |
| Guard against runaway queries | `statement_timeout`, `lock_timeout` | `MAX_EXECUTION_TIME` (SELECT), `innodb_lock_wait_timeout` | `PRAGMA busy_timeout` |
| Block UPDATE or DELETE without a key WHERE | none built in | `sql_safe_updates=1` | none |
| Plan | `EXPLAIN`; `EXPLAIN ANALYZE` runs it | `EXPLAIN`; `EXPLAIN ANALYZE` runs it (8.0.18+) | `EXPLAIN QUERY PLAN` |

## How to use this file

When a query is ported between engines, go row by row through the first table and rewrite each affected construct, then run the checker with the new `--dialect`. When the engine is unknown, write the SQL in the common subset (explicit JOIN, `LIMIT`, `COALESCE`, `CASE`) and say which rows above would change.
