# Quote Estimate Builder

## One line

Totals an itemized quote from a CSV of line items, with per-line discounts, half-up rounding, tax at the rate you supply, and flags for rows that cannot be priced.

## What it does

The skill runs a standard-library Python script on a CSV with the columns `item`, `qty` and `unit_price`, plus an optional `discount_percent`. Each row is checked before any arithmetic happens. A row with a quantity such as `two`, a negative price, or a discount above 100 is flagged and left out of every total, so a single bad cell cannot quietly change the grand total. Valid rows are priced with Decimal arithmetic: each line gross is rounded half-up to the cent, the line discount is taken from that rounded gross, and tax is applied once to the net subtotal. The script prints a plain-text table, then a JSON object on its last line, and returns exit code 0 for a clean file, 1 when rows were flagged, and 2 for input errors. The agent then writes the quote under four fixed headings, with totals copied from the script output rather than recomputed by hand.

## When to use

Use it when someone has a list of line items and needs a total they can trust, for example a service estimate built in a spreadsheet export, or an existing quote whose total needs a second check. It is most useful when discounts apply to some lines and not others, because the half-up rule on each discounted line is where manual totals usually drift by a cent.

## When not to use

Do not use it for invoices with payment terms, for multi-currency pricing, for looking up a tax rate by address, or for quotes that have no line items. The script never determines a tax rate; the user must supply it as a percent.

## Requirements

Python 3.9 or later, standard library only. No network access and no packages to install. The input must be a UTF-8 CSV under 2 MB. The tax rate is a required command-line option.

## Example

Command run on the shipped fixture with a tax rate of 8.25 percent:

```
python -I "scripts/quote.py" "fixtures/smoke_quotes.csv" --tax-rate 8.25
```

Output, exit code 1:

```
Row  Item              Qty  Unit price  Disc %  Gross    Discount  Net      Flags         
---  ----------------  ---  ----------  ------  -------  --------  -------  --------------
1    Website design    1    2400.00             2400.00  0.00      2400.00  -             
2    Logo refresh      1    650.00              650.00   0.00      650.00   -             
3    Hosting setup     12   25.50               306.00   0.00      306.00   -             
4    Stock photo pack  3    49.95       10      149.85   14.99     134.86   -             
5    Training session  2.5  180.00              450.00   0.00      450.00   -             
6    Domain renewal    two  12.00               -        -         -        QTY_NOT_NUMBER

Tax rate (percent): 8.25
Gross subtotal  3955.85
Discount total  14.99
Subtotal        3940.86
Tax             325.12
Grand total     4265.98
{"status": "flagged", "tax_rate_percent": "8.25", "line_count": 6, "valid_line_count": 5, "flagged_line_count": 1, "lines": [{"row": 1, "item": "Website design", "qty": "1", "unit_price": "2400.00", "discount_percent": "", "line_gross": "2400.00", "line_discount": "0.00", "line_net": "2400.00", "flags": []}, {"row": 2, "item": "Logo refresh", "qty": "1", "unit_price": "650.00", "discount_percent": "", "line_gross": "650.00", "line_discount": "0.00", "line_net": "650.00", "flags": []}, {"row": 3, "item": "Hosting setup", "qty": "12", "unit_price": "25.50", "discount_percent": "", "line_gross": "306.00", "line_discount": "0.00", "line_net": "306.00", "flags": []}, {"row": 4, "item": "Stock photo pack", "qty": "3", "unit_price": "49.95", "discount_percent": "10", "line_gross": "149.85", "line_discount": "14.99", "line_net": "134.86", "flags": []}, {"row": 5, "item": "Training session", "qty": "2.5", "unit_price": "180.00", "discount_percent": "", "line_gross": "450.00", "line_discount": "0.00", "line_net": "450.00", "flags": []}, {"row": 6, "item": "Domain renewal", "qty": "two", "unit_price": "12.00", "discount_percent": "", "line_gross": null, "line_discount": null, "line_net": null, "flags": ["QTY_NOT_NUMBER"]}], "totals": {"gross_subtotal": "3955.85", "discount_total": "14.99", "subtotal": "3940.86", "tax": "325.12", "grand_total": "4265.98"}}
```

The agent writes the grand total as 4265.98 under a `Totals (PARTIAL)` heading, lists the Domain renewal row under Flagged rows, and asks the user what quantity was intended.

## Limits

The script checks arithmetic and cell format only. It does not check whether prices are correct, whether a discount was approved, or whether the tax rate fits the customer's location. Amounts of one trillion or more are flagged. A repeated header name is an input error, columns other than the four named ones are ignored, and a row with no non-blank cell is skipped rather than reported. The script writes no file, so the agent must write the quote text itself.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
