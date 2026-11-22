# Chunking guide

Read this when the script cannot run, when choosing metadata, or when a defect needs a longer explanation.

## Contents

- Manual procedure without Python
- Defect meanings and fixes
- Metadata to store
- Why the thresholds are what they are
- Sources

## Manual procedure without Python

1. Pick three files of different length. Split each by the chosen strategy with a text editor or by hand.
2. Count words and punctuation marks per chunk (a word count times 1.15 is close enough for English prose).
3. Look for: a chunk with no words, a code fence or table cut in two, a chunk under 40 tokens, two identical chunks, a chunk that begins mid-section with no heading, a chunk above 1.5 times the target.
4. Take 10 questions, find each answer, and check whether the whole answer sits inside one chunk. Each answer cut in two is a boundary failure. The share of questions whose answer is whole in one chunk is the upper bound on recall for that setting.

## Defect meanings and fixes

| Defect | Meaning | Fix |
|---|---|---|
| `overlap_too_large` | overlap above half the size | lower it; 10 to 15 percent is the normal range |
| `empty_chunk` | no letters or digits, for example a rule line | drop such blocks or merge them into a neighbour |
| `split_code_fence` | a chunk starts or ends inside a fenced block | use `paragraph` or `heading`, which keep blocks whole |
| `split_table` | a chunk starts or ends inside a table | same; for very long tables use row groups with a repeated header row |
| `oversize_chunk` | above 1.5 times the size | a single block that cannot be cut safely; accept for code and tables |
| `orphan_chunk` | under `--min-tokens` (default 40) | raise the size, or accept for short sections that are complete answers on their own |
| `duplicate_chunk` | same text after whitespace and case folding | remove the repeated source text; duplicates take slots in the top k |
| `heading_context_lost` | the chunk's own text lacks its heading | `--prefix-heading`, or store `heading_path` and add it at embedding time |
| `answer_spans_boundary` | the expected passage exists but no chunk holds all of it | more overlap, bigger size, or `heading` |

## Metadata to store

| Field | Use |
|---|---|
| `source` | file path or URL; shown with every answer so the user can check it |
| `heading_path` | the chain of headings above the chunk; can be prepended to the text before embedding |
| `position` | index of the chunk in its file; lets you fetch the neighbours of a hit |
| `start`, `end` | character offsets for highlighting and for rebuilding the surrounding text |
| `tokens` | size filter and cost tracking |
| document date or version | add it yourself when answers can go stale |

## Why the thresholds are what they are

- Under 40 tokens a chunk is usually a heading, a caption or a lone sentence; it matches many queries on a single word and rarely answers one. This is a working value.
- Overlap above half the size means each chunk is mostly a copy of the previous one: the index grows and near-duplicates fill the top k. The 10 to 15 percent default protects a sentence that straddles a boundary without that cost.
- Size ranges by question type come from the trade-off that small chunks match one fact precisely and large chunks keep the context of an explanation. They are starting points; the compare step decides.
- Recall differences below two questions are inside the noise of a small question set.

## Sources

- Fenced code blocks, which the script treats as unbreakable: https://spec.commonmark.org/0.31.2/#fenced-code-blocks
- Tables in GitHub Flavored Markdown, treated as unbreakable when written with leading pipes: https://github.github.com/gfm/#tables-extension-
- The BM25 ranking function used for the offline test: https://en.wikipedia.org/wiki/Okapi_BM25
