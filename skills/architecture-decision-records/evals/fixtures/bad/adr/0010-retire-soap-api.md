# 0010. Retire the SOAP API

Status: superseded

## Context

Two partners still call the SOAP API, about 200 calls a day in total.

## Options considered

- Retire it in June: frees the team, but both partners must migrate.
- Keep it indefinitely: no partner work, but an unpatched stack stays exposed.

## Decision

We will retire it in June.

## Consequences

The old stack is deleted and patching stops being a concern. Partners need a migration guide, and anything they have not moved by June stops working that day.
