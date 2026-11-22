---
name: rubric-anchor-builder
description: "Use when a supplied rubric needs synthetic response anchors that make boundaries between performance levels observable. Do not use for diversifying instructional examples, inventing criteria, or scoring work without descriptor-based evidence."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.3"
  network: none
---

Build short synthetic anchor responses for the supplied prompt and rubric. Start by extracting each criterion, its level descriptors, scoring rules, and non-scorable conditions. Create anchors that differ in the observable feature marking the requested boundary, such as the presence, relevance, or number of required elements. Score every criterion separately and explain each score by quoting or closely paraphrasing only the supplied descriptor; do not add an unstated quality standard.

When a boundary is ambiguous, create a paired anchor that changes one observable feature at a time and label the ambiguity. Do not imply that an anchor represents a real learner, typical performance, or an official exemplar. Keep content synthetic and within the supplied prompt. If the rubric lacks enough detail to justify a score, mark the criterion indeterminate and identify the missing descriptor or rule rather than guessing. Apply non-scorable conditions exactly as provided and distinguish them from low performance.

Return the anchors, criterion-by-criterion scoring, descriptor-linked rationale, boundary feature, non-scorable treatment, and unresolved ambiguity. Report conflicts between scoring rules and descriptors. Respect requested length and number of anchors; if none is specified, produce the minimum set needed to illustrate the stated boundary. Include [input contract](references/input-contract.md) and [worked example](references/worked-example.md) as available companion references.

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit 0 means structural validity, 1 contract violations, and 2 invalid input or unsupported contract. The bounded checker reads at most 2 MiB, 50,000 nodes, and depth 100; it rejects duplicate keys, nonfinite numbers, and oversized numbers but does not check facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
