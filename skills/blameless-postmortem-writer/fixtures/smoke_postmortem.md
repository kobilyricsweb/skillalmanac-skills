# Postmortem: Checkout 5xx spike after connection pool config change

## Summary

On 2026-03-12, a connection pool max size change to the checkout service was applied to production at 14:02 UTC. Checkout 5xx responses began at 14:05 UTC, and an alert fired at 14:09 UTC. The change was rolled back at 14:33 UTC, the error rate returned to baseline at 14:40 UTC, and the incident was declared resolved at 14:52 UTC. The incident lasted 47 minutes from the first failed responses. The contributing factors were a config change that had not been load tested, a review checklist without a pool limits line, a rollback runbook without the config file path, and an alert that waits four minutes of sustained errors before firing.

## Metadata

| Field | Value |
|---|---|
| Incident date | 2026-03-12 |
| Impact start (UTC) | 14:05 |
| Detected (UTC) | 14:09 |
| Mitigated (UTC) | 14:33 |
| Resolved (UTC) | 14:52 |
| Duration (min) | 47 |
| Time to detect (min) | 4 |
| Time to mitigate (min) | 24 |
| Time to resolve after mitigation (min) | 19 |
| Severity | SEV2 (partial failures for more than 15 minutes) |
| Detection method | Alert "checkout 5xx above 5 percent" |

## Impact

- 12,400 failed checkout attempts [payments dashboard, supplied by user]
- Affected customers: not provided

## Timeline

| Time (UTC) | Event | Source note |
|---|---|---|
| 14:02 | Config change to the checkout connection pool max size applied to production | Responder channel, 14:02 |
| 14:05 | First 5xx responses in checkout service logs | Responder channel, 14:05 |
| 14:09 | Alert "checkout 5xx above 5 percent" fired and paged on-call | Responder channel, 14:09 |
| 14:19 | On-call acknowledged the page and began checking dashboards | Responder channel, 14:19 |
| 14:31 | Decision to roll back the config change | Responder channel, 14:31 |
| 14:33 | Rollback applied and service restarted; rollback complete | Responder channel, 14:33 |
| 14:40 | 5xx rate back to baseline | Responder channel, 14:40 |
| 14:52 | Incident declared resolved after 12 minutes of watching the error rate | Responder channel, 14:52 |

## Contributing factors

1. [System] The pool max size change reached production without a load test, so the limit it reached under traffic was unknown. Evidence: "The change was not load tested in staging."
2. [Process] The config review checklist has no line for connection pool limits, so reviewers were not prompted to check them. Evidence: "The config review checklist has no line for pool limits."
3. [Process] The rollback runbook does not give the config file path, so the path had to be found during the incident. Evidence: "The rollback runbook does not give the config file path."
4. [Process] The 5xx alert needs four minutes of sustained errors before it fires, which set the detection delay to four minutes. Evidence: "The 5xx alert needs 4 minutes of sustained errors before it fires."

## What went well

- The alert fired four minutes after the first 5xx responses (14:09).
- The rollback brought the 5xx rate back to baseline seven minutes after it was applied (14:33 to 14:40).

## Action items

| ID | Action | Type | Owner | Due (YYYY-MM-DD) | Done when |
|---|---|---|---|---|---|
| AI-1 | Add the config file path and restart command to the rollback runbook | Mitigate | Checkout on-call lead | 2026-03-26 | The runbook rollback section names the file path and restart command, and a reviewer confirms it by following the section in staging |
| AI-2 | Set the 5xx alert sustained-error window to 2 minutes | Detect | Checkout SRE team | 2026-04-11 | The alert definition in the monitoring configuration has a 2-minute window, and a staging injection of 5xx responses pages within 3 minutes |
| AI-3 | Require a staging load-test result for any connection pool size change in the config pipeline | Prevent | Checkout platform team | 2026-04-26 | The pipeline job fails on a test change with no attached load-test result, and the job log shows the failure |
| AI-4 | Add a required "pool limits and load-test result" field to the config review checklist | Process | Checkout platform team | 2026-05-11 | The checklist template has the required field, and the change template rejects a blank value |

## Author notes

- Missing inputs: number of affected customers; peak 5xx rate; whether checkout was fully unavailable at any point. The last one decides between SEV1 and SEV2 under the supplied criteria. Severity is recorded as SEV2 on the stated criteria only and needs confirmation.
- Untimed notes: none. The 14:19 to 14:31 interval is noted in the source as "ten minutes with no entries"; no cause is recorded, so it is not listed as a factor.
- Blame rewrites: 1 ("change made by the on-call engineer" was rewritten to "config change applied to production").
- Assumptions made by the author: none.
