---
name: quote-estimate-builder
description: Builds an itemized quote from a CSV of line items, with per-line discounts, half-up rounding, tax on the net subtotal at a user-supplied rate, and flags for bad rows. Use when a user has item, quantity, unit price and optional discount lines and needs a correct subtotal, tax and grand total, or when an existing quote total must be checked for arithmetic slips. Do not use for invoices with payment terms, multi-currency pricing, tax-rate lookup by location, or quotes with no line items.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Quote Estimate Builder

Totals a quote from a CSV of line items. The script does all arithmetic. The agent
runs it, reads the exit code, and writes the quote in the output contract below.
The agent never adds up the numbers by hand.

## Workflow

1. **Intake.** Collect two values: the path to the CSV (called `<input-file>` below)
   and the tax rate as a percent, such as `8.25` for 8.25%. Output: both values
   confirmed back to the user in one line. If the rate is missing, stop (see
   "Refuse / stop when").
2. **Check the header.** The CSV must contain the columns `item`, `qty` and
   `unit_price`. The column `discount_percent` is optional; a blank value means 0.
   Other columns are ignored. Rows with no non-blank cell are skipped. Output: the
   list of required columns found, or the missing column names.
3. **Run the script** with the command in "Script contract". Output: the script's
   table and JSON, plus the exit code.
4. **Branch on the exit code** using the decision table below. Output: one of the
   three actions, named.
5. **Write the quote** using the output contract. Copy values from the JSON `totals`
   object exactly as printed. Output: the four headings in the output contract.
6. **Handle flagged rows.** List each flagged row with its flag code and the value as
   entered. Ask the user for a corrected value for each one. After the user answers,
   save a corrected copy under a new file name, change only the cells the user
   named, and run step 3 again on the copy. Never edit the original file. Output: a list of
   questions, one per flagged row.

## Decision table

| Exit code | JSON `status` | Action |
|---|---|---|
| 0 | `ok` | Write the quote (step 5). Totals cover every row. |
| 1 | `flagged` | Do not issue a final total. Write the quote with the heading `Totals (PARTIAL)` and the note "excludes flagged rows". Run step 6. |
| 2 | none (stderr JSON) | Do not write totals. Report the `code` value and fix the input or the command. |

## Calculation rules

| Value | Formula | Rounding |
|---|---|---|
| Line gross | qty x unit_price | 2 decimal places, half-up |
| Line discount | line gross x discount_percent / 100 | 2 decimal places, half-up |
| Line net | line gross - line discount | exact (already 2 places) |
| Gross subtotal | sum of valid line gross values | exact |
| Discount total | sum of valid line discount values | exact |
| Subtotal | gross subtotal - discount total | exact |
| Tax | subtotal x tax rate / 100 | 2 decimal places, half-up, once on the whole subtotal |
| Grand total | subtotal + tax | exact |

Working values (not a published spec): the input file cap is 2 MB and the amount
limit is 1,000,000,000,000 (one trillion) per quantity or unit price. Discount
percent and tax rate must be 0 to 100 inclusive; that range is the arithmetic bound.

## Flag codes (exit 1, one or more rows)

| Code | Meaning |
|---|---|
| `ITEM_EMPTY` | The item cell is blank. |
| `QTY_NOT_NUMBER` | qty is not a plain decimal such as `2` or `2.5`. Commas, currency signs and words are rejected. |
| `QTY_NEGATIVE` | qty starts with a minus sign. |
| `QTY_TOO_LARGE` | qty is at or above the amount limit. |
| `PRICE_NOT_NUMBER` | unit_price is not a plain decimal. |
| `PRICE_NEGATIVE` | unit_price starts with a minus sign. |
| `PRICE_TOO_LARGE` | unit_price is at or above the amount limit. |
| `DISCOUNT_NOT_NUMBER` | discount_percent is present but not a plain decimal. |
| `DISCOUNT_OUT_OF_RANGE` | discount_percent is negative, above 100, or at or above the amount limit. |
| `ROW_MALFORMED` | The row has more or fewer cells than the header. |

A flagged row shows `-` for its line gross, discount and net, and it is left out of
every total.

## Error codes (exit 2, no totals)

| Code | Meaning |
|---|---|
| `USAGE` | Bad or missing command-line argument, including a missing `--tax-rate`. |
| `TAX_RATE_INVALID` | The tax rate is not a plain non-negative decimal. |
| `TAX_RATE_OUT_OF_RANGE` | The tax rate is above 100. |
| `FILE_NOT_FOUND` | The input path is not an existing file. |
| `FILE_UNREADABLE` | The file exists but cannot be read. |
| `INPUT_TOO_LARGE` | The file is over 2 MB. |
| `INVALID_UTF8` | The file is not valid UTF-8 (a UTF-8 byte order mark is accepted). |
| `INPUT_NOT_CSV` | The file has NUL bytes or cannot be parsed as CSV. |
| `EMPTY_INPUT` | The file has no non-blank row. |
| `HEADER_MISSING` | A required column (`item`, `qty`, `unit_price`) is absent. |
| `HEADER_DUPLICATE` | The header repeats a column name. |
| `NO_DATA_ROWS` | The file has a header and no data row. |

## Output contract

Write the quote with exactly these four headings, in this order:

1. `## Status`: one line, `ok` or `flagged`, then the tax rate as `Tax rate: <percent>%`.
2. `## Line items`: a table with the columns `Row | Item | Qty | Unit price | Discount % | Line net | Flags`. Use the `flags` value, or `none` when empty.
3. `## Totals` (or `## Totals (PARTIAL)` when the status is `flagged`): a bullet list in this order: Gross subtotal, Discount total, Subtotal, Tax, Grand total. Each value comes from the JSON `totals` object.
4. `## Flagged rows`: a table with the columns `Row | Flag | Value as entered | Question for the user`. Write `None` when there are no flagged rows.

## Script contract

- Command (type A, run from the skill folder):
  `python -I "scripts/quote.py" "<input-file>" --tax-rate <percent>`
- Positional argument: `input_file`, the CSV path.
- Required option: `--tax-rate`, a percent such as `8.25` (not `0.0825`).
- Stdout: a plain-text table, then one JSON object on the last line with keys
  `status`, `tax_rate_percent`, `line_count`, `valid_line_count`,
  `flagged_line_count`, `lines` (each with `row`, `item`, `qty`, `unit_price`,
  `discount_percent`, `line_gross`, `line_discount`, `line_net`, `flags`) and
  `totals` (`gross_subtotal`, `discount_total`, `subtotal`, `tax`, `grand_total`).
- Stderr: on exit 2 only, one JSON line with keys `error` and `code`.
- Exit codes: 0 ok, 1 flagged rows (totals cover valid rows only), 2 usage or input error.
- The script reads the input and writes nothing. It never overwrites a file.

Shipped files: `scripts/quote.py` (the script), `fixtures/smoke_quotes.csv` (a six-row
test file with one discount and one non-numeric quantity), and `LICENSE.txt`.

## Refuse / stop when

- The user does not give a tax rate. Ask for it. Never assume a rate, never look one up.
- The rate is given as a fraction such as `0.0825`. Confirm with the user that the
  value means percent before running.
- The file is over 2 MB. Ask the user to split it into several quotes.
- The exit code is 2. Do not write totals.
- The user asks to drop flagged rows or treat them as zero without a direct answer
  from the user for each row.
- The request is for tax advice, a jurisdiction's tax rules, currency conversion, or
  approval of a discount. Say this is outside the skill.
- The request asks for an invoice with payment terms or for a quote with no line items.
