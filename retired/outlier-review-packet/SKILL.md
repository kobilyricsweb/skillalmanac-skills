---
name: outlier-review-packet
description: "Use when supplied records have explicit unusual-value flags or thresholds and reviewers need a consistent packet for human disposition. Do not use for automatic error correction, deletion, causal attribution, duplicate matching, or declaring that an outlier is necessarily wrong."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Prepare one review item for each record flagged by an explicit supplied rule. Include the record identifier or location, observed value, rule and threshold that triggered the flag, allowed context fields, relevant neighboring or comparison values when supplied, evidence available, evidence gaps, and permitted disposition options. Preserve the observed value and distinguish a flag from a finding of error. If the rule is incomplete, contradictory, or cannot be applied to a record, mark that item unresolved rather than improvising.

Use only context fields and dispositions authorized in the input. Common dispositions may include retain, correct-with-source, or exclude-with-reason, but do not add options unless supplied. Do not explain why a value occurred, label it fraudulent, or recommend correction without evidence. Do not remove, rewrite, or silently transform records. Verify that every flagged record is included, the triggering rule is quoted or precisely restated, thresholds are applied in the stated direction, and unflagged records are not presented as flagged. Report records omitted because identifiers, rules, or context are missing. Produce a concise packet suitable for human review, with a summary of unresolved evidence and clear separation between observed facts, supplied rules, and reviewer decisions. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
