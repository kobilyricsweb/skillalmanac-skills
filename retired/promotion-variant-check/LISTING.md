# promotion-variant-check

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when comparing approved baseline message-field values with static promotion variants under a one-field experiment design. Do not use for writing copy, market research, statistical significance, causal inference, publishing, or any live campaign action.

## Task boundary

paid-ads-builder and email-marketing-sequences create or audit promotional campaign material and plans. promotion-variant-check does not write or evaluate campaign content; it mechanically checks whether each supplied static variant changes exactly its declared single field from an approved baseline.

## Try the independent synthetic example

The interpreter is unavailable. Provide a labeled manual, unexecuted assessment of this exact input without running or editing the bundled script: {"baseline":{"headline":"Save","body":"Today"},"changed_field":"headline","variants":[{"id":"A","fields":{"headline":"Save now","body":"Today"}},{"id":"B","fields":{"headline":"Save","body":"Today"}},{"id":"C","fields":{"headline":"Save later","body":"Tomorrow"}}]}. Compare strings exactly and report design findings, execution mode, and untested limits. Do not rewrite or publish copy. Shared report-code contract for BOTH baseline and supplied-skill assessments: NO_CHANGE applies when the exact changed-field set is empty; MORE_THAN_ONE_CHANGED applies when its size exceeds1; CHANGED_FIELD_MISMATCH applies when it is not exactly the singleton containing changed_field. Return every applicable code; codes may co-occur.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_bb6c2c46e960`:

```text
Manual, unexecuted assessment. The input satisfies the stated structure. Variant A changes only headline and matches the declared one-field design, so it has no finding. Variant B has changed_fields [], with codes NO_CHANGE and CHANGED_FIELD_MISMATCH. Variant C has changed_fields ["body","headline"], with codes MORE_THAN_ONE_CHANGED and CHANGED_FIELD_MISMATCH. Execution mode: hand calculation only; no script was run. Untested limits include actual CLI behavior, file/encoding handling, duplicate keys, numeric-reader cases, size boundaries, and any live or performance outcome. Copy was not rewritten or published.
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
