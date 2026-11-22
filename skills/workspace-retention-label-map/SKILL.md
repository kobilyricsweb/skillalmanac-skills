---
name: workspace-retention-label-map
description: "Use when supplied document-type definitions, approved labels, mapping rules, exclusions, and synthetic file descriptions must become a draft retention-label map with manual-review cases. Do not use for legal interpretation, taxonomy-gap analysis, file inspection, movement, deletion, retention-policy invention, or changing files."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.3"
  network: none
---

Create a draft label map from supplied document-type definitions, approved retention labels, mapping rules, exclusions, and synthetic file descriptions. For each description, identify only cues explicitly supported by the supplied definitions, then record document type, defining cues, assigned supplied label, conflict, exclusion, and manual-review status. A label assignment requires an applicable supplied rule; names or words that merely resemble a document type are insufficient.

Keep draft status, signed status, version, and purpose distinct unless the inputs explicitly connect them. If a description lacks a required cue, conflicts with more than one rule, or falls under an exclusion, mark it for manual review and explain the missing or conflicting evidence. Do not infer legal requirements, retention duration, ownership, sensitivity, or authority. Do not inspect, move, rename, delete, label, or otherwise alter files. A proposed mapping is not operative authorization.

Output the label map, rule register, exclusion register, unresolved cases, and a short manual-review queue. Verify that every assigned label appears in the supplied approved-label list and every assignment cites a supplied rule. If the supplied label set has no applicable option, report that gap without creating one. If exclusions are supplied, record each supplied exclusion ID when present and its exact rule; if the input explicitly states that no exclusions apply, record that supplied statement without inventing an identifier. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return JSON matching [references/output-schema.json](references/output-schema.json). The schema and synthetic example define the artifact shape; examples are not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
