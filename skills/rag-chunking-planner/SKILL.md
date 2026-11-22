---
name: rag-chunking-planner
description: Plans chunking for RAG and document question answering. Use when the user asks what chunk size or overlap to use, how to chunk docs for a RAG chatbot, why retrieval misses answers that are in the docs, or wants chunking settings compared. A script chunks Markdown or text by fixed, heading or paragraph-with-overlap strategies, reports size spread, orphans, split code blocks and tables, duplicates and lost headings, and compares settings with an offline recall-at-k test, no vector database needed. Do not use for choosing an embedding model or vector store, building the retrieval pipeline, or judging answer quality.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in references/guide.md.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# RAG chunking planner

Choose chunk settings with numbers, not opinion. Classify the corpus, pick a strategy and size from the tables below, then run `scripts/plan_chunks.py` to measure defects and to compare settings by how often the right passage lands in the top k results.

## Run the script first

Every answer about chunk settings starts with a run of `scripts/plan_chunks.py` (path relative to this skill folder, Python standard library only). Do not write a substitute chunker or a substring check: the script already measures token counts, defects and recall@1/3/5, and its numbers are what the user needs to see. Even a tiny corpus or a one-line settings question gets a run.

- **Review a planned setting** ("500 tokens, 350 overlap, is that right?"): run `plan <file-or-folder> --strategy paragraph --size 500 --overlap 350 --questions q.json`. Read `stats.chunks` and `stats.tokens` (a corpus smaller than the size gives one chunk, so the questions cannot tell settings apart: say so and ask for the full corpus or harder questions), then `defects` (for example `overlap_too_large`). Then run the corrected setting and report both.
- **Pick settings for a corpus**: run `compare` with 3 or more `--setting` values (workflow steps 3 and 4), then `plan --out chunks.jsonl` for the winner.
- Report recall as recall@1, @3 and @5 for each candidate, copied from the JSON. If a questions file exists, pass it; if it lists a question whose answer is not in the corpus, the script lists it under `passage_not_in_corpus`: treat that as a refusal test, not a recall miss.
- Always end the reply with the `Not measured:` line from step 7, naming the embedding model and that recall comes from a BM25 word matcher.

## Decision tables

Corpus type decides the strategy:

| Corpus | Strategy | Overlap | Script support |
|---|---|---|---|
| Docs with Markdown headings | `heading` (split at levels 1 to 3), plus `--prefix-heading` | 0, applies only to oversized sections | yes |
| Plain prose (articles, policies, FAQ text) | `paragraph` | 10 to 15 percent of size | yes |
| Unstructured text with no blank lines | `fixed` | 10 to 15 percent of size | yes |
| Source code | one chunk per function or class, signature and docstring kept together | none | no: audit by hand |
| Tables and CSV | row groups of about 20 to 50 rows, header row repeated in every group | none | no: audit by hand |
| Transcripts | time windows of 60 to 120 seconds, 10 to 20 seconds of overlap, speaker label kept | by time | only after conversion to text with one paragraph per speaker turn |

Question type decides the size, in script tokens (one word or punctuation mark each, close to model tokens for English):

| Typical question | Size | Why |
|---|---|---|
| Fact lookup ("what is the refund window") | 200 to 400 | one fact per chunk keeps the match sharp |
| Explanation ("how does rollback work") | 400 to 800 | needs the surrounding steps |
| Synthesis across a section | 800 or more | or retrieve more small chunks and merge by heading path |

These ranges are working values from practice, not measured optima. Keep the size under 70 percent of the embedding model's input limit. Mixed question types: start at 400 and let step 4 decide.

## Workflow

```
- [ ] 1 Classify the corpus and the question type
- [ ] 2 Write the questions file
- [ ] 3 Pick 3 or 4 candidate settings
- [ ] 4 Run compare
- [ ] 5 Inspect defects of the leading setting
- [ ] 6 Write chunks.jsonl for the chosen setting
- [ ] 7 Report
```

1. **Classify.** Look at 3 or 4 files, not all of them. If the folder mixes types, split it and plan each part.
2. **Questions file.** A JSON list of 15 or more objects, taken from the user or written from the corpus: `{"id": "q1", "question": "...", "expected_passage": "...", "source": "file.md"}`. `expected_passage` is a verbatim span of 8 or more characters from the corpus that holds the answer (whitespace and case are ignored). Include at least 3 questions whose answer sits in a table, list or code block, and 3 whose answer needs a sentence from the middle of a long section. `source` is optional and narrows the match. Never write passages from memory: copy them.
3. **Candidates.** Use the tables: the strategy for the corpus at the low, middle and high end of the size range, for example `heading:300:0`, `paragraph:300:40`, `paragraph:600:80`. Add `fixed:400:60` as the structure-blind baseline.
4. **Compare.** Run it, and do not edit the script to change a result:

