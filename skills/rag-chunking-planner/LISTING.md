# Listing page content: rag-chunking-planner

**One line:** Chunks your docs by three strategies and measures defects and offline recall, so chunk settings are chosen with numbers.

## What it does

The skill gives an agent a decision table (corpus type to strategy, question type to chunk size), a seven-step workflow and a script, `plan_chunks.py`. The script splits a folder of Markdown or text files by fixed windows, by heading, or by paragraph with overlap, keeping code fences and tables whole where the strategy allows. It reports chunk count and size distribution, empty, oversize and orphan chunks, chunks that cut a code fence or table, duplicate chunks, heading-path coverage and lost heading context, and writes `chunks.jsonl`. Given a list of questions with the passage that answers each, it measures recall at k with a standard-library BM25 scorer, and `compare` ranks several settings against each other.

## Capabilities

- `plan`: one strict JSON report (`settings`, `stats`, `heading_context`, `defects[]`, `recall_at_k`) and an optional `chunks.jsonl` with source, heading path, position and offsets
- `compare`: recall at k, size summary and defect counts per setting, with a ranking
- Detects overlap above half the chunk size, chunks with no text, answers split across a chunk boundary
- Decision tables for code, tables and transcripts (guidance only; the script does not chunk those)

## When to use

You ask what chunk size or overlap to use for a RAG chatbot over documents, why retrieval misses answers that are in the docs, or which of several chunking settings is better.

## When not to use

Choosing an embedding model or vector database, writing the retrieval or generation pipeline, estimating embedding cost, judging whether answers are faithful. Nearest existing skills: library-docs-lookup (reads library documentation), sql-and-database-helper (queries databases), mcp-server-builder (builds tool servers). This skill differs by measuring chunking quality with an offline recall test instead of recommending a number.

## Requirements

Python 3.9 or newer (standard library only). No network. Without Python the agent follows the manual procedure in `references/guide.md`.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from the saved fixtures in `evals/fixtures/` (a 2-file corpus of 7 to 9 chunks and a 6-question set), run with `python evals/run_fixtures.py`. No with-skill agent run exists yet.

1. Compare three settings:
   `python scripts/plan_chunks.py compare evals/fixtures/corpus --questions evals/fixtures/questions.json --setting fixed:40:5 --setting paragraph:50:10 --setting heading:60:0 --k 1,3`
   Result: ranking `heading:60:0`, `paragraph:50:10`, `fixed:40:5`. Recall at 1 and 3 is 1.0 for the first two and 0.8 for `fixed:40:5`, whose defects are 2 chunks cutting the code fence, 3 cutting the table and 1 answer split across a chunk boundary (`q-lockout`). Exit code 1 because of the error-level defects.
2. Audit one setting: `python scripts/plan_chunks.py plan evals/fixtures/corpus --strategy paragraph --size 50 --overlap 10`
   Result: 9 chunks, median 32 tokens, p95 51; defects are 7 orphan chunks (under 40 tokens), 1 duplicate pair (`faq.txt#1 == faq.txt#3`) and 2 chunks that start mid-section without their heading. Exit code 0.

## Limits

- Recall comes from BM25 word matching: it ranks settings against each other on your corpus and questions, and does not predict embedding-based retrieval or answer quality.
- Tokens are words and punctuation marks, not model tokens.
- Reads only `.md`, `.markdown` and `.txt`; code, table and transcript strategies are guidance only.
- Fewer than 15 questions give noisy recall; questions should come from real users when possible.
- Markdown ATX headings only.

## Evidence

| Check | Result | Date |
|---|---|---|
| House lint | see VERIFICATION.md | 2026-11-21 |
| Script fixtures | 10 of 10 cases pass | 2026-11-21 |
| Trigger test, with/without eval, cross-tool | not run | |

## Demo script (60 to 90 seconds)

1. Prompt: "Which chunk size should my docs chatbot use? Docs are in ./docs."
2. The agent classifies the corpus (headings, fact-lookup questions) and writes a 15-question file with verbatim answer passages.
3. It runs `compare` on four settings and shows recall at 1, 3, 5 side by side.
4. It runs `plan` on the leader, shows the 2 orphan chunks and the duplicate pair, fixes the source and re-runs to zero defects.
5. It writes `chunks.jsonl` and reports the chosen setting with what was not measured.

## FAQ seeds

- Does it need a vector database or network? No; BM25 runs locally in Python.
- Does recall here equal recall with my embeddings? No; use it to compare settings, then confirm with your retriever.
- Can it chunk code or CSV files? No; it gives guidance and skips those extensions.
- What does the heading prefix do? It adds the heading path to the text used for matching, so a chunk from the middle of a section still carries its title.
- Where do the 200 to 400, 400 to 800 and 800 token ranges come from? They are working values, and the compare step is what decides.
- How do I uninstall? Delete the skill folder; the script writes only the `--out` file you name.

## Changelog

| Version | Date | Change | Re-verified |
|---|---|---|---|
| 0.1.0 | 2026-11-21 | First draft | fixtures and lint only |

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5 under the accountable publisher Global Media Holdings; no human review has taken place yet.
