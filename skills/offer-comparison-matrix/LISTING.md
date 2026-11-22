# offer-comparison-matrix

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when comparing supplied internal offers by aligned audience, promise, assets, friction, evidence, and unresolved distinctions. Do not use for competitor research, market or demand estimation, pricing optimization, copywriting, or selecting an unsupported winner.

## Task boundary

landing-page-message-sequencer orders approved messages and message-asset-reuse-map plans reuse; this aligns supplied offers on comparable attributes, evidence and unknowns without choosing an unsupported winner.

## Try the independent synthetic example

Create an internal offer comparison. Focus Session: audience is managers with approved projects; promise is "Produce a reviewed project outline"; assets are a worksheet and review call; proof is one internal record showing the worksheet was completed, source: Program Office, 2026-10-02; friction is scheduling; constraint is approved projects only. Starter Notes: audience is any employee; promise is "Provide prompts for drafting an outline"; asset is a prompt sheet; proof is the prompt sheet itself, owner: Enablement, date not supplied; friction is independent drafting; no constraint supplied. Compare audience eligibility, promise coverage, assets, and proof. Known unknown: whether the review call has ever been completed. Do not select a winner or recommend pricing.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_c864bb4806b3`:

```text
{"offers":[{"name":"Focus Session","audience":"managers with approved projects","promise":"Produce a reviewed project outline","included_assets":["worksheet","review call"],"proof_items":[{"item":"Worksheet was completed","source_note":"Program Office, 2026-10-02"}],"proof_status":"partial","friction":["scheduling"],"testable_distinctions":["review call versus independent prompt use","approved-project eligibility versus any employee eligibility"],"constraints":["approved projects only"],"unresolved_items":["Whether the review call has ever been completed; supplied proof covers worksheet completion, not the complete reviewed-outline promise."]},{"name":"Starter Notes","audience":"any employee","promise":"Provide prompts for drafting an outline","included_assets":["prompt sheet"],"proof_items":[{"item":"Prompt sheet itself","source_note":"Enablement; date not supplied"}],"proof_status":"partial","friction":["independent drafting"],"testable_distinctions":["prompt sheet versus worksheet plus review call","any employee eligibility versus approved-project eligibility"],"constraints":["not supplied"],"unresolved_items":["Whether the prompt sheet enables the stated drafting promise beyond its existence."]}],"cross_offer_summary":{"supplied_contrasts":["Focus Session is for managers with approved projects and includes a worksheet plus review call; Starter Notes is for any employee and includes a prompt sheet.","Focus Session has scheduling friction; Starter Notes has independent-drafting friction."],"evidence_gaps":["Focus Session proof addresses worksheet completion only; review-call completion is unknown.","Starter Notes proof is the prompt sheet itself and does not establish drafting results."],"conflicts":[]},"outside_scope":["Selecting a winner and recommending pricing are outside scope."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
