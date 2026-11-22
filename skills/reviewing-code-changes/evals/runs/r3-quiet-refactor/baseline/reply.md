# Review: "Extract retry helper" (notifier/)

**Verdict: do not merge as is.** The PR is described as a pure refactor with no behaviour change, but it contains two behaviour changes in the Python code and a migration that is likely to fail or lock the table in production. The 3 existing tests pass (I ran them), but none of them cover these problems.

## Blockers

### 1. Timeout cut from 30s to 3s (`notifier/settings.py`, `notifier/sender.py`)
The old code used `TIMEOUT_S = 30`. The new `DEFAULT_TIMEOUT_S = 3` is a tenfold reduction. The README says the provider's p99 latency is about 8 seconds at peak, so at peak well over 1% of requests, possibly far more, will now time out even though the provider would have answered. That is a user-visible behaviour change, and it contradicts "No behaviour change". Restore the value to 30, or choose a new value deliberately (comfortably above 8s) and say so in the PR.

### 2. Retry now catches every exception (`notifier/retry.py`)
The old loop retried only `ConnectionError`. The new helper has `except Exception`, so it also retries timeouts, programming errors such as `TypeError` and `KeyError`, and any provider error raised by the transport.
- Retrying a request that timed out can send the same notification more than once, because the provider may have processed the first attempt. Combined with blocker 1, a 3s timeout against an 8s p99 turns many successful sends into up to 3 duplicate notifications.
- Bugs and bad payloads are now retried and delayed instead of failing immediately.

Fix: make the helper take the exception types to retry (or default to `ConnectionError`), and call it from `sender.send` with `ConnectionError`, as before.

### 3. Migration `0007_add_channel.sql` will fail or block production
- `ADD COLUMN channel text NOT NULL` has no `DEFAULT`. On a table that already has rows (about 40 million in production) PostgreSQL rejects it with a not-null violation, so the migration fails. If it were run against an empty table it would work, but production is not empty. Add a default, or add the column as nullable, backfill in batches, then add the `NOT NULL` constraint.
- `CREATE INDEX` without `CONCURRENTLY` takes a lock that blocks writes to `notifications` for the whole build. On 40M rows that can mean minutes of blocked inserts. Use `CREATE INDEX CONCURRENTLY`, in its own migration or otherwise outside a transaction.
- The migration is also unrelated to the stated refactor. It deserves its own PR so it can be reviewed, deployed and rolled back separately. Also confirm that nothing writes to the table without a `channel` value before this is deployed, since the `NOT NULL` column has no default and `sender.py` never sets `channel`.

## Non-blocking

- **Tests do not cover the changes.** `test_gives_up_after_three` passes before and after, so it does not show that behaviour is preserved. Add tests that a non-`ConnectionError` exception is not retried and that the timeout passed to `post` is the intended value (assert on the `timeout=` kwarg).
- **No test for the migration.** Check the migration against a table that already has rows.
- **Naming and cleanup.** The renames (`msg` to `message`, and so on) and the list comprehension in `send_batch` are fine. `MAX_ATTEMPTS` in `retry.py` could also move to settings if the aim is to centralize tunables.
- **Description.** `PR.md` should be corrected: this is not a pure refactor, and the migration, which the description mentions only in passing, needs its own explanation.

## Suggested path
1. Keep the refactor, restore the old timeout and the `ConnectionError`-only retry, and add tests for both.
2. Move the migration to a separate PR with a default or backfill plan and `CREATE INDEX CONCURRENTLY`.
