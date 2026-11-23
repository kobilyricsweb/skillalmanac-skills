---
name: contradiction-resolution-dossier
description: "Use when supplied sources make a consequential claim that conflicts and a named resolver needs a focused decision packet. Do not use for broad consistency surveys, routine terminology edits, unsupported authority judgments, or choosing a winner without supplied precedence."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Collect each conflicting statement verbatim or by precise excerpt, then describe its scope, date, source metadata, authority, and affected claim. Separate genuine contradiction from differences in audience, version, condition, or measurement. Apply only the authority and precedence rules supplied in the input. If those rules conclusively resolve the conflict, state the controlling source and show the reasoning; otherwise present the conflict as unresolved and formulate decision questions for the named resolving role. Preserve the resolver identity explicitly: record the supplied role when present, or set resolver to null and record the missing-identity gap when absent. Inventory downstream artifacts, links, workflows, or claims that depend on each version, without assuming that citation implies operational use beyond the supplied record. Distinguish facts in the sources from proposed decisions and from requested follow-up. Include an impact summary limited to supplied dependencies, a review packet for the resolver, and a post-decision update list. Verify that every stated conflict is traceable to an excerpt, every precedence conclusion cites an input rule, and no unlisted source is introduced. If source scope, dates, authority, affected artifacts, or resolver identity is missing, flag the gap and narrow the dossier. Do not silently reconcile wording, update artifacts, or declare a source false. Use [input contract](references/input-contract.md) and [worked example](references/worked-example.md) for the required packet shape.

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
