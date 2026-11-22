## Contents

1. CSV columns
2. Issue codes and what to do next
3. File-level issues

Read the section you need; this file links to nothing else.

## 1. CSV columns

Header names are matched case-insensitively with spaces read as underscores. Comma, semicolon and tab delimiters are detected from the header line. Required columns: `quantity`, `unit_price`.

| Column | Level | Notes |
|---|---|---|
| `invoice_number`, `supplier` | invoice | Consecutive rows with the same number and supplier form one invoice; blank on both continues the previous invoice |
| `issue_date`, `due_date`, `terms`, `currency`, `type`, `discount_percent`, `discount_amount`, `prices_include_tax`, `stated_subtotal`, `stated_discount`, `stated_tax`, `stated_total` | invoice | First non-blank value in the invoice's rows is used; a different later value gives `inconsistent_field_across_rows` |
| `description`, `quantity`, `unit_price`, `line_discount_percent`, `tax_rate`, `line_total` | line | `tax_rate` is per line in CSV; percent, so `20` |
| `currency` | line too | A line whose currency differs from the invoice's gives `mixed_currency_in_invoice` |

A row with no description, quantity, price, rate or line total is treated as a header-only row (for example a totals row) and adds no line. Unknown columns give an `unknown_column` file warning.

## 2. Issue codes and what to do next

| Code | Severity | Meaning | Next action |
|---|---|---|---|
| `line_total_mismatch` | info if within 1 minor unit, else error | Printed line amount differs from quantity x price after line discount | Ask for the corrected line; quote the line number and delta |
| `subtotal_mismatch`, `discount_mismatch`, `tax_mismatch`, `total_mismatch` | info or error by the same rule | Printed figure differs from the computed one | If `matches_other_rounding` appears, confirm the issuer's method; else report the delta |
| `matches_other_rounding` | info | The printed total equals the total under another method | State which method reproduces it; re-run with that method |
| `stated_tax_implies_rate` | info | Printed tax over the computed base gives this percent | Report as arithmetic only; never say which rate is right |
| `discount_not_supplied` | warning | A discount is printed but no discount input was given | Ask whether a discount applies and at what rate or amount |
| `tax_rate_missing` | warning | No rate for at least one line; tax not computed (total uses the stated tax if given) | Ask the user for the rate |
| `tax_rate_fraction_suspected` | warning | A rate between 0 and 1 exclusive; read as percent | Confirm: 0.2 means 0.2 percent, not 20 |
| `invalid_tax_rate`, `invalid_percent` | error | Value outside 0 to 100 | Fix the input |
| `conflicting_discount_inputs` | error | Both a percent and an amount were given | Give one |
| `unparseable_number` | error | Not a plain number (for example `1,200`) | Re-enter without separators or symbols |
| `line_incomplete` | error | Quantity or unit price missing | Fill it in |
| `invoice_not_computable` | error | Totals skipped because an input above is bad | Fix the earlier error and re-run |
| `no_lines` | error | The invoice has no line items | Supply lines |
| `negative_quantity_not_credit_note` | error | Negative quantity on an invoice | Mark as `credit_note` if it is one; otherwise report |
| `negative_unit_price` | warning | Negative price (discount line or mistake) | Ask which |
| `zero_quantity` | warning | Quantity 0 | Ask if intended |
| `duplicate_line` | warning | Same description, quantity, price and discount as an earlier line | Ask whether billed twice |
| `duplicate_invoice_number` | error | Same supplier and number as an earlier invoice | Report both; do not decide which is real |
| `same_number_other_supplier` | info | Another supplier uses the same number | Usually harmless; mention once |
| `possible_double_billing` | warning | Same supplier, issue date and amount, different number | Ask the user to compare the documents |
| `mixed_currency_in_invoice` | error | A line currency differs from the invoice currency | Ask for the correct currency; no conversion is done |
| `currency_missing`, `invalid_currency` | warning, error | No code, or not three letters | Ask the user |
| `invalid_date` | error | Not `YYYY-MM-DD` or not a real date | Correct the date |
| `due_before_issue` | error | Due date earlier than issue date | Report; do not repair |
| `due_date_mismatch` | warning | Stated due date differs from the terms | Report the day difference |
| `due_on_weekend` | info | Due date is a Saturday or Sunday | Mention only |
| `terms_unparsed`, `terms_need_issue_date` | warning | Terms not understood, or no issue date to count from | Ask the user |
| `stated_total_missing` | info | No printed total to compare | Mention only |
| `credit_note_positive_total` | info | Credit note with a positive total | Mention only |
| `unsupported_prices_include_tax` | warning | Tax-inclusive pricing is not modelled | Check lines only; tell the user totals were not verified |
| `invalid_rounding_setting` | error | Unknown method or mode, or places outside 0 to 6 | Fix the setting |
| `unknown_type`, `unknown_field`, `missing_number` | warning | Type not recognised, field ignored, or no number | Fix the input |
| `inconsistent_field_across_rows` | warning | CSV rows of one invoice disagree on a header field | Fix the CSV |

## 3. File-level issues

| Code | Severity | Meaning |
|---|---|---|
| `mixed_currencies_in_file` | warning | More than one currency appears; totals are reported per currency |
| `sequence_gap` | warning | With `--check-sequence`: numbers missing inside a run of the same supplier and prefix (credit notes excluded). Details in `sequence_gaps[]`, capped at 20 listed numbers per gap |
| `unknown_column` | warning | CSV columns ignored |
