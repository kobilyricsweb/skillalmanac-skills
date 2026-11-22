START TRANSACTION;
ALTER TABLE orders ADD COLUMN status VARCHAR(20) NULL;
UPDATE orders SET status = 'open' WHERE id > 0;
COMMIT;
ALTER TABLE orders ADD INDEX idx_status (status);
ALTER TABLE orders ADD INDEX idx_created (created_at);
