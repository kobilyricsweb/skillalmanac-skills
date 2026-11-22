# Mocks and edge cases

Read this when deciding what to fake, or when the edge-case checklist in SKILL.md needs worked prompts. Contents: test doubles, the adapter pattern, edge-case prompts, one worked cycle, sources.

## Test doubles in one table

| Kind | What it does | Use for | Danger |
|---|---|---|---|
| Stub | Returns canned answers | Inputs from a dependency (a price lookup) | None if answers are realistic |
| Fake | A small working replacement (in-memory repository) | Storage, queues, clocks | Drifts from the real thing: run one contract test against both |
| Spy | Records calls, real behaviour otherwise | Checking that a side effect happened | Over-asserting on calls |
| Mock | Pre-programmed with expected calls, fails on mismatch | Rarely; when the interaction is the requirement | Couples tests to implementation |

Prefer stubs and fakes. Use a mock or spy only when the observable result of the code is the call itself.

## Adapter pattern for things you do not own

1. Write a thin class that exposes only what your code needs (`send_receipt(order)`), wrapping the HTTP client or SDK.
2. Your logic depends on that class; tests give it a fake that records messages.
3. Write one slow test for the adapter that runs against the real service or a recorded response, kept out of the default fast run.

## Edge-case prompts

For each input ask: what is the smallest, the largest, the empty, the wrong type, the repeated, the out-of-order, the failing neighbour?

- Money: 0.00, 0.005 rounding, negative refunds, currencies with no decimals.
- Pagination: zero results, exactly one page, one more than a page, a page past the end.
- Parsing: leading or trailing whitespace, byte-order mark, mixed line endings, unknown fields, missing required fields.
- Idempotence: the same request twice must not double the effect.
- Concurrency: two writers on the same record; assert the final state, not the order.

## One worked cycle (Python)

Behaviour: `total` sums prices and rejects negatives.

1. RED: `test_total__empty_cart__returns_zero` against a stub that raises `NotImplementedError`. It fails with that error: right reason (behaviour missing).
2. GREEN: `return 0`. Passes.
3. RED: `test_total__two_items__returns_sum`, `total([1, 2])` expects 3. Fails: got 0.
4. GREEN: `return sum(prices)`. Both pass. This is triangulation.
5. Mutation check: change `sum` to `max`; the second test fails, so it guards the line. Restore.
6. RED: `test_total__negative_price__raises_value_error`. GREEN: add the guard. REFACTOR: extract the validation into a helper, run the tests.

## Sources (summarised in the author's own words; the pages were not re-fetched while authoring)

- pytest, how skip and xfail work and why `reason` exists: https://docs.pytest.org/en/stable/how-to/skipping.html
- Python unittest, skipping tests and expected failures: https://docs.python.org/3/library/unittest.html#skipping-tests-and-expected-failures
- Jest API, `test.skip` and `test.only`: https://jestjs.io/docs/api
- Fowler, test double vocabulary: https://martinfowler.com/bliki/TestDouble.html
- Fowler, mocks versus stubs and state versus behaviour verification: https://martinfowler.com/articles/mocksArentStubs.html
