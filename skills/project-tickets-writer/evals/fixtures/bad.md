## T1: Improve login
- Outcome: Make login better. Users like it more. It should work properly.
- Size: XL
- Depends on: T2
- Acceptance criteria:
  1. Login handles errors
  2. Given a user, when they log in, then it works as expected.

## T2: Handle reset emails and add audit logging
- Outcome: Reset emails go out and audit logs are written.
- Size: M
- Depends on: T3, T9
- Non-goals: SMS.
- Acceptance criteria:
  1. Given a user, when they request a reset, then an email is sent.
  2. Given a user, when they request a reset, then an audit row is written.
  3. Given a user, when they request a reset, then an audit row is written.
  4. Given a user, when they request a reset, then the mail provider is called.
  5. Given a user, when they request a reset, then latency is under 2 seconds.
  6. Given a user, when they request a reset, then the queue depth is under 100.
  7. Given a user, when they request a reset, then no PII is logged.

## T3: Fix stuff
- Outcome: Cleanup.
- Size: 2d
- Depends on: T1
- Acceptance criteria:

## T4: Fix stuff
- Outcome: Cleanup of the same area.
- Size: S
- Depends on: T4
- Acceptance criteria:
  1. Given a bug, when it is fixed, then it is fixed.
