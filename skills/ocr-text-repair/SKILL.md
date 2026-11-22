---
name: ocr-text-repair
description: Repairs OCR output from scans, photos or screenshots into a clean copy plus a JSON change log. Use when the user says OCR text is garbled, has words split by hyphens at line ends, hard-wrapped lines, ligature junk, repeated page headers, or misreads such as rn for m and 1 for l. A script fixes a confusion only when the corrected word occurs elsewhere in the same document, rejoins and unwraps lines, removes repeated headers, and never changes numbers, only flags them. Do not use for text-layer PDF extraction or form filling, transcript cleanup, spelling or grammar editing, or running OCR on images.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only, no network. Without Python, follow the manual procedure in the last section of references/repair-rules.md.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# OCR text repair

Turn OCR output into readable text without inventing anything. The input stays untouched; the result is a repaired copy beside it and a JSON log of every change. A correction is made only when the document itself supports it.

## Inputs to collect first

1. The OCR text as a file (save pasted text to a file first; do not retype it).
2. `doctype`: `prose` (articles, letters, book pages), `table`, `form`, or `receipt`. Ask if unclear. Default `prose`.
3. Language code (`en` default). The confusion table is Latin-script only; for other scripts say so and only use the layout repairs.
4. Whether pages are separated by form feed characters (many OCR tools write them). Without them, header and footer removal cannot run.

## Workflow

```
- [ ] 1 Dry run and read the report
- [ ] 2 Settle layout questions (columns, headers)
- [ ] 3 Write the repaired copy
- [ ] 4 Review changes[] with reason "no evidence"
- [ ] 5 Work through suspicious[]
- [ ] 6 Report
```

1. **Dry run:** `python scripts/repair_ocr.py scan.txt --doctype prose --dry-run`. It writes nothing. Read `stats.notes`, `stats.unwrap_note` and `suspicious[]`.
2. **Layout:** a `column-layout` entry means a blank gutter runs down the page, so lines are being read across two columns. Lines are not joined while it is suspected. Look at three lines of the file; if it is two columns, re-run with the `--split-columns` value the entry suggests. If it is not, tell the user, because lines stay unjoined until the option is given. Headers and footers are removed only for `prose` with 3 or more pages (`--headers on` forces it for other doctypes, `--headers off` disables it).
3. **Write:** the same command without `--dry-run`. Add `--out repaired.txt --report report.json` to choose paths. Default output is `<name>.repaired<ext>` beside the input. The script refuses an `--out` or `--report` that is the input file, even with `--force`, and refuses an existing output without `--force`.
4. **Review weak joins:** every `dehyphenate` change whose reason starts "no evidence" is a default join of a line-end hyphen before a lowercase letter. Show these to the user as a short list (`before` to `after`). Keep a hyphen where the compound is right ("well-known" stays).
5. **Residual list:** each `suspicious[]` item is a question for the user or the source image, not something to fix by guessing. Kinds and what to do are in the table below.
6. **Report** in the fixed shape at the end.

Run the script; do not edit it to make a check pass. Do not hand-correct more words in the repaired file unless the user supplies the source image or confirms the word, and then say which lines you changed.

## What the script repairs, and what it never touches

| Class | Applied when | Evidence required |
|---|---|---|
| ligature | always (U+FB00 to U+FB06 expanded) | none |
| invisible-char | soft hyphen or zero-width character inside a word | none |
| quote-artefact | prose only: doubled apostrophe or backtick pair, backtick between letters | none |
| confusable `rn`->`m`, `vv`->`w` | lowercase whole word | corrected word occurs at least 2 times elsewhere and at least twice as often as the form replaced |
| confusable interior capital `I` | lowercase word such as `kIng` | exactly one of the `l`/`i` readings occurs elsewhere |
| confusable digit for letter (`0`->o, `1`->l or i, `5`->s) | prose only, lowercase word, single digits | exactly one reading occurs elsewhere |
| dehyphenate | prose only: line ends with a hyphen after 2+ letters and the next line starts lowercase | joined form attested, else hyphenated form attested, else compound prefix list, else default join (logged as "no evidence") |
| unwrap | prose only: text is hard-wrapped (about 35% of lines near full width, width at most 120) | line filled at least 75% of the width; 90% after a sentence end |
| header-footer | prose, 3+ pages: line among first or last 2 of a page, repeats with digits ignored on at least 60% of pages | repetition |
| column-reflow | only with `--split-columns` | blank gutter in at least 90% of long lines |

