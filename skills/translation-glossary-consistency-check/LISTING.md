# Translation glossary consistency check

## One line

Reports, line by line, whether a translation used the agreed glossary target for each source term, and flags missing terms and known wrong variants.

## What it does

The skill takes three inputs: a glossary CSV with the header `source,target`, a source text file, and a translated text file with one segment per line. The two text files are paired by line number. For each glossary source term found in a source line, the script checks the paired translated line for the agreed target term. A second glossary row that repeats a source term with a different target registers a known variant. If that variant appears in the translated line, the hit is reported as VARIANT. If neither the agreed target nor a variant appears, the hit is reported as MISSING. The output is one JSON object with a coverage percentage and a finding for each flagged line, so a reviewer can jump straight to the line that needs a fix. The script never translates, edits, or writes files.

## When to use

Use it when a translated document must use one approved word for each source term, for example product names, legal terms, or interface labels. It also fits a review pass on translator output where the glossary owner wants proof of term use before sign-off. The input must be line-aligned, so each translated line corresponds to the source line it renders.

## When not to use

Do not use it to judge whether a translation is accurate, fluent, or natural. A clean result shows only that the agreed terms appear. Do not use it on documents whose lines were re-flowed, merged, or split during translation, because the pairing would be wrong. Do not use it for scripts without spaces between words unless a person reviews the flagged lines, since the whole-word rule can fail there.

## Requirements

Python 3.9 or later, standard library only. No network access and no extra packages. Each input file must be 2 MB or smaller and valid UTF-8, with an optional byte-order mark.

## Example

Command, run on the shipped fixtures:

```
python -I scripts/glossary_check.py --glossary fixtures/glossary.csv --source fixtures/source.txt --translated fixtures/translated.txt
```

Output, exit code 1:

```
{
  "status": "findings",
  "source_lines": 6,
  "glossary_terms": 4,
  "term_occurrences": 10,
  "ok_count": 7,
  "coverage_percent": 70.0,
  "findings": [
    {
      "line": 3,
      "source_term": "refund",
      "agreed_target": "reembolso",
      "status": "VARIANT",
      "variant_found": "devolución"
    },
    {
      "line": 5,
      "source_term": "invoice",
      "agreed_target": "factura",
      "status": "MISSING",
      "variant_found": null
    },
    {
      "line": 6,
      "source_term": "shipping address",
      "agreed_target": "dirección de envío",
      "status": "MISSING",
      "variant_found": null
    }
  ]
}
```

## Limits

Matching is literal and whole-term only. Inflected or plural target forms do not count as the agreed target, so `facturas` will not satisfy `factura`. Terms in scripts without spaces between words may be missed or misread. For each source term, the first glossary row is the agreed target, and later rows with a different target are variants, so the glossary must list the agreed target first. Coverage is a count of term use, not a quality score. The script does not check glossary spelling, duplicates across case variants of a target, or whether the agreed target is the correct translation.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
