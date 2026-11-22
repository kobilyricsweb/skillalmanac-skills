---
name: brand-tone-constraint-card
description: "Use when approved brand samples, explicit voice preferences, and prohibited tone patterns must become a concise tone constraint card for new copy. Do not use for glossary normalization, factual claim validation, performance promises, or inferred brand positioning."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Create a tone constraint card from the supplied approved samples, explicit voice preferences, and prohibited tone patterns. Separate observations from samples from rules explicitly approved by the owner. Record positive anchors, negative anchors, context limits, and wording tests that a writer can apply to new copy. Quote or paraphrase only the supplied samples; do not treat a sample as a universal rule unless the input says so. Do not infer factual promises, product benefits, audience motivations, positioning, or legal meaning from tone.

For each rule, state its source: sample observation, explicit preference, or prohibition. Mark rules that apply only in a named context. Include counterexamples only when they follow from an explicit ban or a clearly stated contrast. If samples and preferences conflict, preserve both and flag the conflict for owner resolution. If no preference or prohibition supports a proposed rule, label it as an unresolved observation rather than a constraint. Verify that every constraint has a source, every test checks wording rather than truth, and no factual claim has been approved by tone alone. Report open questions and context limits.

Use the [input contract](references/input-contract.md) and [worked example](references/worked-example.md) for field and output expectations.

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
