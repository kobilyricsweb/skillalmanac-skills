# Worked Example

Synthetic example; values and effects are invented solely for this example.

Input:

Before: `REQUEST_TIMEOUT=10`, `CACHE_MODE=local`, `OLD_FLAG=on`.

After: `REQUEST_TIMEOUT=30`, `CACHE_MODE=distributed`, `NEW_FLAG=on`.

A supplied note says `OLD_FLAG` and `NEW_FLAG` might represent the same setting, but the mapping is unconfirmed. Supplied group labels: Behavior (timeout/cache keys), Lifecycle (flag keys).

Behavior notes: `REQUEST_TIMEOUT` controls client wait duration; `CACHE_MODE=distributed` uses the shared cache; `OLD_FLAG` is no longer referenced according to a supplied application note. Deployment notes: timeout change requires a restart; rollback is restoring the prior snapshot.

Expected artifact decisions:

- Behavior: `REQUEST_TIMEOUT` changed `10→30`; both presence flags are true. Its documented purpose is client wait duration; directional effect is unknown because units and ordering semantics are absent; restart and rollback are documented.
- Behavior: `CACHE_MODE` changed `local→distributed`; both presence flags are true. The documented effect is shared-cache use; deployment impact otherwise remains unknown.
- Lifecycle: `OLD_FLAG` is removed with `before_present: true`, `before: "on"`, `after_present: false`, and `after: null`. The null is only the absent-side placeholder, not an observed after value. The supplied note does not establish universal safe deletion.
- Lifecycle: `NEW_FLAG` is added with `before_present: false`, `before: null`, `after_present: true`, and `after: "on"`. No behavior or rollout effect is supplied.
- `alignments` separately records `removed_key: "OLD_FLAG"`, `added_key: "NEW_FLAG"`, `status: "unconfirmed"`, and the supplied note as its basis. The removal and addition remain in `changes`.

The artifact must not claim that the timeout caused latency, that distributed caching improves performance, that the removed flag is universally safe to delete, or that the two flag names are a confirmed rename.
