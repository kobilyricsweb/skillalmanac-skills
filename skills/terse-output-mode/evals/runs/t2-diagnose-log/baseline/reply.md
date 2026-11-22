Cause: `getPool()` in `src/db.js` builds a new `Pool` (max 20) on every call, and `src/routes/orders.js` calls it on every request. Each request opens its own pool and connections, and none are ever closed. Postgres hits its connection limit ("too many clients already", 53300). The handler has no try/catch, so the failed query becomes an unhandledRejection and the process exits.

Fix:
1. Create the pool once in `src/db.js`: `const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 20 }); module.exports = { pool };`. In the route, use `pool.query(...)` and don't create a pool.
2. Wrap the handler in try/catch and return 500 on error, so a DB error can't crash the process.
3. Make sure instances × `max` stays under Postgres `max_connections`.
