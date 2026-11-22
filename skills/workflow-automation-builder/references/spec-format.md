## Contents

- Top-level fields
- Trigger
- Steps
- on_error
- Rule table W000 to W017

# Spec format

The validator reads one JSON object. Unknown keys are allowed and ignored, so notes can be added anywhere.

## Top-level fields

| Field | Meaning |
|---|---|
| `name`, `purpose` | Short name and one sentence on what the workflow achieves. |
| `owner`, `alert_channel` | A person or on-call alias, and where alerts go. Both are warned about when missing. |
| `concurrency` | `{"max_parallel_runs": n}`. Counts as a workflow-wide rate guard for rule W011. |
| `dead_letter` | `{"destination", "fields", "retention_days"}`. Required when any step says `then: dead_letter`. Store a reference to the payload, not secrets. |
| `defaults.on_error` | An `on_error` block applied to every step that has none of its own. |
| `trigger` | See below. |
| `steps` | Non-empty list of step objects. |

## Trigger

`type` is `webhook`, `schedule`, `poll` or `event`. `next` is the first step id. `dedupe_key` is a template built from the sender's event id. `verify` is `hmac_signature` or `shared_secret_header` for webhooks. `cursor` names the field that marks progress for a `poll` trigger.

## Steps

Every step has a unique string `id`, a `type` and a flow field.

| Type | Extra fields |
|---|---|
| `filter` | `condition`; `next` for pass; `on_reject` for the reject path (null means stop quietly, which is fine for a filter). |
| `action` | `kind` is `read` or `write`; `config` (method, url, headers, body); `timeout_seconds`; `rate_limit {max_per_minute}`; `idempotency_key`; `naturally_idempotent` (true plus a note, when the target upserts by key); `on_error`. A `config.method` of POST, PUT, PATCH or DELETE counts as a write even without `kind`. |
| `branch` | `branches`: list of `{"when", "next"}`; `else`. |
| `loop` | `over` (the list); `loop {max_iterations, exit_when}`; `body` (first step of the loop body); `next` (step after the loop). The last body step may point back at the loop id or end with null. |
| `delay` | `seconds`. |
| `transform` | `config`; `on_error`. |

Flow: `next` is a step id, a list of ids, or null (end of this path).

## on_error

```
"on_error": {
  "retry": {"max_attempts": 4, "backoff": "exponential_jitter", "initial_seconds": 2, "max_seconds": 300},
  "then": "dead_letter",
  "fallback_step": "id of a step"
}
```

`then` is required: `dead_letter`, `alert_stop` (stop the run and alert) or `fallback` (needs `fallback_step`). `skip`, `ignore` and `continue` are recognised only to be flagged. `backoff` is `exponential_jitter`, `exponential` or `fixed`.

## Rule table

| Rule | Severity | Fires when |
|---|---|---|
| W000 | error | Spec shape is wrong: not an object, no steps, bad trigger, step without id or with an unknown type |
| W001 | error for actions, warning for transform and loop | Step has no `on_error` and no `defaults.on_error` |
| W002 | error | Loop without a positive integer `max_iterations`, with neither `over` nor `exit_when`, without `body`, or a cycle not passing through such a loop. Warning above 1,000 iterations |
| W003 | error | A sensitive-named field (password, token, key, authorization, secret and similar) holds a literal instead of `{{secrets.X}}`, or a value matches a credential pattern (AWS key id, private key block, `sk-` token, GitHub token, chat token, chat webhook URL, URL with user and password, JWT, secret in a query string) |
| W004 | error / warning | Write action without `idempotency_key` (error), or a write that retries without one (error), or a constant key with no template (warning) |
| W005 | error | Step cannot be reached from the trigger |
| W006 | error | A flow field names a step that does not exist |
| W007 | error | Duplicate step id |
| W008 | error / warning | Retry without a positive integer `max_attempts` or above 10 (error); backoff missing or unknown (warning) |
| W009 | warning | No `trigger.dedupe_key` |
| W010 | error / warning | `then` missing or invalid (error); `skip`, `ignore`, `continue` (error on a write, warning otherwise); `dead_letter` without a top-level destination (error); `fallback` without `fallback_step` (error) |
| W011 | warning | Action has no `rate_limit` and the workflow has no `concurrency` |
| W012 | warning | No `owner` or no `alert_channel` |
| W013 | warning | Action with no `kind` and no method: cannot tell if it writes, so write checks are skipped |
| W014 | warning | Write inside a loop whose key does not mention the loop item, loop or index |
| W015 | warning | Webhook trigger with no `verify` |
| W016 | warning | Action without `timeout_seconds` |
| W017 | warning | Poll trigger without `cursor` |
