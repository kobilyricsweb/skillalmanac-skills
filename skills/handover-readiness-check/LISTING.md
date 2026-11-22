# handover-readiness-check

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when a supplied handoff must be assessed criterion by criterion for evidence, reproducibility information, ownership, blockers, and continuation readiness. Do not use for deployments, credential handling, independent system audits, or claims that another engineer reproduced work when only instructions were supplied.

## Task boundary

session-handoff-notes writes continuation notes for an agent, and plan-stress-test examines a proposed execution plan; this audits a supplied handoff against readiness criteria and evidence, distinguishing reproduction instructions from a reported reproduction attempt.

## Try the independent synthetic example

Assess this handoff without running anything. Objective: hand over calculator v1. Acceptance criteria: C1, adding 1 and 2 displays 3 in test environment T; C2, another engineer can reproduce the check. Supplied log L1 visibly contains “environment=T; version=v1; input=1+2; output=3.” Procedure P1 says “Open v1 in T, enter 1+2, observe 3.” Owner: Jo. No blocker is reported. Next action: Jo transfers P1 and L1 to Sam.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_5f1a79ddac7b5ba8`:

```text
{"objective":"Hand over calculator v1.","criteria":[{"criterion_id":"C1","text":"Adding 1 and 2 displays 3 in test environment T.","status":"ready","reported_result":"Supplied log L1 shows the required environment, version, input, and output.","directly_read_evidence":["L1 visibly contains: environment=T; version=v1; input=1+2; output=3."],"gap":null,"source":"L1"},{"criterion_id":"C2","text":"Another engineer can reproduce the check.","status":"unassessable","reported_result":"No reproduction attempt or outcome by another engineer is supplied.","directly_read_evidence":["P1 supplies reproduction steps, but does not record another engineer performing them."],"gap":"A supplied attempt and outcome from another engineer are required to assess this criterion.","source":"P1 and handoff note"}],"reproducibility":{"inputs":["1+2","Procedure P1","Log L1"],"environment":"test environment T, calculator version v1","steps":["Open v1 in T.","Enter 1+2.","Observe the displayed result."],"expected_result":"3","actual_result":"L1 records output=3; no separate reproduction attempt by another engineer is supplied.","gaps":["No other-engineer attempt, identity, date, or outcome is supplied."],"source":"P1 and L1"},"evidence":[{"evidence_id":"EV1","level":"directly_read_artifact","examined_material":"The supplied text of L1 containing environment T, version v1, input 1+2, and output 3.","source":"L1","environment":"test environment T, version v1","inspector_date":"not supplied","staleness":"unknown"},{"evidence_id":"EV2","level":"directly_read_artifact","examined_material":"The supplied procedure P1 describing how to open v1 in T, enter 1+2, and observe 3.","source":"P1","environment":"test environment T, version v1","inspector_date":"not supplied","staleness":"unknown"}],"ownership":"Jo","blockers":[],"reported_next_action":"Jo transfers P1 and L1 to Sam.","recommended_next_action":{"action":"Have Sam perform P1 and record the attempt and observed outcome with environment, version, and date.","rationale":"This would provide evidence needed to assess whether another engineer can reproduce the check.","advisory_only":true},"limits":["Assessment is limited to the supplied handoff text.","No command, live test, transfer, or independent reproduction was performed.","No freshness rule was supplied, so evidence staleness is unknown."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
