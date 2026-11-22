-- reviewed: explicit columns, bounded, parameterised
SELECT o.id, o.total, c.name
FROM orders AS o
JOIN customers AS c ON c.id = o.customer_id
WHERE o.created_at >= :since
ORDER BY o.created_at DESC
LIMIT 100;

SELECT count(*) FROM orders;

SELECT status, count(*) AS n FROM orders GROUP BY status;

SELECT id FROM users u
WHERE NOT EXISTS (SELECT 1 FROM employees e WHERE e.manager_id = u.id);

SELECT id FROM users WHERE id NOT IN (SELECT manager_id FROM employees WHERE manager_id IS NOT NULL);

SELECT id FROM users WHERE EXISTS (SELECT * FROM orders o WHERE o.user_id = users.id);

BEGIN;
UPDATE users SET nickname = NULL WHERE id = :id;

DELETE FROM sessions WHERE expires_at < :cutoff;

INSERT INTO audit (user_id, note) VALUES (:user_id, 'it said: DELETE FROM x; SELECT * FROM y');
COMMIT;

SELECT id FROM users WHERE name LIKE '%' || :q || '%' LIMIT 20;

/* SELECT * FROM commented_out; */
SELECT extract(year FROM created_at) AS y, a * b AS area FROM shapes WHERE id = :id;
