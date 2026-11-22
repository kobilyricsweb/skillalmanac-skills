# Runbook: database failover

Last verified: 2027-01-15 against v2.3.1

## Symptoms

The worker logs `connection refused` and the queue depth alert fires.

## Procedure

1. Confirm the primary is down.
2. Promote the replica with `quillpost db promote`.
3. Restart the workers.

## Verification

Queue depth falls below 100 within five minutes. Details are in [the escalation notes](#escalation-notes).
