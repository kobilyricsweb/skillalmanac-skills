# data-lineage-hop-map

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when supplied pipeline notes must be converted into a field-level lineage map across named stages, transformations, filters, aggregates, and undocumented origins. Do not use for tracing documentary evidence for claims, profiling observed field types, or inferring connections from matching names or plausible business meaning.

## Task boundary

Nearest is claim-evidence-map; this traces data fields through transformations rather than claims to documentary excerpts.

## Try the independent synthetic example

Build field-level lineage from these pipeline notes. Stage order: raw_orders R, cleaned_orders C, daily_sales D. Mapping R.amount -> C.net_amount with transformation “subtract R.discount.” Filter at C: include rows where C.status = “paid.” Aggregation C.net_amount -> D.total_sales using “sum by C.sale_date.” Mapping R.sale_date -> C.sale_date is a direct copy. Record each hop, including every explicitly named transformation input, filter placement, aggregate contributor, and any broken path. Do not infer mappings for other fields.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_5d7df6c6f7ab`:

```text
{"stage_order":["raw_orders R","cleaned_orders C","daily_sales D"],"lineage_hops":[{"source_field":"R.amount","destination_field":"C.net_amount","mapping_type":"derived","transformation":"subtract R.discount","support_status":"supported"},{"source_field":"R.discount","destination_field":"C.net_amount","mapping_type":"derived","transformation":"subtract R.discount","support_status":"supported"},{"source_field":"R.sale_date","destination_field":"C.sale_date","mapping_type":"copied","transformation":"direct copy","support_status":"supported"},{"source_field":"C.net_amount","destination_field":"D.total_sales","mapping_type":"filtered_contribution","transformation":"sum by C.sale_date; contribution restricted by C.status = paid","support_status":"supported"}],"filters":[{"stage":"C","condition":"include rows where C.status = paid"}],"aggregations":[{"destination_field":"D.total_sales","contributors":["C.net_amount","C.sale_date"],"rule":"sum C.net_amount by C.sale_date"}],"unknown_origins":["C.status"],"conflicts":[],"verification_findings":["All stated mappings, transformation inputs, filter placement, and aggregate contribution are represented.","C.status is used by the filter but has no supplied origin mapping.","No mappings for other fields were inferred."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
