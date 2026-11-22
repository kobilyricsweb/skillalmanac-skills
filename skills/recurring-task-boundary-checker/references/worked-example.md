# Worked example

Synthetic example only.

Input request: `Every Friday, review stale draft pages, archive those older than 90 days, and tell the owner if anything looks wrong.` Owner: Content Operations. Input: draft-page list with last-edited date. Recipient role Content Operations is supplied, but no action-specific authorization, contact channel, archive authority, completion record, or stop condition is supplied.

Expected artifact:

- Trigger: every Friday, cadence supplied; exact time unresolved.
- Input: draft-page list and last-edited date.
- Requested but unauthorized: review the draft-page list, identify or list pages older than 90 days, archive those pages, and contact the owner. None of these actions has supplied authorization.
- Escalation: recipient role is Content Operations; contact channel and trigger “anything looks wrong” remain unresolved. The request to tell the owner does not itself authorize contact.
- Evidence: completion-record format is missing. A review list may be offered only as a non-operative proposal, not as completed evidence or an authorized future action.
- Stop conditions: missing; behavior on unavailable input is an unresolved pause/skip/retry policy, not an operative default. The proposed contract needs that decision before that branch can be authorized.

The contract does not review or archive pages, schedule a Friday job, contact the owner, or claim that any page was reviewed. It isolates every requested action lacking express authorization and reports the missing evidence, escalation, and stop rules.
