# Spec: rate limiter for the public API

### REQ-001 Per-key limit
The API shall reject the 101st request from one API key within a 60-second window with HTTP 429.

Acceptance:
- Given a key that made 100 requests in the last 60 seconds, when it makes another, then the response is 429 and the request is not processed.

### REQ-002 Burst handling
Short bursts should be handled gracefully. Burst size TBD.

### REQ-003 Retry header
Every 429 response shall include a Retry-After header with the whole seconds until the window resets.

Acceptance:
- Given a rejected request 20 seconds into the window, then Retry-After is 40.

### REQ-004 Limit headers
Successful responses shall include X-RateLimit-Remaining with the number of requests left in the window.

Acceptance: after the 10th request in a fresh window the header reads 90.
