# Listing page content: pdf-extraction-and-forms

**One line:** Gets text, tables and form fields in and out of PDFs with a triage script, a route table and read-back checks.

## What it does

An agent first runs a byte-level triage script on the PDF: page count, whether a text layer exists (or the file is a scan, or a scan with an invisible OCR layer), AcroForm field names, types, current values and checkbox on-values, XFA presence and encryption. A decision table turns that result into a route: direct extraction, OCR the user installs, per-page routing, ask for a password, or stop. Extracted tables are checked by a second script against numbers that come from the PDF itself (row count, column sums, printed total row) and for the usual extraction faults (repeated header rows, split cells, O-for-0 digits). Forms are filled through a written mapping contract, then the output is re-inspected and compared with the mapping by a third script.

## Capabilities

- `scripts/pdf_inspect.py`: strict JSON triage of one PDF, no parsing library, no network
- `scripts/table_check.py`: validates an extracted CSV, exit 1 on any failed check
- `scripts/form_verify.py`: compares a field mapping with the values read back from the filled PDF
- A form-field mapping contract (JSON shape and eight rules)
- Open-source tool options for text, OCR, tables and forms, with licence notes; the user installs, the skill never does
- A fixed report with an explicit "Unverified" line

## When to use

You want text or tables out of a PDF, a scanned PDF read, a table turned into CSV with totals checked, a fillable form completed, or to know whether a PDF is a scan.

## When not to use

Creating, merging, splitting, compressing or redacting PDFs, e-signing, removing passwords, handwriting recognition, and XFA forms. Nearest neighbour in this catalogue: `document-consistency-check` compares document content for consistency; this skill is about getting data out of or into PDF files.

## Requirements

Python 3.9 or newer for the three scripts (standard library only). No network. OCR, table and form-writing tools are options the user installs separately.

## Install

To be generated at publication: one pinned command per tool.

## Examples

Real runs of the scripts on the saved fixtures (`evals/fixtures/`):

1. `python scripts/pdf_inspect.py evals/fixtures/scanned.pdf`: `page_count` 2, `text_layer` `image_only_likely`, `pages_with_text_operators` 0, `image_objects` 1. The route table sends this to OCR the user installs.
2. `python scripts/table_check.py evals/fixtures/invoice_bad.csv --rows 7 --total-row --sum Amount=1300`: exit 1. Findings: a repeated header at CSV line 4, a 2-cell row at line 10, the cell `1.5O` not a number, 8 body rows found against 7 expected, Amount rows sum to 1274.5 against a printed 1300, Qty rows sum to 23 against a printed 22.
3. `python scripts/form_verify.py evals/fixtures/mapping.json <report of form_filled_bad.pdf> --original <report of form_blank.pdf>`: exit 1; `value_mismatch` 1 (Jane Roe read back for Jane Doe), `empty_in_output` 1, `ok` 1.

No with-skill agent run exists yet, so no saved agent transcript is shown.

## Limits

- The triage script is a byte scan, not a parser: compressed object streams and encrypted content are invisible, so many modern files give `unknown`.
- A text layer found is not proof the text is correct.
- The table check cannot catch a wrong cell that still sums correctly.
- The form check reads stored values, not what a viewer renders.
- Not covered: PDF creation, merging, signatures, XFA, password removal, handwriting.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN, 17 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool use, real-world PDFs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A "scanned" contract PDF: triage says `image_only_likely`; the agent asks which OCR tool the user has instead of writing empty text.
2. An invoice table extracted to CSV: `table_check` fails on a repeated header and a total mismatch; the agent re-extracts.
3. A fillable form: mapping file, fill, re-inspect, `form_verify` exit 0.
4. The final report with its Unverified line.

## FAQ seeds

- Does it need network access? No.
- Does it install OCR or PDF libraries? No; it names options and waits for the user.
- Will it remove a PDF password? No; it asks for the password.
- Does it work on any PDF? The triage is a byte scan; many modern PDFs come back `unknown`, and the skill then tests a real extraction tool on page 1.
- Does it guarantee the numbers are right? No. It checks them against totals and counts from the PDF; unverified items are listed.
- Is my form data sent anywhere? The scripts make no network calls; the report does not repeat identity numbers.
- How do I uninstall it? Delete the folder from the skills directory.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
