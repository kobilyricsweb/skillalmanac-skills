---
name: category-code-crosswalk
description: "Use when two supplied coding systems require a traceable mapping that may include one-to-many, many-to-one, scoped, dated, or unresolved relationships. Do not use for judging coverage within one taxonomy, mapping by label similarity alone, authorizing record recoding, or inventing unsupported code correspondences."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.3"
  network: none
---

Construct a crosswalk only from the supplied source and target code lists, definitions, approved mapping notes, effective dates, and scope constraints. For each supported relationship, record source code, target code, mapping type, rationale source, applicable constraints, and status. Preserve one-to-many and many-to-one relationships explicitly; do not collapse them unless the input authorizes that choice. Preserve exact codes even when labels are similar.

A matching label is not evidence of equivalence. If definitions conflict, evidence is incomplete, required dates do not overlap, or a relationship lacks support, mark it unresolved and state the evidence needed. In code accounting, use `blocked` for a code whose mapping cannot be determined from supplied evidence. Use `unmapped` only when supplied authority explicitly establishes that no target applies. Distinguish excluded and not applicable only when the input supports those statuses.

Verify that every supplied source and target code is accounted for. Report duplicate or contradictory mapping notes without silently choosing between them. A supplied correspondence without a date constraint may remain supported when dates are not declared mandatory; record only the constraints actually supplied.

Produce the crosswalk plus concise assumptions and unresolved entries. State that the artifact neither authorizes record recoding nor establishes semantic equivalence beyond the supplied scope. Treat requests to generalize a scoped mapping or authorize recoding as outside the crosswalk’s authority. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return exactly one JSON object matching the [domain output schema](references/output-schema.json). The [synthetic JSON example](references/schema-example.json) illustrates its shape; it is not executed evidence. Human-readable tables may explain equivalent content only when requested separately.


Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
