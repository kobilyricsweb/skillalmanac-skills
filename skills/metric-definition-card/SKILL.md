---
name: metric-definition-card
description: "Use when turning supplied product or operational metric notes into a definition card that exposes population, window, denominator, exclusion, freshness, and zero-policy gaps. Do not use for calculating metric results, auditing weighted-rate implementations, forecasting outcomes, or making causal, financial, or operational recommendations."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

# Metric Definition Card

Create a definition card from supplied metric notes, formulas, schema references, and constraints.

1. Preserve the supplied formula, then identify its components without calculating a result.
2. Record metric class, numerator, denominator, eligible population, event grain, window boundaries, timezone, exclusions, freshness, and missing/zero-denominator policy.
3. For every field, distinguish among:
   - supplied value;
   - explicitly supplied as none;
   - unresolved because it was not supplied or is ambiguous.
   Never use an empty array or blank value alone to represent an unresolved field. In particular, when exclusions are absent, keep `exclusions` empty and add an explicit unresolved choice and implementation question stating that the exclusion policy was not supplied.
4. Preserve distinctions among event, processing, reporting, and calendar dates. Quote ambiguous terms such as “activated,” “current,” “successful,” or “customer” and ask what they mean.
5. Keep conflicting notes visible with provenance. Without a precedence rule, do not select either position; record the conflict as unresolved.

Return JSON matching the [domain output schema](references/output-schema.json), including metric name and supplied purpose, formula, class, components, population, window, timezone, exclusions, grain, freshness, zero policy, source notes, unresolved choices, and implementation questions. The [synthetic example](references/schema-example.json) illustrates shape only.

Do not infer eligibility, boundaries, exclusions, or denominator behavior; treat sample values as context only. Do not convert correlation into causation or recommend action.

Before reporting, confirm that every formula component is represented; every required definition field is either supported or explicitly unresolved; unknown exclusions are not mistaken for confirmed no exclusions; conflicts remain visible; and no result was calculated. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

The bundled offline checker may be used to assess JSON structure only; it does not verify facts or judgment.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
