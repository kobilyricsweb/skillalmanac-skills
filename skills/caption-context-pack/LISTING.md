# caption-context-pack

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when an existing chart or image needs bounded explanatory text covering visible labels, supplied context, reading guidance, limitations, and a source-note placeholder. Do not use for dashboard design, causal interpretation, identity inference, trend claims beyond the artifact, or captions based on information not supplied or visible.

## Task boundary

Nearest is dashboard-design; this creates bounded explanatory text for an existing visual rather than designing a dashboard.

## Try the independent synthetic example

Create a caption context pack for a bar chart. Visible content: title "Tickets by queue, 4 Nov 2026"; bars "Billing: 3" and "Access: 5"; y-axis label "Tickets". Intended takeaway: the chart displays more Access tickets than Billing tickets on that date. Supplied limitation: it covers only tickets logged in these two queues on 4 Nov 2026. Internal source identifier: OPS-17. Return a short caption, extended context, reading guidance, limitation, source-note placeholder, and uncertainty note.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_5382d27c7939`:

```text
{"short_caption":"Tickets by queue, 4 Nov 2026: Billing 3; Access 5.","extended_context":"The bar chart displays 3 tickets for Billing and 5 tickets for Access on 4 Nov 2026. Access has the higher displayed count.","reading_guidance":"Compare the labeled bar values using the y-axis label, Tickets.","limitation":"The chart covers only tickets logged in Billing and Access on 4 Nov 2026.","source_note_placeholder":"Source: internal identifier OPS-17.","uncertainty":[{"claim":"Access had more tickets overall or for other dates or queues","status":"unsupported","reason":"The artifact is limited to two queues and one date."}]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
