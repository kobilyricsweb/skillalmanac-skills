---
name: call-to-action-consistency-map
description: "Use when auditing supplied assets for CTA fit against audience stage, approved wording, asset message, and a factual destination description. Do not use for message-reuse mapping, asset redesign, conversion prediction, implementation, or inferring destination capability from a title, URL, or asset name."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.3"
  network: none
---

Review the supplied asset copy, audience-stage rules, approved CTAs, destination descriptions, and prohibited transitions. Create one row per asset with its exact current CTA, audience state, implied CTA promise, supplied destination description, stage result, destination result, mismatch explanation, and any proposed approved CTA.

Make three distinct comparisons:

1. Compare the current CTA with the stage rule, prohibited transitions, and approved wording scope.
2. Compare the factual destination description with the promise implied by the current CTA. Base `destination_result` only on this comparison. A checkout requesting payment details can fit “Buy now” even when that CTA is prohibited for the audience stage.
3. Separately compare the asset’s surrounding message with the current CTA and destination. Record any conflict in the mismatch explanation; do not convert that conflict into a destination mismatch when the destination fulfills the current CTA’s promise.

Do not infer destination capability from its title, URL, or asset name. If its description is missing, mark destination fit unresolved. Preserve exact CTA text and distinguish a proposed replacement from an approved or implemented change. A replacement CTA must also have a destination that fulfills its promise; otherwise state that dependency.

If inputs conflict or are incomplete, preserve separate decisions and list missing fields. Include a concise progression summary showing where the supplied path breaks. Do not assess conversion, copy quality, accessibility, legal compliance, or implementation, and do not change links or publish assets.

Return JSON matching the [output schema](references/output-schema.json), using the [input contract](references/input-contract.md) and [worked example](references/worked-example.md). The [synthetic example](references/schema-example.json) illustrates structure only.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
