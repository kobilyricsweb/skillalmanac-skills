# 0001. Use RabbitMQ for order events

Status: superseded
Superseded by: 0003
Date: 2025-03-04

## Context

The order service must hand events to billing and shipping. Peak load is about 300 events per second and a lost event means a customer is not charged. The team has two engineers who have run RabbitMQ before and nobody with Kafka experience.

## Options considered

### RabbitMQ
Familiar to the team and a single node handles our peak with room to spare. Cost: no replay of old events, so a new consumer cannot backfill.

### Kafka
Keeps history for replay. Cost: a three-broker cluster to run and no in-house experience, roughly two months before we would trust it.

## Decision

We will use RabbitMQ with durable queues, because the team can operate it today and replay is not needed yet.

## Consequences

- Positive: running within two weeks; no new hiring.
- Negative: no replay, so adding a consumer means a one-off export from the order database.
- Follow-up: revisit when a third consumer is requested.
