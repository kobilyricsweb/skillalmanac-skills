# rubric-anchor-builder

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when a supplied rubric needs synthetic response anchors that make boundaries between performance levels observable. Do not use for diversifying instructional examples, inventing criteria, or scoring work without descriptor-based evidence.

## Task boundary

Nearest is example-set-diversifier; this builds scoring anchors rather than diversifying instructional examples.

## Try the independent synthetic example

Build the minimum paired synthetic anchors for the boundary between Level 1 and Level 2. Prompt: “Give reasons to choose a reusable cup.” Criterion R, reasons: Level 2 = gives two relevant reasons; Level 1 = gives one relevant reason; Level 0 = gives none. Score only criterion R. Non-scorable condition: response is blank. Keep each response to one sentence. Provide each score, descriptor-linked rationale, observable boundary feature, and non-scorable treatment.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_49c6f069fdc3`:

```text
{"anchors":[{"label":"Level 1 anchor","synthetic_response":"Reusable cups reduce single-use waste.","criterion_results":[{"criterion":"R","result":1,"rationale":"The response gives one relevant reason, matching the Level 1 descriptor."}],"boundary_feature":"Exactly one relevant reason is present.","non_scorable_treatment":"This response is not blank, so the non-scorable condition does not apply."},{"label":"Level 2 anchor","synthetic_response":"Reusable cups reduce single-use waste and save money over time.","criterion_results":[{"criterion":"R","result":2,"rationale":"The response gives two relevant reasons, matching the Level 2 descriptor."}],"boundary_feature":"A second relevant reason is added while the first remains unchanged.","non_scorable_treatment":"This response is not blank, so the non-scorable condition does not apply."}],"ambiguity_notes":["A blank response is non-scorable rather than Level 0 under the supplied condition."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
