## Contents

1. Rounding methods and how the script computes each
2. Rounding modes
3. Decimal places by currency
4. Payment terms the script understands
5. Sources

Read the section you need; this file links to nothing else.

## 1. Rounding methods and how the script computes each

The method is a property of the issuer's system, not of the maths. Ask, or run `line` first and read the `matches_other_rounding` hint.

| Method | Line net | Subtotal | Discount | Tax | Total |
|---|---|---|---|---|---|
| `line` | quantity x price x (100 - line discount) / 100, rounded once | sum of rounded line nets | invoice discount rounded | each tax-rate group (base after discount x rate) rounded once, then added | subtotal - discount + tax, all already in minor units |
| `total` | kept at full precision | sum of unrounded nets, rounded for display | full precision | full precision, summed over groups | rounded once at the end; displayed parts may not add to it by one minor unit |
| `line_tax` | rounded as in `line` | sum of rounded nets | rounded as in `line` | each line's share of the discounted base x rate, rounded per line, then added | as in `line` |

Example with three lines of 0.333 and no tax: `line` gives 0.99, `total` gives 1.00 (0.999 rounded). Both are internally consistent; they are different policies. With three lines of 0.15 at 10% tax: `line` tax 0.05 (0.045 rounded), `line_tax` tax 0.06 (three taxes of 0.015 each rounded to 0.02), `total` 0.05.

A stated line total is always compared with the single-rounded line net, whatever the method, because a printed line amount is a rounded amount.

When an invoice discount is shared over several tax-rate groups, each group's base is its net multiplied by (subtotal - discount) and divided by subtotal, computed exactly.

## 2. Rounding modes

| Mode | Rule | Example (to 2 places) |
|---|---|---|
| `half_up` | exact ties go away from zero; the usual shop and invoice default | 0.125 gives 0.13; -0.125 gives -0.13 |
| `half_even` | exact ties go to the even last digit ("banker's rounding") | 0.125 gives 0.12; 0.135 gives 0.14 |
| `down` | truncate toward zero | 0.129 gives 0.12 |

Ties only occur when the exact value ends in a 5 one place beyond the rounding place. The script keeps 50 significant digits and reads every input as text, so a tie is never blurred by binary floating point: 1.005 stays exactly 1.005.

## 3. Decimal places by currency

Default is 2. The script uses 0 for JPY, KRW, VND, CLP, ISK, UGX, PYG, RWF, XAF, XOF, BIF, DJF, GNF, KMF, VUV and XPF, and 3 for BHD, IQD, JOD, KWD, LYD, OMR and TND. Override with `--places` or the invoice's `rounding.places` when the issuer uses a different convention (some systems carry 4 places on unit prices but 2 on totals; the unit price is still read at full precision).

## 4. Payment terms the script understands

| Text (case and spacing ignored) | Due date |
|---|---|
| `net 30`, `net30`, `30 days`, `net 30 days` | issue date + 30 days |
| `eom`, `eom30`, `eom + 30`, `net eom 30` | last day of the issue month, + 30 days (+ 0 if no number) |
| `due on receipt`, `on receipt`, `upon receipt`, `immediate`, `due now` | issue date |
| `2/10 net 30` | issue date + 30 days, plus an early-payment option: 2 percent if paid within 10 days of issue |

Early-payment arithmetic is reported on two bases (computed total, and the pre-tax base after discount) because contracts differ on which one the percent applies to. Day arithmetic is calendar days. No weekend, bank-holiday or business-day shift is applied; a due date on a Saturday or Sunday gets an `info` flag so the user can decide.

Anything else (`pay when able`, `60 days end of month following`) gives a `terms_unparsed` warning. Do not guess; ask the user for the date or a supported form.

## 5. Sources

- Python `decimal` module, rounding modes and context precision: https://docs.python.org/3/library/decimal.html
- ISO 4217 currency codes and minor units: https://www.iso.org/iso-4217-currency-codes.html
- Common payment-term conventions are trade practice; check the contract for the governing wording.
