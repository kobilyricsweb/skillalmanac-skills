# Input Contract

Provide:

- `before`: a redacted key-value snapshot whose values are JSON scalars: string, number, boolean, or null.
- `after`: a redacted key-value snapshot whose values are JSON scalars: string, number, boolean, or null.
- `behavior_notes`: supplied descriptions of what selected keys control.
- `deployment_notes`: supplied rollout, rollback, restart, or other deployment-impact information.
- `group_labels`: optional categories for organizing changes.
- `alignment_notes`: optional supplied statements that two differently named keys may correspond.

Arrays and objects are not valid snapshot values. If either snapshot contains one, identify the input-contract error rather than flattening, stringifying, or partially comparing it.

Decision rules:

- Report additions, removals, changes, and redactions as observations.
- For each change, use `before_present` and `after_present` to distinguish absence from a supplied JSON null value. The value field on an absent side is null only as a schema placeholder and does not mean the key was present with null.
- Retain an observed removal and addition when a possible rename is unconfirmed. Record the possible correspondence separately in `alignments`, using the exact removed and added key names.
- Preserve supplied behavior claims in `behavior`. Set `behavior_status` to `documented` when the claims are consistent, `unknown` when none is supplied, or `conflicting` when claims disagree; do not resolve a conflict by selecting one claim.
- Classify `deployment_impact` as `not-supplied` when no relevant deployment note exists; `possible-but-unknown` when a supplied note identifies a possible impact without establishing it; `documented` when consistent explicit notes establish the impact; or `conflicting` when explicit impact claims are incompatible.
- Classify reversibility as `documented`, `unknown`, or `conflicting` from supplied rollback information.
- Preserve secret placeholders and never reconstruct values.

Boundary: do not inspect files, environments, services, repositories, dashboards, or secrets; infer causality; validate required keys; or perform migration or release actions.
