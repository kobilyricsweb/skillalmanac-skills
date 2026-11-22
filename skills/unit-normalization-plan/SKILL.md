---
name: unit-normalization-plan
description: "Use when supplied measurements use mixed or potentially ambiguous units and need a controlled conversion specification before transformation. Do not use for inventing conversion factors, guessing unlabeled units, interpreting field meaning, or applying conversions without approved formulas and rounding rules."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Build a field-by-field normalization specification from the supplied fields, source units, target units, approved formulas, precision rules, and ambiguous examples. For each field, state the accepted source unit, target unit, formula exactly as supplied, rounding or display precision, validation checks, and treatment of values that lack a unit. Keep conversion planning separate from execution: provide transformed examples only when the input gives enough information to calculate them, and label them as planned outputs or illustrations. Preserve original values and units in the specification.

Never invent a factor, infer a unit from a label or magnitude, or assume that two unit names are interchangeable. If a formula, target, precision, or unit assignment is missing or conflicting, mark the affected field blocked and identify the needed decision. Quarantine ambiguous values rather than converting them. Verify example arithmetic, dimensional direction, rounding, and whether the stated formula applies to every listed source unit. Report exclusions, unresolved units, and any scope limits. The artifact is a transparent proposal for controlled normalization; it is not an authorization to overwrite source data and does not establish scientific, regulatory, or domain validity. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
