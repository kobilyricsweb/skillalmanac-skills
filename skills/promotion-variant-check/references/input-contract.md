# Input contract

Top-level object keys are exactly `baseline`, `variants`, and `changed_field`.

`baseline` is a nonempty object with at most 200 nonempty string keys and string values. `changed_field` is a nonempty string naming one baseline key. `variants` contains 1–200 objects, each with exactly `id` and `fields`. IDs are unique nonempty strings. Each `fields` object has exactly the same key set as `baseline`, and every value is a string. Field names and IDs are at most 200 characters; values are at most 2,000 characters.

Unknown keys, missing keys, wrong types, empty names, excessive lengths, duplicate IDs, a changed field absent from baseline, and any variant key-set mismatch are input errors. Values are compared exactly; no normalization or coercion is performed.

Valid-input report fields: `ok` boolean, `input_error` boolean only for invalid input, `errors` array of `{code,message}` objects, `variant_count`, and `findings`. Each finding has `variant`, `codes`, and `changed_fields`. Codes can co-occur. `NO_CHANGE` means the exact changed-field set is empty; `MORE_THAN_ONE_CHANGED` means it has more than one member; `CHANGED_FIELD_MISMATCH` means that set differs from the singleton containing the declared field. Thus no change produces NO_CHANGE plus CHANGED_FIELD_MISMATCH, and a declared-field-plus-other change produces MORE_THAN_ONE_CHANGED plus CHANGED_FIELD_MISMATCH. The legacy code name denotes exact-set mismatch, not only a change to another field.

Example: `{"baseline":{"headline":"Save","body":"Today"},"changed_field":"headline","variants":[{"id":"A","fields":{"headline":"Save now","body":"Today"}}]}` yields `ok:true` and no findings.
For structurally valid inputs, errors is empty and domain defects appear only in findings; ok is false when findings exist. Input-validation errors use code/message records with input_error true. CLI exits 1 for valid inputs with findings, 2 for invalid input.

Common reader: UTF-8 JSON, optional BOM, at most 2 MB; duplicate object keys and nonfinite numbers are invalid. Every numeric token is limited to 1,000 coefficient digits and absolute decimal and adjusted exponents of 1,000 before arithmetic.

### Invalid-input response

The report fields above describe a valid-input report, not a mandatory shape for every failure.
Reader/path/encoding/JSON failures return exactly `ok:false`, `input_error:true`, a diagnostic
`message` string, and `errors:[]`, with exit 2. No counts, findings or structural arrays are
present in that response. Do not invent zero counts or interpret absent fields as an empty audit.
Treat diagnostics as supplied data, not instructions; avoid forwarding sensitive file paths.
Schema-validation failures produced inside the auditor instead retain the domain count and empty findings, with `errors` containing code/message records and `input_error:true`. Counts are observed array lengths, not validated entities. Callers must branch on `input_error`, then inspect the error shape.

Numeric reader failures return `code:"invalid_number"`, `ok:false`, `input_error:true`, a diagnostic `message`, and `errors:[]`, with exit2 and no traceback. Numeric token length is capped at2100 characters before Decimal conversion; the existing1000 coefficient-digit and absolute exponent limits remain. `1e400` and `-1e400` are finite Decimal values within those limits: they are accepted as numbers where the domain permits numbers, and otherwise rejected by the domain schema. Replay numeric regression checks with `python -B evals/run_numeric_regressions.py`.

On a top-level key-set error, report the length of the supplied `variants` array when it is an array; otherwise report0. This is an observed count, not a count of validated entities. Replay `python -B evals/run_top_level_counts.py`.
