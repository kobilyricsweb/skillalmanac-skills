---
status: "superseded"
superseded-by: 0002
date: 2026-01-12
---
# ADR-0001: Split the billing module out of the monolith

## Context and Problem Statement

Billing changes ship once a fortnight because they ride the monolith release train. Billing has 11 engineers and wants daily deploys.

## Considered Options

* Extract billing as its own service: independent deploys, but we take on a network boundary and a second database.
* Keep billing in the monolith behind a module boundary: no new infrastructure, but release cadence stays shared.

## Decision Outcome

Extract billing as its own service, because deploy cadence is the bottleneck.

## Consequences

Good: billing deploys daily. Bad: invoices now cross a network call, so a billing outage must be handled in checkout, and we must run and monitor a second database.
