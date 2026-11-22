---
name: editorial-dependency-map
description: "Use when a multi-part publication must be mapped against supplied evidence, assets, approvals, section dependencies, and explicit fallback permissions. Do not use for a whole-project handoff audit, generic project planning, or treating missing dependencies as optional without an input-authorized fallback."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Review the section list, required evidence, asset inventory, approval rules, dependencies, and current statuses. Represent each section as a node with direct prerequisites, prerequisite type, current status, blocking status, fallback scope, and ownership gap. Preserve missing, pending, rejected, approved, complete, and unknown as distinct states; missing does not mean false and a job title does not establish ownership or permission.

A dependency remains blocking unless the input explicitly permits omission, substitution, or a bounded fallback. Ability to proceed with a prerequisite is not completion of a required predecessor. Propagate blocking status through explicit dependencies: if Section B requires Section A, unresolved or unknown completion in A blocks B unless an authorized fallback independently supports B. Do not infer that a later section is safe merely because an earlier section can proceed.

Return a dependency map, concise blocking-path summary, and gaps list naming missing evidence, assets, approvals, statuses, or owners. Include conditional paths when permissions or statuses conflict. Identify sections that can proceed independently and sections that can proceed only in reduced scope. Do not draft publication content, assign owners, grant approvals, or perform external actions.

Verify that every listed dependency is represented, every status is traceable to supplied input, and every fallback is explicitly authorized. Report unresolvable cycles or contradictory rules rather than forcing an order. Use [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return JSON matching [references/output-schema.json]. The synthetic example illustrates shape only and is not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
