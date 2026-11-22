# Input contract

Provide:

- `requirements`: requirement IDs and exact statements.
- `priority`: supplied priority or importance for each requirement.
- `workflow`: intended users, scenario, and desired outcome.
- `duration`: total demonstration time and any supplied segment limits.
- `participants`: available roles or unavailable stakeholders.
- `constraints`: data, environment, access, or presentation limits.
- `evidence_format`: what the team wants captured.

Decision rules:

- Preserve requirement meaning and IDs.
- Prioritize only from supplied priority.
- Request observable live actions, not unsupported claims.
- Mark a requirement non-demonstrable when the scope lacks an action, data, participant, or necessary condition.
- Include every timed segment in the duration check; report overflow explicitly when arithmetic is determinable.
- If segment timing remains unknown, preserve the gap: affected duration totals and feasibility conclusions are null, with the missing timing input recorded. Use provisional allocations only when supplied or explicitly requested, and label them provisional.

Boundaries: do not browse, rank vendors, score products, validate claims, contact vendors, or treat a proposed demonstration as observed proof.

Segment durations may be supplied constraints or clearly labeled provisional planning allocations when a timed plan is requested. Keep their basis separate; estimates are not observed timing or feature evidence. Missing validation responsibility stays unresolved unless explicitly supplied.
