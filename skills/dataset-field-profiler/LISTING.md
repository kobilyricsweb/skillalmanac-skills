# dataset-field-profiler

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when you need a descriptive inventory of top-level fields and observed JSON value types across supplied records. Do not use for enforcing a declared schema, validating business rules, inferring data meaning, or exposing sample values.

## Task boundary

data-analysis-eda and spreadsheet-analysis inspect datasets for quality issues and analytical findings. dataset-field-profiler is narrower: it inventories top-level JSON field presence, absence, nulls, and observed value types without exposing values, enforcing a schema, or treating variation as a defect.

## Try the independent synthetic example

The interpreter is unavailable. Produce a labeled manual, unexecuted profile of this exact JSON input without running or modifying the bundled script: {"records":[{"a":1,"b":null},{"a":1.5,"c":[]},{"a":true,"c":{}}]}. Use only direct fields, sort fields alphabetically, distinguish booleans from numbers, and do not emit raw values. State the input scope, execution mode, and untested limits.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_011b0fce6b87`:

```text
Manual profile (unexecuted). Input scope: one object with 3 records; direct fields only; raw values omitted. Execution mode: interpreter unavailable, bundled script neither run nor modified. Sorted field observations: a — row_count 3, present 3, missing 0, null 0, string 0, boolean 1, integer 1, number 1, array 0, object 0. b — present 1, missing 2, null 1, string 0, boolean 0, integer 0, number 0, array 0, object 0. c — present 2, missing 1, null 0, string 0, boolean 0, integer 0, number 0, array 1, object 1. Untested limits: execution status, file/path handling, duplicate keys, size and numeric bounds, and any semantic or business validation.
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
