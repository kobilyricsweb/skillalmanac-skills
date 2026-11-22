# bank-statement-reconcile

## One line

Matches a bank CSV against a ledger CSV and lists the rows that did not pair up, with the net difference.

## What it does

The skill runs a small Python script that reads two CSV exports, each with date, description and amount columns. A bank row and a ledger row pair when their amounts are equal to the cent and their dates are no more than 3 days apart. The 3-day window is a working value, and you can change it between 0 and 31 days. Each row can pair only once. The script walks the bank file in order and gives each bank row the unused ledger row with the smallest date gap, so a ledger entry that should have gone to a later bank row can be taken early. The output is a JSON object with the matched pairs, the unmatched rows on each side, the two totals and their difference, all computed with decimal arithmetic.

The language model then labels each unmatched row. It flags a possible typo when a bank row and a ledger row fall within the same tolerance window, share a sign, and their amounts differ by less than half of the larger one. The typo label is applied by the model, not the script, and must quote both amounts. Every other unmatched row is labelled as missing on the ledger or missing on the bank. The report has a fixed set of headings so two runs on the same files produce the same layout.

## When to use

Use it when a bookkeeper or small-business owner has a bank export and a ledger export for the same account and period, and wants a list of entries that do not line up. It suits a month-end check where eyeballing the two files has already missed something.

## When not to use

Do not use it for tax preparation, audit sign-off, posting journal entries, or deciding what a line should be booked as. It does not read PDFs, bank APIs, spreadsheets or multi-currency statements. It does not match on description text.

## Requirements

Python 3.9 or later, standard library only. No network access and no subprocesses. Each input file must be UTF-8 CSV and at most 2,097,152 bytes.

## Example

Run on the bundled sample pair (`fixtures/bank.csv` and `fixtures/ledger.csv`):

```
python -I scripts/reconcile.py --bank fixtures/bank.csv --ledger fixtures/ledger.csv
```

Output, exit code 1:

```
{
  "status": "findings",
  "tolerance_days": 3,
  "bank_rows": 5,
  "ledger_rows": 5,
  "matched_count": 3,
  "matched_pairs": [
    {
      "bank_line": 2,
      "ledger_line": 2,
      "day_shift": 0
    },
    {
      "bank_line": 3,
      "ledger_line": 3,
      "day_shift": 1
    },
    {
      "bank_line": 4,
      "ledger_line": 4,
      "day_shift": 0
    }
  ],
  "unmatched_bank": [
    {
      "line": 5,
      "date": "2026-03-12",
      "amount": "-47.90",
      "description": "CARD PURCHASE FUEL"
    },
    {
      "line": 6,
      "date": "2026-03-15",
      "amount": "-15.00",
      "description": "SERVICE FEE"
    }
  ],
  "unmatched_ledger": [
    {
      "line": 5,
      "date": "2026-03-12",
      "amount": "-74.90",
      "description": "Fuel"
    },
    {
      "line": 6,
      "date": "2026-03-01",
      "amount": "-850.00",
      "description": "Office lease"
    }
  ],
  "unmatched_bank_total": "-62.90",
  "unmatched_ledger_total": "-924.90",
  "difference": "862.00"
}
```

The sample shows one row matched across a one-day gap, one fuel charge whose ledger amount is mistyped, one bank fee missing from the ledger, and one ledger lease missing from the bank.

## Limits

The matching is greedy, not a global optimum, so an unusual pattern of same-amount rows can pair differently than a person would. The date window is fixed per run; there is no per-row override. The typo rule is applied by the model, not by the script, so its labels should be checked by a person. Masking account numbers is the agent's job; descriptions in the script output are raw. Descriptions are cut to 120 characters in the output. The script does not handle currency, sign conventions beyond a leading minus or parentheses, or files with more than one account.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
