# 0009. Pick a CI service

Status: accepted

## Context

Builds take 40 minutes on the shared runner.

## Options considered

- Hosted CI: parallel runners, but per-minute cost.
- Self-hosted runners: cheap per build, but we patch and scale them.

## Decision

We will use hosted CI.

## Consequences

Builds should fall under 10 minutes. The monthly bill grows by an estimated 400 dollars, and build secrets now live with a third party. See ADR-0042 for the secrets policy.
