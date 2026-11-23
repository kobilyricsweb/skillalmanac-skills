---
name: data-lineage-hop-map
description: "Use when supplied pipeline notes must be converted into a field-level lineage map across named stages, transformations, filters, aggregates, and undocumented origins. Do not use for tracing documentary evidence for claims, profiling observed field types, or inferring connections from matching names or plausible business meaning."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.4"
  network: none
---

Build a hop-by-hop lineage map from supplied dataset names, ordered stages, field mappings, transformation notes, aggregation rules, and filters. Represent every explicit source contribution as a directed hop, including each named input to a derived destination. Preserve stage sequence and stated transformations. Record filters at the stage where they apply and show how they affect contribution.

Separate copied, derived, aggregated, filtered-contribution, and unknown-origin mappings. Matching names, similar labels, and plausible business meaning are not evidence. If a stage identifier, order, or mapping is missing, report the broken segment rather than bridging it. If declarations differ, preserve them as competing or potentially conflicting statements. Call them a definite conflict only when the supplied input establishes the same scope and mutually incompatible derivations.

Produce the stage order, lineage hops, filters, aggregations, unknown origins, conflicts or applicability notes, and verification findings. Verify that every claimed hop has supplied support, every named transformation input is represented, filters are not omitted, and unknown origins remain visible. Do not infer data quality, ownership, business definitions, or downstream correctness. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return exactly one JSON object matching [references/output-schema.json], with no Markdown fence, introductory text, trailing explanation, comments, or second JSON value. Place every requested report and qualification inside the schema’s fields. The [synthetic example](references/schema-example.json) illustrates the required shape only and is not executed evidence.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
