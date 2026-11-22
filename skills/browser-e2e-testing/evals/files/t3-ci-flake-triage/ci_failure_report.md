# CI report, test "user can place an order" (Playwright, 4 CI workers, 1 retry)

Last 30 runs on main: 9 failed on the first attempt, 7 of those passed on the retry, 2 failed both attempts. Locally (1 worker): 30 of 30 pass.

Failure from the trace of a failed first attempt:

    Error: expect(locator).toHaveText(expected)
    Locator: getByTestId('order-total')
    Expected: "$42.00"
    Received: "$84.00"

Facts gathered:
- All users in the suite log in as the same seeded account, qa@example.test.
- The "place an order" test and the "add a gift card" test both add items to that account's cart.
- No test clears the cart. The suite's global setup resets the database once, before the first test.
- The failing runs always had both tests scheduled at the same time on different workers.
- Source code for the test contains one line: `await page.waitForTimeout(3000)` after clicking "Add to cart", added last month "to make it stable".
