# Review: orders-node (order list, invoice, cancel)

**Verdict: do not merge as is.** Two blockers (one is a security hole), plus several should-fix items.

## Blockers

### 1. Invoice endpoint: SQL injection and missing ownership check (`src/routes/orders.js`, GET `/orders/:id/invoice`)
```js
router.get('/orders/:id/invoice', requireAuth, async (req, res) => {
  const { rows } = await db.query(`SELECT * FROM invoices WHERE order_id = ${req.params.id}`);
```
- **SQL injection.** `req.params.id` is concatenated straight into the SQL string. Any authenticated user can send e.g. `/orders/0 OR 1=1/invoice` or a stacked/UNION payload to read or alter arbitrary data. Use a parameter: `db.query('SELECT * FROM invoices WHERE order_id = $1', [req.params.id])`.
- **Broken access control (IDOR).** The route uses only `requireAuth`, not `requireOwner(loadOrder)`. `auth.js` says "Every route that takes a resource id must use this." As written, any logged-in user can download the invoice of any order id, which leaks other customers' data. The other two id-based routes (`GET /orders/:id`, cancel) do use it. Add `requireOwner(loadOrder)` before the handler.

Both fixes are needed; parameterizing alone still leaves the IDOR.

### 2. Cancel swallows refund failures and cancels anyway (`POST /orders/:id/cancel`)
```js
try { await refunds.issue(req.order); } catch (err) {}
await db.query('UPDATE orders SET status = $1 ...', ['cancelled', req.order.id]);
res.json({ ok: true });
```
If the processor call fails (timeout, declined, outage), the error is silently ignored, the order is marked `cancelled`, and the client gets `{ ok: true }`. The customer is told they were refunded when they were not, and nothing records that a refund is owed. This is a money-correctness bug. At minimum: do not mark cancelled and return a 5xx (and log) when the refund fails. Better:
- Check the current status first and reject if already cancelled (see next point), and only refund orders that were actually paid.
- Make the refund idempotent (pass an idempotency key such as the order id to the processor) and record refund state (e.g. `refund_id`, `refund_status`) so a failed or unknown refund can be retried or reconciled.
- Do the status update and refund bookkeeping in a way that cannot leave "cancelled but not refunded" silently (transaction or explicit `refund_pending` state).

## Should fix

### 3. Cancel is not idempotent and has a double-refund race
There is no check of `req.order.status`. Calling cancel twice (mobile retry, double tap) issues a second full refund for the same charge. Two concurrent requests both read the unchanged order and both refund. Guard with an atomic conditional update, e.g. `UPDATE orders SET status='cancelled' WHERE id=$1 AND status IN (<cancellable states>) RETURNING *`, and only refund if a row was updated. Also decide which statuses may be cancelled (shipped/delivered orders should presumably be rejected).

### 4. Pagination is off by one and unvalidated (GET `/orders`)
```js
const page = parseInt(req.query.page || '1', 10);
... OFFSET page * PAGE_SIZE
```
Default page is 1 but the offset is `page * 20`, so the first page returned skips the first 20 orders and page 1 starts at order 21 (page 0 is the real first page). Use `(page - 1) * PAGE_SIZE`. Also validate: `?page=abc` gives `NaN` (query error / 500), `?page=-1` gives a negative OFFSET (Postgres error), and a very large value is allowed. Clamp to an integer >= 1. Ordering by `id` is stable but returns oldest first; confirm that is what the app wants (newest first is typical for an order list). Consider returning a total or `hasMore` so the client knows when to stop.

### 5. Unhandled promise rejections in async handlers
Express 4.19 does not catch rejected promises from async handlers. Any DB error (including the NaN/negative-offset cases above, or a failed `UPDATE` in cancel) leaves the request hanging and can raise an unhandled rejection. Wrap handlers (or add an async wrapper) and return a 500. The same applies to `requireOwner`'s `await load(req)`, which is pre-existing but now used by more routes.

### 6. `SELECT *` leaks internal columns
List and invoice endpoints return full rows, including `charge_id` (a payment processor identifier) and whatever else the tables contain, to the mobile client. Select an explicit column list for the API response.

## Minor / nits
- `refunds.js` passes `order.total_cents` as the refund amount. Confirm this is the amount actually charged (discounts, partial shipments, previous partial refunds) and that the processor call returns something worth persisting; the result of `refunds.issue` is currently discarded.
- No tests are included for any of the three endpoints. At least add tests for: non-owner gets 403 on invoice, SQL metacharacters in id, first page contents, cancel when the refund throws, double cancel.
- `PR.md` is very thin. It should mention the new `refunds` module, the status transitions allowed for cancel, and that refunds hit a payment processor.
- `GET /orders/:id/invoice` returns 404 when there is no invoice, but the same 404 vs 403 distinction elsewhere reveals which order ids exist; once `requireOwner` is added this is consistent with the existing routes, so no extra action needed.

## Summary of required changes before merge
1. Parameterize the invoice query and add `requireOwner(loadOrder)`.
2. Stop swallowing refund errors; do not mark cancelled or return `ok` on refund failure.
3. Make cancel idempotent / state-checked.
4. Fix the page offset and validate `page`.
