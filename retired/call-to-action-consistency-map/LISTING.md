# call-to-action-consistency-map

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when auditing supplied assets for CTA fit against audience stage, approved wording, asset message, and a factual destination description. Do not use for message-reuse mapping, asset redesign, conversion prediction, implementation, or inferring destination capability from a title, URL, or asset name.

## Task boundary

Nearest is message-asset-reuse-map; this audits CTA progression and destination fit rather than message reuse locations.

## Try the independent synthetic example

Audit one synthetic asset. Asset A copy: “See how the method works.” Current CTA: “View the demo.” Audience state: evaluating. Stage rule: evaluating readers may move to an educational demonstration. Approved CTA: “View the demo,” scoped to web pages. Destination D description: “A two-minute page showing the method with three labeled screenshots; no signup.” Prohibited transition: evaluating directly to purchase. Channel: web page. Return stage fit, destination fit, mismatch, recommendation status, and path summary.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_6a8c30f08074`:

```text
{"assets":[{"asset":"Asset A","current_cta":"View the demo.","audience_state":"evaluating","promised_destination":"An educational demonstration of how the method works.","destination_description":"A two-minute page showing the method with three labeled screenshots; no signup.","stage_result":"fit","destination_result":"fit","mismatch":null,"proposed_approved_cta":null}],"missing_inputs":[],"conflicts":[],"progression_summary":"Evaluating reader -> approved educational demonstration -> destination fulfills the CTA promise; the web-page path is consistent."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
