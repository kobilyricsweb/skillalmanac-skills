# ADR 2: Bring billing back into a modular monolith

## Status

Accepted. Supersedes: 0001

## Context

After nine months the billing service has had 4 outages caused by the network boundary, and daily deploys turned out to be used twice a month. Deploy tooling for the monolith has since gone to hourly releases.

## Options considered

1. Stay as a separate service. Cost: continued cross-service failures and the second database bill, about 900 dollars a month.
2. Merge back as an enforced module. Cost: two weeks of work, and billing loses its independent scaling.

## Decision

We will merge billing back as a module with its own schema, because the monolith now releases hourly and the boundary costs more than it returns.

## Consequences

Positive: one fewer database to run and no network hop on checkout. Negative: two weeks of migration work, and billing can no longer be scaled separately, so a billing spike now shares capacity with checkout.
