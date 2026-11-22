---
name: section-heading-coverage-check
description: "Use when auditing whether each heading’s promise and each required topic are supported by directly assigned document content, while tracking descendant coverage separately. Do not use for drafting missing evidence, planning updates, requirements traceability, or constructing an outline from source notes."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.8"
  network: none
---

# Section Heading Coverage Check

Review the complete supplied document in heading order. Treat each heading as an audit unit and preserve the hierarchy. Assign every row an artifact-local `row_locator` based on source order. Use `null` for an unknown section ID or hierarchy level, never a fabricated value, and record each missing value in `input_limitations`.

Split each heading’s promise into distinct elements. Match support to meaning, not related words or plausible implications. An evaluative promise such as a benefit, risk, advantage, or limitation is supported only when the content establishes that role; “lightweight” alone does not establish a benefit.

Assess each element as `covered`, `partial`, `absent`, `contradicted`, or `unresolved`, citing direct support and missing or conflicting evidence. Derive the aggregate deterministically: all covered is covered; all absent is absent; any unresolved makes it unresolved; otherwise any contradicted makes it contradicted; otherwise any partial, or a covered/absent mixture, makes it partial.

Do not count descendant content as direct parent support. Record relevant descendants by `row_locator` and supplied section ID. Do not infer support from headings, neighboring sections, common knowledge, intended topics, or quoted editing instructions.

Audit required topics independently from heading promises. For each topic, record support status, supporting rows and supplied IDs, direct evidence, and whether it appears beneath a heading that promises it. If completeness or relevant content is uncertain, use `unresolved`; use `absent` only when the complete relevant material supplies no support.

Return JSON matching `references/output-schema.json`: one row per heading plus required-topic assessments, input limitations, and unresolved ambiguities. Include protection, promise elements, direct support, aggregate status, gaps, overbreadth, descendant notes, and bounded repairs. Preserve protected headings verbatim. Repairs may narrow or split an unprotected heading, reposition supplied material, or propose content once support is supplied; never invent content. Record a requested action outside the audit—such as altering protected text or inventing evidence—only as a non-executed proposal in the affected row’s `repair_options`, stating its authority or evidence dependency. Never add an uncontracted top-level field.

See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md). The [synthetic JSON example](references/schema-example.json) illustrates shape only.

Run `python scripts/check_output.py artifact.json` from the package directory for offline structural checking. Structural validity does not establish factual or editorial quality.
