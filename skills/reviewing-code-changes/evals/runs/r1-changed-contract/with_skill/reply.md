Verdict: Do not merge - the diff changes `calculate_discount`'s units but `billing/invoice.py` still treats the result as a percentage, so monthly invoices are almost undiscounted.

Blocking
1. billing/invoice.py:6-7 (not in the diff) - `pct = calculate_discount(...)` / `return subtotal_cents - subtotal_cents * pct // 100` still assumes whole-number percent. It now gets 0.15 and divides by 100 again.
   Fails when: any gold or silver invoice -> discount is about 1/100 of intended and the result is a float (verified by running: `invoice_total(20000, "gold")` returns `19970.0`, expected `17000`; `invoice_total(20000, "silver")` returns `19980.0`, expected `18000`). Customers are overbilled on every discounted invoice.
   Fix: change the invoice to the new contract, in integer cents with the same rounding as the old code (or share one helper with the cart), and add a gold/silver test for `invoice_total`.

2. checkout/cart.py:7 - `round(subtotal * (1 - discount))` replaces the integer floor-of-discount arithmetic, so the PR's "No behaviour change" is false for the cart.
   Fails when: the discount has a fractional cent -> the customer is charged one cent less than before (verified: silver, 5 cents: old 5, new 4; silver, 25 cents: old 23, new 22). Python `round` also rounds half to even, and floats are used for money.
   Fix: keep the old rule, e.g. `discount_cents = subtotal * rate_pct // 100`, with rates stored as integer percent or basis points, or explicitly decide and document the new rounding.

Should fix
3. tests/test_discounts.py:8 - gold test weakened from `assertEqual(..., 15)` to `assertIsNotNone(...)`, which passes for any value, including the 15 that would now be wrong. Restore an exact check: `assertAlmostEqual(..., 0.15)`.
4. tests/test_discounts.py - `test_unknown_tier_is_zero` was deleted though the behaviour still exists (`RATES.get(tier, 0.0)`). Restore it, expecting 0.0.
5. The existing suite passes only because `test_invoice` uses tier "none" (no discount) and the cart test uses gold on 2000 cents, where rounding does not differ. No test covers a discounted invoice, which is why item 1 is invisible to CI.

Notes
- README gives the test command `python -m unittest discover -s tests -t .`; from the repo root I ran `python -m unittest discover -s . -t .`.

Checked: ran the suite (4 tests, OK, so it does not catch items 1-2); searched the whole repo for `calculate_discount` and `cart_total` (callers: checkout/cart.py, billing/invoice.py, tests); read invoice.py, README and all tests.
Not checked: other services or clients outside this repo that may call `calculate_discount`; production invoice data and how many invoices were affected if a similar change has already shipped.
