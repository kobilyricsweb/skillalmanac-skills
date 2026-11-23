---
name: table-footnote-scope-map
description: "Use when a supplied report table contains footnote markers and definitions whose applicability may be cell-, row-, column-, or table-level, and you need an auditable scope map. Do not use for extracting table content, formatting references, validating claims, or inferring qualifier inheritance from marker placement alone."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Create a cell-level qualifier-scope map from the supplied table only. First inventory labeled cells, row and column headings, every marker placement, each supplied definition, and any explicit scope legend. Preserve marker text exactly and assign stable cell identifiers.

For each marker, separate three facts: placement, definition text, and scope rule. Apply a scope beyond the marked cell only when the supplied legend or an explicit supplied instruction authorizes that inheritance. A marker in a heading, row label, column label, or nearby cell does not independently establish broader applicability. If supplied definitions conflict, preserve each definition and mark the qualifier meaning or definition binding unresolved. Keep any independently authorized scope unless the supplied scope rules themselves conflict; only a scope-rule conflict makes scope unresolved. If a marker has no supplied definition, record it as orphaned. If a definition has no placement, record it as unbound. Never treat a qualifier as proof of the underlying claim, and do not add unstated exclusions, inclusions, or interpretations.

Return: (1) a scope map with cell ID, visible value, marker, exact definition reference, authorized scope, and rationale; (2) orphan markers; (3) unbound definitions; (4) unresolved inheritance, definition bindings, or conflicts; and (5) a short boundary note stating which scopes were explicitly supplied versus left unresolved. Use [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit 0 means structural validity, 1 contract violations, and 2 invalid input or unsupported contract. This bounded schema-profile checker reads at most 2 MiB, 50,000 nodes, and depth 100; rejects duplicate keys, nonfinite numbers, and oversized numbers; and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
