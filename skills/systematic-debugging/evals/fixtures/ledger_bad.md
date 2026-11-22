# Ledger: invoice total is one cent too high

## Reproduction
- command: python -m billing.cli total --cart fixtures/cart_17.json
- reproduced: yes

## Hypotheses
### H1
- statement: Each line is rounded before summing
- prediction: Rounding once after the sum gives 0.25
- status: confirmed

### H2
- statement: The tax rate is parsed as a float
- prediction: Using an exact Decimal tax rate leaves the total unchanged
- status: open

### H3
- statement: The CLI formats numbers differently from the library
- status: open

## Experiments
### E1
- hypothesis: H1
- changed: rounding moment; tax rate parsing; cart fixture
- result: total is 0.25
- outcome: confirmed

## Root cause
It is probably the rounding in totals.py.

## Fix
- description: Sum unrounded Decimals and quantize once
- test: T1

## Regression test
- id: T1
- path: tests/test_totals.py::test_half_cent_lines_round_once
- failed before fix: no
