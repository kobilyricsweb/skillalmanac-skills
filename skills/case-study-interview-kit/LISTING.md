# case-study-interview-kit

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when preparing neutral customer-interview questions, fact-confirmation requests, evidence requests, quotation-permission prompts, and optionally a timed agenda from supplied case-study material. Do not use to invent statements, grant publication rights, conduct market research, or make legal or causal conclusions.

## Task boundary

jobs-to-be-done-interview investigates a user job and user-research-synthesis interprets collected research; this drafts a vendor-claim interview kit with evidence questions and quotation permission, distinct from testimonial-use-readiness and objection-response-evidence-grid.

## Try the independent synthetic example

Create an interview kit for CloudCart used by a two-person shop to organize returns. Company assumption: returns became faster in June. Supplied record: a June log lists four returns; it has no May baseline or duration values. Interviewee: shop manager. Audience: small-shop operators. Approved topics: prior workflow, June workflow, setup effort, limitations. Restrictions: shop may be named, but no direct quote may be published without written approval. Ask neutral questions, request fact confirmation and evidence, address quotation permission, and identify anything outside the approved topics.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_d00b2f206789`:

```text
{"context":"CloudCart returns workflow at a named two-person shop; intended audience: small-shop operators.","source_items":[{"item":"Returns became faster in June.","classification":"company-assumption","status":"unverified"},{"item":"June log lists four returns.","classification":"supplied-record","status":"supplied"},{"item":"May baseline and duration values.","classification":"unknown","status":"unknown"}],"core_questions":["How were returns handled before CloudCart, and how were they handled in June?","What, if anything, changed in the workflow or responsibilities?","What setup work was required, and how long did it take?","What limitations, exceptions, or unchanged parts have you observed?"],"fact_confirmations":["Does the June log accurately list four returns, and what dates and scope does it cover?","What does faster mean in this context, and how was it observed or measured?","Is there a May comparison record or any duration information?"],"permission_prompts":["May the shop be named in a draft for review?","If wording is considered for quotation, may it be submitted for written approval before publication?","What role and organization description may accompany any approved quote, and what edits or channels are acceptable?"],"evidence_requests":[{"request":"Confirm the June log and provide relevant May records or duration data if available.","artifact_type":"record"},{"request":"Identify any customer-approved wording suitable for later quotation review.","artifact_type":"quote-candidate"}],"unresolved":["No May baseline or duration values are supplied.","The faster outcome remains unverified.","Quotation permission is not granted.","Any topic outside prior workflow, June workflow, setup effort, and limitations should be flagged for separate approval."],"timed_agenda":{"status":"not_applicable","time_cap":"not supplied","allocations":[],"optional_outside_core":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
