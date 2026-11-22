# 0003. Adopt a GraphQL gateway

Status: accepted

## Context

Mobile clients make seven calls per screen.

## Options considered

- GraphQL gateway: one call per screen, but a new component to run.
- Keep REST and add aggregate endpoints: no new component, but one endpoint per screen to maintain.

## Decision

We will adopt a GraphQL gateway.

## Consequences

TBD
