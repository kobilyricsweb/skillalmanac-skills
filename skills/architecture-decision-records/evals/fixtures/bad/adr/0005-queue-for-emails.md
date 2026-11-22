# 0005. Use a queue for outgoing emails

Status: superseded
Superseded by: 0009

## Context

Email sending blocks requests for up to 4 seconds when the provider is slow.

## Options considered

- Background queue: requests return at once, but failures need a retry policy.
- Send inline with a timeout: simple, but still delays the request by the timeout.

## Decision

We will send emails from a background queue.

## Consequences

Requests no longer wait on the provider. A dead-letter queue must be monitored, and a failed email can now arrive minutes late, which support must know about.
