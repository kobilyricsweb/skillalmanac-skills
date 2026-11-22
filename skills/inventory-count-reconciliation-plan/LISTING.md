# inventory-count-reconciliation-plan

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when two supplied inventory observations disagree and you need a controlled worksheet that preserves both counts, explains documented arithmetic differences, and identifies recounts. Do not use for duplicate-record similarity classification, stock correction, shrinkage estimation, or record changes.

## Task boundary

Nearest is duplicate-record-triage; this reconciles count discrepancies rather than classifying record similarity.

## Try the independent synthetic example

Create a reconciliation worksheet. Matching rule: identical SKU values match. First count at 09:00: SKU-A=5, SKU-B=3. Second count at 10:00: SKU-A=4, SKU-B=5. Units are pieces in Shelf 1. Evidence: sale S1 records one SKU-A piece between the counts; no adjustment evidence exists for SKU-B. Permitted steps: request a recount; propose a record correction only after manager approval. Preserve both observations and calculate second minus first. Do not update records.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_220a7005cf85`:

```text
{"comparison_basis":"Identical SKU values match; units are pieces in Shelf 1; difference is second count minus first count.","rows":[{"item":"SKU-A","first_observation":5,"second_observation":4,"count_times":["09:00","10:00"],"difference":-1,"documented_adjustment":"Sale S1 records one SKU-A piece between counts.","arithmetic_explanation":"5 - 1 = 4, matching the second observation.","classification":"explainable_difference","evidence":["S1"],"proposed_next_step":null},{"item":"SKU-B","first_observation":3,"second_observation":5,"count_times":["09:00","10:00"],"difference":2,"documented_adjustment":null,"arithmetic_explanation":null,"classification":"recount_candidate","evidence":[],"proposed_next_step":"Request a recount; propose a record correction only after manager approval."}],"unresolved_inputs":["No adjustment evidence explains the SKU-B increase."],"review_summary":"Both observations are preserved. SKU-A is explained by S1; SKU-B remains unresolved. No records were updated."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
