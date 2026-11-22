## Contents

1. Evidence rules and thresholds
2. Confusion table: automatic, suggestion-only, excluded
3. Dehyphenation decision order
4. Doctype matrix
5. Column and page handling
6. Manual procedure without Python

Source of the character facts: the Unicode block "Alphabetic Presentation Forms" (https://www.unicode.org/charts/PDF/UFB00.pdf) holds the Latin ligature code points U+FB00 to U+FB06 that the script expands. Everything else here describes the behaviour of `scripts/repair_ocr.py` in this skill.

## 1. Evidence rules and thresholds

The document is its own dictionary. The script counts every whole lowercase word (hyphen-break fragments and URL or e-mail chunks excluded) and decides from those counts.

| Rule | Value | Reason |
|---|---|---|
| Minimum occurrences of the corrected word (rn/m, vv/w) | 2 | one match could be a coincidence |
| Ratio corrected : original | at least 2 : 1 | a word used often in its odd form is probably real (corn, burn) |
| Digit-for-letter and interior `I` | corrected word at least 1, unique best | the damaged form cannot be a word, so one attestation is enough; a tie is flagged |
| Suggestion-only pairs (li/h, cl/d) | alternative at least 3 times, original once | flagged, never changed |
| Hard-wrap width | 90th percentile of non-blank line lengths, at most 120 | ignores a few long lines |
| Hard-wrap share | at least 35% of lines between 75% and 100% of the width | otherwise text is left alone |
| Line filled | at least 75% of width, 90% after `. ! ? :` | a line ending a sentence early is a paragraph end |
| Header or footer | first or last 2 non-blank lines of a page, same text with digits replaced by `#` on at least 60% of pages and at least 3 pages | one-off lines are content |
| Column gutter | 3 or more blank character columns in at least 95% of lines (8 or more lines) | reported, not acted on |

Expected behaviour when evidence is thin: the script changes less and flags more. That is intended.

## 2. Confusion table

| Seen | Likely truth | Handling |
|---|---|---|
| rn | m | automatic with evidence (rnodern -> modern) |
| vv | w | automatic with evidence |
| capital I inside lowercase (kIng) | l or i | automatic when one reading is attested |
| 0 inside a lowercase word | o | automatic in prose with evidence (b0at -> boat) |
| 1 inside a lowercase word | l or i | automatic in prose when exactly one reading is attested |
| 5 inside a lowercase word | s | automatic in prose with evidence |
| li | h | suggestion only (tlie, but also real words such as lie) |
| cl | d | suggestion only (clog and dog are both words) |
| O, o, l, I, \| inside a digit string (2O24, l00, 1O.50) | 0 or 1 | flagged as number-confusable, never changed |
| b for h, c for e, and other single-letter swaps | varies | not handled; the user or the image decides |

## 3. Dehyphenation decision order

A line qualifies when it ends with a hyphen (also U+2010, U+2011, U+00AC, or a soft hyphen at line end) after at least two letters that are not preceded by a digit, and the next line starts with a lowercase letter. Then, in order:

1. The hyphenated compound is attested inside a line elsewhere at least as often as the joined word: keep the hyphen, remove only the line break.
2. The joined word is attested elsewhere: join without the hyphen.
3. English only: the left part is one of self, ex, vice, well, ill, half, cross and the right part is itself a word in the document: keep the hyphen.
4. Otherwise join without the hyphen and log it as "no evidence". Review these.

A next line that starts with a capital letter or a digit is never joined (it may be a name or a number range).

## 4. Doctype matrix

| Repair | prose | table | form | receipt |
|---|---|---|---|---|
| ligature, invisible-char | yes | yes | yes | yes |
| quote-artefact | yes | no | no | no |
| rn/m, vv/w, interior I | yes | yes | yes | yes |
| digit for letter | yes | no | no | no |
| dehyphenate, unwrap | yes | never | never | never |
| header-footer | auto (3+ pages) | with `--headers on` | with `--headers on` | with `--headers on` |

In tables, forms and receipts, tokens such as A1B2 are expected to be codes and appear in `suspicious[]` as `mixed-letters-digits`; read the list for amounts, not for every code.

## 5. Column and page handling

Pages are split on the form feed character. Line numbers in `changes[]` are physical lines of the input (a form feed does not start a new line number). With `--split-columns N`, N is the 0-based character index where the right column starts; at least 2 blank characters must sit just before it in 90% of long lines on a page. Pages where that fails are left alone and named in `stats.notes`; if no page qualifies the script exits 2. The left column is emitted first, then a blank line, then the right column.

## 6. Manual procedure without Python

1. Copy the OCR file; never edit the original.
2. Replace the ligature characters with plain letters.
3. For each line ending in a hyphen before a lowercase letter, search the text for the joined word and for the hyphenated compound; join accordingly and list the joins you could not support.
4. Join hard-wrapped lines of a paragraph; keep blank lines, list items, headings and table rows.
5. For each suspected rn/m or digit-in-word error, search the document for the corrected word; change only when it occurs at least twice (rn/m) or once (digit in word).
6. Delete a header or footer only when the same line (ignoring page numbers) appears on most pages; list what you removed.
7. Do not change any number; list damaged-looking numbers for the user.
8. Write the change list with line numbers.
