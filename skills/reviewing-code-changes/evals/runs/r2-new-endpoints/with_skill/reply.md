Verdict: Do not merge - the invoice endpoint is SQL-injectable and lets any logged-in user read anyone's invoice, and cancel marks orders cancelled even when the refund fails.

Blocking
1. orders-node/src/routes/orders.js:29 - invoice query is built with a template string, `... WHERE order_id = ${req.params.id}`.
   Fails when: `GET /orders/0 OR 1=1/invoice` (URL-encoded) -> query becomes `WHERE order_id = 0 OR 1=1`, returns the first invoice of any customer; stacked/UNION payloads can read other tables (verified by: read; the id goes unescaped into the SQL text).
   Fix: `db.query('SELECT * FROM invoices WHERE order_id = $1', [req.params.id])`, as `loadOrder` does.

2. orders-node/src/routes/orders.js:28 - the invoice route has only `requireAuth`, not `requireOwner(loadOrder)`. The repo rule in middleware/auth.js says "Every route that takes a resource id must use this", and `GET /orders/:id` and cancel both do.
   Fails when: user A requests `/orders/<B's order id>/invoice` -> 200 with B's invoice, with no ownership check (verified by: read; no user_id check anywhere in the handler).
   Fix: `router.get('/orders/:id/invoice', requireAuth, requireOwner(loadOrder), ...)`, then query by `req.order.id`.

3. orders-node/src/routes/orders.js:38-41 - `catch (err) {}` swallows any refund failure, and the status update then runs anyway, followed by `{ ok: true }`.
   Fails when: the processor rejects (declined, timeout, charge already refunded) -> order is set to `cancelled`, customer is told ok, and no money is returned. Nothing is logged, so support cannot find it (verified by: read).
   Fix: on a refund error, return 502 and leave the status unchanged. Update the status only after the refund succeeds, and log the error.

4. orders-node/src/routes/orders.js:36 - cancel has no state check or idempotency guard.
   Fails when: the same `POST /orders/5/cancel` is sent twice (mobile retry, double tap), or sent for an order already cancelled -> `processor.refund(charge_id, total_cents)` is called each time, so the customer is refunded repeatedly (verified by: read; nothing reads `req.order.status`).
   Fix: return 409 if `req.order.status` is already `cancelled`, or use `UPDATE orders SET status='cancelled' WHERE id=$1 AND status <> 'cancelled' RETURNING *` before refunding. Pass an idempotency key to the processor, if it supports one.

Should fix
5. orders-node/src/routes/orders.js:17 - offset is `page * PAGE_SIZE` with `page` starting at 1.
   Fails when: `GET /orders` (page 1) -> OFFSET 20, so the user's first 20 orders are never returned. A user with 20 or fewer orders sees an empty list (verified by: read).
   Fix: `(page - 1) * PAGE_SIZE`.

6. orders-node/src/routes/orders.js:15 - `page` is not validated.
   Fails when: `?page=abc` -> NaN offset, `?page=0` -> negative offset; Postgres rejects the query and the async handler throws. Express 4.19 does not catch rejected promises, so the request hangs or the error goes unhandled (verified by: read).
   Fix: clamp with `Math.max(1, parseInt(...) || 1)`, and wrap async handlers in try/catch or an async wrapper.

7. No tests are added for any of the three endpoints, which include a money path and an authorization path. The repo has no test setup (package.json has no test script).
   Fix: add tests for cross-user invoice access, refund failure on cancel, double cancel, and the page 1 offset.

Notes
- The PR description says nothing about refunds, which move real money. Mention it and the failure behaviour.
- `SELECT *` on orders and invoices returns every column to the client, so check that no internal fields are exposed to the mobile app.

Checked: read PR.md, change.diff, and the repo files src/routes/orders.js, src/middleware/auth.js, src/refunds.js, src/processor.js, src/db.js and package.json. Ran scripts/diff_risk_map.py, which flagged the string-built SQL and the swallowed error; I confirmed both by reading. Searched for other users of `requireOwner` and `loadOrder` (only orders.js). No tests exist, so none were run.
Not checked: the real processor's behaviour (here it is a stub that always succeeds), the invoices schema and indexes, and whether `req.user` is populated correctly upstream. I ran none of the failing inputs against a database.
