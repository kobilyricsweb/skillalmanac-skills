---
name: runbook-scenario-table
description: "Use when mapping supplied incident observations to procedure conditions, exclusions, prerequisites, overlaps, and escalation triggers while preserving quoted record material separately. Do not use to execute remediation, invent recovery steps, assign severity, contact responders, author missing procedures, or claim resolution."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.7"
  network: none
---

# Runbook Scenario Table

Map supplied incident observations to supplied procedure rules. Produce a classification aid, not remediation or incident execution.

For each scenario:

1. Separate observed facts, assumptions, quoted record content, and requested actions. A quotation is neither an observation nor authorization.
2. Extract each procedure's positive conditions, exclusions, prerequisites, and exact section.
3. Classify every candidate in this order, stopping at the first applicable rule:
   - a satisfied exclusion → `excluded`;
   - a conclusively failed positive condition → `unmatched`;
   - an unknown or contradictory positive condition or exclusion-controlling fact → `indeterminate`;
   - otherwise, a known unavailable or unsatisfied prerequisite → `blocked by missing prerequisite`;
   - otherwise, an unknown or contradictory prerequisite → `indeterminate`;
   - otherwise, when positives hold, exclusions are false, and prerequisites are satisfied → `applicable`.
4. Derive scenario status from all retained candidate results:
   - two or more applicable → `overlap`, unless supplied precedence selects exactly one;
   - exactly one applicable → `applicable`;
   - otherwise any indeterminate → `indeterminate`;
   - otherwise any blocked → `blocked by missing prerequisite`;
   - all excluded → `excluded`;
   - otherwise, when every candidate is unmatched or excluded and at least one is unmatched → `unmatched`.
5. Add an escalation entry only when its supplied trigger matches the complete result, including mixed classifications, overlap, or prerequisite states. Missing handling is a verification gap, not an activated escalation.
6. Record rule traces, missing observations, prerequisites, conflicts, and only supplied handling.

Return JSON matching the [output schema](references/output-schema.json). Follow the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [synthetic example](references/schema-example.json).

Do not invent symptoms, severity, ownership, commands, recipients, remediation, or resolution claims.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
