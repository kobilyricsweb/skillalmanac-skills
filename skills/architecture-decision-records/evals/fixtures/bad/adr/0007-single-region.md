# 0007. Run in a single region

Status: accepted
Supersedes: 0001

## Context

Traffic is 95 percent from one country and a second region would double the hosting bill.

## Options considered

- Single region: cheapest, but a regional outage takes the site down.

## Decision

We will stay in one region.

## Consequences

Hosting stays at the current bill. A regional outage means full downtime, and we accept up to four hours of it per year as the budget for this risk, as agreed with the business.
