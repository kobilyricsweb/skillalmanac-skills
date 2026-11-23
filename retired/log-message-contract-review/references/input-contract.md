Required inputs:

- Proposed log templates, each with an identifier or label and its literal fields.
- Event definitions mapping event identifiers to applicable templates.
- Required diagnostic context fields for each event.
- Redaction policy listing prohibited fields and any stated scope.
- Severity guidance defining permitted or expected severity values.

Optional inputs may identify policy versions or unresolved ownership, but they do not authorize runtime checks. If a required input is absent, report which review dimensions cannot be assessed and continue only with the dimensions supported by supplied data. If an event cannot be mapped to a template, keep it unresolved.

Output fields: review table, missing required fields, prohibited fields, severity assessment, repair notes, conflicts, unresolved questions, and a verification statement. Treat exact field names as distinct unless the input explicitly defines aliases. A static match or absence is not evidence about emitted logs or runtime behavior.
