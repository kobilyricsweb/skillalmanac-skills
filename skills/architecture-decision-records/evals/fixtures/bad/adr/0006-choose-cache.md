# 0006. Choose a cache

Status: approved

## Context

Product pages hit the database 14 times per view.

## Decision

We will add Redis in front of the database.

## Consequences

Page loads drop to a few queries. Cache invalidation becomes our problem, and stale prices for up to 60 seconds are possible, which sales has accepted.
