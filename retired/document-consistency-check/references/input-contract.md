# Input contract

## Required

- `documents`: at least two supplied peer document records with IDs, content, and available locations.
- Optional `comparison_scope`.

## Handling gaps

With no documents, report missing input. With one, state that cross-document agreement is unassessable. Preserve missing units, dates, versions, or scope and normally classify the affected comparison as unknown. Use `location_unavailable` when no marker exists. Do not correct or mathematically convert values.

## Deliverable

Markdown tables or equivalent structured output are accepted. Preserve comparison ID, field type, subject, assertions, classification, basis, and unresolved questions. Each assertion includes document ID, location state and value, original value, qualifiers, and any presentation-only normalized display.

Example: “8 kg” and “8 lb” are not converted. If the shipment identity is not established, classify the comparison as unknown and ask whether both assertions concern the same shipment.
