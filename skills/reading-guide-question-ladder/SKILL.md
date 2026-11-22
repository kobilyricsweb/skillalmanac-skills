---
name: reading-guide-question-ladder
description: "Use when turning a complete supplied passage and learning goal into an evidence-grounded ladder of locating, explaining, interpreting, and evaluating questions. Do not use for outlining notes, adding outside facts, or asking factual questions the passage cannot answer."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Read the complete supplied passage and learning goal before drafting questions. Build a ladder that moves only through permitted levels. For every question, provide a precise passage location, cognitive move, expected evidence, response length, and answerability check. Keep factual claims inside the passage. Label reflection explicitly. Preserve qualifiers and distinguish stated sequence or association from causation. Evaluation questions must state what the text supports and leaves unproven. If the passage is incomplete, ambiguous, or too short for a requested level, flag that limitation and lower or omit the question.

Return the ordered question ladder and a brief teacher note on unresolved limits. Include the [input contract](references/input-contract.md) and [worked example](references/worked-example.md) references in the final skill package.

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
