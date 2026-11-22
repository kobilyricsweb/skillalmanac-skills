# Input contract

Provide:

- Cohort names.
- Inclusion and exclusion conditions.
- Fields used by each condition.
- Date boundaries with timezone or boundary convention.
- Precedence for overlapping rules.
- Behavior for missing, unknown, or invalid values.
- Whether multiple cohort membership is allowed.
- Synthetic records or a record schema sufficient to demonstrate classifications.

Missing cohort rules, field definitions, boundary semantics, or precedence must be listed as unresolved rather than completed by inference. If multiple membership is not allowed and overlapping eligible cohorts have no precedence, final assignment is indeterminate.

The output contains an operational rule table, required-input notes, one classification row per supplied record, and unresolved conflicts. Each record row contains:

- A per-cohort evaluation of `eligible`, `ineligible`, `excluded`, or `indeterminate`, with a rule path.
- `candidate_cohorts`, listing cohorts whose inclusion conditions are met and whose exclusions do not apply.
- `assigned_cohorts`, listing final memberships after applying the supplied multiple-membership and precedence policy.
- `assigned_cohort`, containing the sole final assignment when exactly one exists, or null when there are zero or multiple final assignments.
- A final status of `included`, `excluded`, or `indeterminate`.
- A record-level rule path and uncertainty note.

When multiple membership is allowed, every eligible candidate is included in `assigned_cohorts`. When it is prohibited, `assigned_cohorts` contains at most one cohort; an unresolved overlap leaves it empty and makes the record indeterminate. Key rules: missing required values do not become false; overlapping candidates without supplied resolution do not receive an invented winner; date endpoints follow only the supplied convention; and every output assertion traces to supplied input.
