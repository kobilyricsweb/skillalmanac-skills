# Spec: newsletter signup form (agreed 2026-11-10)

### REQ-001 Email field
The form shall accept one email address and reject values without an @ sign, showing the message "Enter a valid email".

Acceptance:
- Given the value "abc", when the user submits, then "Enter a valid email" is shown and no request is sent.

### REQ-002 Confirmation
After a successful signup the form shall show "Check your inbox to confirm" and clear the field.

Acceptance:
- Given a 201 response, then the message is shown and the field is empty.

### REQ-003 Server error
On a 5xx response the form shall show "Something went wrong, try again" and keep the typed value.

Acceptance:
- Given a 503 response, then the message is shown and the field still holds the typed email.
