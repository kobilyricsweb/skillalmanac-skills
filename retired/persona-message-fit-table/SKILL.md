---
name: persona-message-fit-table
description: "Use when explicitly assigned audience-profile needs must be compared with approved message options, evidence notes, exclusions, and permitted CTAs in a traceable fit table. Do not use for inventing profile-to-need assignments, sequencing content, inferring motivation, predicting conversion, or making unsupported market-behavior claims."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.8"
  network: none
---

Create a fit table from supplied profiles, approved needs, explicit profile-to-need assignments, messages, evidence, exclusions, and CTA permissions. Evaluate every candidate message for every explicitly assigned profile/need pair; never infer an assignment from order, similar IDs, profile attributes, or CTA entries.

For each assignment and candidate message, record status, grounded rationale, evidence references, disqualifier, permitted CTA, and unresolved gap.

Assign exactly one status: `matched`, `unmatched`, `blocked`, or `unresolved`. `blocked` takes precedence when an exclusion prevents message use. `unmatched` means the wording does not address the need and needs no claim evidence. `unresolved` applies when relevant wording lacks required evidence or conflicting statements prevent a decision. Preserve supporting evidence when a separate restriction blocks use.

Apply CTA exclusions before reporting permission. A CTA exclusion alone does not block the message. If no CTA is listed, use null and record “CTA not supplied.” If all listed CTAs are excluded, use null and identify the exclusions. If one CTA remains, report it on every candidate row for that assignment. If several remain, repeat each candidate row once per permitted CTA, preserving its message status and noting excluded alternatives.

An assignment is covered only when it has at least one `matched` row. CTA availability remains separate unless the supplied design explicitly makes it a condition of message use.

Aggregate `unmatched_messages` globally: include an ID only when it has no matched row anywhere and at least one unmatched row. Exclude blocked-only and unresolved-only messages. Report `uncovered_needs` by explicit profile/need assignment.

If a required input is absent, set `artifact_status` to `provisional`, list it, and return only supported rows without inventing assignments.

Use the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [output schema](references/output-schema.json). Run `python -B scripts/check_output.py artifact.json` for structure only; not source truth or classification coherence.
