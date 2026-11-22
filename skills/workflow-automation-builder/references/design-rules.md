## Contents

- Idempotency key recipes
- Rate-limit arithmetic
- Dead-letter record
- Secrets
- Synthetic events
- Runbook template
- Sources

# Design rules

## Idempotency key recipes

| Write | Key | Note |
|---|---|---|
| Create a record from an event | `<event id>-<step id>` | The most common case. |
| Create one record per list item | `<event id>-<step id>-<item id>` | Item id, not index, when the list can be reordered by a re-delivery. |
| Update a record | `<record id>-<field set>-<version or updated_at>` | Without a version, a late retry can overwrite a newer value: also add an "only if newer" condition. |
| Send a message | `<event id>-notify` | If the tool cannot dedupe, first look up a processed-ids table and skip when found. |
| Charge or refund | the provider's own idempotency header with `<order id>-charge` | Never build this write without it. Alert on any dead letter at once. |
| Target has no key support | a "processed ids" table written after the write, checked before it | A narrow window remains (crash between write and mark); state it in the report. |

A key made only of a timestamp or a random value is not an idempotency key: a retry produces a new one.

## Rate-limit arithmetic

1. Peak events per second `E`, calls per event `C` to the busiest service, documented quota `Q` per minute.
2. Needed rate is `E x C x 60`. Allowed rate is `0.5 x Q`. If needed exceeds allowed, queue and smooth: process at the allowed rate and accept the delay.
3. Drain time for a backlog of `B` calls is `B / (allowed rate per minute)` minutes. State it; a 20,000-call backlog at 30 per minute is over 11 hours.
4. Concurrency is `ceil(E x p95 seconds per run)`. Above that, runs only queue up.
5. On a 429, back off and also lower the step rate for the next 5 minutes; a retry storm after an outage is the usual way a second outage starts.

## Dead-letter record

Fields: run id, step id, event id, error class (transient exhausted, permanent, validation), attempts, first failure time, reference to the stored payload. Do not store tokens or full personal records; keep a reference or a masked copy. Retention 30 days. Alert when a write step dead-letters (within 15 minutes) and when more than 5 entries arrive in one hour. A dead letter nobody can replay is just a log: the runbook must name who replays and how.

## Secrets

- Spec and exported flow files contain only `{{secrets.NAME}}`. If a real credential ever appears in one, rotate it before anything else.
- One secret per service per environment (test and live differ). Smallest scope the service offers: a read-only token for read steps.
- Keep credentials out of trigger payloads, dead-letter records, alert text and run logs; mask headers in logs.
- Rotate every 90 days and when someone with access leaves. Put the next rotation date and the owner in the runbook.
- A 401 or 403 is a credential problem, not a transient one: one retry at most, then alert the owner.

## Synthetic events

Build them from one real sample with identifiers replaced (no real customer data). Run against a sandbox target.

| # | Event | Change | Expected result |
|---|---|---|---|
| T1 | Happy path | none | every write once; run succeeds |
| T2 | Duplicate delivery | same event id sent twice, 1 s apart | second run stops at the dedupe check; no second write |
| T3 | Retry after lost response | downstream accepts the write but the response is dropped (force a timeout) | retry sends the same idempotency key; one record |
| T4 | Missing field | remove a required field | validation error to dead letter or alert, no partial writes |
| T5 | Filtered out | status or type not in the filter | run ends quietly, counted in metrics, no alert |
| T6 | Rate limit | downstream returns 429 with a retry-after | wait, retry, succeed; step rate drops |
| T7 | Permanent failure | downstream returns 422, then a 503 for longer than the retry window | 422: dead letter with no retry; 503: retries then dead letter; alert fires in both |
| T8 | Burst | 50 events in 10 seconds (or 10 x the peak rate) | concurrency cap holds; no 429 storm; all processed in the drain time |
| T9 | Bad signature | change one character of the signature | rejected before step 1; body not written to logs |
| T10 | Silent stop | disable the source for 2 intervals | the heartbeat alert fires |

For loops add: an empty list (no writes, no error) and a list one over `max_iterations` (stops with an alert, not silently truncated).

## Runbook template

```
Workflow: <name>        Owner: <name or alias>        Backup: <name>
Alerts: <alert> -> <channel> -> <first response>
First five minutes: 1 open run history, find the first failed step; 2 read its error class;
  3 transient: wait for retries; permanent: go to dead letters; 4 credential error: rotate (below)
Dead letters: where they are; who replays; replay = re-run the failed step with the SAME event id
  (the idempotency key makes it safe); never edit the key; record the outcome on the entry
Kill switch: <how to pause the trigger>; effect on in-flight runs; how to resume and catch up (cursor reset rules)
Backlog after an outage: expected drain time from the rate arithmetic
Secrets: names, owners, last rotated, next rotation, where to rotate
Known limits: quotas, max batch, platform run-time cap
Change log: date, change, who, test events re-run
```

## Sources

- Retry-After header semantics for 429 and 503: https://www.rfc-editor.org/rfc/rfc9110 (section on Retry-After).
- Idempotency-Key request header for unsafe methods, in draft: https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/
- The numeric defaults in this file and in SKILL.md are the author's working values, not taken from either source.