Never touched: any number, amount, date or code (tokens with digits other than the digit-for-letter case above); capitalised and all-caps words (names, acronyms); anything inside URL or e-mail-like chunks; table cells and form fields (lines are never joined for `table`, `form`, `receipt`); `cl`/`d` and `li`/`h` confusions, which are suggestions only because real words collide (clog/dog, lie/he).

## suspicious[] kinds

| kind | Meaning | Action |
|---|---|---|
| `number-confusable` | digits mixed with O, o, l, I or `\|` (for example `1O.50`); `suggestion` shows the likely number | check against the image; never change silently |
| `mixed-letters-digits` | letters and digits in one token, not an ordinal or unit | may be a SKU or a misread; ask |
| `confusable-unconfirmed` | a known confusion where the document has too little evidence | confirm with the user |
| `isolated-symbol`, `stray-symbol-in-word` | scan noise | delete or keep with the user's say |
| `replacement-char` | undecodable byte | needs the source |
| `column-layout` | blank gutter on a page | step 2 |

`stats.numbers_unchanged` must be `true`. If it is `false` the script exits 1 and writes no repaired file; report that and do not work around it.

## Report format

```
Files: <input> -> <output>, report <path>
Repaired: <counts by class from stats.changes_by_class>
Weak joins for review: <list, or none>
Numbers: unchanged (stats.numbers_unchanged), <n> flagged as suspicious
Left for the user: <suspicious[] items by kind, with line numbers>
Not checked: <e.g. text compared with the image; words not attested in the document; non-English words>
```

## Script contract

`python scripts/repair_ocr.py INPUT [--doctype prose|table|form|receipt] [--lang en] [--out FILE] [--report FILE] [--force] [--dry-run] [--split-columns N] [--headers auto|on|off] [--no-unwrap]` prints one JSON object on stdout:

- `changes[]`: `line`, `line_end` (original line numbers), `class`, `before`, `after`, `reason`.
- `suspicious[]`: `repaired_line`, `original_line`, `kind`, `token`, `suggestion`, `note` (capped at 300 entries; the counts in `stats` stay exact).
- `stats`: `changes_total`, `changes_by_class`, `suspicious_total`, `suspicious_by_kind`, `numbers_unchanged`, `numbers_missing`, `numbers_added`, `unwrap_applied`, `unwrap_note`, `line_width`, `pages`, `lines_in`, `lines_out`, `notes[]`.

Exit 0 done, 1 number check failed (nothing written), 2 usage or file error with a message on stderr. Read [references/repair-rules.md](references/repair-rules.md) when a decision is unclear: the evidence thresholds, why `cl`/`d` is excluded, what to do per doctype, and the manual procedure without Python.

## Limits

- Evidence comes from the document alone. A word that appears once, or only in its damaged form, is flagged, not fixed. Short documents give little evidence and fewer automatic fixes.
- The script cannot see the image. A repaired file is not proof that it matches the page; numbers in particular must be checked against the source when they matter.
- Words joined across a line break are not run through the confusion check afterwards.
- Hard-wrap detection is a heuristic on line lengths; ragged poetry, code and lists can be misjudged. Use `--no-unwrap` for those.
- Header and footer removal can delete a legitimate line that repeats at page edges (a repeated column heading); every removed line is logged.
- Right-to-left and non-Latin scripts: layout repairs only; the confusion table does not apply.
- Thresholds are working values, not measured optima.
