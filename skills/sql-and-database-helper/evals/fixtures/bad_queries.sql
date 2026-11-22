-- exploratory queries for the orders report
SELECT * FROM orders;
SELECT o.id, c.name FROM orders o, customers c;
SELECT o.id FROM orders o, customers c WHERE o.customer_id = c.id;
DELETE FROM sessions;
UPDATE users SET active = false;
UPDATE users SET active = false WHERE 1=1;
SELECT id FROM users WHERE id NOT IN (SELECT manager_id FROM employees);
SELECT id FROM users WHERE id NOT IN (1, 2, NULL);
SELECT id FROM users WHERE deleted_at = NULL;
INSERT INTO audit VALUES (1, 'x');
SELECT id FROM users WHERE email = '?';
