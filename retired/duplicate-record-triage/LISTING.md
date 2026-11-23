# duplicate-record-triage

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when classifying supplied records under explicit exact, normalization, or candidate rules while preserving IDs, originals, conflicts, uncertainty, and every qualifying relationship. Do not use to merge or delete records, choose a canonical record, identify people, or infer identity from similarity without a represented candidate rule.

## Task boundary

csv-version-diff compares records across file versions and data-analysis-eda explores datasets; this classifies within-input record matches under explicit equality and normalization rules without merging records. dataset-field-profiler reports field observations.

## Try the independent synthetic example

Triage these synthetic records using only the stated rules. Records: R1 {email:"a@example.test", city:"Haifa"}; R2 {email:"a@example.test", city:"Haifa"}; R3 {email:" A@example.test ", city:"Haifa"}; R4 {email:"a@example.test", city:"Acre"}. Rules: compare email and city; exact requires both original values equal; normalized equality trims and case-folds email while city remains exact. No candidate rule exists. Preserve originals and IDs; do not merge or choose a winner.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_9d5a7e776921`:

```text
{"comparison_rules":[{"field":"email","comparison":"trim_and_case_fold"},{"field":"city","comparison":"exact"}],"candidate_rule":null,"classifications":[{"record_ids":["R1","R2"],"classification":"exact_duplicate","rule_basis":"Original email and city values are both equal.","original_values":{"R1":{"email":"a@example.test","city":"Haifa"},"R2":{"email":"a@example.test","city":"Haifa"}},"conflicts":[]},{"record_ids":["R1","R3"],"classification":"normalized_match","rule_basis":"Email matches after trimming and case-folding; city is exactly equal.","original_values":{"R1":{"email":"a@example.test","city":"Haifa"},"R3":{"email":" A@example.test ","city":"Haifa"}},"transformed_values":{"R1":{"email":"a@example.test","city":"Haifa"},"R3":{"email":"a@example.test","city":"Haifa"}},"conflicts":[]},{"record_ids":["R2","R3"],"classification":"normalized_match","rule_basis":"Email matches after trimming and case-folding; city is exactly equal.","original_values":{"R2":{"email":"a@example.test","city":"Haifa"},"R3":{"email":" A@example.test ","city":"Haifa"}},"transformed_values":{"R2":{"email":"a@example.test","city":"Haifa"},"R3":{"email":"a@example.test","city":"Haifa"}},"conflicts":[]},{"record_ids":["R4"],"classification":"unmatched","rule_basis":"No exact or normalized relationship with another record because city differs.","original_values":{"R4":{"email":"a@example.test","city":"Acre"}},"conflicts":[]}],"unresolved_cases":[],"remediation_boundary":"No records were merged, deleted, enriched, used for identity inference, or selected as canonical."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
