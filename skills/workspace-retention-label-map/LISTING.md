# workspace-retention-label-map

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when supplied document-type definitions, approved labels, mapping rules, exclusions, and synthetic file descriptions must become a draft retention-label map with manual-review cases. Do not use for legal interpretation, taxonomy-gap analysis, file inspection, movement, deletion, retention-policy invention, or changing files.

## Task boundary

workspace-wiki-organizer organizes a workspace and notes-vault-organizer organizes notes; this only maps supplied document descriptions to a supplied retention label list, with exclusions and manual review, authorizing no file operation.

## Try the independent synthetic example

Create a draft map. Definitions: Signed order requires an order purpose and explicit signed status; Draft order requires an order purpose and explicit draft status. Approved labels: ORDER-FINAL, ORDER-DRAFT. Rules: M1 maps Signed order to ORDER-FINAL; M2 maps Draft order to ORDER-DRAFT. Exclusions: training samples require manual review. Conflict policy: signed and draft cues together require manual review. Missing cues remain unresolved. Synthetic descriptions: A: "Purchase order; status signed." B: "Purchase order; status draft." Return mappings, defining cues, assigned supplied labels, applicable rules, conflicts, exclusions, approved-label checks, unresolved queue, and rule register. Do not alter files or infer retention periods.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_82d63a34fc5b`:

```text
{"mappings":[{"document_description":"Purchase order; status signed.","candidate_type":"Signed order","defining_cues":["Order purpose","Explicit signed-status cue"],"assigned_label":"ORDER-FINAL","applicable_rule":"M1","conflict":null,"exclusion":false,"manual_review":false},{"document_description":"Purchase order; status draft.","candidate_type":"Draft order","defining_cues":["Order purpose","Explicit draft-status cue"],"assigned_label":"ORDER-DRAFT","applicable_rule":"M2","conflict":null,"exclusion":false,"manual_review":false}],"approved_label_check":[{"label":"ORDER-FINAL","approved":true},{"label":"ORDER-DRAFT","approved":true}],"unresolved_queue":[],"rule_register":[{"rule_id":"M1","rule":"Signed order maps to ORDER-FINAL."},{"rule_id":"M2","rule":"Draft order maps to ORDER-DRAFT."}],"exclusion_register":[{"exclusion_id":null,"exclusion":"Training samples require manual review."}],"decision_summary":"Both synthetic descriptions include an order purpose and one explicit status cue; each maps under its supplied rule. Signed-and-draft conflicts and missing cues remain unresolved.","operative_authorization":false}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
