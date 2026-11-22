# capacity-slot-allocation-table

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when allocating supplied tasks into finite resource slots while preserving durations, eligibility, priorities, blackouts, fixed assignments, and non-overlap constraints. Do not use for staffing forecasts, external booking, optimization or maximality claims, or proposals dependent on capacity absent from the supplied input.

## Task boundary

schedule-conflict-check detects conflicts in an existing calendar and critical-path-planner computes dependency timing; this places supplied tasks into supplied finite slots and lists unmet constraints, without editing calendars or computing a critical path.

## Try the independent synthetic example

Create a provisional allocation. Tasks: T1 duration 2 hours, eligible R1; T2 duration 1 hour, eligible R1. Resource: R1. Slots on 2026-11-24: R1 09:00–11:00 and R1 11:00–12:00. Priority: lower priority number first; T2 priority 1, T1 priority 2. Placement rule: among placements for the current priority task, choose one that preserves a feasible placement for the greatest number of remaining tasks; if still tied, use the latest fitting slot. Tasks may not be split. Simultaneous work on one resource is prohibited. No fixed assignments or blackouts. Use supplied local times. Report assumptions or conflicts, allocations, unallocated tasks, unused slots, feasibility, and verification notes.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_exec_medium_de6ad1db77e6`:

```text
{"assumptions":[],"input_conflicts":[],"allocations":[{"task":"T2","resource":"R1","start":"2026-11-24 11:00","end":"2026-11-24 12:00","duration_hours":1,"supporting_rule":"Priority 1 is placed first; the latest fitting placement also preserves a feasible contiguous two-hour slot for T1.","status":"assigned"},{"task":"T1","resource":"R1","start":"2026-11-24 09:00","end":"2026-11-24 11:00","duration_hours":2,"supporting_rule":"Priority 2; fits its eligible remaining slot without splitting.","status":"assigned"}],"unallocated_tasks":[],"unresolved_tasks":[],"unused_slots":[],"feasibility_status":"feasible","verification_notes":["Both durations are unchanged and each interval is contained in one supplied slot.","R1 assignments do not overlap.","Eligibility and priority rules are satisfied.","All tasks and slot time are reconciled."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
