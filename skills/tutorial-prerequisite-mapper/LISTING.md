# tutorial-prerequisite-mapper

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when mapping supplied tutorial steps to prior knowledge, state, inputs and verification cues. Do not use to execute setup, obtain credentials or replace a general handover audit.

## Task boundary

handover-readiness-check audits transfer readiness and instruction-sequence-repair repairs ordering; this maps the prerequisite producer/consumer dependency of each tutorial step. technical-docs-writer authors broader documentation.

## Try the independent synthetic example

Map prerequisites for this tutorial without executing it. Environment: a writable practice folder is open. Learner can create and read text files. Input: the supplied word “sun”. Steps: S1 “Save sun in source.txt.” S2 “Copy the contents of source.txt into result.txt.” Verification: after S1, source.txt displays sun; after S2, result.txt displays sun.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_d688a11ec810`:

```text
{"scope_assumptions":{"environment":"Writable practice folder is open.","learner_assumptions":["Learner can create and read text files."],"unknowns":[]},"step_map":[{"step_id":"S1","action":"Save sun in source.txt.","required_knowledge":["Create a text file."],"required_state":["Writable practice folder open."],"required_inputs":["Supplied word sun."],"produced_artifact":"source.txt containing sun","later_consumers":["S2"],"verification_cue":"After S1, source.txt displays sun.","dependency_status":"supplied"},{"step_id":"S2","action":"Copy source.txt contents into result.txt.","required_knowledge":["Read and create text files."],"required_state":["Writable practice folder open; source.txt from S1."],"required_inputs":["source.txt containing sun"],"produced_artifact":"result.txt containing sun","later_consumers":[],"verification_cue":"After S2, result.txt displays sun.","dependency_status":"supplied"}],"dependency_edges":[{"from_step":"S1","to_step":"S2","artifact_or_state":"source.txt containing sun"}],"gaps":[],"planning_status":"planning_complete","verification":{"all_steps_have_status":true,"all_consumed_artifacts_traced":true,"actions_executed":false}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
