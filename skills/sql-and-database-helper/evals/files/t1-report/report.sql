-- weekly revenue report (PostgreSQL 15)
SELECT * FROM orders o, customers c WHERE o.customer_id = c.id AND o.created_at > '2026-01-01';

SELECT id, email FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders);

UPDATE orders SET status = 'archived' WHERE created_at < now() - interval '2 years';
UPDATE customers SET segment = 'lapsed';
