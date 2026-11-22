# Password reset by email

## T1: Request a reset link from the login page
- Outcome: A user who forgot their password can request a reset link by email.
- Size: S
- Depends on: none
- Non-goals: Resetting by SMS; changing the password itself (T2); rate limiting (T3).
- Acceptance criteria:
  1. Given a registered email, when the user submits the "Forgot password" form, then an email with a single-use link is sent within 60 seconds.
  2. Given an unregistered email, when the user submits the form, then the page shows the same confirmation text and no email is sent.
  3. Given a malformed email, when the user submits the form, then the form shows "Enter a valid email" and nothing is sent.
- Definition of done: Criteria covered by automated tests; copy approved by support; deployed behind the `password_reset` flag.

## T2: Set a new password from the reset link
- Outcome: A user holding a valid reset link can set a new password and sign in with it.
- Size: M
- Depends on: T1
- Non-goals: Forcing sign-out of other devices; password strength meter.
- Acceptance criteria:
  1. Given a link less than 30 minutes old, when the user submits a new password of 12 or more characters, then the password is changed and the user lands on the login page with a success banner.
  2. Given a link older than 30 minutes, when the user opens it, then the page shows "This link has expired" and offers a new request.
  3. Given a link that was already used, when the user opens it, then the page shows "This link has expired".
  4. Given a password shorter than 12 characters, when the user submits it, then the form shows "Use at least 12 characters" and the password is unchanged.
- Definition of done: Criteria covered by automated tests; security review of token handling signed off.

## T3: Limit reset requests to 5 per hour per email
- Outcome: Repeated reset requests for one email address are refused after the fifth in an hour.
- Size: S
- Depends on: T1
- Non-goals: Per-IP limits; CAPTCHA.
- Acceptance criteria:
  1. Given 5 requests for one email in the last hour, when a sixth request arrives, then the API returns status 429 and sends no email.
  2. Given the oldest of 5 requests is over 60 minutes old, when a new request arrives, then it is accepted and the email is sent.
- Definition of done: Criteria covered by automated tests; limit value read from configuration.
