# InviteMembers: decisions

## Data flow
- Pending invites: `GET /api/invites?team=<teamId>` (encoded), expects a JSON array of `{id, email, sentAt}`. A non-array body is treated as an error.
- Send: `POST /api/invites` with `{teamId, emails}` (JSON). The response body is not used. After a successful send the list is reloaded from GET, so the server stays the source of truth.

## teamId changes while mounted
- A reset effect on `[teamId]` clears invites, chips, draft, errors and notices.
- The load effect on `[teamId, reloadKey]` aborts the previous request through AbortController, and ignores results after abort.
- `teamRef` holds the current team. A send started for team A does not write state after the user has moved to team B, and its `finally` does not clear `sending` for B.

## Emails
- Input is split on whitespace, commas and semicolons. Each token is trimmed and lowercased.
- Validation uses a simple pattern (`local@domain.tld`, no spaces) and a 254-character limit. This is a sanity check only; the server must still validate.
- Duplicates are checked case-insensitively against chips in the current batch and against existing pending invites.
- Invalid tokens stay in the text box so the user can fix them. Valid tokens become chips.
- Chips are added with Enter, comma, the Add button, or paste of a multi-address list. Backspace on an empty box removes the last chip. Each chip has a remove button labelled "Remove <email>". Removing a chip moves focus back to the input.
- Enter and comma are ignored during IME composition.
- Clicking Send flushes whatever is in the box first. If anything is invalid, nothing is sent.

## States
- Loading: a `role="status"` message, shown only while no invites are on screen. Reloads after a send keep the old list visible.
- Error: `role="alert"` with a Try again button, which bumps `reloadKey`.
- Empty: a "No pending invites" message.
- Sending: the submit button label changes to "Sending..." and inputs are disabled.
- Success: a polite live-region message. Chips and draft are cleared.
- Send failure: `role="alert"`, and the chips are kept so the user can retry.

## Accessibility
- Section labelled by its heading. The input has a visible label and a hint linked with `aria-describedby`. Errors are linked too, and `aria-invalid` is set when there is an error.
- Chips are a labelled list. Buttons are `type="button"` and labelled. The "×" is `aria-hidden`.
- The form uses `noValidate` so the browser's own email popups do not replace these messages. The input is `type="text"` with `inputMode="email"`.

## Open points
- No maximum batch size is enforced on the client. A server limit is not specified in the task.
- The success message does not say how many were skipped as duplicates.
- Styling is not included. Classes are not set and no CSS is shipped.
- The file has not been type-checked or run, because the work folder has no project config or React install.
