---
name: approval-path-mapper
description: "Use when mapping supplied roles, authority rules, states, evidence, branches, cycles, and reachability into an approval path. Do not use to grant authority, choose missing decision rights, approve an artifact, schedule reviews, or produce generic meeting actions."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

# Approval Path Mapper

Use this skill when a team supplies roles, authority rules, artifact states, conditions, evidence, escalation rules, and ordering constraints but lacks a dependable review sequence. The result is a proposed map, not an approval decision or grant of authority.

Normalize each rule into actor, action, prerequisite, decision right, evidence, and next state. Identify the entry state and first permitted reviewer; if unsupported, mark the path unresolved. Order only explicit prerequisites, keep branches separate, record handoff evidence, and add escalations only when their trigger, recipient, or time boundary is supplied.

Traverse every branch to a terminal outcome. Flag loops, unreachable states or roles, missing transitions, contradictory rights, undeclared actors, and branches without an owner. A branch that explicitly requires an actor absent from the supplied role list may be shown as conditional, but the actor remains undeclared and gains no inferred authority.

Return JSON matching the output schema: scope, assumptions, ordered path, branch table, handoffs, escalations, unresolved ambiguities, reachability findings, cycle findings, and verification support. Do not invent approvers, evidence, deadlines, outcomes, or authority. If rules conflict, preserve both interpretations and identify the decision needed. If a cycle is detected, stop that branch at the repeated state. Do not approve, schedule, contact, or execute workflow actions.

Return JSON matching the [domain output contract](references/output-schema.json); the [synthetic shape example](references/schema-example.json) is an illustration, not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.

Resources: [input contract](references/input-contract.md), [worked example](references/worked-example.md).
