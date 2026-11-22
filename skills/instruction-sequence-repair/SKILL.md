---
name: instruction-sequence-repair
description: "Use when a complete set of written instructions has explicit dependencies, hidden prerequisites, forward references, or late verification steps and needs a dependency-supported reordering. Do not use for general prerequisite mapping, rewriting immutable actions, inventing missing steps, or changing an instruction sequence without supplied dependency evidence."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Inspect the supplied instruction steps, dependency statements, starting state, expected end state, and immutable step text. Build a dependency view in which each action is placed only after the prerequisites explicitly supported by the input. Identify forward references, hidden prerequisites, and verification checkpoints that occur after the action they are meant to validate.

Produce a reordered step plan that preserves every immutable action’s wording. For each moved step, record its original position, new position, and the dependency that justified the move. Place a verification checkpoint immediately after the relevant action when the input identifies what it verifies; do not create a new verification action. If several orders satisfy the dependencies, retain the original relative order where possible and state the tie-break rule.

Do not infer dependencies from convenience, common practice, or domain knowledge. Do not silently edit, merge, split, or add steps. If a dependency is missing, contradictory, or cyclic, report the affected steps and provide a conditional order only when the condition is explicit. If starting or ending state is absent, identify the resulting boundary uncertainty. Verify that all original actions remain present and that the proposed order reaches the stated end state only to the extent supported by the supplied input.

Use [input contract](references/input-contract.md) and [worked example](references/worked-example.md) as the governing output references.

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
