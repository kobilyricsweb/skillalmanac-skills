---
name: dependency-upgrade-impact-map
description: "Use when translating supplied old and new dependency notes plus named usage references into a bounded, offline upgrade impact map. Do not use for executing upgrades, proving breakage or safety, claiming complete repository coverage, or planning feature-flag retirement."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Build an offline impact map from supplied old-version notes, new-version notes, usage references, supported-environment constraints, and project assumptions. Extract documented removals, renames, behavior changes, environment constraints, and migration guidance only when explicitly stated. Connect each documented change to named usage sites using textual or explicitly defined semantic matches.

Use “directly exposed” when a supplied usage reference names the changed symbol or behavior, even if its location, syntax, runtime use, or reachability is incomplete; record that uncertainty separately. Use “possibly exposed” for weaker textual or contextual matches. Mark “not matched in supplied references” when no match exists; do not call it unaffected globally.

State that textual matching does not prove breakage, safety, runtime reachability, compatibility, or complete usage coverage. If release notes conflict, preserve both statements and identify the conflict. If usage references, environment constraints, or assumptions are missing, label the corresponding assessment incomplete. Do not execute code, inspect files beyond supplied references, recommend unsupported versions, or invent migration steps.

Verify by enumerating each documented change against every supplied usage reference and report coverage as limited to that list. Include [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return JSON matching [references/output-schema.json]. The synthetic example illustrates shape only and is not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
