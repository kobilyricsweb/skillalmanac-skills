# decision-evidence-ledger

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when supplied decision records mix final decisions, proposals, assumptions, evidence, unresolved authority, or genuinely incompatible accounts that need a traceable ledger. Do not use for meeting minutes, choosing among options, or treating a superseded proposal as a factual conflict with an authorized decision.

## Task boundary

decision-council deliberates on options; this records decisions, proposals, evidence and incompatible accounts from supplied notes without deliberating or selecting an option. source-note-to-outline organizes content and approval-path-mapper models approval rules.

## Try the independent synthetic example

Create a decision-evidence ledger from these supplied notes. Scope: choose exactly one launch channel. S1: Niko proposed kiosk. S2: the test report recorded web loading in 2 seconds and kiosk in 5 seconds. S3: Leah is the authorized final approver for launch channel. S4: on 3 June, Leah approved web and said the test report was her rationale. Preserve entries, relations, conflicts, open questions, and missing facts. Do not choose a different channel or add evidence.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_996d0dd1d6fd`:

```text
{"title":"Launch channel decision ledger","source_scope":"Supplied notes S1-S4 concerning selection of exactly one launch channel","entries":[{"id":"E1","classification":"proposal","statement":"Niko proposed kiosk.","status_finality":"proposed","authority":"not stated","time":"not stated","source_reference":"S1","classification_basis":"S1 explicitly reports a proposal."},{"id":"E2","classification":"evidence","statement":"The test report recorded web loading in 2 seconds and kiosk loading in 5 seconds.","status_finality":"evidentiary","authority":"not stated","time":"not stated","source_reference":"S2","classification_basis":"S2 reports test observations."},{"id":"E3","classification":"unknown","statement":"Leah is the authorized final approver for launch channel.","status_finality":"unknown","authority":"Leah is stated to hold scope-specific authority.","time":"not stated","source_reference":"S3","classification_basis":"S3 establishes authority but is not itself an approval."},{"id":"E4","classification":"decision","statement":"Leah approved web as the launch channel and said the test report was her rationale.","status_finality":"final","authority":"Leah is established as the authorized final approver by S3.","time":"3 June","source_reference":"S4","classification_basis":"S4 reports approval; S3 establishes relevant authority."}],"relations":[{"source_id":"E2","target_id":"E4","relation":"rationale_for","basis":"S4 explicitly identifies the test report as Leah's rationale."},{"source_id":"E1","target_id":"E4","relation":"related_context","basis":"Both concern the launch-channel choice; S1 is a proposal and S4 is an authorized decision."}],"conflicts":[],"open_questions":[{"id":"Q1","text":"Which test-report details beyond loading times informed the approval, if any?","source_reference":"S2-S4","related_ids":["E2","E4"]}],"coverage_notes":["Web is the sole final launch-channel decision supplied.","No conflict is recorded because the kiosk statement is a proposal, not an incompatible authorized decision."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
