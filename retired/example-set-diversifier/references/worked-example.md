# Worked Example

The rules and scenario domain are invented for this illustration. Retained examples are identified as supplied; additions are synthetic.

Input:

Objective: identify whether a form submission is ready for review.

Rules: a submission is ready when the name and date are present; a missing field is incomplete; contradictory dates require clarification.

Existing supplied examples: Ana, Ben, and Cara each have a name and one date.

Coverage diagnosis: all three supplied examples have the same signature—`name present=true`, `date present=true`, learner decision `classify readiness`, outcome `determined: ready`. Retain one and consolidate the repetitions.

Minimal-pair decision table:

| Role | Provenance | Change from retained normal case | Signature difference | Newly covered decision |
|---|---|---|---|---|
| Normal | supplied | None | Both required predicates true | Ready for review |
| Missing input | created; synthetic | Remove the date | `date present=missing` | Incomplete |
| Conflict | created; synthetic | Replace one date with two contradictory dates | `date consistent=conflicting` | Clarification required |

Diversified plan:

- Normal — supplied, not synthetic: a supplied example with a name and one date. Expected lesson: ready for review.
- Missing input — created and synthetic: the same structure lacks the date. Expected lesson: incomplete.
- Conflict — created and synthetic: the name is present and two contradictory dates are supplied. Expected lesson: clarification is required.

No numerical threshold or inclusion rule was supplied, so no boundary pair is created. A second missing-field example could change which field is absent, but it would add no new outcome beyond `incomplete`; include it only if practicing field recognition is itself a supplied objective.

Preservation note: every retained or added example teaches readiness classification. No supplied example is mislabeled as synthetic, and no customer result, external fact, or invented precedence is claimed.
