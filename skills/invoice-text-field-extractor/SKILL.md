---
name: invoice-text-field-extractor
description: Extracts the invoice number, issue and due dates, currency symbols, subtotal, tax, total and line items from extracted invoice text, reports each field's source line and a found, ambiguous or missing confidence, and flags totals that do not add up. Use when invoice text must become a structured record, or when line items need checking against the subtotal and the total. Do not use for accounting or tax advice, invoice approval or payment decisions, bank statement matching, scanned images without OCR text, or layouts outside the label patterns in this skill.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Invoice text field extractor

This skill turns plain invoice text into one record. A script does the reading and the arithmetic. The agent runs it, maps its output to the tables below, and reports what it found without filling gaps by guessing.

Shipped files: `scripts/invoice_fields.py` (the extractor), `fixtures/invoice_mismatch.txt` (a 25-line sample with a total that does not add up, for smoke testing only), and `LICENSE.txt`.

## Workflow

1. **Intake.** Confirm the input is a UTF-8 text file that holds the invoice text. Output: the input file name and its line count. If the input is a PDF, image or Word file, stop (see the refuse list).
2. **Run the script.** Output: the JSON object on stdout and the exit code. Command: `python -I scripts/invoice_fields.py <input-file>`
3. **Handle exit code 2.** Output: the one-line JSON error from stderr, copied verbatim under Status. Stop; do not retry with altered input.
4. **Build the record table.** For each of the seven fields in `fields`, copy `value`, `confidence` and `line`. For an `ambiguous` field, list every entry of `candidates` in Open questions. Output: the Record table.
5. **Copy line items.** One row per entry in `line_items`. If the list is empty, write "none". Output: the Line items table.
6. **Read the two checks.** Copy `sum`, `subtotal`, `subtotal_plus_tax`, `total`, `difference` and `status` from `checks`. Output: the Checks table.
7. **Map findings.** Each entry in `findings` gets one row in the Findings table and one question or note in Open questions using the table in the next section. Output: the Findings table and Open questions.
8. **Set the status** from the exit code (table below) and write the record in the output contract.

## Decision and threshold table

| Rule | Value | Note |
|---|---|---|
| Input size cap | 2 MB (2,097,152 bytes) | Larger input exits 2 with `input_too_large`. |
| Encoding | UTF-8; a byte order mark is accepted | Invalid UTF-8 exits 2 with `invalid_utf8`. |
| Amount shape | optional `$`, `€`, `£` or `¥`; digits with optional comma groups; exactly two decimals | Working value. Amounts without two decimals are not read. |
| Arithmetic tolerance | difference of 0.01 or less counts as a match | Working value. |
| Line item shape | description, quantity, optional unit price, amount, columns separated by 2 or more spaces | Working value. Descriptions cannot contain digits. |
| Date shapes | `YYYY-MM-DD`, `MM/DD/YYYY` (month first), `Mon D, YYYY`, `D Mon YYYY` | Output is always `YYYY-MM-DD`. Impossible dates are ignored. |
| Confidence: found | exactly one distinct value across all matching lines | Line is the first matching line. |
| Confidence: ambiguous | two or more distinct values | Value is null; all candidates are listed. |
| Confidence: missing | no matching line | Value is null. |
| Exit code 0 | no findings | Status `complete`. |
| Exit code 1 | one or more findings | Status `review`. |
| Exit code 2 | usage or input error | Status `error`. |

## Label patterns

A label must start its line (leading spaces allowed). A label in the middle of a line is not read. Labels match case-insensitively.

| Field | Accepted labels | Value read from |
|---|---|---|
| invoice_number | `Invoice No`, `Invoice Number`, `Invoice #`, `Inv #` | text after the label, letters, digits, hyphen or slash |
| issue_date | `Invoice Date`, `Issue Date`, `Date Issued`, `Date` | the date after the colon |
| due_date | `Due Date`, `Payment Due`, `Due` | the date after the colon |
| currency | any amount carrying `$`, `€`, `£` or `¥` | the sign itself; every sign found is a candidate |
| subtotal | `Subtotal` | last amount on the line |
| tax | `Tax`, `Sales Tax`, `VAT`, `GST`, then any text up to a colon | last amount on the line |
| total | `Total`, `Total Due`, `Total Amount`, `Amount Due`, `Balance Due` | last amount on the line |
| line item | description, quantity, optional unit price, amount on one line | the four columns |

