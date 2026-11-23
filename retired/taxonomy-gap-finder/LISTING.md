# taxonomy-gap-finder

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when reviewing assignment coverage, explicit membership conflicts, and definition-quality gaps in a supplied taxonomy snapshot, including incompatibilities stated inside category definitions. Do not use for validating parent-child graphs, researching demand, creating or ranking categories, or silently assigning unclassified items.

## Task boundary

taxonomy-structure-check detects graph defects; this maps supplied content needs to category coverage and proposes gaps without treating a structurally valid taxonomy as complete.

## Try the independent synthetic example

Review this taxonomy snapshot. Items: P1 “paper guide”, P2 “audio guide”, P3 “mixed kit”. Categories: C1 “Printed materials”; C2 “Audio recordings”. Assignments: P1→C1, P2→C2, P3→C1, P3→C2. Constraint: C1 and C2 are mutually exclusive, and every item requires an assignment. Review scope: all supplied items and categories. Do not create classifications.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_exec_medium_b96f7f6425df`:

```text
{"scope":{"item_ids":["P1","P2","P3"],"category_ids":["C1","C2"],"rules":["C1 and C2 are mutually exclusive.","Every item requires an assignment."]},"definition_coverage":[{"category_id":"C1","definition":"Printed materials","status":"unknown_without_standard"},{"category_id":"C2","definition":"Audio recordings","status":"unknown_without_standard"}],"item_coverage":[{"item_id":"P1","assigned_category_ids":["C1"],"status":"assigned","basis":"Supplied assignment P1 to C1."},{"item_id":"P2","assigned_category_ids":["C2"],"status":"assigned","basis":"Supplied assignment P2 to C2."},{"item_id":"P3","assigned_category_ids":["C1","C2"],"status":"conflicting","basis":"Both assignments are supplied, and C1 and C2 are explicitly mutually exclusive."}],"unassigned_items":[],"conflicting_memberships":[{"item_id":"P3","category_ids":["C1","C2"],"violated_rule":"C1 and C2 are mutually exclusive."}],"weak_definition_findings":[],"unresolved_questions":["No definition-quality standard was supplied."],"excluded_checks":["Parent-graph validation","New classification creation"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
