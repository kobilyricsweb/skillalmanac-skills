# Ledger: invoice total is one cent too high

## Reproduction
- command: python -m billing.cli total --cart fixtures/cart_17.json
- reproduced: yes
- minimised: cart with two items at 0.125 and 0.125 and a 0% tax rate; total prints 0.26, expected 0.25
- bisect: git bisect between v2.3.0 (good) and v2.4.0 (bad) names commit 9f2c1ab, which swapped Decimal rounding for round()

## Hypotheses
### H1
- statement: Each line is rounded before summing, so two half-cent lines each round up
- prediction: Summing unrounded values and rounding once gives 0.25 on the minimised cart
- status: confirmed

### H2
- statement: The tax rate of 0% is applied as 1.0 plus noise from float parsing
- prediction: Changing the cart tax rate to 0.0 exact leaves the total at 0.26
- status: refuted

### H3
- statement: The CLI formats the number with a different rounding mode than the library
- prediction: Calling the library function directly in a REPL prints 0.25
- status: refuted

## Experiments
### E1
- hypothesis: H1
- changed: rounding moment (per line before sum, to once after sum)
- result: minimised cart total is 0.25
- outcome: confirmed

### E2
- hypothesis: H2
- changed: tax rate literal (0 to 0.0)
- result: total still 0.26
- outcome: refuted

### E3
- hypothesis: H3
- changed: entry point (CLI to direct library call)
- result: library call also prints 0.26
- outcome: refuted

## Root cause
Commit 9f2c1ab rounds each line item with round() before summing in billing/totals.py line_total(); half-cent lines round up independently, so the sum drifts by one cent.
- hypothesis: H1

## Regression test
- id: T1
- path: tests/test_totals.py::test_half_cent_lines_round_once
- failed before fix: yes
- failure output: AssertionError: Decimal('0.26') != Decimal('0.25')

## Fix
- description: Sum unrounded Decimals and quantize once in invoice_total()
- test: T1
- test passes after: yes
