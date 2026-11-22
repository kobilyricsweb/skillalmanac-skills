# Input contract

## Required

- Supplied handoff note or work-transfer document.
- Objective and acceptance criteria, if stated.
- Any supplied state, artifacts, evidence, owner, blockers, environment, or next action.

## Handling gaps

Use `not supplied` for absent information. With no criteria, leave the criterion list empty and record the gap. Missing evidence normally yields `unassessable`; `not ready` requires an evidenced failure or an explicitly absent required prerequisite. Preserve conflicting reports separately. Apply staleness only from supplied freshness rules.

## Deliverable

Return JSON matching the domain output schema. Each criterion preserves ID, text, status, reported result, directly read evidence, gap, and source. Evidence records state their level and exactly what was read. Reproducibility, ownership, blockers, and next actions retain source and status. Recommendations are advisory and confer no authority to send, save, deploy, or modify anything.
