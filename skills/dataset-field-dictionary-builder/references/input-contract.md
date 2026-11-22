# Input Contract

Required:

- `fields`: field names, optionally with schema types.
- `source_material`: notes, definitions, constraints, examples, or source descriptions.

Optional:

- `samples`: representative values, labeled as samples rather than definitions.
- `requested_format`: table or structured sections.

Decision rules:

- Source wording outranks interpretation.
- A stated type or constraint may be recorded; sample appearance alone cannot define business meaning.
- Allowed values are recorded as exhaustive only when the source says so; otherwise `allowed_values_exhaustive` is null.
- In JSON, absent source material is represented by null together with `status="not_supplied"`.
- Sample observations must be labeled separately.

Boundaries:

- Do not produce observed type counts or profiling statistics.
- Do not invent definitions, allowed values, owners, or remediation.
- Do not resolve conflicts by guessing.
- Do not validate a full record contract.

Output separates null semantics from blank/empty-string semantics. Missing semantics are not supplied; a one-way implication never establishes its converse.
