# log-message-contract-review

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when reviewing proposed log templates against declared event fields, redaction rules, required diagnostic context, and severity guidance. Do not use for runtime verification, configuration-drift explanations, incident diagnosis, or inferring behavior from emitted logs.

## Task boundary

Nearest is configuration-drift-explainer; this reviews static observability contracts rather than explaining configuration changes.

## Try the independent synthetic example

Review this static logging contract. Template T1 has severity ERROR and literal fields event_id, file_id, and error_code. Event upload_failed maps to T1. Its required context is event_id, file_id, request_id, and error_code. The redaction policy prohibits auth_token in all templates. Severity guidance requires ERROR for upload_failed. Return the contract review, smallest supported repair, unresolved matters, and the boundary of verification.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_c198d3fa9286`:

```text
{"review_table":[{"template_id":"T1","event_id":"upload_failed","declared_fields":["event_id","file_id","error_code"],"missing_required_fields":["request_id"],"prohibited_fields":[],"severity":"ERROR","severity_assessment":"permitted","repair_notes":["Add the required request_id field to T1."],"unresolved_questions":[]}],"conflicts":[],"unresolved_questions":[],"verification_statement":"The supplied template was checked against its mapped required fields, the stated redaction policy, and severity guidance; this assesses the declared static contract only and does not establish runtime behavior."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
