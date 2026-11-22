# InviteMembers.tsx: decisions

## Contract
- `export function InviteMembers({ teamId }: { teamId: string })`. Also exports `InviteMembersProps`, `PendingInvite`, `isValidEmail`.
- Load: `GET /api/invites?team=<encodeURIComponent(teamId)>` expecting `[{id, email, sentAt}]`. Non-array or wrong-shaped JSON is treated as an error.
- Send: `POST /api/invites` with `Content-Type: application/json` and body `{teamId, emails}`. Any non-2xx or network failure is an error. Only the status is used; the response body is ignored.

## Structure
- `InviteMembers` is a thin wrapper that renders `InviteMembersForTeam` with `key={teamId}`. A team change remounts the form, so chips, draft, status messages and state from the previous team are discarded. The skill's rule is "reset state on identity change with a key, not an effect."
- The pending-invite fetch lives in an effect keyed on `[teamId, reloadToken]`, with an `AbortController` cleaned up on change or unmount. A stale response cannot overwrite a newer one.
- `reloadToken` is bumped after a successful send and by the "Try again" button. Loading state is set in the handler, not in the effect.
- An in-flight send is aborted on unmount.

## Emails
- Valid: a simple shape check (`local@domain.tld`, no whitespace), max 254 characters. It is a sanity check, not RFC 5322; the server must still validate.
- Input splits on whitespace, comma and semicolon. Enter, comma and semicolon commit the draft as chips. Paste of a list is split into chips; a single pasted address goes into the draft as normal. Blur commits the draft.
- Invalid tokens stay in the input and are named in an error, so the user can fix them. Valid tokens become chips.
- Duplicates are case-insensitive, checked against current chips and against already-pending invites. Only the first occurrence in a batch is kept.
- Submit with invalid or duplicate text in the draft does not send. It shows the problems and keeps the valid part as chips; the user sends again. Submit with no addresses shows "Add at least one email address."
- Chips are keyed by the address string, which is unique because of the dedupe.
- Backspace on an empty input removes the last chip.
- A failed send keeps the chips so the user can retry without retyping.

## Accessibility
- Visible `label` tied to the input. Hint text and error are linked with `aria-describedby`; `aria-invalid` is set while there is an error.
- Each chip has a real `button` with `aria-label="Remove <email>"`. The "x" glyph is `aria-hidden`. After removal, focus returns to the input.
- Draft errors and send/load failures use `role="alert"`. "Sent N invites" uses a polite `role="status"` live region. Loading uses `role="status"`.
- Sections are labelled by headings. The pending list is a real `ul` with `time` elements.
- Form has `noValidate` so the component's own messages are used instead of the browser's email validation.

## States
- Load: loading text, error with "Try again", empty ("No invites are pending for this team."), list.
- Send: button label changes to "Sending invites..." and the form is disabled while sending. Send is disabled when there are no chips and the draft is empty.

## Not done / not verified
- Not run: no project was available, so no `tsc`, lint, or tests were executed. The scanner (`react_scan.py`) reports 0 FAIL and 0 WARN.
- Not verified at runtime: fetch behavior, focus handling, screen-reader output.
- No styling is included; class names (`invite-members`, `invite-chips`, `invite-chip`) are hooks only.
- Assumes `id` is a string. If the API returns numeric ids, change `isPendingInviteList` and `PendingInvite`.
- Assumes an unchanged team id after a send. The POST body uses the `teamId` prop at submit time.
- The send does not optimistically add pending rows; it refetches the list after success.
- The `×` close glyph assumes the surrounding font has it; swap for an icon if the design system uses one.
