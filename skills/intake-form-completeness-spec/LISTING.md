# intake-form-completeness-spec

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when an intake workflow needs field-level requirements that vary by request type and must be tied to supplied routing, format, validation, and incomplete-case rules. Do not use for configuration-key comparison, generic form redesign, data diagnosis, or making fields mandatory merely because they seem useful.

## Task boundary

Nearest is configuration-key-drift-check; this specifies conditional business intake fields rather than comparing configuration key names.

## Try the independent synthetic example

Create an intake completeness specification. Request types: new badge and replace badge. Candidate fields: employee_id, delivery_site, loss_report. Rules: employee_id is required for both types and must be six digits, validated against the supplied HR roster; delivery_site is optional for both and accepts Site A or Site B without external validation; loss_report is required only for replace badge and accepts an incident reference beginning IR-, validated by Security. Policy: reject a submission as incomplete when a required field is absent or invalid; if required validation results are not supplied, completeness is unresolved. No successful HR-roster or Security validation results are supplied. Evaluate these cases: new badge {employee_id:123456}; replace badge {employee_id:123456, loss_report:IR-7}; replace badge {employee_id:123456}. Do not change any submission.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_exec_medium_2f0d65f81819`:

```text
{"fields":[{"field":"employee_id","purpose":"Identify the employee","accepted_format":"Six digits","validation_source":"Supplied HR roster","validation_result_status":"unavailable","request_type_rules":[{"request_type":"new badge","applicability":"applicable","requiredness":"required","absent_or_invalid_handling":"Incomplete; unresolved if required validation is unavailable","rule_trace":"Required for both types"},{"request_type":"replace badge","applicability":"applicable","requiredness":"required","absent_or_invalid_handling":"Incomplete; unresolved if required validation is unavailable","rule_trace":"Required for both types"}]},{"field":"delivery_site","purpose":"Delivery destination","accepted_format":"Site A or Site B","validation_source":"None","validation_result_status":"not_required","request_type_rules":[{"request_type":"new badge","applicability":"applicable","requiredness":"optional","absent_or_invalid_handling":"Absence does not make submission incomplete","rule_trace":"Optional for both types"},{"request_type":"replace badge","applicability":"applicable","requiredness":"optional","absent_or_invalid_handling":"Absence does not make submission incomplete","rule_trace":"Optional for both types"}]},{"field":"loss_report","purpose":"Incident reference for replacement","accepted_format":"Begins IR-","validation_source":"Security","validation_result_status":"varies_by_request_type","request_type_rules":[{"request_type":"new badge","applicability":"not_applicable","requiredness":"not_applicable","absent_or_invalid_handling":"No effect","rule_trace":"Required only for replace badge","validation_result_status":"not_required"},{"request_type":"replace badge","applicability":"applicable","requiredness":"required","absent_or_invalid_handling":"Incomplete; unresolved if Security validation is unavailable","rule_trace":"Required only for replace badge","validation_result_status":"unavailable"}]}],"completeness_examples":[{"request_type":"new badge","status":"unresolved","reasons":["123456 matches format; HR validation result is unavailable"]},{"request_type":"replace badge","status":"unresolved","reasons":["Formats match; HR and Security validation results are unavailable"]},{"request_type":"replace badge","status":"incomplete","reasons":["Required loss_report is absent"]}],"unresolved_conflicts":[],"gaps":["No successful HR-roster or Security validation results are supplied"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
