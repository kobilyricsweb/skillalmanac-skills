# idempotency-key-behavior-spec

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when converting supplied idempotency-key scope, retention, replay, payload comparison, and error rules into a bounded behavior matrix. Do not use for retry-budget audits, live payment diagnosis, proving retry safety, or filling undocumented duplicate-request behavior by assumption.

## Task boundary

Nearest is retry-budget-audit; this specifies duplicate-request semantics rather than evaluating retry limits.

## Try the independent synthetic example

Create an idempotency-key behavior matrix for POST /labels, scoped per tenant and operation. Retention: 10 minutes from acceptance of the first request. Payload comparison: exact equality of fields name and color; field order is irrelevant. First request: process it and store its response. Exact replay within retention: return the stored response without reprocessing. Changed-payload replay within retention: return error KEY_PAYLOAD_MISMATCH. Concurrent duplicate: return error KEY_IN_PROGRESS while the first request is unfinished. After expiry: treat the key as new. Return structured JSON and state the contract’s evidentiary limit.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_75178eb4c9c6`:

```text
{"scope":"Per tenant and POST /labels operation.","comparison_basis":"Exact equality of fields name and color; field order is irrelevant.","timing":"10 minutes from acceptance of the first request.","scenario_matrix":[{"scenario":"first_request","comparison_basis":"Exact equality of fields name and color; field order is irrelevant.","outcome":"Process the request and store its response.","response_behavior":"Return the processed response.","timing_condition":"On first acceptance.","evidence":"Supplied first-request rule.","contract_status":"specified"},{"scenario":"exact_replay","comparison_basis":"Exact equality of fields name and color; field order is irrelevant.","outcome":"Do not reprocess.","response_behavior":"Return the stored response.","timing_condition":"Within 10 minutes of first acceptance.","evidence":"Supplied exact-replay rule.","contract_status":"specified"},{"scenario":"changed_payload","comparison_basis":"Exact equality of fields name and color; field order is irrelevant.","outcome":"KEY_PAYLOAD_MISMATCH.","response_behavior":"Return the documented error.","timing_condition":"Within retention.","evidence":"Supplied changed-payload rule.","contract_status":"specified"},{"scenario":"concurrent_duplicate","comparison_basis":"Exact equality of fields name and color; field order is irrelevant.","outcome":"KEY_IN_PROGRESS.","response_behavior":"Return the documented error.","timing_condition":"While the first request is unfinished.","evidence":"Supplied concurrent-duplicate rule.","contract_status":"specified"},{"scenario":"after_expiry","comparison_basis":"Exact equality of fields name and color; field order is irrelevant.","outcome":"Treat the key as new.","response_behavior":"Process under the first-request rule and store its response.","timing_condition":"After 10 minutes from first acceptance.","evidence":"Supplied expiry rule.","contract_status":"specified"}],"unspecified_questions":[],"conflicts":[],"verification_statement":"This is a contract representation from supplied documentation, not evidence of implementation behavior, retry safety, or compliance."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
