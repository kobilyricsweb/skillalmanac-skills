# dataset-field-dictionary-builder

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when building a field dictionary from supplied schemas, definitions, constraints, notes, and labeled samples while separating source meaning from observations. Do not use for dataset profiling, record validation, inferred business semantics, web research, schema remediation, or backfill design.

## Task boundary

dataset-field-profiler reports observed field shapes; this builds a declared field dictionary while separating documented semantics from samples and unresolved definitions.

## Try the independent synthetic example

Build a field dictionary from this synthetic input. Fields: customer_id (string), status (string), closed_at (string or null). Source notes: customer_id: “Stable account identifier.” status: “One of active or closed; this list is exhaustive.” closed_at: “Closure timestamp; null means the account has not been closed.” Samples: customer_id=C-1, status=active, closed_at=null. Return only the dictionary and unresolved questions. Do not profile records or validate a record contract.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_756a9df11187`:

```text
{"fields":[{"field_name":"customer_id","source_wording":"Stable account identifier.","normalized_definition":"Identifier for a customer account.","expected_type":"string","allowed_values":null,"allowed_values_exhaustive":null,"null_semantics":null,"blank_semantics":null,"sample_observations":["Sample value: C-1"],"provenance":["field schema","customer_id note","sample"],"status":"supported"},{"field_name":"status","source_wording":"One of active or closed; this list is exhaustive.","normalized_definition":"Account status.","expected_type":"string","allowed_values":["active","closed"],"allowed_values_exhaustive":true,"null_semantics":null,"blank_semantics":null,"sample_observations":["Sample value: active"],"provenance":["field schema","status note","sample"],"status":"supported"},{"field_name":"closed_at","source_wording":"Closure timestamp; null means the account has not been closed.","normalized_definition":"Timestamp associated with account closure.","expected_type":"string or null","allowed_values":null,"allowed_values_exhaustive":null,"null_semantics":"Null means the account has not been closed.","blank_semantics":null,"sample_observations":["Sample value: null"],"provenance":["field schema","closed_at note","sample"],"status":"supported"}],"unresolved_questions":["What do blank or empty-string values mean for each field?","What format is required for non-null closed_at values?"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
