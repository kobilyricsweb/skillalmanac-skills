# Planted defects (never shown to executors)

r1 pricing-svc
- billing/invoice.py (not in the diff) still computes `subtotal - subtotal * pct // 100` with the new fractional result, so a gold invoice of 20000 gives 19970.0 instead of 17000 (wrong amount, and a float). No existing test covers a discounted invoice.
- tests/test_discounts.py: gold assertion weakened to assertIsNotNone; unknown-tier test deleted.
- Bait: type hints, renames, RATES constant (all fine).

r2 orders-node
- GET /orders/:id/invoice: no requireOwner (the sibling routes use it; middleware comment says every id route must).
- Same route: SQL built with a template string from req.params.id.
- GET /orders: OFFSET page * PAGE_SIZE, page defaults to 1, so the first page is skipped. No validation of page (NaN, negative).
- POST /orders/:id/cancel: empty catch around the refund, then the order is marked cancelled.

r3 notifier
- Timeout 30 -> 3 seconds while PR says no behaviour change; README says provider p99 is about 8 s.
- with_retry catches Exception (was ConnectionError), so programming errors and non-retryable failures are retried.
- migrations/0007: NOT NULL column without default on a table with 40M rows fails; plain CREATE INDEX locks writes; PR calls it an index migration.
- Bait: renames, list comprehension, new test (all fine).
