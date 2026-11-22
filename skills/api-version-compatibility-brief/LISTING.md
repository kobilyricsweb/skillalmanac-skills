# api-version-compatibility-brief

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when two supplied API specifications must be compared for documented contract changes across paths, methods, fields, status codes, and behavior. Do not use for live endpoint testing, implementation, migration certification, or producing illustrative errors without a version comparison.

## Task boundary

Nearest is api-error-example-builder; this compares complete version contracts rather than illustrating documented error handling.

## Try the independent synthetic example

Compare these documentary API specifications only. v1: GET /pets/{id}; response 200 has required field name:string and optional field age:integer; response 404 documented. v2: GET /pets/{id}; response 200 has required name:string, required age:integer, and optional color:string; responses 404 and 410 documented. No rename, deprecation, or behavior notes exist. Return an element comparison, classifications, impacts limited to the documents, unresolved items, and scope limits.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_d688a11ec810`:

```text
{"comparisons":[{"area":"path","element":"/pets/{id}","version_1":"GET /pets/{id}","version_2":"GET /pets/{id}","classification":"unchanged","impact":"Documented path remains present."},{"area":"method","element":"GET /pets/{id}","version_1":"GET","version_2":"GET","classification":"unchanged","impact":"Documented method remains unchanged."},{"area":"response_field","element":"name","version_1":"required string","version_2":"required string","classification":"unchanged","impact":"Type and requiredness match."},{"area":"response_field","element":"age","version_1":"optional integer","version_2":"required integer","classification":"changed","impact":"Clients must account for changed requiredness."},{"area":"response_field","element":"color","version_1":null,"version_2":"optional string","classification":"added","impact":"Field appears only in supplied v2 documentation."},{"area":"status_code","element":"404","version_1":"documented","version_2":"documented","classification":"unchanged","impact":"404 remains documented."},{"area":"status_code","element":"410","version_1":null,"version_2":"documented","classification":"added","impact":"410 is newly documented in v2."},{"area":"behavior","element":"rename, deprecation, and behavior notes","version_1":null,"version_2":null,"classification":"behaviorally_uncertain","impact":"Intent and runtime behavior are not documented."}],"conflicts":[],"unresolved_items":["Runtime compatibility and migration readiness are not established."],"scope":"Documentary comparison only; no endpoint testing or runtime claims."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
