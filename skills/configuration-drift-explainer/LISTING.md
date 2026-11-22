# configuration-drift-explainer

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when explaining differences between supplied redacted before-and-after configuration snapshots with supplied behavior, deployment, rollback, and alignment notes. Do not use for live inspection, secret discovery, required-key validation, causal incident analysis, migration, or deployment execution.

## Task boundary

configuration-key-drift-check executes a strict key inventory check; this explains supplied drift observations, impact hypotheses and verification questions without executing or certifying configurations.

## Try the independent synthetic example

Explain this offline configuration drift. Before: {"TIMEOUT":2,"LOG":"brief","LEGACY":true}. After: {"TIMEOUT":3,"LOG":"brief","CACHE":false}. Behavior notes: TIMEOUT is the request wait limit; CACHE=false disables the local cache. No behavior note exists for LEGACY. Deployment notes: TIMEOUT changes require restart; rollback for TIMEOUT is restoring 2 and restarting. No rollback information exists for CACHE or LEGACY. Group labels: TIMEOUT=traffic, CACHE=storage, LEGACY=release. Separate observations from documented consequences and do not infer incident causality.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_682193f83e56`:

```text
{"scope":"Offline comparison of the supplied before-and-after snapshots.","changes":[{"key":"TIMEOUT","change_type":"changed","before_present":true,"before":2,"after_present":true,"after":3,"behavior":"The supplied note says TIMEOUT is the request wait limit.","behavior_status":"documented","deployment_impact":"documented","reversibility":"documented","group":"traffic"},{"key":"LEGACY","change_type":"removed","before_present":true,"before":true,"after_present":false,"after":null,"behavior":"","behavior_status":"unknown","deployment_impact":"not-supplied","reversibility":"unknown","group":"release"},{"key":"CACHE","change_type":"added","before_present":false,"before":null,"after_present":true,"after":false,"behavior":"The supplied note says CACHE=false disables the local cache.","behavior_status":"documented","deployment_impact":"not-supplied","reversibility":"unknown","group":"storage"}],"alignments":[],"deployment_notes":["TIMEOUT changes require restart.","Rollback for TIMEOUT is restoring 2 and restarting."],"unresolved":["No behavior, deployment, or rollback information is supplied for LEGACY.","CACHE=false is documented as disabling the local cache; no causal or incident conclusion is supplied."],"inspection_status":"offline-only","acceptance_checks":["Every added, removed, or unequal key is represented once.","Unchanged LOG is excluded from changes.","Supplied behavior and deployment notes are separated from observations.","No incident causality or live action is claimed."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
