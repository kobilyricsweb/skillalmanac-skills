---
name: terminology-consistency-editor
description: "Use when applying a supplied preferred glossary to editable prose with location-specific term changes. Do not use for factual reconciliation across documents or modifying quotations and code identifiers."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

# Terminology Consistency Editor

Use this skill when the user supplies content plus a preferred glossary or explicit naming policy. The task is to distinguish genuine aliases from terms that intentionally carry different meanings. Do not infer a preferred term from frequency alone when no glossary or decision rule is supplied.

Required inputs are: the passage or bounded set of passages; a glossary with preferred terms and allowed variants, if available; exclusions such as quotations or code; and any output format requested. First inventory candidate terms and their locations. Group candidates only when context shows they refer to the same concept. Compare each group with the supplied glossary. Mark a term as inconsistent only when the glossary or an explicit rule supports replacement and the local meaning matches.

Produce a preferred-terms table with concept, preferred term, observed variants, scope, and rationale grounded in the supplied glossary. Then produce a location-specific replacement list containing passage location, current wording, proposed wording, and preservation note. Keep intentionally distinct meanings separate, including near-synonyms that differ by state, role, object, or operation. Exclude verbatim quotations and code identifiers unless the user explicitly authorizes changes to them. If the glossary conflicts with itself or a passage is ambiguous, report the conflict and leave the replacement unresolved.

Return: scope and exclusions; candidate-term inventory; preferred-terms table; replacement list; unresolved distinctions; and a verification report. Verify ordinary glossary replacements as location-specific, glossary-supported, meaning-preserving and outside protected text. Verify explicitly authorized exception proposals separately: paraphrase preserves the original and is not attributed as verbatim; code rename is scoped and unexecuted. Report when no explicit glossary is supplied. Do not resolve factual disagreements across documents, rewrite style globally, or silently alter names, URLs, API fields, commands, or quoted speech.

See [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

Explicit user instructions can request broader edits, but any rewritten quotation must be labeled proposed paraphrase with the original preserved, never presented as verbatim speech. A code rename requires supplied scope and remains a proposal, not automatic refactoring. Default glossary editing still protects both.

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
