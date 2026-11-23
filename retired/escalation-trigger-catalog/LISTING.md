# escalation-trigger-catalog

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when an operational policy must be converted into observable escalation triggers with thresholds, evidence, destinations, timing, and explicit non-triggers. Do not use for approval-path mapping, inventing severity levels, diagnosing incidents, or filling policy gaps with industry norms or personal judgment.

## Task boundary

Nearest is approval-path-mapper; this operationalizes escalation conditions rather than approval sequences.

## Try the independent synthetic example

Convert this policy into a trigger catalog and evaluate the examples; do not send alerts. Policy T1: escalate to Operations within 15 minutes when failed_jobs > 3 in a single 10-minute window. Evidence required: scheduler window report. Non-trigger boundary: exactly 3 failures does not trigger. Examples: E1 has failed_jobs values 4 in one 10-minute window with a scheduler report; E2 has 3 in one 10-minute window with a scheduler report. No severity scale is defined.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_44caf71014da`:

```text
{"triggers":[{"trigger_identifier":"T1","observable_condition":"failed_jobs > 3 within a single 10-minute window","threshold":"> 3 failed jobs per 10-minute window","evidence":"Scheduler window report","destination":"Operations","timing":"Within 15 minutes","non_trigger_boundary":"Exactly 3 failures does not trigger","source_trace":"Policy T1 and supplied boundary","policy_gap":"Severity is not defined."}],"example_evaluations":[{"example":"E1","result":"triggers","reason":"Four failures in one 10-minute window exceed 3 and the required scheduler report is supplied."},{"example":"E2","result":"does_not_trigger","reason":"Exactly 3 failures meet the supplied non-trigger boundary."}],"policy_gaps":["Severity scale is not defined."],"outside_scope":["Alert design or implementation","Sending notifications","Incident diagnosis","Performing or authorizing an escalation"],"verification_report":{"checks":[{"subject":"T1 operator, threshold, and 10-minute window","status":"preserved","source_trace":"Policy T1","notes":"Preserves failed_jobs > 3 in one 10-minute window."},{"subject":"T1 evidence","status":"preserved","source_trace":"Policy T1 evidence requirement","notes":"Scheduler window report is required."},{"subject":"T1 destination and timing","status":"preserved","source_trace":"Policy T1","notes":"Operations within 15 minutes."},{"subject":"T1 boundary","status":"preserved","source_trace":"Supplied non-trigger boundary","notes":"Exactly 3 does not trigger."},{"subject":"T1 severity","status":"unresolved","source_trace":"No severity scale supplied","notes":"Severity remains undefined."}],"issues":["Severity is undefined."]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
