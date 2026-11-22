## Contents

- Recipe 1: add a NOT NULL column to a large PostgreSQL table
- Recipe 2: add an index without blocking writes
- Recipe 3: add a foreign key
- Recipe 4: rename a column with no downtime
- Recipe 5: batched backfill
- Recipe 6: SQLite table rebuild
- Recipe 7: MySQL online change

# Migration recipes

Each recipe is one or more files, in order. Table `orders` and the column names are examples. Read only the recipe that matches the change.

## Recipe 1: add a NOT NULL column to a large PostgreSQL table

File 1 (transaction, fast):
```sql
BEGIN;
SET LOCAL lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN plan text;                         -- nullable: no rewrite
ALTER TABLE orders ADD CONSTRAINT orders_plan_nn CHECK (plan IS NOT NULL) NOT VALID;
COMMIT;
```
Deploy code that writes `plan`. Run Recipe 5 to backfill. File 2:
```sql
ALTER TABLE orders VALIDATE CONSTRAINT orders_plan_nn;           -- scans, blocks no writes
BEGIN;
SET LOCAL lock_timeout = '3s';
ALTER TABLE orders ALTER COLUMN plan SET NOT NULL;               -- scan skipped by the valid check (PostgreSQL 12+)
ALTER TABLE orders DROP CONSTRAINT orders_plan_nn;
COMMIT;
```
Before PostgreSQL 12 the SET NOT NULL scans the table while holding the strongest lock; schedule it. Adding the column with a constant `DEFAULT` and `NOT NULL` in one statement is also instant since 11; use the steps above when the value has to be computed.

## Recipe 2: add an index without blocking writes

PostgreSQL, one statement per file, never inside BEGIN:
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_customer ON orders (customer_id);
```
It takes two table scans and waits for old transactions. If it fails or is cancelled it leaves an INVALID index: find it with `SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;`, `DROP INDEX CONCURRENTLY` it, and retry. For a unique constraint: build a unique index concurrently, then `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE USING INDEX idx_name;`. MySQL: `ALTER TABLE orders ADD INDEX idx_customer (customer_id), ALGORITHM=INPLACE, LOCK=NONE;`. SQLite: plain `CREATE INDEX IF NOT EXISTS`.

## Recipe 3: add a foreign key

PostgreSQL:
```sql
ALTER TABLE orders ADD CONSTRAINT orders_customer_fk FOREIGN KEY (customer_id) REFERENCES customers (id) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_customer_fk;
```
Also index `orders (customer_id)`: PostgreSQL does not, and deletes on `customers` scan `orders` without it. MySQL creates the index itself if none exists but rebuilds the table; run in a quiet window. SQLite: foreign keys are declared in `CREATE TABLE`; adding one later means Recipe 6.

## Recipe 4: rename a column with no downtime

Expand: add `new_name`, write both columns from the application (or a trigger), backfill with Recipe 5. Switch reads to `new_name`. Contract in a later release: stop writing `old_name`, then drop it. A direct `RENAME COLUMN` is instant on all three engines (SQLite 3.25+) but breaks every running instance that still uses the old name; use it only with a full stop or on a table nobody else reads.

## Recipe 5: batched backfill

PostgreSQL (repeat until 0 rows, committing each batch, pausing between):
```sql
UPDATE orders SET plan = 'basic'
WHERE id IN (SELECT id FROM orders WHERE plan IS NULL ORDER BY id LIMIT 5000);
```
MySQL: `UPDATE orders SET plan = 'basic' WHERE plan IS NULL ORDER BY id LIMIT 5000;`. SQLite: the subquery form. A batch size of 1,000 to 10,000 is a working range; shrink it when replication lag or lock waits rise. Report the total rows changed. The loop belongs in the application or a script, not in one giant transaction.

## Recipe 6: SQLite table rebuild

For anything ALTER cannot do (change a type, add a constraint, drop a keyed column). Turn foreign keys off first (the pragma is a no-op inside a transaction), then check them before commit:
```sql
PRAGMA foreign_keys = OFF;
BEGIN;
CREATE TABLE orders_new (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers (id), total INTEGER NOT NULL);
INSERT INTO orders_new (id, customer_id, total) SELECT id, customer_id, total FROM orders;
DROP TABLE orders;
ALTER TABLE orders_new RENAME TO orders;
-- recreate indexes, triggers and views that referenced orders
PRAGMA foreign_key_check;
COMMIT;
PRAGMA foreign_keys = ON;
```

## Recipe 7: MySQL online change

State the algorithm so MySQL refuses instead of silently locking: `ALTER TABLE orders ADD COLUMN plan VARCHAR(20) NULL, ALGORITHM=INSTANT;` (8.0.12+), else `ALGORITHM=INPLACE, LOCK=NONE`. If MySQL answers that the clause is not supported, the change needs a table copy: run it on a replica or a copy first, or use an external online-schema-change tool, and say so in the report. DDL commits implicitly, so keep one DDL statement per migration and make it re-runnable.
