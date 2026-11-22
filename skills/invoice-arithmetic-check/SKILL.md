---
name: invoice-arithmetic-check
description: "Checks the arithmetic of invoices, quotes and supplier bills with exact decimal maths: line totals, subtotal, discount, tax at the rates the user states, rounding policy, currency consistency, duplicate invoice numbers, numbering gaps and due dates from payment terms, and returns strict JSON with a delta per invoice. Use when the user says check my invoice, do these totals add up, did the supplier overcharge me, find duplicate invoices, or needs net 30 due-date maths. Do not use for tax advice or which rate applies, legal validity, bookkeeping entries, OCR of scans, creating invoices, or making payments."
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in the last section.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Invoice arithmetic check

Verify that the numbers on an invoice follow from each other, to the last minor unit, and say exactly where they do not. This skill does arithmetic. It never says which tax rate is correct, whether a document is legally valid, whether a charge is deductible, or whether to pay.

## Boundary rule

Tax rates, discounts and terms are inputs the user states or the document shows. Read them as given and check the maths at that rate. If asked "is 20% the right rate" or "is this a valid invoice", answer that this is outside the check and point to the user's tax authority or accountant. Do not guess a missing rate from the country or the product. A rate the script reports as implied (stated tax divided by base) is arithmetic, not a finding about the right rate.

## Collect before running

Ask for anything missing; do not assume.

