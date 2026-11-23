---
name: caption-context-pack
description: "Use when an existing chart or image needs bounded explanatory text covering visible labels, supplied context, reading guidance, limitations, and a source-note placeholder. Do not use for dashboard design, causal interpretation, identity inference, trend claims beyond the artifact, or captions based on information not supplied or visible."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Review the artifact description, visible labels, intended takeaway, supplied limitations, and internal source identifier. Create a caption pack with five parts: a short caption, extended context, key or reading guide, limitation statement, and source-note placeholder. Describe what the artifact visibly presents and connect it to the supplied context without adding facts.

State exact values, categories, dates, units, and comparisons only when supplied or visibly legible in the input. If the intended takeaway conflicts with the displayed artifact, identify the conflict and use conditional wording. Explain how to read the visual, such as comparing bar heights or following a labeled axis, but do not imply a method or measurement that is not supplied.

Never infer causes, identities, intentions, significance, quality, or future direction. A visible difference can be described as a displayed difference, not as a causal or substantive explanation. If labels, timeframe, units, limitations, or source identifier are missing, mark them as unavailable and use a placeholder where appropriate. Do not claim that an image is representative, complete, verified, or statistically meaningful.

Return the five labeled components plus an uncertainty note listing any unsupported requested claims. Keep wording concise and suitable for publication beside the existing visual. The source-note placeholder must preserve the supplied internal identifier without inventing a public citation.

Use [input contract](references/input-contract.md) and [worked example](references/worked-example.md) as the governing output references.

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
