# Invoice text field extractor

## One line

Reads invoice text, pulls out the invoice number, dates, currency signs, subtotal, tax, total and line items, and flags when the line items or the total do not add up.

## What it does

The skill runs a small Python script over a plain text copy of an invoice. The script looks for labels that start a line, such as "Invoice No", "Due Date" or "Total Due", and reads the value after each label. Amounts must carry two decimal places, which keeps a stray quantity from being taken for a total. Each of the seven header fields comes back with the line number it was read from and one of three confidence levels: found, ambiguous or missing. Ambiguous fields list every candidate so a person can decide which one is right.

Line items are read from rows that hold a description, a quantity, an optional unit price and an amount. The script then adds the item amounts and compares the sum with the subtotal, and it adds the subtotal and tax and compares that with the total. Both comparisons allow a difference of 0.01. The output is one JSON object, and the exit code tells a caller whether anything needs review.

## When to use

- A bookkeeper or analyst has invoice text from a PDF copy-paste or an OCR run and needs the same fields in every record.
- A batch of invoices must be checked for totals that do not match their line items before anyone looks at them.
- A spreadsheet or database import needs one row per invoice with the source line recorded beside each value.

## When not to use

- The input is a PDF, an image or a Word file. The script reads text only.
- The question is about tax treatment, approval, payment or how to book the invoice.
- The invoice uses labels or layouts outside the patterns in the skill, such as totals written in words or amounts without cents.

## Requirements

- Python 3.9 or later. The script uses only the standard library.
- An extracted text file of at most 2 MB, encoded as UTF-8.
- No network access and no extra packages.

## Example

Run on the shipped sample `fixtures/invoice_mismatch.txt`, which has three line items and a total of 199.00 where the subtotal and tax give 199.80:

```
{
  "input_lines": 25,
  "fields": {
    "invoice_number": {
      "value": "INV-2026-0147",
      "confidence": "found",
      "line": 6,
      "candidates": []
    },
    "issue_date": {
      "value": "2026-11-03",
      "confidence": "found",
      "line": 7,
      "candidates": []
    },
    "due_date": {
      "value": "2026-12-03",
      "confidence": "found",
      "line": 8,
      "candidates": []
    },
    "currency": {
      "value": "$",
      "confidence": "found",
      "line": 16,
      "candidates": []
    },
    "subtotal": {
      "value": "185.00",
      "confidence": "found",
      "line": 16,
      "candidates": []
    },
    "tax": {
      "value": "14.80",
      "confidence": "found",
      "line": 17,
      "candidates": []
    },
    "total": {
      "value": "199.00",
      "confidence": "found",
      "line": 18,
      "candidates": []
    }
  },
  "line_items": [
    {
      "line": 12,
      "description": "Widget A",
      "qty": "4",
      "unit_price": "12.50",
      "amount": "50.00"
    },
    {
      "line": 13,
      "description": "Cable Kit",
      "qty": "2",
      "unit_price": "30.00",
      "amount": "60.00"
    },
    {
      "line": 14,
      "description": "Service Visit",
      "qty": "1",
      "unit_price": "75.00",
      "amount": "75.00"
    }
  ],
  "checks": {
    "line_items_vs_subtotal": {
      "sum": "185.00",
      "subtotal": "185.00",
      "difference": "0.00",
      "status": "match"
    },
    "total_vs_subtotal_plus_tax": {
      "subtotal_plus_tax": "199.80",
      "total": "199.00",
      "difference": "-0.80",
      "status": "mismatch"
    }
  },
  "findings": [
    {
      "code": "TOTAL_MISMATCH",
      "subject": "total_vs_subtotal_plus_tax"
    }
  ]
}
```

The exit code for this run is 1. The line items agree with the subtotal, so only the total check is flagged.

## Limits

- It checks arithmetic and labels only. It does not confirm that the invoice is genuine, that the vendor exists, that the amounts are owed, or that the tax rate is correct.
- It reads English labels and the four currency signs listed in the skill. ISO codes such as USD or EUR are not read.
- A description that contains a digit, such as "Cable 2-pack", is not read as a line item, and the checks then report no items.
- Amounts without two decimal places are not read.
- The 0.01 arithmetic tolerance is a working value, not a figure taken from a specification.
- It has been run on one 25-line sample only. Invoices with several pages, columns in another order, or item rows wrapped onto two lines have not been tried.
- The output repeats invoice numbers, dates, amounts and item descriptions, so the output needs the same care as the invoice.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
