---
name: product-update-announcement-frame
description: "Use when framing one documented product change with confirmed availability, audience impact, limitations, required action, permitted CTA, and evidence references. Do not use for refreshing existing pages, inventing benefits, authorizing deployment, notifying users, or planning broader campaigns."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Use the approved change notes, affected audiences, release status, limitations, required action, permitted CTA, and evidence references to frame one product-update announcement. Preserve the exact release status and audience scope. Use the supplied permitted CTA exactly; if none is supplied, set CTA to null and list it as unresolved. Do not call a feature available, improved, easier, faster, beneficial, or generally released unless the supplied notes support that wording. If inputs conflict, show the conflict and keep the announcement conservative. Distinguish announcement framing from product authorization, deployment, documentation changes, or user notification. Do not infer rollout completion, compatibility, performance, adoption, or customer outcomes.

See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
