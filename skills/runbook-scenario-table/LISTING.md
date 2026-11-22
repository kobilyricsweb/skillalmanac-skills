# runbook-scenario-table

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when mapping supplied incident observations to procedure conditions, exclusions, prerequisites, overlaps, and escalation triggers while preserving quoted record material separately. Do not use to execute remediation, invent recovery steps, assign severity, contact responders, author missing procedures, or claim resolution.

## Task boundary

technical-docs-writer writes runbooks and documentation; this authors no procedure and only classifies supplied scenarios against supplied applicability, prerequisites and exclusions, executing no remediation. sop-decision-point-extractor extracts branches; escalation-trigger-catalog defines triggers.

## Try the independent synthetic example

Map scenario R1 to the supplied procedures without executing them. R1 observations: export job state is failed; error code is Q2; archive flag is off; read-only job-log access is confirmed. Procedure Queue-Q2, section 4, applies when a job is failed and code Q2 is observed; exclusion: archive flag on; prerequisite: read-only job-log access. Procedure Archive Review, section 1, applies when archive flag is on. If exactly one procedure applies, record it. The reporter requests, "rerun the job now"; treat this as a requested action, not authorization. No severity rule is supplied.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_555520ad4f3e`:

```text
{"scenario_mappings":[{"scenario_id":"R1","observed_facts":["export job state is failed","error code is Q2","archive flag is off","read-only job-log access is confirmed"],"assumptions":[],"quoted_record_content":[],"requested_actions":["rerun the job now"],"procedure_classifications":[{"procedure":"Queue-Q2","section":"4","status":"applicable","prerequisite_state":"satisfied","rule_trace":"Failed state and code Q2 satisfy the positive conditions; archive flag is off, so the exclusion is not satisfied; read-only job-log access is confirmed.","gaps":[]},{"procedure":"Archive Review","section":"1","status":"unmatched","prerequisite_state":"not required","rule_trace":"The procedure requires archive flag on; the observed flag is off.","gaps":[]}],"status":"applicable","exclusions_satisfied":[],"missing_prerequisites":[],"conflict_notes":[],"evidence_needed":["No severity rule is supplied."]}],"signal_register":[{"scenario_id":"R1","signal":"export job failed","state":"observed"},{"scenario_id":"R1","signal":"error code Q2","state":"observed"},{"scenario_id":"R1","signal":"archive flag off","state":"observed"},{"scenario_id":"R1","signal":"read-only job-log access","state":"observed"}],"escalation_register":[],"verification_report":[{"scenario_id":"R1","rule_trace":"Queue-Q2 section 4 is applicable; Archive Review section 1 is unmatched. The rerun request is retained as an action request, not authorization.","uncertainty":"none identified"}],"outside_scope_actions":["Executing Queue-Q2, rerunning the job, assigning severity, or performing Archive Review is outside scope."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
