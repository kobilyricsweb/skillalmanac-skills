---
name: validation-rule-conflict-map
description: "Use when labeled validation rules from multiple notes overlap or contradict and implementers need a field-level compatibility analysis. Do not use for making an unstated policy choice, separating general decision evidence, or writing validation code."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.2"
  network: none
---

Collect each supplied validation rule with its field, scope, operator, limit or predicate, source ID, and exception or precedence clause. Compare rules only where their supplied scopes overlap. Classify intersections as compatible, redundant, contradictory, conditional, or undecidable. Preserve original wording and source identifiers so evidence remains distinct from interpretation.

Missing precedence does not by itself make a comparison undecidable. Classify the relationship when scope, units, boundaries, and applicability are sufficiently supplied; record absent precedence and leave a genuine conflict unresolved rather than selecting a governing rule. If one supplied statement asserts precedence while another explicitly says no precedence exists, preserve both statements, identify the governance conflict, and leave control unresolved unless the input states which statement governs. Apply precedence only when its authority is established by the supplied input. Do not choose the stricter limit, newer-looking note, job title, or assumed business preference.

Produce a field-level conflict map with rule pairs or groups, scope intersection, exact constraints, classification, supplied precedence statements, and resolution-needed status. Add unresolved questions for missing or conflicting evidence. If required inputs are absent, return a partial map and name the gap. Do not write implementation code or declare a final policy unless the notes do so. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return JSON matching [references/output-schema.json](references/output-schema.json). The schema and synthetic example define the artifact shape; examples are not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema. The checker is offline and checks structure only; behavioral quality is assessed separately.
