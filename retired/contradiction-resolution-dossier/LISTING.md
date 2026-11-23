# contradiction-resolution-dossier

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when supplied sources make a consequential claim that conflicts and a named resolver needs a focused decision packet. Do not use for broad consistency surveys, routine terminology edits, unsupported authority judgments, or choosing a winner without supplied precedence.

## Task boundary

Nearest is document-consistency-check; this packages one consequential contradiction for resolution rather than surveying consistency broadly.

## Try the independent synthetic example

Prepare a conflict dossier. Source S1, Policy v2 dated 2026-04-01: “Expense receipts are required for claims above $20.” Source S2, Team Guide v5 dated 2026-05-01: “Expense receipts are required for claims above $10.” Supplied precedence rule: the current Policy controls reimbursement requirements over team guides. Affected artifacts: claim form help text currently says “above $10”; onboarding checklist links to Team Guide v5. Named resolver: Finance Policy Owner. Determine the precedence result, inventory supplied impacts, and separate the resolver’s decision from later updates.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_5382d27c7939`:

```text
{"conflict_summary":"S1 and S2 specify different receipt thresholds for expense claims: above $20 versus above $10.","statements":[{"source_id":"S1","statement":"Expense receipts are required for claims above $20.","scope":"Expense reimbursement claims","metadata":{"policy":"Policy v2","date":"2026-04-01"}},{"source_id":"S2","statement":"Expense receipts are required for claims above $10.","scope":"Expense reimbursement claims","metadata":{"guide":"Team Guide v5","date":"2026-05-01"}}],"scope_comparison":"The supplied statements address the same reimbursement requirement and conflict on the threshold.","authority_analysis":"The supplied precedence rule states that the current Policy controls reimbursement requirements over team guides.","resolver":{"identity":"Finance Policy Owner","status":"supplied","gap":null},"precedence_status":{"status":"resolved","controlling_source":"S1","basis":"The current Policy controls reimbursement requirements over team guides; S1 is the supplied Policy and S2 is the Team Guide."},"affected_artifacts":["Claim form help text currently says \"above $10\".","Onboarding checklist links to Team Guide v5."],"decision_questions":["Should the Finance Policy Owner confirm that the claim form and onboarding materials should reflect Policy v2?"],"post_decision_actions":["After the resolver's decision, update the claim form help text as authorized.","After the resolver's decision, review the onboarding checklist link or guidance for alignment."],"verification_notes":["Both conflicting claims and their metadata are traceable to the supplied records.","The precedence conclusion uses only the supplied rule.","No document or policy was changed by this dossier."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
