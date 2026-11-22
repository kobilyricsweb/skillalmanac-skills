# Notes layout

Copy this layout. Keep the heading names exactly; the check script looks for them.

```markdown
# <Meeting name>, <date as given in the transcript>

Attendees: <names as they appear in the transcript>

## Summary
<Up to three lines: what was decided and what happens next.>

## Decisions
- <Decision in one sentence.> (<who decided>; <source>)
- <Decision that replaced an earlier position.> Replaces: <earlier position>. (<who>; <source>)

## Action items
| Owner | Action | Due | Source |
|---|---|---|---|
| Dana | Send the revised price list to the three pilot stores | 2026-11-20 ("by Friday") | Dana, 00:14:10 |
| Unassigned | Update the landing page with the new date | No date set | Raised by Omar, 00:21:40 |

## Open questions
- <Question nobody answered, or a request that got "I'll check".> (<who asked>; <who is expected to answer, if said>)

## Discussed, not decided
- <Idea that was floated or parked.> (<source>)
```

## Filling the table

- **Owner**: first name as used in the transcript. Two owners only if both accepted. Otherwise `Unassigned`.
- **Action**: verb + object + enough detail to act without re-reading the meeting. "Follow up" alone is not an action.
- **Due**: the date as said; or the computed date followed by the spoken phrase in double quotes; or `No date set`. Compute a date only when the meeting date is known.
- **Source**: speaker and timestamp, or speaker and a few identifying words when there are no timestamps.

## Telling a decision from a discussion

| What was said | Where it goes |
|---|---|
| "OK, we go with option B." No objection follows | Decisions |
| "I think B is better." Topic moves on with no close | Discussed, not decided |
| "Let's park that" / "take it offline" | Discussed, not decided |
| "I'll check with finance and come back" | Open questions, plus an action for that person |
| "We agreed last month that ..." | Not a decision of this meeting; mention only if an action depends on it |
| A date or figure stated, then corrected | Only the corrected value, in the place it belongs |

## Recap email shape

Subject: `<Meeting name> <date>: decisions and actions`. Body: decisions as a short list; then one block per person with their actions and due dates; then unassigned items with a request for volunteers; then open questions. No narrative.
