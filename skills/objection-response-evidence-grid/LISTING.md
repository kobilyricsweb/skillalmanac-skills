# objection-response-evidence-grid

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when stated buyer objections must be paired with bounded responses, evidence IDs, limitations, explicit rejection of conflicting supplied claims, prohibited assurances, and useful next questions. Do not use for vendor evaluation, invented outcomes, dismissive rebuttals, or advice beyond supplied evidence.

## Task boundary

sales-call-prep-and-followup prepares sales conversations and customer-support-replies drafts support responses; this maps supplied objections to permitted evidence and bounded responses, without inventing guarantees.

## Try the independent synthetic example

Create an evidence grid. Objections: O1="Will this work for our two-person support team?"; O2="Can you guarantee setup by Friday?" Approved facts: F1="In supplied pilot note E1, one two-person support team completed the checklist without outside help."; F2="Setup time varies with data access." Evidence IDs: E1="pilot note"; E2="implementation note supporting F2". Known limitations: E1 describes one team and no general success rate; no Friday schedule evidence is supplied. Prohibited assurances: guaranteed outcomes and guaranteed completion dates. Ask a useful next question for each unresolved point.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_249a02b13374`:

```text
{"missing_inputs":[],"objections":[{"objection_id":"O1","objection":"Will this work for our two-person support team?","concern_acknowledgment":"The team-size concern is reasonable to clarify.","supported_response":"E1 reports that one two-person support team completed the checklist without outside help.","evidence_ids":["E1"],"limitation":"E1 covers one team and provides no general success rate.","prohibited_assurance_check":"prohibited assurance avoided","rejected_supplied_claims":[],"next_question":"Would you like evidence from additional two-person teams or a team-specific support assessment?","support_status":"partial"},{"objection_id":"O2","objection":"Can you guarantee setup by Friday?","concern_acknowledgment":"The requested schedule certainty depends on the available data access.","supported_response":"Setup time varies with data access, according to E2; no evidence supports a Friday guarantee.","evidence_ids":["E2"],"limitation":"No Friday schedule evidence is supplied.","prohibited_assurance_check":"prohibited assurance avoided","rejected_supplied_claims":[],"next_question":"What data access will be available, and what date should be assessed against it?","support_status":"partial"}],"unresolved_conflicts":[]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
