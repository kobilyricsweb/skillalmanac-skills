# procedure-branch-test-matrix

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when supplied procedure conditions, actions, boundaries, and precedence rules need synthetic cases that expose covered, unknown, unreachable, and missing branches. Do not use for executing procedures, routing observed incidents, inventing defaults, or claiming runtime verification.

## Task boundary

runbook-scenario-table routes supplied observations; this designs synthetic cases to cover procedure branches.

## Try the independent synthetic example

Design a synthetic branch-test matrix for this procedure. Domain: integer x from -1 through 1. R1: if x<0, action REJECT. R2: if x=0, action HOLD. R3: if x>0, action ACCEPT. Missing x has action REQUEST_VALUE. The conditions are mutually exclusive, so no precedence is needed. Boundary values are -1, 0, and 1. Time budget is 4 minutes; each case costs 1 minute; prioritize boundaries, then missing-value behavior. Do not execute the procedure. Include condition evaluations, expected paths, supporting rules, coverage statuses, boundary notes, and budget allocation.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_b9d823e93e52`:

```text
{"cases":[{"case_id":"C1","inputs":{"x":-1},"condition_evaluation":"R1 true; R2 false; R3 false.","expected_path":"R1","expected_action":"REJECT","supporting_rule":"R1: x<0.","boundary_rationale":"Lower boundary.","coverage_status":"covered"},{"case_id":"C2","inputs":{"x":0},"condition_evaluation":"R1 false; R2 true; R3 false.","expected_path":"R2","expected_action":"HOLD","supporting_rule":"R2: x=0.","boundary_rationale":"Equality and middle boundary.","coverage_status":"covered"},{"case_id":"C3","inputs":{"x":1},"condition_evaluation":"R1 false; R2 false; R3 true.","expected_path":"R3","expected_action":"ACCEPT","supporting_rule":"R3: x>0.","boundary_rationale":"Upper boundary.","coverage_status":"covered"},{"case_id":"C4","inputs":{"x":null},"condition_evaluation":"Explicit missing-value rule applies.","expected_path":"missing-value branch","expected_action":"REQUEST_VALUE","supporting_rule":"Missing x has action REQUEST_VALUE.","boundary_rationale":"Prioritized missing behavior.","coverage_status":"covered"}],"uncovered_branches":[],"unknown_branches":[],"unreachable_branches":[],"conflicting_branches":[],"coverage_summary":"All three condition branches and the explicit missing-value branch are covered by synthetic cases.","unresolved_rules":[],"boundary_notes":["-1, 0, and 1 exercise all supplied boundaries."],"budget":{"supplied_minutes":4,"allocated_minutes":4,"status":"within_budget"}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
