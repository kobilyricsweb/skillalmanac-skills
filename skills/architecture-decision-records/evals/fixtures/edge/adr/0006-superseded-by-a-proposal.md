# 0006. Superseded by a proposal

Status: superseded
Superseded by: 0005
## Context

Constraint x forces a choice now because load doubled to 600 requests per second.

## Options considered

- Option one: fast to ship, but costs a second database to operate.
- Option two: no new system, but needs two weeks of refactoring.

## Decision

We will take option one because shipping speed matters this quarter.

## Consequences

Positive: shipped this quarter. Negative: a second database to monitor and back up, owned by the platform team, with an estimated 300 dollars a month in hosting cost.
