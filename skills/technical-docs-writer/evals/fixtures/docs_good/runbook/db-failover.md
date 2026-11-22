# Runbook: database failover

Last verified: 2026-11-12 against v2.3.1

## Symptoms

The worker logs `connection refused` and the queue depth alert fires.

## Procedure

1. Confirm the primary is down.
2. Promote the replica with `quillpost db promote`.
3. Restart the workers.

## Verification

Queue depth falls below 100 within five minutes.

## Rollback

Run `quillpost db demote` on the replica and point the workers at the old primary.

## Escalation

Page the data on-call if the replica does not promote within ten minutes.
