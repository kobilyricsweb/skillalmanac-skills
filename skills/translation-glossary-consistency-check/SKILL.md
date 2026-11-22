---
name: translation-glossary-consistency-check
description: Checks that a translation uses the agreed glossary target term on each line, pairing source and translated text by line number and flagging missing terms and known wrong variants. Use when a translated document must use one approved term per source term, when reviewing translator output for terminology drift, or when a glossary CSV and line-aligned source and translated text files are ready to compare. Do not use for translating text, judging translation quality, fluency or meaning, or comparing files that are not line-aligned.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Translation glossary consistency check

This is a type A skill. The script reads three files and reports term use. It does not translate, rewrite, or edit anything, and it writes no file.

## Workflow

1. **Confirm the three inputs.** You need a glossary CSV, a source text file, and a translated text file. Output: the three paths, each stated as present or missing. If one is missing, stop (see Refuse / stop when).
2. **Check file size and encoding.** Each file must be 2 MB (2,097,152 bytes) or less and valid UTF-8. A leading byte-order mark is accepted. Output: pass or fail for each file.
3. **Check line alignment.** Line N of the translated file must be the translation of line N of the source file. Count the lines of both files. If the counts differ, stop with exit 2. Do not pad, drop, or re-split lines to make them match. Empty lines count as lines.
4. **Check the glossary shape.** The header row must be exactly `source,target`. Each data row needs exactly two non-empty cells. If one source term appears on several rows with different targets, the first row is the agreed target and each later distinct target is a known variant. Output: count of distinct source terms, and count of variant rows.
5. **Run the script** with the command line below. Use the actual paths in place of the placeholders.
6. **Apply the decision table** to the report and write the reply in the output contract below.

Command line (run from the skill folder):

```
python -I scripts/glossary_check.py --glossary <glossary-csv> --source <source-file> --translated <translated-file>
```

## Matching rules (fixed)

| Rule | Value |
|---|---|
| Term match | Case-insensitive, whole term only |
| Word boundary | A letter, digit, or underscore directly before or after a match means no match |
| Inflection and stemming | None. `facturas` does not match a target `factura` |
| Status precedence | If any known variant appears in the translated line, the status is VARIANT even when the agreed target also appears |
| Source term with no match in the translated line | MISSING |
| Scripts without spaces between words | The boundary rule can fail. Review those lines by hand |

## Decision table

Coverage is `ok_count` divided by `term_occurrences`, shown as a percentage with one decimal. The 90.0 threshold is a working value, not a published standard.

| Condition | Action |
|---|---|
| Exit 0, status `ok`, coverage 100.0 | Accept the terminology. No fix needed |
| Exit 1, findings are all VARIANT | Return the listed lines to the translator with the agreed target |
| Exit 1, MISSING present, coverage 90.0 or higher | Fix the listed lines and re-run |
| Exit 1, coverage below 90.0 (working value) | Return the whole document for terminology review, then re-run |
| Exit 1 or 0 with `coverage_percent` null | No source term matched any source line. The check proved nothing. Do not accept. Confirm the glossary matches the source language |
| Exit 2 | Fix the input named in the error, then re-run. Do not accept |

## Output contract

The script prints one JSON object to stdout, UTF-8, indented by two spaces. Keys in this order:

| Key | Type | Meaning |
|---|---|---|
| `status` | string | `ok` (exit 0) or `findings` (exit 1) |
| `source_lines` | integer | Number of paired lines |
| `glossary_terms` | integer | Distinct source terms in the glossary |
| `term_occurrences` | integer | Source term hits across all lines |
| `ok_count` | integer | Hits whose agreed target appears and no variant does |
| `coverage_percent` | number or null | `ok_count / term_occurrences * 100`, one decimal; null when there are no hits |
| `findings` | array | One object per flagged hit, in line order |

Each finding object has these keys: `line` (1-based), `source_term`, `agreed_target`, `status` (MISSING or VARIANT), `variant_found` (the variant text, or null for MISSING).

On a usage or input error the script prints one JSON line to stderr, `{"error": "<message>"}`, and exits 2.

Reply to the user with three headings: **Summary** (status, coverage, counts), **Findings** (table with columns Line, Source term, Agreed target, Status, Variant found; write "None" when empty), and **Next step** (the action from the decision table).

## Script contract

- Script: `scripts/glossary_check.py`
- Arguments, all required: `--glossary <path>`, `--source <path>`, `--translated <path>`
- Output: JSON object on stdout, keys as in the output contract
- Exit codes: 0 = no findings; 1 = one or more MISSING or VARIANT findings; 2 = usage, read, size, encoding, glossary shape, or line-count error
- Reads only. No network, no subprocess, no file writes

## Smoke check

Run on the shipped fixtures: `python -I scripts/glossary_check.py --glossary fixtures/glossary.csv --source fixtures/source.txt --translated fixtures/translated.txt`. Expected: exit 1, `status` findings, 6 source lines, 4 glossary terms, 10 term occurrences, 7 OK, coverage 70.0, and three findings at lines 3 (VARIANT), 5 (MISSING), and 6 (MISSING).

## Files in this skill

- [scripts/glossary_check.py](scripts/glossary_check.py): the checker described above
- [fixtures/glossary.csv](fixtures/glossary.csv): smoke-test glossary, 5 data rows for 4 terms
- [fixtures/source.txt](fixtures/source.txt): smoke-test source, 6 lines
- [fixtures/translated.txt](fixtures/translated.txt): smoke-test translation, 6 lines with 3 planted inconsistencies
- [LICENSE.txt](LICENSE.txt): Apache License 2.0

## Refuse / stop when

- The request is to translate, rewrite, or correct the translated text. This skill only reports term use.
- The request is to judge fluency, accuracy, tone, or meaning. A clean result proves term use only.
- Any of the three inputs is missing or unreadable. Exit 2, and name the missing input.
- The glossary header is not exactly `source,target`, or a data row does not have two non-empty cells.
- The source and translated files have different line counts. Do not pad or re-split them.
- Any input is over 2 MB or is not valid UTF-8.
- The request is to write the report into a file or to overwrite an input. This skill writes no files; say so and offer the printed report instead.
- The request is to change the agreed target because the translator used another word. The glossary owner decides that, not this check.
