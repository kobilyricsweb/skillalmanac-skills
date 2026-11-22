---
name: bank-statement-reconcile
description: Matches a bank CSV against a ledger CSV row by row and lists every unmatched item with the net difference. Use when two CSV exports with date, description and amount columns must be compared and missed, late or mistyped entries found. Do not use for tax, audit or accounting advice, for posting journal entries, or for any file that is not a CSV export of bank or ledger rows.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Bank statement reconcile

Use [scripts/reconcile.py](scripts/reconcile.py) to do the matching. The script
finds the pairs and the unmatched rows. You classify the unmatched rows and write
the report. Do not match rows by eye when the script is available.

Sample inputs for a smoke run are in [fixtures/bank.csv](fixtures/bank.csv) and
[fixtures/ledger.csv](fixtures/ledger.csv). License text is in [LICENSE.txt](LICENSE.txt).

## Workflow

1. **Intake.** Confirm you have two CSV files, one bank export and one ledger
   export. Each must have a header naming date, description and amount (case does
   not matter, column order does not matter). Note the tolerance in days; the
   default is 3 (working value). Output: one intake line per file with its name
   and tolerance.
2. **Size and encoding check.** Each file must be at most 2,097,152 bytes and
   valid UTF-8. Output: the byte size of each file. A file over the limit is a
   stop; see the refusal list.
3. **Run the script.** Output: the JSON on standard output and the exit code.
4. **Branch on the exit code.** Exit 0 means every row matched: report that and
   stop. Exit 1 means unmatched rows exist: continue to step 5. Exit 2 means the
   input was refused: quote the `error` value and stop. Do not guess a fix and
   run again.
5. **Classify each unmatched row** with the table below. Output: one label per
   unmatched row.
6. **Write the report** in the output contract below. Output: the report only.
7. **Close with the scope line** from the output contract. The matching is not
   a decision about what to book.

## Decision and threshold table

| Check | Value | Result |
| --- | --- | --- |
| Amount equality | exact to the cent | unequal amounts never match |
| Date gap | 0 to 3 days (working value) | eligible match |
| Date gap | 4 days or more | not eligible |
| `--tolerance-days` argument | 0 to 31 | outside this range: exit 2 |
| File size | 2,097,152 bytes per file | larger: exit 2 |
| Possible typo | dates within the tolerance days (same window as matching), same sign, amounts differ by less than 50 percent of the larger absolute amount (working value) | label `possible typo` |
| Missing on ledger | bank row unmatched, no typo partner | label `missing on ledger` |
| Missing on bank | ledger row unmatched, no typo partner | label `missing on bank` |

Pair each unmatched bank row with at most one unmatched ledger row for the typo
check. Take the pair with the smallest amount difference first. A row used in a typo
pair is not counted again as missing.

The typo label is applied by you, not by the script. Each typo label must quote
both amounts. The script never pairs typos.

## Script contract

Command line, run from the skill folder:

`python -I scripts/reconcile.py --bank <bank-csv> --ledger <ledger-csv> [--tolerance-days <n>]`

Arguments: `--bank` and `--ledger` are required paths. `--tolerance-days` is an
integer from 0 to 31 and defaults to 3.

Standard output on exit 0 or 1 is one JSON object with these keys: `status`,
`tolerance_days`, `bank_rows`, `ledger_rows`, `matched_count`, `matched_pairs`
(each with `bank_line`, `ledger_line`, `day_shift`), `unmatched_bank` and
`unmatched_ledger` (each item with `line`, `date`, `amount`, `description`),
`unmatched_bank_total`, `unmatched_ledger_total`, `difference`.

`line` is the physical line number in the file, so the header is line 1. Blank
lines are skipped. `description` is cut to 120 characters. Amounts are strings that
keep the precision written in the file. `difference` equals
`unmatched_bank_total` minus `unmatched_ledger_total`.

| status | exit code | meaning |
| --- | --- | --- |
| `match` | 0 | every row on both sides matched |
| `findings` | 1 | at least one unmatched row on either side |
| `error` | 2 | usage or input refused; standard error holds `{"status": "error", "error": "..."}` |

## Output contract

Write these headings in this order and nothing before them:

1. `## Summary`: a two-column table, Metric and Value, with the rows Status,
   Tolerance days, Bank rows, Ledger rows, Matched, Unmatched bank, Unmatched
   ledger, Unmatched bank total, Unmatched ledger total, Difference.
2. `## Unmatched bank rows`: columns Line, Date, Amount, Description, Label.
3. `## Unmatched ledger rows`: same five columns.
4. `## Possible typos`: columns Bank line, Ledger line, Bank amount, Ledger
   amount, Gap. Gap is the absolute amount difference, |bank amount minus ledger
   amount|, written to two decimals. Write "None" as the only line if the table is
   empty.
5. `## Scope`: one sentence. It must say the result lists matching differences
   and is not accounting advice.

Mask every account or card number in a description to its last four digits.
Masking is your job: descriptions in the script output are raw and may contain
full numbers.

## Refuse or stop when

- Either file is missing, not CSV, not UTF-8, or over 2,097,152 bytes. Exit 2 is
  the answer; ask for a re-export or for a split by month.
- The header does not name date, description and amount. Ask the user to rename
  the columns or re-export.
- The two files do not cover overlapping dates at all. Stop and ask whether the
  user picked the wrong period.
- The requested tolerance is outside 0 to 31 days.
- The user asks what to book, how to classify an entry for tax, or whether the
  books pass audit. Say this skill only lists differences and that those
  decisions belong to the user's accountant.
- A description contains a full account, card or tax number and the user asks you
  to print it. Refuse and mask it.
