---
name: concept-contrast-table
description: "Use when supplied definitions, examples, nonexamples, and learner confusions must become a focused comparison with evidence-backed boundaries. Do not use for terminology standardization, general glossary work, unsupported distinctions, or a discriminating question the inputs cannot establish."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.6"
  network: none
---

# Concept Contrast Table

Build a learner-focused contrast from supplied definitions, examples, nonexamples, known confusions, and learner level. Extract only distinctions present in those inputs and preserve all qualifiers and conflicts.

For each concept, record defining features, supported non-features, and support status. Treat evidence according to its actual direction:

- An approved example supports only its stated concept.
- A nonexample establishes only that the case is not that concept.
- Do not classify a nonexample as the other concept unless separate supplied evidence supports that classification.
- Do not turn either concept’s definition into the converse of the other.

For every boundary case, test each concept independently. Use a concept label only when its own definition or approved evidence supports it; otherwise use a null classification and explain exactly what remains unknown. Similar wording, polished presentation, or absence of one concept’s feature does not establish the other concept.

Before drafting, check whether each concept has enough information. Preserve conflicting definitions without choosing one. If a concept lacks a definition or examples, provide only the supported portion and identify the missing distinction.

Provide `discriminating_question` only if the supplied evidence proves that its alternatives separate the concepts for the stated decision. Explicitly test both possibilities:

1. Could a case satisfy both concepts?
2. Could a case satisfy neither?

If either possibility is not ruled out by supplied evidence, set `discriminating_question` to null and record the unsupported exclusivity or exhaustiveness in `unresolved_ambiguities`. Recognition prompts may ask about each defining property separately, but must not imply an either-or result.

Return orientation, concepts with support status, boundary cases, recognition cues, the supported question or null, evidence mappings, and unresolved ambiguities. Return JSON matching the [output schema](references/output-schema.json). See the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [synthetic shape example](references/schema-example.json).

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
