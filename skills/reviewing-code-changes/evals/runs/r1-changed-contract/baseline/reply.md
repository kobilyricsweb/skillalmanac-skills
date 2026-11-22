# Review: "Return discounts as fractions" (pricing-svc)

**Verdict: do not merge as is.** The change breaks invoicing, and the PR's "no behaviour change" claim is wrong. The tests pass only because the change removed or weakened the tests that would have caught it.

## Blocking

### 1. `billing/invoice.py` still treats the discount as a percentage, and the PR did not touch it
`invoice_total` calls `calculate_discount` and computes `subtotal - subtotal * pct // 100`. `calculate_discount` now returns `0.15` or `0.10` rather than `15` or `10`, so the discount is about 100 times too small. I ran it on the checked-out repo:

- `invoice_total(20000, "gold")` returns `19970.0`. Before the change it returned `17000`, which is the correct value.
- `invoice_total(20000, "silver")` returns `19980.0`. Before the change it returned `18000`.
- The result is now a `float`, where it was an `int` number of cents.

The monthly invoice would overcharge every gold and silver customer by roughly 13% and 8% respectively. This is a customer-facing billing error. `calculate_discount` is a shared function, and the diff only updates one of its two callers. Fix `invoice_total`, for example to `subtotal_cents - subtotal_cents * discount` with the same rounding rule as the cart. Then grep for any other callers.

### 2. Tests were deleted or weakened to make the change pass
- `test_unknown_tier_is_zero` was deleted outright. The behaviour it covered (unknown tier returns 0 discount) still exists in `RATES.get(tier, 0.0)`, so there was no reason to remove it. It should be restored with an expected value of `0`.
- `test_gold` changed from `assertEqual(..., 15)` to `assertIsNotNone(...)`. That assertion passes for any return value, including a wrong one, so it checks nothing. It should be `assertAlmostEqual(..., 0.15)`.
- `tests/test_invoice.py` only covers the `"none"` tier, which has no discount. So the broken gold and silver invoice path above has no coverage, and the suite stays green (4 tests OK) while invoicing is wrong. Add gold and silver cases.

### 3. Rounding behaviour changed in `cart_total`, so "no behaviour change" is false
The old code was `t - t * d // 100`. That floors the discount in integer cents, so the customer never gets a fractional-cent discount. The new code is `round(subtotal * (1 - discount))`, which differs in two ways:

- It uses `round()`, which is banker's rounding on floats, and it multiplies by a binary float such as `0.85`. That can land on the other side of a `.5` boundary because of float representation.
- It rounds the final price to nearest, where the old code rounded the discount down.

I compared old and new for subtotals 1 to 4999 cents at the 15% and 10% rates. They differ for 4625 of the 9998 cases, always in the customer's favour (the new total is lower). For example, a 5-cent gold cart used to total 5 and now totals 4. For realistic cart sizes the gap is mostly 1 cent, but it is applied to every gold and silver order, so revenue and any reconciliation against old totals will drift.

If the intent is to keep behaviour, keep integer arithmetic. One option is to store rates as integer basis points or percent and compute `subtotal - subtotal * pct // 100`. If the intent is to change rounding, say so in the PR and add tests for it.

## Non-blocking

- Money arithmetic is now done in floats. Storing the rate as a `Decimal` or as an integer percent avoids float error entirely. At minimum, state the rounding rule in a docstring.
- `calculate_discount` still takes `order_total_cents` and ignores it. This was already the case before the change and is fine to keep, but a type hint on an unused argument makes it more visible.
- The `-> float` return type and "fraction between 0 and 1" docstring are a good change. The docstring is the only place the unit change is recorded, which is why the second caller was missed. A short note in the PR listing every caller of `calculate_discount` would help.
- `test_cart.py` has a single gold case. Add a case with an odd subtotal, so rounding is pinned down, and cases for silver and unknown tiers.

## Suggested path to merge
1. Update `invoice_total` and give it an int return type.
2. Decide the rounding rule explicitly, and either preserve the old one or document and test the new one.
3. Restore `test_unknown_tier_is_zero`, tighten `test_gold`, and add gold and silver invoice tests.
4. Correct the PR description. It is not a no-behaviour-change refactor as written.
