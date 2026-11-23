# taxonomy-structure-check

Status: unpublished free candidate; no score or verification badge.

## One Line

Check parent-pointer taxonomy records for roots, orphan links, self-links, and cycles.

## Audience

Taxonomy maintainers and data pipeline owners.

## Benefit

Separates malformed input from structural graph defects using deterministic evidence.

## Limits

Checks graph shape only; it does not evaluate category meaning or completeness.

## Synthetic Example

A node whose parent is absent is reported as an orphan; a node parenting itself is also a one-node cycle.
