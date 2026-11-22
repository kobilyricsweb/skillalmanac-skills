-- one transaction for the schema change and the backfill
BEGIN;
SET LOCAL lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN status text;
UPDATE orders SET status = 'open' WHERE status IS NULL;
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;
COMMIT;

-- must run outside the transaction above
CREATE INDEX CONCURRENTLY idx_orders_status ON orders (status);
