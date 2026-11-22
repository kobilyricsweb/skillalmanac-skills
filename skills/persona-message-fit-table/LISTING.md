# persona-message-fit-table

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when explicitly assigned audience-profile needs must be compared with approved message options, evidence notes, exclusions, and permitted CTAs in a traceable fit table. Do not use for inventing profile-to-need assignments, sequencing content, inferring motivation, predicting conversion, or making unsupported market-behavior claims.

## Task boundary

copywriting-landing-pages and paid-ads-builder write or audit promotional messaging for deployment contexts. persona-message-fit-table writes no copy and predicts no performance; it traces approved messages, evidence, exclusions, and permitted CTAs across only explicitly assigned profile-and-need pairs.

## Try the independent synthetic example

Create a persona-message fit table using only these inputs. Profiles: P-A has the supplied attribute “coordinates weekly volunteer shifts”; P-B has “reviews monthly expense reports.” Needs: N-A “see uncovered shifts”; N-B “identify reports awaiting review.” Explicit profile-to-need assignments: P-A is assigned N-A; P-B is assigned N-B. Messages: M-A “See uncovered shifts on one board”; M-B “Receive automatic tax advice”; M-C “View reports awaiting review.” Evidence: E-A supports M-A’s board claim; E-C supports M-C’s awaiting-review claim. Exclusions: M-B is excluded for every profile because tax advice is outside product scope. Allowed CTAs: P-A/N-A may use “Open the scheduling guide”; P-B/N-B may use “Open the review guide.” Decide matches, blocked candidates, unmatched messages, and need coverage without inferring motivations or performance.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_43ab592dfb69`:

```text
{"artifact_status":"complete","missing_required_fields":[],"fit_rows":[{"profile_id":"P-A","need_id":"N-A","message_id":"M-A","match_status":"matched","rationale":"M-A directly addresses seeing uncovered shifts, and E-A supports its board claim.","evidence_references":["E-A"],"disqualifier":null,"permitted_cta":"Open the scheduling guide","unresolved_gap":null},{"profile_id":"P-A","need_id":"N-A","message_id":"M-B","match_status":"blocked","rationale":"M-B concerns tax advice, which is excluded for every profile.","evidence_references":[],"disqualifier":"Tax advice is outside product scope.","permitted_cta":"Open the scheduling guide","unresolved_gap":null},{"profile_id":"P-A","need_id":"N-A","message_id":"M-C","match_status":"unmatched","rationale":"M-C addresses reports awaiting review, not uncovered volunteer shifts.","evidence_references":[],"disqualifier":null,"permitted_cta":"Open the scheduling guide","unresolved_gap":null},{"profile_id":"P-B","need_id":"N-B","message_id":"M-A","match_status":"unmatched","rationale":"M-A addresses uncovered shifts, not reports awaiting review.","evidence_references":[],"disqualifier":null,"permitted_cta":"Open the review guide","unresolved_gap":null},{"profile_id":"P-B","need_id":"N-B","message_id":"M-B","match_status":"blocked","rationale":"M-B concerns tax advice, which is excluded for every profile.","evidence_references":[],"disqualifier":"Tax advice is outside product scope.","permitted_cta":"Open the review guide","unresolved_gap":null},{"profile_id":"P-B","need_id":"N-B","message_id":"M-C","match_status":"matched","rationale":"M-C directly addresses reports awaiting review, and E-C supports that claim.","evidence_references":["E-C"],"disqualifier":null,"permitted_cta":"Open the review guide","unresolved_gap":null}],"unmatched_messages":[],"uncovered_needs":[],"gaps":[]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
