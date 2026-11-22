# api-error-example-builder

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when converting supplied API error documentation into bounded request/response scenarios, client actions, fallback gaps, status conflicts, and recovery findings. Do not use to infer undocumented schemas or retry safety, verify live server behavior, execute endpoint checks, or generate production SDK implementations.

## Task boundary

cli-help-example-designer builds command examples from CLI grammar and api-version-compatibility-brief compares versions; this builds examples of documented API error responses without inventing status codes or response fields.

## Try the independent synthetic example

Build an offline API error scenario matrix from these facts. Request schema: POST /cards accepts required field title and optional field color; color is red or blue. Error E_COLOR occurs when color is outside that domain, status 422, body {"code":"E_COLOR","field":"color"}. Error E_TITLE occurs when title is empty, status 400, body {"code":"E_TITLE"}. Client policy: for E_COLOR, retain title and ask for red or blue; for E_TITLE, ask for a nonempty title. No fallback or retry policy is supplied. Identify missing guidance and actions outside scope.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_9d5a7e776921`:

```text
{"scope":"Offline API error scenario matrix from supplied documentation.","assumptions":["No endpoint was executed."],"scenarios":[{"error_id":"E_COLOR","condition":"color is outside the allowed red or blue domain","request":{"title":"Example title","color":"green"},"status":422,"response_body":{"code":"E_COLOR","field":"color"},"client_action":"Retain title and ask for red or blue.","safe_fallback":"unknown","recovery_status":"partial"},{"error_id":"E_TITLE","condition":"title is empty","request":{"title":""},"status":400,"response_body":{"code":"E_TITLE"},"client_action":"Ask for a nonempty title.","safe_fallback":"unknown","recovery_status":"partial"}],"missing_guidance":["No safe fallback is documented for either error.","No retry, retry-budget, transport, or authentication guidance is supplied."],"conflicts":[],"acceptance_checks":["One scenario covers each supplied error.","Requests use only documented fields and values except the documented invalid color example.","Statuses and bodies are reproduced exactly.","No request was executed."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
