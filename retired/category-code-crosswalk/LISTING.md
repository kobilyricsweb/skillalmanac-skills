# category-code-crosswalk

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when two supplied coding systems require a traceable mapping that may include one-to-many, many-to-one, scoped, dated, or unresolved relationships. Do not use for judging coverage within one taxonomy, mapping by label similarity alone, authorizing record recoding, or inventing unsupported code correspondences.

## Task boundary

translation-and-localization adapts language and locale; this maps coded categories between supplied systems under explicit definitions, approval notes and scope constraints without translating terms or silently recoding records.

## Try the independent synthetic example

Build a source-to-target crosswalk. Source system S contains S1 "paper invoices" and S2 "electronic invoices." Target system T contains T-A "paper billing documents" and T-B "digital billing documents." Approved note N1 says S1 maps to T-A and S2 maps to T-B for jurisdiction J, effective 2026-01-01 through 2026-12-31. Direction is S to T; one-to-many and many-to-one mappings are permitted. Account for every supplied code and state that the artifact does not authorize record recoding.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_62e2e8197ba1`:

```text
{"direction":"S to T","relationships":[{"source_code":"S1","target_code":"T-A","mapping_type":"scoped","rationale_source":"Approved note N1","constraints":["Jurisdiction J","Effective 2026-01-01 through 2026-12-31"],"status":"supported"},{"source_code":"S2","target_code":"T-B","mapping_type":"scoped","rationale_source":"Approved note N1","constraints":["Jurisdiction J","Effective 2026-01-01 through 2026-12-31"],"status":"supported"}],"code_accounting":[{"system":"source","code":"S1","status":"mapped"},{"system":"source","code":"S2","status":"mapped"},{"system":"target","code":"T-A","status":"mapped"},{"system":"target","code":"T-B","status":"mapped"}],"unresolved_entries":[],"assumptions":["The artifact records mappings only within N1's scope.","It does not authorize record recoding or establish broader equivalence."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
