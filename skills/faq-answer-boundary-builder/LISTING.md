# faq-answer-boundary-builder

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when creating reusable FAQ answer frames from supplied questions, approved facts, policy clauses, exceptions, prohibitions, and escalation instructions. Do not use for individualized customer-support replies, filling policy gaps from common practice, or making promises not present in the supplied rules.

## Task boundary

Nearest is customer-support-replies; this builds reusable bounded FAQ entries rather than responding to individual customers.

## Try the independent synthetic example

Create reusable FAQ entries for employees. Questions: (1) “Can I return an unopened badge holder?” (2) “Can I return an engraved badge holder?” Approved facts: unopened standard badge holders may be returned within 14 calendar days of delivery with a receipt. Policy: refunds use the original payment method. Exception: engraved items are excluded from returns. Prohibited promise: do not guarantee when funds will appear. Unknown cases must be escalated to the Returns Policy Team using: “Ask the Returns Policy Team to review the case.” Required format: structured JSON.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_75178eb4c9c6`:

```text
{"audience":"employees","entries":[{"question":"Can I return an unopened badge holder?","direct_response":"An unopened standard badge holder may be returned within 14 calendar days of delivery with a receipt.","supported_detail":["Refunds use the original payment method."],"exceptions":["The supplied exception excludes engraved items from returns."],"unknown_cases":["Any case outside the stated unopened standard-item conditions is not covered by the supplied rules."],"escalation":"Ask the Returns Policy Team to review the case.","status":"complete"},{"question":"Can I return an engraved badge holder?","direct_response":"No. Engraved items are excluded from returns.","supported_detail":[],"exceptions":[],"unknown_cases":[],"escalation":"Ask the Returns Policy Team to review the case.","status":"complete"}],"missing_inputs":[],"conflicts":[]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
