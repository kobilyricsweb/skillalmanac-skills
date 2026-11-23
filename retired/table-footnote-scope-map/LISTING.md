# table-footnote-scope-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when a supplied report table contains footnote markers and definitions whose applicability may be cell-, row-, column-, or table-level, and you need an auditable scope map. Do not use for extracting table content, formatting references, validating claims, or inferring qualifier inheritance from marker placement alone.

## Task boundary

reference-list-formatter formats references, pdf-extraction-and-forms extracts source content, document-template-field-map binds placeholders and claim-evidence-map checks entailment; this maps qualifier applicability within an already supplied table.

## Try the independent synthetic example

Create an auditable qualifier-scope map for this table only. Table: Support options. Headings: H1 = Tier, H2 = Email‡, H3 = Phone. R1L = Starter; R1C1 = Yes; R1C2 = No. R2L = Plus; R2C1 = Yes; R2C2 = Yes. Marker ‡ is placed in heading H2. Legend: a marker in a column heading applies to every data cell in that column. Definition ‡ = business days only. No other markers, definitions, or scope rules are supplied. Identify authorized targets, unsupported inheritance, and work outside a scope map.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_exec_medium_9a30c62606d7`:

```text
{"scope_map":[{"cell_id":"H2","visible_value":"Email","marker":"‡","definition_reference":"‡ = business days only.","authorized_scope":"Every data cell in column H2","affected_cell_ids":["R1C1","R2C1"],"status":"resolved","rationale":"The supplied legend expressly authorizes a marker in a column heading to apply to every data cell in that column."}],"orphan_markers":[],"unbound_definitions":[],"unresolved_issues":[],"boundary_note":{"explicitly_supplied_scopes":["‡ applies to R1C1 and R2C1 through the column-heading rule."],"unresolved_scopes":["No broader scope is authorized for H1, H3, row labels, or other cells."],"outside_scope":["The map does not verify whether Yes or No is accurate, nor does it establish any meaning beyond the supplied qualifier and legend."]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
