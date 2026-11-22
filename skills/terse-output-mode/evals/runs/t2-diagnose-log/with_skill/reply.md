Cause: each request builds a new `Pool` (`orders-api/src/db.js:4`, called at `orders-api/src/routes/orders.js:7`) and never closes it, so Postgres connections leak until the server hits its limit.
Evidence: "error: sorry, too many clients already" (code `53300`), then "unhandledRejection, exiting" at the last line of `orders-api/logs/error.log`; the route has no try/catch, so the rejected query crashes the process.
Fix:
```js
// orders-api/src/db.js
const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 20 });
module.exports = { getPool: () => pool };
```
```js
// orders-api/src/routes/orders.js, wrap the handler body
router.get('/orders/:id', async (req, res, next) => {
  try {
    const { rows } = await getPool().query('SELECT * FROM orders WHERE id = $1', [req.params.id]);
    if (rows.length === 0) return res.status(404).json({ error: 'not found' });
    res.json(rows[0]);
  } catch (e) { next(e); }
});
```
Keep `max` times the number of app instances below Postgres `max_connections`.
