# 0001. Use Postgres for the catalogue

Status: accepted

## Context

The catalogue has 2 million rows and needs joins across suppliers and categories.

## Options considered

- Postgres: relational joins and mature tooling, but we must run backups ourselves.
- MongoDB: flexible documents, but joins are awkward and the team has less experience.

## Decision

We will use Postgres because joins are the main access pattern.

## Consequences

Positive: joins are cheap and the schema is enforced. Negative: schema changes need migrations, and we own backup and failover for a database that now holds every product record.
