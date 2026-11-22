# Flags and fixes

Read only the rows for flags that fired in the report. Severity is what the script assigns; info flags never change the verdict.

## Contents

- Errors
- Warnings
- Info

## Errors

| Flag | Meaning | Fix |
|---|---|---|
| NO_GOAL_TYPE | item has no type, or an unknown one | Ask what the item is for: a choice (decide), input (discuss), news (inform), ideas (brainstorm). |
| NO_TITLE | empty title | Name the topic in a few words. |
| NO_OWNER | nobody is named | Name one person who runs the item. A shared owner is no owner. |
| NO_OUTCOME | no desired outcome | Write what should be true at the end. No outcome: pre-read or delete. |
| NO_DECISION_QUESTION | decide item without a question mark | Rewrite as the choice itself, with its options if known: "Do we ship Friday or Monday?". |
| OVERBOOKED | item minutes exceed the slot | Apply suggested_cuts, then drop or move whole items; do not shrink decide items. |
| RUNS_PAST_SLOT | an item ends after the slot ends | Same as OVERBOOKED; also check explicit start times. |
| OVERLAP | an explicit start is before the previous item ends | Move the start, or shorten the previous item. |
| START_BEFORE_MEETING | explicit start earlier than the meeting start | Correct the time. |
| NO_DECISION_ITEM | purpose is decide but no decide item exists | Add the decision as a question, or change the purpose to inform or discuss. |

## Warnings

| Flag | Meaning | Fix |
|---|---|---|
| BUFFER_TOO_SMALL | free time is under 10 percent of the slot (rounded up) | Apply suggested_cuts in order. |
| DURATION_ABOVE_MAX / DURATION_BELOW_MIN | outside the time rule for the type | Over: split, convert to pre-read, or change the type. Under: merge with a neighbouring item. |
| OUTCOME_NO_VERB | outcome does not start with a result verb or a question | Start with decide, approve, choose, agree, confirm, assign, share, list, generate, and so on. |
| OUTCOME_WEAK_VERB | outcome starts with discuss, talk, cover, sync, go, look, check | Say what comes out of it: "Choose two themes", not "Talk about themes". |
| ASYNC_CANDIDATE | item marked as needing no discussion | Send it as a pre-read and remove the item, or keep a 5 minute question slot. |
| DECISION_LATE | a decide item starts in the last 10 percent | Move it earlier; late decisions get squeezed or deferred. |
| DECISION_NOT_EARLY | decide meeting, first decision after the midpoint | Move the first decision into the first half. |
| NO_BREAK / BREAK_TOO_SHORT | slot over 90 minutes without a break, or break under 5 | Add a break item of 5 to 10 minutes about midway. |
| OWNER_DOMINANT | one owner holds over half the item minutes (3 or more items) | Hand an item to another owner or ask the dominant owner to pre-read part of theirs. |
| NO_BRAINSTORM_ITEM | purpose brainstorm, no brainstorm item | Add one, or change the purpose. |
| NO_CONVERGE_STEP | nothing to discuss or decide after the last brainstorm | Add a discuss or decide item to choose among the ideas. |

## Info

| Flag | Meaning | Fix |
|---|---|---|
| GAP_BEFORE | explicit start leaves unscheduled minutes before an item | Intended buffer is fine; otherwise close the gap. |
| COULD_BE_ASYNC | purpose inform and every item is inform | Offer a written update; keep the meeting only if questions are expected. |

## How the clock is built

Items run back to back from the meeting start (or minute 0). An explicit item `start` overrides the chain: earlier than the previous end is OVERLAP, later is GAP_BEFORE. `buffer_min` is the slot length minus the latest item end, so gaps eat buffer. `total_min` is the plain sum of durations.
