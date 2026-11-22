# 0004. Adopt feature flags for risky releases

Status: proposed

## Context

Two of the last five releases were rolled back by redeploying, which took 25 minutes each time. We want to switch behaviour off without a deploy.

## Options considered

- Hosted flag service: fast to adopt, but a monthly fee and a network dependency on the request path.
- Config file flags read at start-up: free and simple, but a change still needs a restart.

## Decision

Proposed: use the config file approach first, because it costs nothing and covers the two incidents seen.

## Consequences

Positive: small change. Negative: a restart is still needed, which is a risk we accept for now and will review after one quarter.
