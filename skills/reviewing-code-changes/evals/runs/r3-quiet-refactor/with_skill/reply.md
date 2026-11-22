Verdict: Do not merge - the "pure refactor" changes timeout and retry behaviour, and the migration fails on the 40M-row production table.

Blocking
1. notifier/settings.py:3 - timeout dropped from 30 s to 3 s (`DEFAULT_TIMEOUT_S = 3`; old `TIMEOUT_S = 30`).
   Fails when: the provider answers slowly. README says p99 is about 8 s at peak, so every request slower than 3 s now times out. Combined with finding 2, each slow send is retried 3 times and then fails -> notifications lost at peak (verified by: read; `send` now calls `post(..., timeout=3)`, confirmed by running it).
   Fix: set `DEFAULT_TIMEOUT_S = 30`, or get explicit sign-off for a new value and say so in the PR.

2. notifier/retry.py:13 - `except Exception` replaces `except ConnectionError`, so every error is now retried.
   Fails when: the provider rejects a message (ValueError or a 4xx-style error from `post`) -> the same bad request is sent 3 times instead of once, and invalid payloads or non-idempotent sends can be duplicated (verified by: run; a `post` that raises ValueError was called 3 times, previously once).
   Fix: catch `ConnectionError` only (make the retryable exception types a parameter of `with_retry`).

3. migrations/0007_add_channel.sql:2 - `ADD COLUMN channel text NOT NULL` with no default.
   Fails when: the migration runs on `notifications`, which README says has about 40 million rows -> Postgres rejects it ("column contains null values") and the deploy fails. Nothing in the diff writes `channel`, so new inserts would also fail once it is applied (verified by: read; not run against a database).
   Fix: add the column nullable or with a constant default (`DEFAULT 'email'` or similar, once the right value is decided), backfill in batches if needed, then add NOT NULL separately.

Should fix
4. migrations/0007_add_channel.sql:3 - `CREATE INDEX` without `CONCURRENTLY` takes a write-blocking lock on a 40M-row table for the whole build. Fails when: it runs during traffic -> inserts to `notifications` stall. Fix: `CREATE INDEX CONCURRENTLY` in its own migration outside a transaction.

5. notifier/PR.md - description says "pure refactor ... No behaviour change", but the change alters the timeout, the retried exception set, and the schema. The migration is also unrelated to the retry extraction; split it into its own PR. Fix: correct the description and split.

6. tests/test_sender.py:16 - the new test only asserts that ConnectionError is eventually raised. It passes with the old and the new retry code, so it would not catch findings 1 or 2. Fix: also assert `post` call count is 3, add a test that a non-connection error is not retried, and one that asserts the timeout passed to `post`.

Checked: ran `python -m unittest discover -s tests -t .` (3 tests, all pass; they do not cover the findings above); searched the repo for TIMEOUT_S, MAX_TRIES and sender uses (only notifier/sender.py and its tests; no other callers); read README, migration 0006 and transport.py.
Not checked: real row count and Postgres version, whether other code or services write `notifications`, the real provider behaviour.
