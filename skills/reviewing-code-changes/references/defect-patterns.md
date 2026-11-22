# Defect patterns by change type

Read the section that matches the change. Each line is a question to answer from the code, not a finding to paste.

## Contents

- Changed function or interface
- Request handlers and endpoints
- Data access and queries
- Schema and data migrations
- Refactors described as behaviour-preserving
- Error handling and retries
- Concurrency and ordering
- Money, time and units
- Configuration, flags and dependencies
- Tests

## Changed function or interface

- Did the return type, unit or scale change (percent to fraction, seconds to milliseconds, cents to dollars, list to iterator, value to optional)? Every caller must change with it.
- Did parameter order or a default change? Positional callers break silently.
- Is the symbol re-exported, aliased, looked up by name, or used from another language or service?
- Did an exception type or an error return change? Who catches the old one?
- Is there a serialised form (JSON field, database column, cache entry, message) that older code or data still holds?

## Request handlers and endpoints

- Authentication: does the route require it like its siblings?
- Authorisation: an id in the path or body means an ownership or role check. Compare with the neighbouring routes and use the repo's own guard.
- Input: are numbers parsed and bounded (NaN, negative, zero, huge)? Are strings length-limited?
- Pagination: first page offset is zero. Check `(page - 1) * size`, the default page, and the upper bound on size.
- Output: does the response leak fields (password hashes, internal ids, other tenants' rows)?
- Errors: does a failure return the right status, or fall through to success?
- Side effects before validation: is anything written or charged before the request is known to be valid?

## Data access and queries

- Any query built with string concatenation, interpolation or formatting from request data is an injection; use parameters.
- N+1: a query inside a loop over query results.
- Missing tenant or user filter on a list query.
- Unbounded result sets; missing `LIMIT`.
- A read-modify-write without a transaction or a conditional update.
- Several writes that must succeed together but are not in one transaction.

## Schema and data migrations

- `ADD COLUMN ... NOT NULL` without a default fails on a table that has rows. Safe order: add nullable, backfill in batches, then add the constraint.
- Building an index without the engine's online option locks writes for the duration on a large table; online builds usually cannot run inside a transaction and need their own migration.
- Dropping or renaming a column or table while deployed code still reads it: needs expand, migrate, contract across releases.
- Changing a column type can rewrite the table and hold a lock.
- Is there a down migration, and does it really reverse the change?
- Deploy order: does new code need the migration first, or old code survive it? State which.
- Backfills inside a schema migration: long transactions, replication lag.
- Does the description call it what it is? "Adds an index" that also changes the schema is a finding.

## Refactors described as behaviour-preserving

The claim is checkable. Compare old and new for:

- Constants and defaults moved between files: is the value identical?
- Exception handling moved into a helper: is the caught type the same width?
- Loop and retry bounds: same count, same condition (`>=` against `>`), same delay.
- Order of side effects; early returns added or removed.
- Conditions rewritten: negations, `and`/`or`, off-by-one on boundaries.
- Visibility: something private made importable and now part of the interface.
- Log lines, metrics names and error messages that monitoring or callers match on.

Any difference is either a bug or an undisclosed behaviour change. Both get reported.

## Error handling and retries

- Empty or log-only catch blocks: what state is left when the call fails? Does the code go on to record success?
- Catching the base exception type: programming errors and cancellations get swallowed or retried.
- Retrying a non-idempotent call (send, charge, create) after a timeout can do it twice; is there an idempotency key?
- A timeout shorter than the dependency's normal latency turns successes into failures; look for stated latency in docs or config.
- Resources released on the error path (connections, locks, files, temp data).

## Concurrency and ordering

- Check-then-act on shared state (exists? then create; balance >= x? then debit).
- Shared mutable module state touched from request handlers.
- Missing `await` on a promise whose failure matters; fire-and-forget writes.
- Lock ordering, and locks held across network calls.
- Cache invalidation: is the cache updated or cleared on every write path the change adds?

## Money, time and units

- Floating point used for money; rounding direction; integer division on amounts.
- Currency assumed; mixed units in one calculation.
- Time zones: naive datetimes, local time for stored values, day boundaries, daylight saving.
- Inclusive against exclusive ranges; "older than 90 days" at the boundary.

## Configuration, flags and dependencies

- New config key: is there a default, is it documented, is it set in every environment file?
- Feature flag: what happens when it is off, and is the old path still tested?
- Dependency added or bumped: major version, licence, lockfile updated with the manifest.
- Secrets or tokens in code, tests, fixtures or logs.

## Tests

- Assertion weakened (exact value to existence check).
- Test deleted or skipped without the behaviour being removed.
- Test that cannot fail: asserts inside a loop over an empty collection, a mock that replaces the code under test, a patched name that the code no longer uses.
- New behaviour and new error paths with no test.
- The unhappy cases: empty input, boundary, unauthorised caller, dependency failure.
