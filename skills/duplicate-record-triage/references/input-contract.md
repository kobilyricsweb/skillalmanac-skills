# Input Contract

Required:

- `records`: rows containing stable record IDs.
- `comparison_rules`: explicit fields and permitted transformations.

Optional:

- `candidate_rule`: stated threshold, blocking key, or condition.
- `grouping_preference`: record-level or group-level output.

Decision rules:

- Exact means original untransformed values are equal across selected fields. Normalized equality applies only the named transformations, keeping any other selected fields exact.
- Normalized means equality only after an explicitly supplied transformation.
- Candidate requires an explicit candidate rule.
- Unmatched means not matched under the evaluated rule, not real-world non-identity.
- Preserve originals, IDs, missing values, and conflicts.
- Evaluate all relevant record relationships. Unless group-level output is explicitly requested, enumerate every qualifying pair rather than matching each record only to a representative. In group-level output, preserve exact subgroups and make all additional normalized or candidate relationships unambiguous.

Boundaries:

- Never merge, delete, enrich, identify people, or choose a canonical winner.
- Do not treat normalization or candidate status as identity proof.
- Do not invent thresholds, fields, or transformations.
- Incomplete or conflicting rules produce unresolved classifications.
- The remediation boundary must explicitly state that no merge, deletion, enrichment, identity inference, or canonical selection was performed.
