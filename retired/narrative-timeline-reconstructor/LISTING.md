# narrative-timeline-reconstructor

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when unordered notes must become a chronological narrative while preserving exact dates, ranges, relative order, dependencies, overlap, and uncertainty. Do not use for authorization decisions, evidence-status classification, causal inference, or assigning dates and sequence that the notes do not establish.

## Task boundary

Nearest is decision-evidence-ledger; this reconstructs event order rather than classifying decision status and authority.

## Try the independent synthetic example

Reconstruct a timeline from these notes using the stable IDs and source labels. E1, source memo: testing began on 2026-04-02. E2, source diary: review occurred after E1; no date is stated. E3, source calendar: planning occurred during 2026-04-01 through 2026-04-03. Preserve exact dates, ranges, and relative timing. When intervals overlap, leave unsupported order unresolved. Return an event table, narrative scaffold, conflicts, unresolved placement, and event-coverage check.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_51a8a20003aa`:

```text
{"status":"complete","events":[{"event_id":"E1","description":"Testing began.","time_expression":"2026-04-02","precision":"exact_date","dependencies":[],"source_labels":["memo"],"conflicts":[],"placement":"partially_ordered"},{"event_id":"E2","description":"Review occurred.","time_expression":"after E1","precision":"relative","dependencies":["E1 precedes E2"],"source_labels":["diary"],"conflicts":[],"placement":"partially_ordered"},{"event_id":"E3","description":"Planning occurred.","time_expression":"2026-04-01 through 2026-04-03","precision":"date_range","dependencies":[],"source_labels":["calendar"],"conflicts":[],"placement":"unresolved"}],"narrative_scaffold":["Planning occurred during 2026-04-01 through 2026-04-03; its order relative to the other events is unresolved because the range overlaps 2026-04-02.","Testing began on 2026-04-02.","Review occurred after E1, with no exact date stated."],"unresolved_placement":["E3 overlaps E1's date, so their order is unresolved.","E2 has no exact date; only its placement after E1 is supported."],"coverage_statement":"All three supplied events appear once; dates, range, source labels, and the stated after relation are preserved without inferring unsupported order."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
