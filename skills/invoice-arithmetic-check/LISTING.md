# Listing page content: invoice-arithmetic-check

**One line:** Checks invoice and bill arithmetic to the last cent with exact decimals, never tax or legal advice.

## What it does

The skill takes invoice data (CSV or JSON) with quantities, unit prices, discounts, the tax rates the user states and the printed totals. It asks for the currency and the rounding policy first, because the same lines give different totals under per-line and end-of-invoice rounding. A script using Python `decimal` recomputes every line, subtotal, discount, tax and grand total, compares each with the printed figure, and grades the difference: one minor unit or less is information, more is an error. It also flags duplicate invoice numbers, possible double billing, numbering gaps, mixed currencies, negative quantities not marked as credit notes, and due dates that disagree with the payment terms. Output is strict JSON.

## Capabilities

- Line, subtotal, discount, tax and total verification with three rounding methods (`line`, `total`, `line_tax`) and three modes (`half_up`, `half_even`, `down`)
- Hint naming the rounding method that reproduces a printed total
- Duplicate invoice numbers, same supplier/date/amount under different numbers, gaps in your own sequence
- Due dates from `net N`, `eom N`, `due on receipt` and `2/10 net 30`, with overdue days when you give a date
- Currency decimals by ISO minor unit (JPY 0, KWD 3, default 2)
- A fixed report: errors, warnings, rounding-sized differences, dates, what was not checked

## When to use

You say: check my invoice, do these totals add up, did the supplier overcharge me, find duplicate invoices, what is the due date on net 30.

## When not to use

Which tax rate applies, whether an invoice is legally valid, bookkeeping entries, bank reconciliation, scanning a receipt, creating an invoice, currency conversion, chasing payment.

How it differs from nearby skills: `inventory-count-reconciliation-plan` reconciles stock counts, `weighted-rate-audit` audits blended rates, `spreadsheet-analysis` and `excel-formula-debugger` work on general sheets, `offer-comparison-matrix` compares offers. This one verifies invoice arithmetic and duplicates in exact decimals.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the manual procedure in the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output from the saved fixture `evals/files/t1-supplier-bill/bill.csv` (a supplier bill with one wrong line):

```
python scripts/check_invoices.py evals/files/t1-supplier-bill/bill.csv --rounding line
```

Result (trimmed to the key fields):

```
N-5521: subtotal 148.75, tax 29.75, computed_total 178.50, stated_total 179.50, delta 1.00
error line_total_mismatch (line 2): stated 78.80, computed 77.80 (delta 1.00)
error total_mismatch: stated 179.50, computed 178.50 (delta 1.00)
summary.verdict: fail
```

Second example, `evals/fixtures/rounding_hint.json`: three sweets at 0.333 each with a printed total of 1.00. Under `line` rounding the computed total is 0.99 (delta 0.01, info) and the report adds that the printed total equals the total under method `total`.

## Limits

- Arithmetic only; it cannot say whether a rate, discount or term is lawful or agreed.
- Tax-inclusive pricing, cash rounding to 0.05, withholding tax, deposits and currency conversion are not modelled.
- Dates must be `YYYY-MM-DD`; terms must be one of four recognised forms.
- Gap checking is meaningful only for your own issued invoices.
- In CSV, the rows of one invoice must be adjacent.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN, and 11 script fixture cases pass with expected values worked out by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a supplier bill as CSV and answer the two questions the agent asks (currency, rounding).
2. Run the script: verdict fail, line 2 delta 1.00.
3. The agent reports the toner line as the cause of the whole 1.00 difference, and states it did not check the VAT rate.
4. Run a second file with a one-cent difference: the report names the other rounding method that reproduces it.

## FAQ seeds

1. Does it need network access? No.
2. Will it tell me which VAT or sales tax rate to use? No; it checks the maths at the rate you state.
3. Why does it ask for a rounding method? The same lines give totals one cent apart under per-line and end-of-invoice rounding.
4. Can it read a PDF invoice? No; the agent must first put the amounts into CSV or JSON. Check those figures against the PDF yourself.
5. Is a one-cent difference an error? No; one minor unit or less is information, more is an error.
6. How is it different from a spreadsheet check? Exact decimal arithmetic, duplicate and sequence checks, and date arithmetic in one JSON report.
7. How do I uninstall it? Delete the skill folder.

## Changelog

- 0.1.0, 2026-11-21: first draft; lint and script fixtures run; not re-verified by any other method.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted with AI assistance (claude-sonnet-5-5) under the Skill Almanac Editorial name; the accountable editor is Global Media Holdings. No human review has taken place yet.
