---
name: missingness-pattern-brief
description: "Use when a supplied table needs an evidence-bounded summary of blank values by field, subgroup, or co-occurrence pattern. Do not use for profiling field types, explaining why values are absent, imputing data, or treating blanks, zeros, and unknowns as equivalent."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Analyze only the records, blank markers, subgroup fields, and scope supplied by the user. First confirm which representations count as missing; preserve zero, empty-but-valid values, unknown labels, and unlisted values separately unless the input explicitly groups them. For every in-scope field, report total records, missing count, and missing proportion only when the denominator is defined. If subgroups are declared, repeat the field summary within each subgroup and state subgroup sizes. Identify co-missing field combinations only when the records support them, distinguishing pairwise co-occurrence from broader patterns. Preserve record order or identifiers when needed for auditability.

Interpret absence descriptively. Do not infer causes, mechanisms, bias, intent, or data-quality failures from patterns alone. Do not infer that a field is complete outside the declared scope. If markers conflict, subgroup labels are missing, or scope is ambiguous, list the conflict and pause the affected calculation rather than choosing silently. Produce a concise missingness brief with assumptions, tables, observed patterns, and interpretation limits. Verify reported counts against the supplied rows and disclose excluded records or fields. The result is an analytical draft, not an imputation, diagnosis, or remediation decision. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
