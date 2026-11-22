---
name: inventory-count-reconciliation-plan
description: "Use when two supplied inventory observations disagree and you need a controlled worksheet that preserves both counts, explains documented arithmetic differences, and identifies recounts. Do not use for duplicate-record similarity classification, stock correction, shrinkage estimation, or record changes."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Create a reconciliation worksheet from the supplied count lists and evidence. Normalize item identifiers only when an explicit identifier rule permits it; otherwise retain the original labels and flag ambiguity. For each item, preserve both observations, count times, documented adjustments, and permitted resolution steps. Group rows as exact match, arithmetically explainable difference, recount candidate, or unresolved discrepancy. An explainable difference must be supported by a supplied adjustment whose arithmetic reconciles the observations; do not infer sales, shrinkage, transfers, timing effects, or corrections. Never alter either observed count.

Report the comparison basis, calculation for every explained difference, evidence used, and any conflicting or missing inputs. Mark items for recount when no supplied adjustment explains the difference or when identifiers, times, or policies conflict. If a permitted resolution step would change a record, describe it as a proposed next step only; do not perform it. If either list or required evidence is missing, produce a partial worksheet and identify the blocked rows rather than filling values.

Output the worksheet, an unresolved-input section, and a concise review summary. Verify that every row retains both observations, every explanation cites supplied evidence, and no arithmetic is asserted without calculation. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
