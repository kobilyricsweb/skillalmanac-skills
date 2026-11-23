---
name: procedure-branch-test-matrix
description: "Use when supplied procedure conditions, actions, boundaries, and precedence rules need synthetic cases that expose covered, unknown, unreachable, and missing branches. Do not use for executing procedures, routing observed incidents, inventing defaults, or claiming runtime verification."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Design a branch-to-test-input matrix from the supplied procedure conditions, actions, boundary values, and precedence rules. Translate each explicit condition into synthetic inputs that exercise true, false, equality, boundary, and precedence behavior where those cases are defined by the procedure. Record the expected path only when the supplied rules determine it. Include the exact input, applicable condition, expected action or branch, rationale, and coverage status.

Separate covered branches from branches that are unspecified, unreachable under the supplied constraints, or not testable because required inputs are missing. Missing-value behavior must remain unknown unless the procedure explicitly defines it. Do not create a default action, infer condition ordering, or treat a plausible outcome as an expected result. If conditions overlap and no precedence rule is supplied, report a conflict and keep the expected path unresolved. Use synthetic values and label them as such.

Output the matrix, branch coverage summary, unresolved-rule register, and boundary notes. Verify that every expected path is traceable to a supplied rule, arithmetic or comparisons are correct, and no row claims execution, runtime verification, or operational success. If a time budget is supplied, allocate only within it and state infeasibility when the requested cases cannot fit. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
