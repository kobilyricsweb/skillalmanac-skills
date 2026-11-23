# landing-page-message-sequencer

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when ordering approved page messages by visitor question, supplied evidence and permitted call to action. Do not use for interface code, campaign planning, conversion predictions, or CTA details that are not supplied or authorized.

## Task boundary

copywriting-landing-pages writes landing-page copy; this orders supplied approved messages and evidence without inventing copy or claims. offer-comparison-matrix compares offers; message-asset-reuse-map plans channel reuse.

## Try the independent synthetic example

Sequence a synthetic landing page for audience “small museum staff” with objective “request a demo.” Approved messages: M1 exact wording “Catalog objects in one workspace” (promise); M2 “Imports require CSV headers” (qualification). Evidence asset E1 description “Product guide documents single-workspace cataloging,” location /guide. Authorized CTA: “Request a demo,” destination /demo, for this audience, after M2. Visitor questions: What does it do? What must I prepare? What next? No other claims are approved.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_4505420f67c5`:

```text
{"audience":"small museum staff","objective":"request a demo","sections":[{"order":1,"visitor_question":"What does it do?","message_ids":["M1"],"approved_claim":"Catalog objects in one workspace","evidence":{"asset_id":"E1","description":"Product guide documents single-workspace cataloging","location":"/guide","support_status":"direct"},"cta":null,"cta_status":"not_applicable","restrictions":[],"gaps":[]},{"order":2,"visitor_question":"What must I prepare?","message_ids":["M2"],"approved_claim":"Imports require CSV headers","evidence":null,"cta":null,"cta_status":"not_applicable","restrictions":[],"gaps":["No evidence asset was supplied for the CSV-header qualification."]},{"order":3,"visitor_question":"What next?","message_ids":[],"approved_claim":null,"evidence":null,"cta":{"wording":"Request a demo","destination":"/demo","audience":"small museum staff","authority_status":"authorized","prerequisites":["After M2"]},"cta_status":"authorized","restrictions":["CTA follows M2."],"gaps":[]}],"sequence_rationale":"The sequence answers capability, preparation, then the authorized next action in the supplied visitor-question order.","rejection_log":[],"unresolved_gaps":["M2 has no supplied evidence asset."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
