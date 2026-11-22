---
name: peer-review-protocol
description: "Use when students need a bounded peer-review sequence for a supplied assignment, rubric, duration, feedback scope, and submission format, including a timed disagreement path. Do not use for code review, personal judgments, or criteria invented beyond the assignment and rubric."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Design a timed peer-review protocol from the assignment prompt, rubric, review duration, allowed feedback scope, and submission format. Keep every action focused on the submitted artifact and supplied criteria. Allocate time for artifact checks, evidence-based comments, author questions, a revision choice, and disagreement handling; disagreement may be a reserved interval or an explicitly timed conditional branch whose arithmetic stays within the total.

Translate rubric criteria into concrete checks without expanding their meaning. Use evidence stems such as “I found…” and identify artifact locations. Distinguish observations from suggestions. If reviewers disagree, quote the criterion, state the competing readings, and invite the author or instructor to decide. Do not assess effort, intelligence, personality, intent, or other personal qualities.

Return the timed sequence, reviewer prompts, evidence fields, author questions, one revision-selection step, disagreement procedure, and completion check. If the duration cannot fit the required checks, show the arithmetic and identify what must be shortened or omitted. Use the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

Return JSON matching [references/output-schema.json](references/output-schema.json). The examples are synthetic specifications, not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
