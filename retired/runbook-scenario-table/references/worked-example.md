# Worked example

Synthetic example only.

Input procedures:

- `P1 Queue backlog`: applies when queue depth exceeds the supplied threshold and workers are healthy; excludes worker failure.
- `P2 Worker failure`: applies when health checks fail; excludes a healthy worker with queue growth.

Scenarios:

- `S1`: queue depth above threshold; worker health checks pass.
- `S2`: health checks fail; queue depth unknown.
- `S3`: queue depth rising; no threshold supplied and health status missing.

Expected candidate classifications:

| Scenario | Scenario status | Procedure | Candidate status | Prerequisite state | Basis | Gap |
|---|---|---|---|---|---|---|
| S1 | applicable | P1 | applicable | not required | Queue depth is above the supplied threshold and workers are healthy | none |
| S1 | applicable | P2 | unmatched | not required | Health checks pass, conclusively failing P2's positive condition | none |
| S2 | applicable | P1 | excluded | not required | Worker failure satisfies P1's exclusion | none |
| S2 | applicable | P2 | applicable | not required | Health checks fail | none |
| S3 | indeterminate | P1 | indeterminate | not required | Queue growth does not establish that an unspecified threshold is exceeded, and worker health is unknown | threshold and worker-health observations are missing |
| S3 | indeterminate | P2 | indeterminate | not required | Whether health checks fail is unknown; the exclusion-controlling health fact is also unknown | worker-health observation is missing |

S3 retains separate classifications for P1 and P2. Its scenario status is `indeterminate` because no candidate is applicable and both candidates depend on missing observations. Because no escalation rule for an indeterminate scenario was supplied, that absence is recorded as evidence needed or `missing escalation rule` in verification; it does not activate an escalation entry. Unmatched-only handling, if supplied, would apply only after the facts conclusively leave no applicable, indeterminate, or prerequisite-blocked candidate.

If a scenario otherwise satisfied P1 but a required console-access prerequisite were unknown, P1 would be indeterminate with prerequisite state `unknown`. If the input expressly stated that console access was unavailable, P1 would be `blocked by missing prerequisite` with prerequisite state `unsatisfied`.

The artifact does not prescribe a command, claim severity, declare recovery, or invent an escalation recipient.
