# sop-decision-point-extractor

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when a complete standard operating procedure must be converted into documented decision branches with observable conditions and rejoin points. Do not use for routing incoming requests, inventing policy defaults, diagnosing operations, or mapping approval authority across separate procedures.

## Task boundary

Nearest is runbook-scenario-table; this converts one procedure into decision logic rather than matching scenarios to runbook rules.

## Try the independent synthetic example

Extract a decision table from this complete synthetic SOP, preserving its terms. P1: The Receiving Clerk logs every parcel. P2: After logging, the clerk checks whether the parcel's seal is visibly broken. P3: If visibly broken, the clerk places the parcel in the Hold Bin and the procedure terminates. P4: If not visibly broken, the clerk places it on the Intake Shelf and proceeds to Labeling. Defined roles: Receiving Clerk performs P1-P4; Labeling is a named downstream stage, not a role assignment. Identify genuine decisions, branch actions, termination or rejoin points, source references, and uncovered conditions. Do not create approval or routing rules.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_aff9c0b0def3`:

```text
{"decisions":[{"decision_id":"D1","trigger":"After the clerk logs every parcel.","decision_question":"Is the parcel's seal visibly broken?","branches":[{"observable_condition":"Seal is visibly broken.","branch_action":"Place the parcel in the Hold Bin.","role":"Receiving Clerk","rejoin_or_termination":"Procedure terminates.","supporting_passages":["P2-P3"],"missing_or_ambiguous":null},{"observable_condition":"Seal is not visibly broken.","branch_action":"Place the parcel on the Intake Shelf and proceed to Labeling.","role":"Receiving Clerk","rejoin_or_termination":"Continues to named downstream stage Labeling; no rejoin point is stated.","supporting_passages":["P2","P4"],"missing_or_ambiguous":null}],"supporting_passages":["P1-P4"],"status":"documented"}],"input_gaps":[],"scope_exclusions":["Approval rules","Routing or role assignment for Labeling","Actions after termination"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
