# 0003. Replace RabbitMQ with Kafka

Status: accepted
Supersedes: 0001
Date: 2026-02-20

## Context

Four consumers now need order events and two of them need to rebuild state from history. The platform team now runs a Kafka cluster for analytics, so the operating cost we feared in 0001 is already paid.

## Options considered

### Stay on RabbitMQ
No migration. Cost: each backfill is a manual export, about two engineer days per consumer.

### Move to Kafka
Replay is built in and the cluster exists. Cost: producers and consumers need rewriting, estimated six weeks, and ordering guarantees change from per queue to per partition.

## Decision

We will move order events to the shared Kafka cluster, because replay removes the recurring backfill work and the cluster cost is already carried.

## Consequences

- Positive: new consumers can start from offset zero; no more manual exports.
- Negative: six weeks of migration work and a dual-write period of about a month; partition keys must be chosen carefully to keep per-order ordering.
- Follow-up: remove the RabbitMQ deployment once all consumers have moved.
