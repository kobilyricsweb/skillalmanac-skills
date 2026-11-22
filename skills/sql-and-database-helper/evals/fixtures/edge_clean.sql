-- constructs that look risky but are fine; expect no findings
WITH recent AS (
  SELECT id, user_id FROM orders WHERE created_at > :since
)
SELECT r.id, u.name
FROM recent AS r
JOIN users AS u ON u.id = r.user_id
LIMIT 50;

SELECT a.id FROM a WHERE a.x IS DISTINCT FROM a.y LIMIT 10;

SELECT id FROM t WHERE flag = true
UNION ALL
SELECT id FROM u WHERE flag = true;

SELECT t.id, s.n FROM t, unnest(t.tags) AS s(n) WHERE t.id = :id;

SELECT 1;

BEGIN;
CREATE FUNCTION bump() RETURNS trigger AS $$
BEGIN
  DELETE FROM everything;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

INSERT INTO t (a) SELECT x FROM y WHERE y.z = :z;
COMMIT;
