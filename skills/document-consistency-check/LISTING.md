# document-consistency-check

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Compares named entities, quantities, units, dates, and version assertions across supplied peer documents, distinguishing contradictions, established scope differences, and unknowns. Do not use for choosing an authority, browsing, or editing records.

## Task boundary

# document-consistency-check

Status: unpublished free candidate; no score or verification badge.

## One Line

Compare document facts while preserving scope, originals, and unresolved conflicts.

## Audience

Auditors, project teams, editors, and analysts reviewing multiple offline documents.

## Benefit

Separates real contradictions from scope differences and missing context.

## Limits

Does not select a canonical document, convert uncertain values, or resolve conflicts externally.

## Suggested Example

Fictional example: compare two fictional inventory reports for the Harbor Lantern project.

## Evidence

See VERIFICATION.md. Examples are synthetic, not customer outcomes.

## Try the independent synthetic example

Compare these peer documents. D1, location summary row 2: “Shipment Q contains 8 kg of material for batch A.” D2, location page 1: “Shipment Q contains 8 kg of material for batch A.” D3, location note 4: “Shipment Q contains 8 kg of material for batch B.” Compare quantity, unit, and batch scope only.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_4caa1a5621e0`:

```text
{"comparisons":[{"comparison_id":"CMP1","field_type":"quantity","subject":"Shipment Q material for batch A","assertions":[{"document_id":"D1","location_state":"available_location","location_value":"location summary row 2","original_value":"8","qualifiers":"Shipment Q; material; batch A","normalized_display":"8"},{"document_id":"D2","location_state":"available_location","location_value":"location page 1","original_value":"8","qualifiers":"Shipment Q; material; batch A","normalized_display":"8"}],"classification":"consistent","basis":"D1 and D2 state the same quantity for batch A.","unresolved_questions":[]},{"comparison_id":"CMP2","field_type":"unit","subject":"Shipment Q material for batch A","assertions":[{"document_id":"D1","location_state":"available_location","location_value":"location summary row 2","original_value":"kg","qualifiers":"Shipment Q; batch A","normalized_display":"kg"},{"document_id":"D2","location_state":"available_location","location_value":"location page 1","original_value":"kg","qualifiers":"Shipment Q; batch A","normalized_display":"kg"}],"classification":"consistent","basis":"D1 and D2 use kg for batch A.","unresolved_questions":[]},{"comparison_id":"CMP3","field_type":"other","subject":"Shipment Q batch scope","assertions":[{"document_id":"D1","location_state":"available_location","location_value":"location summary row 2","original_value":"batch A","qualifiers":"Shipment Q; 8 kg","normalized_display":"batch A"},{"document_id":"D2","location_state":"available_location","location_value":"location page 1","original_value":"batch A","qualifiers":"Shipment Q; 8 kg","normalized_display":"batch A"},{"document_id":"D3","location_state":"available_location","location_value":"location note 4","original_value":"batch B","qualifiers":"Shipment Q; 8 kg","normalized_display":"batch B"}],"classification":"different scope","basis":"D1 and D2 refer to batch A, while D3 refers to batch B.","unresolved_questions":[]}],"unresolved_questions":[],"limits":["Only quantity, unit, and batch scope were compared."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
