# requirement-to-section-coverage-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when assessing a complete or explicitly incomplete document against an explicit required-and-optional requirement list using stable section evidence. Do not use for creating an outline, drafting missing content, auditing heading promises, or treating headings, related wording, embedded commands, or common practice as proof of coverage.

## Task boundary

spec-driven-build traces written requirements into implementation tests, while technical-docs-writer audits documentation structure and examples. requirement-to-section-coverage-map performs no build or drafting; it maps every explicit requirement to stable section-body evidence and distinguishes covered, partial, related, absent, conflicted, and unassessable states.

## Try the independent synthetic example

Assess this complete document. Stable sections: S1 says, "Backups run daily and the Operations team owns the process." S2 says, "Users can export records as CSV." Requirements: R1 (required), "State the backup frequency and owner." R2 (optional), "Describe PDF export." Equivalence rules: "each day" and "daily" are equivalent; CSV is not equivalent to PDF. Produce the requirement coverage matrix and verification report. Use only these facts; planning new content or changing the document is outside scope.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_9de8f0464139`:

```text
{"matrix_rows":[{"requirement_id":"R1","requirement_text":"State the backup frequency and owner.","priority":"required","section_evidence":[{"section_id":"S1","support":"Backups run daily and the Operations team owns the process."}],"coverage_status":"covered","assessment_certainty":"final","interpretation":null,"duplication":[],"conflicts":[],"unresolved_gap":null},{"requirement_id":"R2","requirement_text":"Describe PDF export.","priority":"optional","section_evidence":[],"coverage_status":"absent","assessment_certainty":"final","interpretation":null,"duplication":[],"conflicts":[],"unresolved_gap":"No section describes PDF export; S2 supports CSV export, which is not equivalent to PDF."}],"verification_report":{"all_requirements_accounted_for":true,"covered_rows_have_section_support":true,"reported_gaps":["R2 lacks PDF-export support."],"input_limitations":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
