---
name: role-coverage-gap-map
description: "Use when a supplied process schedule must be checked for role coverage across required windows, assignments, backups, overlaps, and uncovered intervals. Do not use for mapping approval authority, inferring availability, substituting similar job titles, or deciding who should be authorized."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.6"
  network: none
---

Create a coverage map from supplied responsibilities, required windows, assignments, backup rules, permissions, and availability intervals. Split each required window at every assignment, availability, or rule boundary.

For each segment, copy only facts that apply to that exact interval. A role assigned for one interval must not remain the `assigned_role` after that assignment ends; use null when no assignment applies. Likewise, do not extend availability, backup status, or permission beyond supplied boundaries. Coverage exists only where an applicable assignment, explicit permission, and supplied availability coincide.

Report fully covered segments, overlaps, uncovered intervals, missing or unverified backups, conflicting assignments, and unsupported assumptions. A named backup without applicable availability or permission is unverified, not covered. Similar titles, seniority, proximity, and prior practice do not establish substitution.

Use `uncovered` when the supplied record affirmatively leaves a segment without any qualifying provider. Use `unresolved` only when a supplied conflict or ambiguity prevents deciding coverage. Missing required assignment, availability, or permission is a coverage gap, not uncertainty about facts that were never supplied. Preserve conflicting rules and identify the affected segment without choosing a winner.

Show exact boundaries and the supplied time zone, or state that it is unspecified. Produce the interval map, gap/conflict register, and decisions requiring authorized review. Do not assign people, alter schedules, promote a role, or grant authority. Verify that the required windows are fully partitioned and that every claimed covered segment has interval-specific support.

See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return JSON matching the [domain output schema](references/output-schema.json); the [synthetic JSON example](references/schema-example.json) illustrates shape only.

Run `python scripts/check_output.py artifact.json` from the package directory for offline structural checking. Structural validity does not establish factual accuracy or task judgment.
