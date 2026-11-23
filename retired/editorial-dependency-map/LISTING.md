# editorial-dependency-map

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when a multi-part publication must be mapped against supplied evidence, assets, approvals, section dependencies, and explicit fallback permissions. Do not use for a whole-project handoff audit, generic project planning, or treating missing dependencies as optional without an input-authorized fallback.

## Task boundary

Nearest is handover-readiness-check; this maps dependencies within a publication rather than auditing an overall handoff.

## Try the independent synthetic example

Map publication dependencies; do not draft or publish content. Sections: Overview, Results, Methods. Requirements: Overview needs approved summary S1; Results needs dataset D1 and chart C1; Methods needs protocol P1. Inventory: S1 approved, D1 available, C1 pending, P1 available. Explicit dependencies: Overview independent; Results requires Methods; Methods has no section dependency. Approval rule: a section may proceed only when all its required items are available or approved. Owners: Overview—Nia; Results—Omar; Methods—Lei. No fallbacks are authorized. Treat Methods as an unresolved prerequisite for Results until its completion is explicitly supplied.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_220a7005cf85`:

```text
{"sections":[{"section":"Overview","prerequisites":[{"item":"S1","type":"evidence","status":"approved"}],"status":"can_proceed","blocking_status":"Not blocked by supplied prerequisite; downstream completion is not supplied.","fallback_scope":null,"owner_status":"Nia"},{"section":"Results","prerequisites":[{"item":"D1","type":"evidence","status":"available"},{"item":"C1","type":"asset","status":"pending"},{"item":"Methods","type":"section","status":"unknown"}],"status":"blocked","blocking_status":"Blocked by pending C1 and unresolved completion of Methods.","fallback_scope":null,"owner_status":"Omar"},{"section":"Methods","prerequisites":[{"item":"P1","type":"evidence","status":"available"}],"status":"can_proceed","blocking_status":"Not blocked by supplied prerequisite; completion is not explicitly supplied.","fallback_scope":null,"owner_status":"Lei"}],"blocking_paths":["C1 pending -> Results blocked","Methods completion unresolved -> Results blocked"],"gaps":["Methods completion is not explicitly supplied.","Results cannot proceed until Methods completion is supplied and C1 is available or approved."],"cycle_or_conflict_notes":[],"outside_scope":["Drafting content","Assigning owners","Granting approval","Publishing"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
