# Templates for the checker

## Contents

- Source log
- Report skeleton
- Rules the checker applies
- Error and warning codes

## Source log

A single table in `sources.md`. Other text in the file is ignored.

```
| id | title | url | accessed | quote |
|---|---|---|---|---|
| S1 | Title of the page | https://host/path | 2026-01-31 | "The sentence you relied on, copied from the page." |
```

- `id`: `S` plus digits, unique.
- `accessed`: ISO date the page was opened; not later than today.
- `quote`: non-empty; under about 300 characters.

## Report skeleton

```
# Title

## Question
<one sentence question, then scope: window, region, definitions>

## Summary
<claims only, each paragraph cites> [C1, C2]

## Findings
<one paragraph or list item per point, each cites> [C3]

## Claim table
| claim_id | claim | source_ids | quote | confidence |
|---|---|---|---|---|
| C1 | One atomic claim | S1 | verbatim fragment | 0.7 |
| C2 | Claim backed by two sources | S1, S2 | fragment found in S1 or S2 | 0.9 |

## Contradictions
| topic | claim_ids | resolution |
|---|---|---|
| What differs | C3, C4 | Why, or "unresolved; both shown" |

## Gaps
- What could not be answered or opened.
```

If there are no contradictions, keep the heading and write one sentence such as "None found." Omit the table.

## Rules the checker applies

- Sections are found by level-2 headings, case-insensitive.
- Only paragraphs and list items under Summary and Findings need a citation. Headings, tables, block quotes and code fences are skipped. Sub-headings (level 3) stay inside their section.
- A claim's `quote` must appear, after lowercasing and whitespace and quote-mark normalisation, inside the logged quote of at least one cited source.
- `source_ids` may be separated by commas, semicolons or spaces.
- Confidence is a number from 0.0 to 1.0.

## Error and warning codes

Errors make `ok` false: `sources_table_missing`, `sources_empty`, `source_id_invalid`, `source_id_duplicate`, `source_url_invalid`, `source_date_invalid`, `source_date_future`, `source_quote_missing`, `section_missing`, `claim_table_missing`, `claim_table_empty`, `claim_id_invalid`, `claim_id_duplicate`, `claim_text_missing`, `claim_no_source`, `claim_unknown_source`, `claim_quote_missing`, `claim_quote_not_in_source`, `confidence_out_of_range`, `source_unused`, `paragraph_uncited`, `citation_unknown_claim`, `contradiction_needs_two_claims`, `contradiction_unknown_claim`, `contradiction_no_resolution`.

Warnings: `source_quote_long`, `single_source_high_confidence`, `claim_not_cited_in_text`.
