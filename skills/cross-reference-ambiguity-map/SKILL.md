---
name: cross-reference-ambiguity-map
description: "Use when bounded document excerpts contain references such as above, this section, or duplicate headings and the possible target locations must be mapped explicitly. Do not use for judging factual consistency, rewriting prose, modifying navigation, or selecting a target merely because it appears nearest."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.4"
  network: none
---

# Cross-Reference Ambiguity Map

Create a location-specific map from bounded excerpts, the section inventory, and every reference occurrence. Give each occurrence an identifier and preserve its source location, wording, and context. Candidate targets must be stable IDs from the supplied inventory.

Apply these decisions in order:

1. If an explicit ID or supplied identity rule uniquely selects an inventoried target, mark the occurrence `resolved` and record that cue.
2. If multiple inventoried targets satisfy the supplied heading or identity rules and none is selected, retain all candidates, set `selected_target` to null, and mark it `ambiguous`.
3. If no inventoried target fits, or an external reference lacks sufficient document identity, use no selected target and mark it `unresolved`.

Do not choose by proximity, topic similarity, or a quoted comment. Duplicate headings are not interchangeable. Never create a missing target or treat an external document as identified without supplied evidence.

Verify that every occurrence has exactly one status and all selected targets exist. Report duplicate headings, missing IDs, broken targets, absent ordering rules, and insufficient context. In `verification_report.findings`, explicitly state both scope boundaries when relevant: the map does not judge whether referenced content is true or consistent, and it does not modify or repair navigation or document text. Do not imply that either action was performed.

Return exactly one JSON object matching the [output schema](references/output-schema.json), containing `reference_map`, `ambiguity_report`, and `verification_report`. Use the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [synthetic JSON example](references/schema-example.json).

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
