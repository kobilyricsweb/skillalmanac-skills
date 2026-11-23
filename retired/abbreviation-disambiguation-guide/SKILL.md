---
name: abbreviation-disambiguation-guide
description: "Use when repeated abbreviations have multiple approved expansions in supplied contexts and reviewers need occurrence-level possibilities with evidence. Do not use for terminology normalization, preferred-term replacement, or authorizing an expansion absent from the approved glossary."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.2"
  network: none
---

Collect each abbreviation occurrence, its excerpt, document or section context, and the approved expansion glossary. For every occurrence, list only glossary expansions that remain possible. Use supplied rules or direct context to narrow the set; treat merely associated clues as weak evidence, not proof. Mark an occurrence unresolved when the excerpt does not distinguish allowed expansions. If required context is missing, use an input-gap status and request it. If no glossary expansion fits, report an input gap rather than inventing a meaning. Do not replace wording, select a preferred term, or treat capitalization alone as conclusive unless the supplied glossary or context rule says so. Organize results by occurrence identifier, excerpt, possible expansions, local evidence, status, and questions. Verify that every occurrence is covered, every proposed expansion appears in the glossary, and no clue is treated as proof of a converse. The result is a disambiguation aid, not an editorial change. Use [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

A contextual association such as power, invoice, alerts, or message retention may be recorded as weak local evidence, but it does not remove an approved possibility or resolve an occurrence unless a supplied rule makes it dispositive.

Return only the requested guide; do not edit source wording or establish a preferred term.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
