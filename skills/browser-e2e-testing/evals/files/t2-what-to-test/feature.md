# Feature: account profile page

Signed-in users open /profile and can:

1. Change their display name (2 to 40 characters, no leading or trailing spaces, emoji allowed).
2. Change their email. The server sends a confirmation link; the new address is active only after the link is opened.
3. Upload an avatar (PNG or JPEG, up to 2 MB; larger or other types show an error message).
4. Delete the account: a dialog asks them to type DELETE, then the account is removed and they land on the home page logged out.

Test environment: the app runs at http://localhost:3000, there is a test endpoint POST /api/test/users that creates a user and returns its email and password, DELETE /api/test/users/:id removes it, and emails go to an inbox the tests can read at GET /api/test/inbox?to=<email>.
Framework in the repo: Playwright with TypeScript (playwright.config.ts present, no tests yet for the profile).
