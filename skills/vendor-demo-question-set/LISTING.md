# vendor-demo-question-set

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when turning supplied requirements, participants, evidence needs, and time limits into a proposed vendor demonstration script with explicit timing uncertainty. Do not use for vendor rankings, market research, procurement scoring, contacting vendors, or claims that any capability was observed or validated.

## Task boundary

case-study-interview-kit investigates claims and quotation permission and approval-path-mapper models authority; this plans timed live demonstration requests and observable validation evidence.

## Try the independent synthetic example

Create a proposed vendor demo script. Requirements: R1 "A clerk can create a list with items A and B," mandatory; R2 "A supervisor can view that list," optional. Workflow: clerk creates, supervisor views. Duration: 6 minutes total; R1 gets 3 minutes, transition 1 minute, R2 gets 2 minutes. Participants: clerk, supervisor, vendor presenter. Constraint: use only synthetic items A and B. Evidence format: capture the resulting screen after each requirement.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_5daef110eadf`:

```text
{"objective":"Request a live demonstration of clerk list creation and supervisor viewing using only synthetic items A and B.","assumptions":["Clerk, supervisor, and vendor presenter are available.","R1 is mandatory and R2 is optional.","Each requirement's resulting screen is captured."],"timed_script":[{"requirement_ids":["R1"],"segment":"Clerk creates list","duration_minutes":3,"timing_basis":"supplied","live_action_request":"Have the clerk create a list containing synthetic items A and B.","observable_result":"A screen showing the created list with items A and B.","status":"planned"},{"requirement_ids":[],"segment":"Transition","duration_minutes":1,"timing_basis":"supplied","live_action_request":"Transition control to the supervisor and capture the R1 screen.","observable_result":"The R1 resulting screen is captured.","status":"planned"},{"requirement_ids":["R2"],"segment":"Supervisor views list","duration_minutes":2,"timing_basis":"supplied","live_action_request":"Have the supervisor open and view the list created by the clerk.","observable_result":"A screen showing the supervisor viewing that list.","status":"planned"}],"traceability":[{"requirement_id":"R1","priority":"mandatory","status":"planned","script_segments":["Clerk creates list"]},{"requirement_id":"R2","priority":"optional","status":"planned","script_segments":["Supervisor views list"]}],"evidence_requests":[{"requirement_id":"R1","demo_evidence":"Capture the resulting screen after the clerk creates the list.","later_validation_evidence":null},{"requirement_id":"R2","demo_evidence":"Capture the resulting screen after the supervisor views the list.","later_validation_evidence":null}],"follow_up_questions":[{"requirement_id":"R1","question":"What later check, if any, should confirm that the created list persists?"},{"requirement_id":"R2","question":"What later check, if any, should confirm that the supervisor's view reflects the clerk's list?"}],"non_demonstrable":[],"overflow":{"duration_cap_minutes":6,"in_cap_planned_minutes":6,"total_requested_minutes":6,"arithmetic_overflow_minutes":0,"deferred_minutes":0,"full_scope_feasible":true,"in_cap_agenda_feasible":true},"verification":{"all_requirements_have_status":true,"duration_arithmetic_checked":true,"vendor_capabilities_claimed_as_observed":false,"unresolved_validation_owner":true}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
