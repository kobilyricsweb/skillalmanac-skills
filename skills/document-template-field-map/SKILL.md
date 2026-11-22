---
name: document-template-field-map
description: "Use when supplied template placeholders must be bound to candidate source fields under explicit mapping and transformation policies, with conflicts and unknowns exposed. Do not use for defining a general dataset dictionary, filling or sending documents, or inventing sources, conversions, or defaults."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Build a placeholder-to-source binding map from the supplied template, candidate fields, and explicit mapping or transformation policies. Record each placeholder exactly, its selected source if authorized, the binding rationale, permitted transform, required format, conflict status, and unresolved value behavior. Treat similar names as candidates only; equivalence requires an explicit rule, structural evidence supplied by the user, or an unambiguous declared mapping. Do not use current date, nearby fields, inferred defaults, or guessed conversions.

For each placeholder, classify the result as bound, conflicting, unresolved, or intentionally unfilled. A transform may be listed only when supplied, such as date formatting, unit conversion, or concatenation rules. If multiple candidates qualify, retain all candidates and identify the conflict rather than choosing silently. If a source is absent, state that the value remains unknown. If a mapping policy conflicts with a template requirement, report the conflict and do not resolve it by preference.

Output the binding map, unresolved and conflicting items, and a compact implementation note describing what a later document-filling step would need. Do not fill, save, send, or otherwise modify a document. Verify that every placeholder is represented once, every binding cites supplied support, and every transform is explicit. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
