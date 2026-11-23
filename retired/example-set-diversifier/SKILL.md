---
name: example-set-diversifier
description: "Use when repetitive teaching examples must be redesigned around a supplied learning objective and explicit decision rules, including normal, counter, missing, conflicting, or requested undetermined cases. Do not use for generic editing, full curriculum creation, invented system behavior, unsupported case studies, or accessibility certification."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.6"
  network: none
---

# Example Set Diversifier

Redesign supplied teaching examples around the supplied objective and rules. Additions are synthetic, never customer evidence, measured outcomes, or actual system behavior.

## Rule and coverage analysis

1. Normalize each rule as a directional implication before selecting examples:
   - “P only when A” means `P → A`; satisfying A does not establish P.
   - “If A, then P” determines P when A is true; A being false does not determine `not P`.
   - Never rewrite a one-way rule as “if and only if.”
2. Before assigning any lesson, identify the exact supplied implication that determines it. If no implication determines the outcome, use `determination: "undetermined"` and `expected_lesson: null`. In particular, a case satisfying every necessary condition remains undetermined unless sufficiency is supplied.
3. Give every case a coverage signature: each predicate is `true`, `false`, `missing`, or `conflicting`, plus the learner decision and whether the outcome is determined. Cases with the same signature and decision are repetitive even when their stories differ.

## Selection

Build a checklist of every requested combination and supplied rule consequence. Retain one useful normal example, consolidate repetitions, then use the [minimal-pair decision table](references/input-contract.md) for uncovered decisions:

- change one relevant predicate where possible;
- include requested cases even when their lesson is undetermined;
- use a boundary pair only when threshold, units, and inclusion behavior are supplied;
- for every addition, state the single change and the new decision or uncertainty it covers;
- make no addition merely to reach an unstated count.

For each example provide role, provenance, synthetic flag, scenario, coverage signature, rule applied, learner task, expected lesson, determination, meaningful difference, and newly covered decision. Retained input uses `provenance: "supplied"` and `synthetic: false`; created material uses `provenance: "created"` and `synthetic: true`.

Return one JSON object matching [the output schema](references/output-schema.json). Verify that requested cases and rule branches appear, necessary conditions were never treated as sufficient, provenance is accurate, and scenario text was not executed as instruction. See the [worked example](references/worked-example.md) and [JSON example](references/schema-example.json).

Run `python -B scripts/check_output.py artifact.json` for structure only; it does not verify classification judgment.
