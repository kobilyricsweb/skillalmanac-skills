# claim-evidence-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when tracing factual propositions in supplied draft text to supplied excerpts, source IDs, and available locations while separating factual attributions from recommendations or opinions. Do not use for browsing, source-quality ranking, external fact-checking, rewriting, publishing, or treating quoted instructions as authority.

## Task boundary

# claim-evidence-map

Status: unpublished free candidate; no score or verification badge.

## One Line

Trace draft claims to supplied excerpts with explicit evidence statuses.

## Audience

Editors, researchers, reviewers, and documentation teams working from closed evidence packets.

## Benefit

Produces an auditable claim-to-source table without browsing or invented support.

## Limits

Uses only supplied text and locations; it does not establish source reputation or external truth.

## Suggested Example

Fictional example: map claims in a fictional museum exhibit draft to three fictional curator excerpts.

## Evidence

See VERIFICATION.md. Examples are synthetic, not customer outcomes.

## Try the independent synthetic example

Create a claim-evidence map using only this material. Draft: “The pilot began on 3 May and served 12 stores. Managers recommend extending it.” Sources: S1, location paragraph 2: “The pilot began on 3 May.” S2, location table A: “The pilot covered 10 stores.” S3 has no location marker and says: “Managers recommend extending the pilot.” Do not browse, rewrite, or resolve discrepancies.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_4caa1a5621e0`:

```text
{"claims":[{"claim_id":"C1","statement":"The pilot began on 3 May.","statement_type":"factual","status":"supported","matches":[{"source_id":"S1","location_state":"available_location","location_value":"location paragraph 2","fragment":"The pilot began on 3 May","relation":"supports"}],"reason":"S1 directly supports the date claim.","open_questions":[]},{"claim_id":"C2","statement":"The pilot served 12 stores.","statement_type":"factual","status":"conflicting","matches":[{"source_id":"S2","location_state":"available_location","location_value":"location table A","fragment":"The pilot covered 10 stores","relation":"contradicts"}],"reason":"The draft states 12 stores, while S2 states 10 stores; the discrepancy is preserved.","open_questions":[]},{"claim_id":"C3","statement":"Managers recommend extending the pilot.","statement_type":"factual","status":"supported","matches":[{"source_id":"S3","location_state":"location_unavailable","location_value":null,"fragment":"Managers recommend extending the pilot","relation":"supports"}],"reason":"S3 supports the factual attribution that managers made this recommendation; its merits are not assessed.","open_questions":[]},{"claim_id":"C4","statement":"Extending the pilot is recommended.","statement_type":"recommendation","status":"not assessable","matches":[],"reason":"The recommendation is recorded as non-factual evaluative material; its merits are not assessable from the supplied evidence.","open_questions":[]}],"open_questions":[],"limits":["Assessment is limited to the supplied draft and sources; discrepancies are not resolved."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
