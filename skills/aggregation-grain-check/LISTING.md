# aggregation-grain-check

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when checking a proposed summary against supplied table keys, measure grain, joins, filters, grouping keys, and aggregation rules for duplication and non-additivity hazards. Do not use for auditing join cardinality alone, designing cohorts, executing queries, or declaring a sum safe without evidenced uniqueness, additivity, or approved deduplication.

## Task boundary

Nearest is join-cardinality-audit; this evaluates aggregation safety after relationships are supplied rather than auditing join cardinality itself.

## Try the independent synthetic example

Assess this proposed summary without running queries. Tables: Orders has one row per order_id with amount at order grain; Items has one row per item_id, with order_id as a foreign key. Relationship: one Orders row may match many Items rows. Join on order_id, filter Items.category='book', group by Orders.region, then sum Orders.amount. No deduplication rule is approved. Intended result: order amount by region for orders containing a book. Provide the worksheet, sequence, risk, measure status, supported alternative, and verification.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_22638f26a73a`:

```text
{"tables":[{"name":"Orders","row_identity":"order_id","grain":"one row per order; amount at order grain"},{"name":"Items","row_identity":"item_id","grain":"one row per item; order_id foreign key"}],"measures":[{"name":"amount","source":"Orders","additivity":"additive","status":"unsafe","hazards":["duplication"],"basis":"The Orders-to-Items join is one-to-many, so an order amount can repeat for each matching book item; no approved deduplication rule is supplied."}],"sequence":["Join Orders to Items on order_id.","Filter Items.category='book'.","Group by Orders.region.","Sum Orders.amount."],"risks":["Order rows may be repeated by multiple qualifying Items rows, causing structural duplication.","No observed numerical error or overcount is inferred."],"alternatives":["Supported: create a distinct qualifying order_id set using a semi-join, then aggregate Orders.amount by region.","Conditional: aggregate Orders before joining only if the intended matching semantics and resulting entity set are confirmed."],"verification":{"evidence_limited":true,"query_executed":false,"unresolved":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
