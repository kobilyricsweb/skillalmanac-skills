---
name: capacity-slot-allocation-table
description: "Use when allocating supplied tasks into finite resource slots while preserving durations, eligibility, priorities, blackouts, fixed assignments, and non-overlap constraints. Do not use for staffing forecasts, external booking, optimization or maximality claims, or proposals dependent on capacity absent from the supplied input."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.7"
  network: none
---

# Capacity Slot Allocation Table

Create a provisional task-to-slot allocation from supplied durations, eligible resources, slots, and priority rules. Normalize identifiers and record conflicting eligibility, duration, priority, blackout, fixed-assignment, or slot definitions. Preserve every duration; do not split, compress, bridge separate slots, or overlap work unless explicitly permitted.

Apply priority only where a choice exists. A missing rule blocks an assignment only when competing feasible choices could change the result. If a task has one eligible fitting placement and no competitor or alternative placement, allocate it without inventing priority.

Assign a task only within one supplied eligible slot containing its full interval. For each assignment, show task, resource, slot, start/end or duration, and supporting rule. List each unallocated task with its direct capacity or eligibility constraint. Use `unresolved` only when missing or conflicting input materially prevents a decision.

Report:

- `feasible` when every task is conclusively allocated and none is unallocated or unresolved;
- `partially_feasible` when at least one task is allocated and at least one is conclusively unallocated, with no material unresolved input controlling overall feasibility;
- `infeasible` when every task is conclusively unallocated and none is allocated or unresolved;
- `undetermined` when material unresolved input prevents the overall feasibility assessment.

Independent conflict-free assignments may be recorded as assigned or provisional while overall feasibility is undetermined. Do not claim a partial allocation is optimal, maximal, or largest.

Return JSON matching the [output schema](references/output-schema.json), following the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [synthetic example](references/schema-example.json).

Verify slot containment, eligibility, unchanged duration, non-overlap, conflict treatment, and reconciliation of every task across assigned, unallocated, and unresolved lists. Distinguish supplied facts from provisional choices.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
