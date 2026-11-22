# Archive and merge policy to propose

These are defaults chosen by this skill for a team without a policy. Replace any value with the user's own policy; say which one is in force in the report.

## Ownership rules to propose

1. Every page has one named owner: a person, or a team with a channel or mailbox that someone reads.
2. The owner line sits in the first 10 lines of the page, as `Owner: <name or team>`, so it survives every export format.
3. A page whose owner left is ownerless. The space owner reassigns it within 14 days or archives it.
4. A group is acceptable as owner only when it has a contact channel; "Engineering" alone is not an owner.

## Review cadence

| Page type | Review every | Owner action when due |
|---|---|---|
| Runbooks, on-call | 90 days | Re-run the steps or confirm in writing |
| Onboarding, how-to | 180 days | Confirm or update, set the last-reviewed date |
| Policies | 365 days | Re-approve |
| Decision records | none | Mark superseded with a link, never edit history |

## Archive steps (after the owner agrees or the notice period ends)

1. Notice: send the owner the page list, the reason and the date; wait 14 days.
2. Move the page to an Archive area inside the same space, keeping its folder path, so history stays findable.
3. Add a banner at the top: archive date, reason, link to the replacement if one exists.
4. Fix or remove links that pointed to it; for a merge, point them to the surviving page.
5. Keep archived pages 12 months, then ask the space owner whether to delete. Deletion is never part of a first cleanup pass.
6. Record the batch in a log page: date, who approved, counts per action.

## Merging two pages

- Keep the page with the newer update date; break ties by more inbound links, then by length.
- Copy across only content the keeper lacks; do not paste both bodies.
- Leave a one-line redirect note in the retired page for the notice period, then archive it.
- Merge only when body similarity is high. Same title with different content is renamed, not merged.

## Batch size

Archive at most 10 percent of pages in one pass, or 50 pages, whichever is smaller, so owners can object before the next batch. Start with the high-confidence archive entries.