1. **Currency** (three-letter code). It sets the decimals: 0 for JPY and KRW, 3 for KWD and BHD, otherwise 2. Details in [references/rounding-and-terms.md](references/rounding-and-terms.md).
2. **Rounding method**, which the script requires explicitly: `line` (round each line net, tax rounded per rate group), `total` (no rounding until the end) or `line_tax` (each line's tax rounded too). If the user does not know, run `line`, then read the `matches_other_rounding` hints and say which method reproduces the stated total.
3. **Rounding mode**: `half_up` (default), `half_even` or `down`.
4. **Tax rates per line or per invoice**, read as percent (`20` means 20%). Whether prices already include tax (not supported: see Limits).
5. **Document type**: invoice or `credit_note`. Negative quantities are only normal on credit notes.
6. **Whose sequence it is**: gap checking is only meaningful for the user's own issued invoices; never run it on a pile of supplier bills.
7. **Dates** as `YYYY-MM-DD`. Ask the order before converting `03/04/2026`.

## Workflow

```
- [ ] 1 Put the data in JSON or CSV (never retype amounts from memory)
- [ ] 2 Run the script, always with an explicit --rounding
- [ ] 3 Read errors, then warnings, then info
- [ ] 4 Re-run if an input was corrected, never edit the script
- [ ] 5 Report in the fixed format
```

1. **Prepare input.** For pasted text or a PDF the user already extracted, write a CSV (one row per line item; header fields on the first row of each invoice) or JSON. Field names are in the table below and in [references/issue-codes.md](references/issue-codes.md). Keep amounts as plain numbers: no `1,200`, no currency symbols. In CSV the rows of one invoice must be adjacent.
2. **Run** from the skill folder:

```bash
python scripts/check_invoices.py invoices.json --rounding line --currency EUR
python scripts/check_invoices.py bills.csv --rounding total --mode half_even --as-of 2026-12-01
python scripts/check_invoices.py mine.json --rounding line --check-sequence --output report.json
```

   `--output` writes the report to a new file and refuses the input path, even with `--force`. Exit 0 means no error-level issue, 1 means at least one, 2 means a usage or input problem.
3. **Triage** with the tables below. A single-cent difference is not an accusation; a difference larger than one minor unit on any line is.
4. **Report** in the fixed format below. Quote the `delta`, the line number and the code.

## Input fields

| Level | JSON key (CSV column) | Meaning |
|---|---|---|
| Invoice | `number`, `supplier`, `issue_date`, `due_date`, `terms`, `currency`, `type` | `terms`: `net 30`, `eom 30`, `due on receipt`, `2/10 net 30` |
| Invoice | `tax_rate`, `discount_percent` or `discount_amount` | One discount only; both is an error |
| Invoice | `stated_subtotal`, `stated_discount`, `stated_tax`, `stated_total` | What the document prints; compared with the computed figure |
| Invoice | `rounding` object `{method, mode, places}` | Overrides the command line for that invoice |
| Line | `description`, `quantity`, `unit_price`, `discount_percent`, `tax_rate`, `line_total` (CSV: `line_discount_percent`) | `line_total` is the net amount after the line discount, before invoice discount and tax |

Unknown keys are reported as `unknown_field` warnings so a typo such as `stated_totl` cannot silently skip a check.

## Decision tables

**Tolerance** (one minor unit is 0.01 for 2 places, 1 for JPY, 0.001 for KWD):

| Absolute delta, stated minus computed | Severity | Meaning |
|---|---|---|
| 0 | none | Agrees exactly |
| at most 1 minor unit | `info` | Rounding-sized; check `matches_other_rounding` |
| more than 1 minor unit, on any line or any total | `error` | Real difference |

**Issue severity** (full catalogue with next action in [references/issue-codes.md](references/issue-codes.md)):

| Severity | Examples | Verdict effect |
|---|---|---|
| `error` | `line_total_mismatch`, `total_mismatch`, `duplicate_invoice_number`, `negative_quantity_not_credit_note`, `mixed_currency_in_invoice`, `due_before_issue`, `unparseable_number` | verdict `fail`, exit 1 |
| `warning` | `possible_double_billing`, `sequence_gap`, `due_date_mismatch`, `tax_rate_missing`, `tax_rate_fraction_suspected`, `duplicate_line`, `mixed_currencies_in_file` | verdict `review` |
| `info` | rounding-sized deltas, `matches_other_rounding`, `due_on_weekend`, `stated_tax_implies_rate` | no effect |

**Duplicates.** Same supplier and same number (case, spaces and punctuation ignored) is an `error`. Same supplier, issue date and amount under different numbers is a `warning`, not proof; ask the user. The same number from different suppliers is only `info`.

**Due dates** come from `terms` by fixed rules: `net N` is issue date plus N days; `eom N` is the last day of the issue month plus N days; `due on receipt` is the issue date. No business-day or holiday shift is applied; a weekend due date is flagged `info`. When both a stated due date and terms exist and disagree, the script reports the day difference and treats the stated date as the one in force for `days_until_due`.

## Output contract

The script prints strict JSON (no NaN, ASCII only). Money values are strings so no digit is lost.

```
{ "tool": "check_invoices", "source": "<file name>",
  "defaults": {"rounding", "mode", "places", "currency"},
  "invoices": [ { "index", "number", "supplier", "type", "currency",
      "rounding": {"method", "mode", "places"},
      "issue_date", "due_date", "computed_due_date", "due_basis", "days_until_due",
      "early_payment": null | {"discount_percent", "pay_by", "discount_on_total", "discount_on_pretax_base"},
      "lines": [ {"line", "description", "quantity", "unit_price", "computed_net", "stated_net", "delta"} ],
      "computed_subtotal", "computed_discount", "computed_tax", "computed_total", "total_basis",
      "stated_subtotal", "stated_discount", "stated_tax", "stated_total",
      "delta",
      "issues": [ {"severity", "code", "field", "line", "message"} ] } ],
  "file_issues": [ ... ], "sequence_gaps": [ ... ],
  "summary": {"invoices", "errors", "warnings", "info", "verdict": "pass|review|fail",
              "by_currency": {"EUR": {"invoices", "computed_total", "stated_total"}}} }
```

`delta` is stated minus computed. A null computed value means the invoice could not be computed; the issue list says why. `early_payment` gives both bases because contracts differ on whether the discount applies before or after tax; do not pick one for the user.

## Report format

```
Checked: <n invoices>, currency <code>, rounding <method/mode/places>, tax rates as stated by you
Verdict: <pass | review | fail>
Errors: <invoice number, line, code, stated vs computed, delta> one per line
Warnings: <same shape>
Rounding-sized differences: <count, and which method reproduces the stated total if a hint exists>
Dates: <computed due dates, overdue days if --as-of was used>
Not checked: tax rate correctness, legal validity, goods or services delivered, bank details, the source scan
```

If the verdict is `pass`, say that the arithmetic is consistent at the stated rates and nothing more.

## Script

`scripts/check_invoices.py`: run it, do not edit it to make a check pass. It reads one JSON or CSV file, uses `decimal` for all money maths, and writes only to an explicit `--output` file that is never the input. It has no network access and no clock; `--as-of` supplies today's date.

## Limits

- Arithmetic only. It cannot tell whether a rate, a discount or a term is lawful or agreed.
- Prices that already include tax (`prices_include_tax`) are not supported: lines are checked, totals are not computed, and a warning says so.
- Dates must be `YYYY-MM-DD`; other formats are rejected, not guessed.
- Payment terms understood: the four forms above. Anything else gives `terms_unparsed`.
- Cash rounding to 0.05, withholding tax, deposits, partial payments and multi-currency conversion are not modelled; handle them as separate lines the user states.
- With several tax rates and an invoice-level discount, the discount is shared across rate groups in proportion to their net amounts. If the issuer shared it differently, expect a cent-level `info` difference.
- In CSV, rows of one invoice must be adjacent; a number that reappears later is read as a new invoice and flagged as a duplicate.
- Input files over 5 MB are refused.
- A file of mixed currencies is checked invoice by invoice; totals are never added across currencies.

## Manual fallback without Python

For each invoice: multiply quantity by unit price, apply the line discount, round per the stated method, sum the lines, apply the invoice discount, apply tax per rate group at the stated rates, and compare each result with the printed figure using the tolerance table. Then list duplicate numbers by eye, compare issue and due dates, and compute due dates from the terms rules above. State in the report that the check was done by hand and could not use exact decimal arithmetic.
