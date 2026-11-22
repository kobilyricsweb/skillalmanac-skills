# revision-rationale-log

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when documenting observable substantive changes between supplied before-and-after passages and linking each change to supplied style or evidence rules, including verification of protected text. Do not use for glossary-only edits, inventing author intent, rewriting or overriding protected quotations, approving revisions, or claiming unsupported impact.

## Task boundary

natural-prose-editor edits prose; this edits nothing and logs supplied before/after changes against supplied rules. decision-evidence-ledger records decisions and evidence; this preserves visible textual changes and unresolved author intent.

## Try the independent synthetic example

Create a revision log from this complete synthetic record. Location A2 before: “The kit prevents all delays.” Location A2 after: “The kit may reduce packing delays.” Style rule S1: qualify outcomes that are not guaranteed. Evidence note E1: the trial observed fewer packing delays but did not test other delays. Source label: E1. Protected quotation at A3: “Pack light.” It is unchanged. The A2 revision is approved. Report the visible change at the smallest meaningful unit, its supported rationale and source, protection result, decision status, and any unresolved impact. Do not assess truth beyond these supplied facts.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_exec_medium_289d7b7c4248`:

```text
{"entries":[{"location":"A2","original_text":"The kit prevents all delays.","revised_text":"The kit may reduce packing delays.","change_type":["scope","qualification","evidence_alignment"],"rationale":"The revision removes the guarantee and limits the claim to packing delays, matching S1 and E1, which observed fewer packing delays but did not test other delays.","source":"E1; S1","protected_text_result":"not_protected","decision_status":"approved","unresolved_impact":"Effects on delays other than packing delays were not tested."}],"unresolved_impacts":["No conclusion is supplied about delays beyond packing delays."],"protected_text_verification":[{"location":"A3","protected_text":"Pack light.","result":"unchanged","note":"Protected quotation is unchanged."}]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
