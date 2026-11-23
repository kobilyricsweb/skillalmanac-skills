---
name: aggregation-grain-check
description: "Use when checking a proposed summary against supplied table keys, measure grain, joins, filters, grouping keys, and aggregation rules for duplication and non-additivity hazards. Do not use for auditing join cardinality alone, designing cohorts, executing queries, or declaring a sum safe without evidenced uniqueness, additivity, or approved deduplication."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.7"
  network: none
---

# Aggregation Grain Check

Create a grain worksheet from supplied tables, row identities, measures, joins, filters, grouping keys, deduplication rules, and aggregation order.

1. Transcribe the proposed operation sequence exactly as stated, including filters, joins, grouping, and aggregation. Preserve ambiguous predicate placement and flag it. Put remedies in alternatives rather than rewriting the proposed sequence.
2. Classify each measure's additivity as `additive`, `non_additive`, `already_aggregated`, or `unknown`.
3. Record every applicable hazard:
   - `duplication`: supplied relationship or cardinality evidence establishes that the join can repeat the measure's row identity and no approved prevention rule removes that repetition;
   - `non_additivity`: aggregation crosses a documented snapshot or other non-additive grain.
   Missing relationship cardinality or row identity creates an unresolved safety question; do not convert mere absence of evidence into an established duplication hazard.
4. Set overall measure status to `unsafe` when an established hazard applies, `safe` only when relevant uniqueness, join direction, additivity, and approved rules support the operation, and `unresolved` when material evidence is missing. A measure may have both hazards; never suppress one because the other is present.
5. Keep alternatives evidence-bounded. Aggregation-before-join, distinct-key sets, and semi-joins are supported only when supplied intent establishes entity keys and matching semantics. Otherwise label them conditional and name the required confirmation. Do not propose defining, deriving, or substituting a new business measure as a remedy: measure definition is outside this assessment and must be identified as such.
6. Reject unsupported semantic conversions explicitly. Summing balances does not create a deposit measure without a supplied rule; note the unsupported claim and state that defining a deposit-flow measure is outside the assessment.
7. Preserve conflicting notes and explain how each possibility changes safety.

Return JSON matching the [output schema](references/output-schema.json), following the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

Do not execute queries, invent row selection or deduplication, estimate overcounts, or claim observed duplication from structural risk. Verify that each measure's status agrees with all recorded hazards and supplied evidence.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
