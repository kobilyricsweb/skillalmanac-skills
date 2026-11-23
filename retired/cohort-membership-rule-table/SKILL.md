---
name: cohort-membership-rule-table
description: "Use when an analyst needs deterministic assignment of supplied records to one or more cohorts using inclusion, exclusion, precedence, date, and missing-value rules, including unresolved overlaps. Do not use for defining metric populations or denominators, profiling fields, estimating cohort sizes, or inferring membership from undocumented assumptions."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.3"
  network: none
---

# Cohort Membership Rule Table

Create a deterministic cohort rule table from supplied cohort definitions, fields, date boundaries, exclusions, precedence, and missing-value behavior.

1. Restate each rule operationally, including endpoint inclusivity and evaluation order.
2. Identify required fields and distinguish false from missing, unknown, or invalid.
3. Evaluate every supplied record against every cohort. Record each result as eligible, ineligible, excluded, or indeterminate, with its rule path.
4. List every eligible cohort in `candidate_cohorts`; this is eligibility evidence, not final assignment.
5. Resolve final membership according to the supplied policy:
   - If multiple membership is allowed, put every eligible candidate in `assigned_cohorts`.
   - If multiple membership is prohibited, use supplied precedence to select at most one candidate.
   - If prohibited overlap lacks precedence, set status to indeterminate and leave `assigned_cohorts` empty.
   Set `assigned_cohort` to the sole final assignment when there is exactly one; otherwise set it to null.
6. If no cohort is eligible and all relevant evaluations are determinate, classify the record as excluded. If a missing input or conflicting rule could change assignment, classify it as indeterminate.
7. Preserve conflicting field meanings, boundaries, exclusions, or precedence as unresolved; do not choose by assumption.

Return one classification row per supplied record, plus operational rules, required-input notes, per-cohort evaluations, candidate cohorts, final assignments, and unresolved conflicts. Verify that every decision cites supplied facts, missing values never become false, and excluded or indeterminate records are not presented as assigned.

Return JSON matching the [output schema](references/output-schema.json). See the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [synthetic shape example](references/schema-example.json). Do not estimate population size or act outside the supplied records.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
