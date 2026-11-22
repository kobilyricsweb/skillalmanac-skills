---
name: workflow-automation-builder
description: Designs a no-code or low-code automation (trigger, filter, actions) that does not fail silently, as a JSON spec with idempotency keys, retry and dead-letter rules, secret references, rate limits, a synthetic-event test plan and a runbook, then checks the spec with a validator script. Use when someone wants to automate a business process, connect apps, build a zap, scenario or flow, or asks why an automation double-posts, drops records or stopped running. Do not use for writing application code, API integrations in code, RPA screen-scraping bots, or auditing delivery logs of a running webhook.
license: Apache-2.0
compatibility: The validator needs Python 3.9 or newer, standard library only, no network. Without Python, apply the rule table in references/spec-format.md by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Workflow automation builder

Produce a design that an ops person can build in any visual automation tool and that tells a human when it breaks. The product is a spec file, a test plan and a runbook, not a build in a specific tool. Every write needs an idempotency key, every failure needs a destination, and every number below is a default to change only with a stated reason.

## Workflow

```
- [ ] 1 Intake (6 answers or stated assumptions)
- [ ] 2 Draft the spec from assets/workflow-spec-template.json
- [ ] 3 Apply the design defaults
- [ ] 4 Validate, fix, re-validate
- [ ] 5 Write the test plan with synthetic events
- [ ] 6 Write the runbook
- [ ] 7 Report
```

1. **Intake.** Get these, or write each unanswered one down as an assumption in the report: (a) the trigger source and whether it delivers at least once, (b) peak events per minute and per day, (c) every side effect and whether it can be undone, (d) the documented rate limit of each downstream service, (e) who is alerted and where, (f) which fields are personal or financial data. Do not ask for credentials, keys or tokens; the design only names where they will be stored.
2. **Draft.** Copy `assets/workflow-spec-template.json`, rename it, and keep its structure. Field meanings and the rule table are in [references/spec-format.md](references/spec-format.md); read it before editing anything unusual (branches, fallback steps, polling).
3. **Apply the defaults** from the table below, then the extra defaults in [references/design-rules.md](references/design-rules.md) (read the sections for idempotency key recipes, rate-limit arithmetic and secrets when the workflow has writes, bursts or credentials).
4. **Validate.** Run `python scripts/validate_workflow.py <spec.json>`. Fix every `error`. Fix each `warning` or write one line in the report saying why it stays. Re-run until `"ok": true`. Do not edit the script to make a spec pass.
5. **Test plan.** Use the ten synthetic events in [references/design-rules.md](references/design-rules.md), section "Synthetic events". Name the exact payload field changed for each, the expected result, and where to look to see it. Run it in a test copy with the real writes pointed at a sandbox target or a dry-run flag; never replay synthetic events against production.
6. **Runbook.** Fill the template in the same reference: alerts, first five minutes, replay of dead letters, kill switch, rotation. One page.
7. **Report** in the fixed shape below.

## Design defaults

| Topic | Default | Change only when |
|---|---|---|
| Retry count | 4 attempts, exponential backoff with jitter, start 2 s, cap 300 s | the downstream documents its own advice |
| Retry which errors | network errors, timeouts, 408, 425, 429, 500, 502, 503, 504 | never retry 400, 401, 403, 404, 409, 422: send to dead letter or alert |
| 429 | wait the `Retry-After` value if present, else the backoff | - |
| After last retry | `dead_letter` for writes, `alert_stop` for a step whose output is needed next | never `skip` on a write |
| Idempotency key | `<trigger event id>-<step id>`, plus `-<item id>` inside a loop | the target upserts by a natural key (set `naturally_idempotent`) |
| Dedupe store | keep keys at least as long as the sender's longest retry window; 7 days when unknown | - |
| Rate | sustained rate at most half the documented quota; concurrency = ceil(peak events per second x p95 seconds per run) | the quota is shared with other tools: halve again |
| Timeout | 10 to 30 s per call; a hung call counts as a failure | file uploads, long exports |
| Loops | `max_iterations` = 2 x the largest legitimate batch, never above 1,000 without a filter | - |
| Polling | store a cursor; re-read an overlap of 2 x the poll interval; rely on the dedupe key for the repeats | - |
| Webhook in | verify a signature or shared secret header; reject on mismatch before any step runs | the sender cannot sign: allow-list its addresses and say so |
| Secrets | only `{{secrets.NAME}}` references in the spec; one secret per service and per environment; rotate every 90 days; 401 or 403 alerts the owner at once | - |
| Silent-stop watch | scheduled triggers alert when no run started in 2 x the interval | - |

## Report shape

```
Workflow: <name>, trigger <type>, <n> steps, <n> writes
Validator: ok <true|false>, errors <n>, warnings <n> (kept: <rule ids and reason>)
Assumptions: <unanswered intake items>
Failure map: <for each write step: what happens on duplicate, on 429, on permanent failure>
Test plan: <file or section>; Runbook: <file or section>
Not checked: <e.g. real quota values, platform support for each field, sandbox availability>
```

Give the spec file first; keep the report under 25 lines.

## Scripts and files

- `scripts/validate_workflow.py <spec.json>`: run it, do not edit it. Prints one JSON object (`ok`, `summary`, `findings` with rule, severity, step, path, message, fix). Reads one file, writes nothing, no network. Exit 0 no errors, 1 errors, 2 unreadable file or invalid JSON. Secret values are redacted in its output; if it reports one, treat that credential as exposed and rotate it.
- `assets/workflow-spec-template.json`: a spec that validates clean; copy and edit.
- [references/spec-format.md](references/spec-format.md): field meanings and the rules W000 to W017.
- [references/design-rules.md](references/design-rules.md): idempotency recipes, rate arithmetic, secrets, synthetic events, runbook template.

## Boundaries

- The spec is vendor-neutral. Before promising a feature (per-step retry, a dedupe store, secret storage), tell the user to confirm their tool has it, and name the workaround if not (for example an extra lookup step against a table of processed ids).
- Do not build against production accounts, send test messages to real customers, or run replays without the user's go-ahead.

## Limits

- The validator checks the design file, not the live automation: a step can pass and still be built wrongly.
- It cannot tell whether an idempotency key really identifies one business event, only that one exists, is not constant and varies per loop item.
- Thresholds (4 attempts, 10 maximum, 1,000 iterations, half the quota) are working defaults, not measured optima.
- It reads JSON only; convert YAML or exported flow files into the spec shape by hand.
- Quota and retry-window figures must come from the user's services; the skill does not look them up.
