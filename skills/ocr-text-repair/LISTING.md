# OCR text repair

**One line:** Repairs broken OCR text with a change log, fixing a misread only when the document itself proves the correct word.

## What it does

A script reads OCR output, leaves the input file untouched, and writes a repaired copy next to it plus a JSON report. It rejoins words split by a hyphen at a line end, unwraps hard-wrapped paragraphs, expands ligature characters, removes page headers and footers that repeat across pages, and corrects letter confusions (rn for m, vv for w, a digit inside a word) only when the corrected word occurs elsewhere in the same document. Numbers, amounts and codes are never changed: damaged-looking ones are listed as suspicious, and the script refuses to write the result if a number differs from the input.

## Capabilities

- Repaired text file plus `changes[]` (line, reason, before, after), `suspicious[]` and `stats` as strict JSON.
- Decisions per document type: prose, table, form, receipt (tables, forms and receipts are never re-flowed).
- Two-column detection with an opt-in split; page header and footer removal for paged text.
- Hard refusal to overwrite the input, even with `--force`.

## When to use / when not to

Use when text from a scan, photo or screenshot has split words, broken lines, odd characters or misread letters and the user wants it cleaned without rewriting.

Not for: extracting text or fields from text-layer PDFs (see `pdf-extraction-and-forms`), cleaning speech transcripts (see `transcript-cleanup`), editing style or grammar, translation, or running OCR on an image. How it differs: those handle other inputs; this repairs the damage OCR itself leaves, using counts from the document as evidence.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the skill gives a manual procedure.

## Examples

Prompt: "This is OCR output from a scanned report page. Fix the line breaks and the OCR misreads, keep the original, tell me what you changed."

Real output of `python scripts/repair_ocr.py prose_basic.txt` on the fixture (16 input lines, 9 changes):

```
The field survey of the harbour towns was made in the spring of 1987 by a small team. Every morning the team collected samples from the quay, ... A modern harbour has a long quay, ... no exception to that rule. ...
```

Selected log entries: `rnodern` -> `modern` ("'modern' appears 2x in the document, 'rnodern' 1x"); `sma1l` -> `small`; `excep-<NL>tion` -> `exception` ("no evidence in the document; default join", listed for review). Left unchanged and flagged: `tirne` (only one `time` in the document) and `l987` (possible number, never auto-changed).

Second example, a receipt: `rnilk semi` becomes `milk semi` because `milk` occurs twice; `1O.50` is reported as `number-confusable` with suggestion `10.50` and left as printed; `T0TAL` and `A1B2` are listed as letter-digit tokens.

## Limits

Evidence comes only from the document; short texts get fewer automatic fixes. The script never sees the page image, so numbers must be checked against the source. Hard-wrap detection is a line-length heuristic. Header and footer removal can drop a legitimate repeated line (every removal is logged). Latin script only for confusion repairs.

## Evidence

Script fixtures: 15 of 15 cases pass (see VERIFICATION.md, 2026-11-21). Not tested: efficacy against a baseline agent, trigger rate, other tools, other operating systems, real scanned documents at scale, human review.

## Demo script (60 to 90 seconds)

1. Show a hard-wrapped OCR page with `sam-` / `ples`, `rnodern`, `1O.50` and a repeated "ACME Annual Report / Page N" at page edges.
2. Run the dry run; show `stats` and the two `suspicious` entries.
3. Run the real command; show the repaired paragraphs and three log entries with their reasons.
4. Show `numbers_unchanged: true` and the refusal message when `--out` points at the input file.

## FAQ seeds

- Does it need network or send my text anywhere? No.
- Can it run OCR on an image? No; it repairs text that OCR already produced.
- Why did it leave `tirne` alone? The document has too little evidence that it is `time`; it is flagged instead.
- Will it change prices or amounts? Never; it flags them and aborts if any number differs.
- How is it different from the PDF skill? That one extracts from text-layer PDFs and forms; this one repairs OCR damage.
- Is my original file safe? Yes; the script refuses to write to it.
- How do I uninstall? Delete the skill folder; nothing else was installed.

## Changelog

0.1.0, 2026-11-21: first draft; script fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted with AI assistance (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