```bash
python scripts/plan_chunks.py compare <corpus-folder> --questions questions.json --setting heading:300:0 --setting paragraph:300:40 --setting paragraph:600:80 --setting fixed:400:60 --k 1,3,5
```

   Add `--prefix-heading` when the corpus has headings. Read `ranking` and each run's `recall_at_k`. One question is worth 1/n of recall: treat a gap smaller than 2 questions as a tie and prefer the setting with fewer defects, then fewer chunks.
5. **Inspect.** Run `plan` for the leader with the same settings and read `defects`:

```bash
python scripts/plan_chunks.py plan <corpus-folder> --strategy paragraph --size 300 --overlap 40 --questions questions.json
```

   Fix by rule: any error-level defect (`empty_chunk`, `split_code_fence`, `split_table`, `overlap_too_large`) must be zero. `orphan_chunk` above 10 percent of chunks means the size is too small or sections are too short: raise the size or use `paragraph`. `duplicate_chunk` means repeated text: deduplicate the sources before indexing, not after. `oversize_chunk` is an unsplittable block: accept it if it is a code block or table, otherwise add blank lines to the source. `answer_spans_boundary` names questions whose answer was cut in two: raise the overlap (up to half the size) or the size, or switch to `heading`. `heading_context_lost` disappears with `--prefix-heading`; it only matters if the index text will not include the heading path.
6. **Write chunks.** Add `--out chunks.jsonl` to the `plan` command. Each row has `id`, `source`, `position`, `heading_path`, `tokens`, `start`, `end` (character offsets into the normalised file text) and `text`. Store `source`, `heading_path` and `position` as retrieval metadata; show the source and heading path with every answer. An existing output file is refused unless `--force` is given.
7. **Report** in this shape:

```
Corpus: <type, files, question type>
Chosen: <strategy:size:overlap, prefix-heading yes/no>
Evidence: <recall@1/3/5 for each candidate, questions evaluated>
Defects left: <type and count, or none>
Not measured: <embedding model, real tokenizer, answer quality, questions beyond the file>
```

## Script

`scripts/plan_chunks.py`: run it, do not edit it. Two commands, both print one strict JSON document.

- `plan <path>`: keys `settings`, `stats` (chunks, tokens min, median, p95, max, mean, histogram), `heading_context`, `defects[]` (type, severity, count, up to 5 examples, note), `recall_at_k` (null without `--questions`). Exit 0 with no error-level defect, 1 with at least one, 2 on bad input (message on stderr).
- `compare <path> --questions <file> --setting strategy:size:overlap ...` (two or more): per run chunk count, size summary, defect counts and recall, plus `ranking`.

`recall_at_k` holds `k` (recall at each k), `questions_evaluated`, `answer_spans_boundary`, `missed_at_max_k`, `passage_not_in_corpus` (fix these questions) and `passage_too_short`.

Strategies: `fixed` slides a window of `--size` tokens with `--overlap`. `heading` cuts at headings up to `--split-level` (default 3) and repacks sections above the size by paragraph. `paragraph` packs whole paragraphs, code blocks and tables up to the size, carries whole trailing blocks as overlap, never splits a fence or table, and cuts only paragraphs larger than the size, at sentence ends. Headings stay with the block after them.

Without Python, do steps 1 to 3 and 7 by hand, split a few files at the chosen setting and check the defect list in [references/guide.md](references/guide.md) against them. Read that file also for the metadata fields and the reasoning behind the thresholds.

## Limits

- Recall comes from a plain BM25 word matcher. It ranks settings against each other for this corpus and these questions. It does not predict embedding-based retrieval, rerankers or answer quality, and a setting that wins here can lose with a different retriever.
- Tokens are words and punctuation marks, not model tokens. Check the real count with the embedding model's own tokenizer before fixing a size near its limit.
- Only `.md`, `.markdown` and `.txt` files are read, up to 2 MB each; other files are skipped and listed. Code, table and transcript strategies are guidance only.
- Fewer than 15 questions give noisy recall. Questions written by the same agent that tunes the settings flatter them; use questions from real users when they exist.
- Headings are Markdown ATX headings (`#`). Setext headings and HTML headings are not recognised.