A tax rate such as `(8%)` is not read as a value. `Total` never matches `Subtotal`, because the label must start the line.

## Finding codes

| Code | Trigger | Action in the record |
|---|---|---|
| `MISSING_FIELD` | a field has confidence missing (`subject` is the field name) | Note the field as not found. Do not infer it from other fields. |
| `AMBIGUOUS_FIELD` | a field has confidence ambiguous (`subject` is the field name) | List the candidates and ask which value is correct. |
| `NO_LINE_ITEMS` | no line matched the line item shape (`subject` is `line_items`) | Say the item list is empty and that the checks were not run. |
| `LINE_ITEMS_MISMATCH` | line items differ from the subtotal by more than 0.01 (`subject` is `line_items_vs_subtotal`) | Report both sums. Do not adjust any figure. |
| `TOTAL_MISMATCH` | subtotal plus tax differs from the total by more than 0.01 (`subject` is `total_vs_subtotal_plus_tax`) | Report both figures and the difference. Do not adjust any figure. |

## Output contract

Write these sections in this order, with these headings.

- `## Record`: table with columns `Field | Value | Confidence | Line`, seven rows in this order: invoice_number, issue_date, due_date, currency, subtotal, tax, total.
- `## Line items`: table with columns `Line | Description | Qty | Unit price | Amount`, one row per item, or the word "none".
- `## Checks`: table with columns `Check | Computed | Stated | Difference | Status`, two rows: line_items_vs_subtotal and total_vs_subtotal_plus_tax.
- `## Findings`: table with columns `Code | Subject`, one row per finding, or the word "none".
- `## Open questions`: numbered list, or the word "none".
- `## Status`: one of `complete`, `review`, `error`, followed by the script exit code.

## Refuse / stop when

- The input is a PDF, image, spreadsheet or Word file rather than extracted text. Stop and ask for the extracted text.
- The script exits 2. Stop and report the error line.
- The user asks whether an invoice is correct under tax law, whether it should be paid or approved, or how to book it. Refuse that clause only. Finish the extraction, set Status to `review`, and list the refused question under Open questions.
- A field is missing or ambiguous. Leave it empty or list the candidates. Never choose a value to fill the field.
- A total does not match. Report the mismatch. Never edit amounts so the check passes.

## Script contract (type A)

- Command: `python -I scripts/invoice_fields.py <input-file>`
- Arguments: exactly one positional argument, the path to a UTF-8 text file of at most 2 MB.
- Standard output: one JSON object with keys `input_lines`, `fields` (seven keys, each with `value`, `confidence`, `line`, `candidates`), `line_items` (each with `line`, `description`, `qty`, `unit_price`, `amount`), `checks` (keys `line_items_vs_subtotal` and `total_vs_subtotal_plus_tax`, each with `status`), and `findings` (each with `code` and `subject`).
- Standard error on exit 2: one line of JSON with keys `error` and `message`.
- Error codes on exit 2: `usage` (wrong argument count), `missing_file` (path is not a regular file), `input_too_large` (over 2 MB), `empty_input` (no text), `read_error` (file could not be read), `invalid_utf8` (not UTF-8).
- Exit codes: 0 no findings, 1 findings present, 2 usage or input error.
- The script is read-only. It writes no files, opens no network connections and starts no subprocesses.
- Finding codes emitted: `MISSING_FIELD`, `AMBIGUOUS_FIELD`, `NO_LINE_ITEMS`, `LINE_ITEMS_MISMATCH`, `TOTAL_MISMATCH`.
- The output includes invoice numbers, dates, amounts and item descriptions from the input. Treat the output as confidential when the invoice is.
