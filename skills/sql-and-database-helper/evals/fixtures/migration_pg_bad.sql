-- add a status column and backfill it
ALTER TABLE orders ADD COLUMN status text;
UPDATE orders SET status = 'open' WHERE status IS NULL;
CREATE INDEX idx_orders_status ON orders (status);
BEGIN;
CREATE INDEX CONCURRENTLY idx_orders_created ON orders (created_at);
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;
