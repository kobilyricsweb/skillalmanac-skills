---
name: lesson-activity-alignment-map
description: "Use when a lesson plan must show which supplied activities produce observable evidence for each stated learning objective and assessment criterion. Do not use for prerequisite mapping, inventing new activities or assessments, or treating topic exposure and attendance as demonstrated alignment."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.6"
  network: none
---

Map each supplied objective to the activities, learner performances, products, time limits, and assessment criteria.

For each connection, identify the observable learner action and evidence, then classify it:

- `direct_evidence`: the supplied performance or product demonstrates the full objective under the supplied criterion.
- `partial_evidence`: observable supplied evidence demonstrates a proper subset of the objective or criterion.
- `exposure_only`: the activity addresses the topic, but no observable learner performance or assessable product demonstrates a criterion-relevant part.
- `uncovered`: no supplied activity provides criterion-relevant evidence for the objective.

Topic similarity and attendance are insufficient. A durable product is unnecessary when a supplied live or oral performance can be assessed. Preserve supplied descriptions; do not invent actions, evidence, or criteria.

For each connection, list every applicable uncertainty reason: `missing_product`, `missing_criterion`, `missing_time`, or `conflicting_inputs`. Use an empty array when none applies. `missing_product` applies only when a product is needed to evidence the stated learner action; it does not apply when the activity supplies no observable learner performance at all.

Account for lesson time by unique supplied activity or explicitly distinct activity instance, not by connection row. When one activity connects to several objectives, count its duration once. Treat repeated references with the same supplied activity identifier as one instance; if identifiers are absent, deduplicate only descriptions that clearly denote the same instance and flag ambiguous identity as conflicting input. Omit unknown durations, add `missing_time` to affected connections, and report `known_mapped_minutes` as the sum of unique known-duration instances. Use `unresolved` when missing or conflicting time data prevents a complete feasibility judgment.

Return JSON matching the [domain output schema](references/output-schema.json), using the [input contract](references/input-contract.md) and [worked example](references/worked-example.md). The [synthetic shape example](references/schema-example.json) is illustrative, not executed evidence. Keep requested proposals separate from analysis.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
