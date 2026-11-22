# Spec: password reset

## Scope

Users who forgot their password can reset it by email. Out of scope: SMS reset.

## Requirements

### REQ-001 Request a reset link
The system shall send one reset email to a registered address within 60 seconds of the request.

Acceptance:
- Given a registered user, when they submit their address, then one email with a reset link is queued and the response is 202.

### REQ-002 Unknown addresses look the same
The system shall return the same response and timing class for unregistered addresses as for registered ones.

Acceptance: a request for an unregistered address returns 202 and queues no email.

### REQ-003 Link expiry
A reset link shall stop working 30 minutes after it was issued.

Acceptance:
- Given a link issued 31 minutes ago, when it is used, then the response is 410 and the password is unchanged.

### REQ-004 Single use
A reset link shall work once.

AC1: using the same link a second time returns 410.

### REQ-005 Legacy export [deferred]
Export the reset audit log as CSV. Deferred to the next release.
