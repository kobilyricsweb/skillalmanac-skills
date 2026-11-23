# content-refresh-plan

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when planning bounded offline updates to a supplied existing page from supplied evidence, with section-level actions, impact, locations, and verification gaps. Do not use for browsing, speculative SEO scoring, full rewriting, publishing, or treating absent evidence alone as a reason to remove or verify existing content.

## Task boundary

document-consistency-check compares peer assertions, claim-evidence-map links claims to evidence and evidence-expiry-review-queue schedules evidence review; this plans section-level actions on a supplied existing page from supplied new evidence.

## Try the independent synthetic example

Create an offline refresh plan. Existing page: section A [anchor pricing]: “The basic plan includes 2 projects.” Section B [anchor support]: “Email support is available.” New evidence: E1, release note paragraph 3: “The basic plan now includes 3 projects.” E2, policy paragraph 1: “Email support remains available.” User-impact criterion: changes affecting included capacity are high priority; confirmed unchanged details are low priority. Do not write replacement copy or edit the page.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_c1413a779077`:

```text
{"changes":[{"change_id":"CH1","location":"pricing","location_type":"supplied","current_summary":"The basic plan includes 2 projects.","action":"update","evidence_references":["E1, release note paragraph 3"],"user_impact":"Included capacity changed; high impact.","priority":"high","readiness":"proposed","verification_gap":null,"notes":"Evidence supports updating the stated project count to 3; replacement copy is out of scope."},{"change_id":"CH2","location":"support","location_type":"supplied","current_summary":"Email support is available.","action":"retain","evidence_references":["E2, policy paragraph 1"],"user_impact":"Confirmed unchanged detail; low impact.","priority":"low","readiness":"proposed","verification_gap":null,"notes":"No content change is indicated."}],"open_questions":[],"exclusions":["Replacement copy, page editing, publishing, and additional verification are out of scope."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
