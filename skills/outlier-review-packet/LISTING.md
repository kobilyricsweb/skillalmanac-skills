# outlier-review-packet

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when supplied records have explicit unusual-value flags or thresholds and reviewers need a consistent packet for human disposition. Do not use for automatic error correction, deletion, causal attribution, duplicate matching, or declaring that an outlier is necessarily wrong.

## Task boundary

Nearest is duplicate-record-triage; this packages unusual-value review rather than evaluating possible record matches.

## Try the independent synthetic example

Prepare a human review packet. Records: A has temperature 9 C and note="sensor moved"; B has temperature 10 C and note="none"; C has temperature 4 C and note="none". Explicit rule R1: flag temperature greater than or equal to 10 C; the boundary is inclusive. Allowed context fields: note only. Permitted dispositions: retain; correct-with-source; exclude-with-reason. Include only records triggered by R1, preserve observed values, list evidence gaps, and do not choose a final disposition or infer a cause.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_90443213829f`:

```text
{"missing_inputs":[],"review_items":[{"record_id":"B","observed_value":10,"unit":"C","triggering_rule":"R1: flag temperature greater than or equal to 10 C (inclusive boundary)","supplied_context":{"note":"none"},"evidence_available":["Observed temperature: 10 C","Supplied note: none"],"evidence_gaps":["No source evidence establishes whether correction or exclusion is warranted."],"allowed_dispositions":["retain","correct-with-source","exclude-with-reason"],"flag_status":"flagged","reviewer_decision":null}],"omitted_records":[{"record_reference":"A","reason":"Temperature 9 C does not meet the inclusive threshold of 10 C."},{"record_reference":"C","reason":"Temperature 4 C does not meet the inclusive threshold of 10 C."}],"verification_notes":["Only R1-triggered records are included as review items.","The flag is not a finding of error or cause."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
