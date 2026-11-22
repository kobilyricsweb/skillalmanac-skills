---
name: meeting-agenda-timebox-check
description: "Checks a meeting agenda before the meeting: does it fit the slot, is it overbooked, does every item have an owner, a goal type (decide, inform, discuss), a timebox and an outcome. Use when the user says check my agenda, will this fit in 30 minutes, is this meeting overbooked, timebox this agenda, or pastes agenda items with minutes. A script adds the minutes up against the slot with a 10 percent buffer and flags items with no decision question, overlaps, a missing break, one person talking over half the time and late decisions, then suggests cuts. Do not use for meeting notes or action items after the meeting, finding a free slot, sending invites or changing a calendar."
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the tables in steps 3 and 4 by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Meeting agenda timebox check

Turn a list of topics into an agenda that fits its slot and ends in outcomes. This skill works before the meeting. For what was said and who owes what afterwards, use a notes-and-actions skill instead.

## Workflow

```
- [ ] 1 Collect the meeting facts
- [ ] 2 Collect items; refuse any without an outcome
- [ ] 3 Write the agenda file
- [ ] 4 Run the check
- [ ] 5 Fix flags with the tables, run again
- [ ] 6 Report
```

1. **Meeting facts.** Ask for slot length, start time (optional), purpose (decide, inform, brainstorm, review) and, only if the user knows it, the number of attendees. Never guess an attendee count; without one the script reports no attendee-hours.
2. **Items.** Each item needs a title, an owner (a named person, not "team"), a goal type and the outcome wanted. Goal types: `decide` (a choice is made), `discuss` (input is gathered), `inform` (people learn something), `brainstorm` (ideas are generated), `break`. A topic with no outcome is not an agenda item: ask "what should be true when this item ends?". If the user cannot say, it is a candidate for a pre-read or for deletion. A `decide` item must carry the decision as a question ("Do we ship on Friday?"), not a topic ("Launch").
3. **Write the agenda file** in one of two layouts and keep the user's original untouched. Markdown:

```
# Weekly product sync
length: 60m
start: 10:00
attendees: 5
purpose: decide

- [10m] Launch date | owner: Dana | decide: Do we ship Friday or the Monday after?
- [5m] Hiring status | owner: Sam | inform: Share the two open offers | discussion: no
- [10m] Break
```

   `[..]` accepts `10m`, `1h`, `1h30m`; keys after `|` are `owner`, one of `decide|inform|discuss|brainstorm` (its value is the outcome), `outcome`, `question`, `discussion: yes|no`, `start`, `type`. A title starting with break, lunch, coffee or pause is a break. JSON layout: `{"meeting": {"title", "length_min", "start", "attendees", "purpose"}, "items": [{"title", "owner", "type", "minutes", "outcome", "question", "needs_discussion", "start"}]}`. Unknown keys exit 2 so typos are caught.
4. **Run** (read-only; do not edit the script to make a flag disappear):

```bash
python scripts/check_agenda.py agenda.md
python scripts/check_agenda.py agenda.json --length 45 --attendees 6 --out check.json
```

   Exit 0 = pass, 1 = warn or fail, 2 = bad input (the message says what to fix). `--out` also saves the report; it refuses a path that resolves to the agenda and refuses an existing file without `--force`. Flags and their fixes are in [references/flags-and-fixes.md](references/flags-and-fixes.md); read only the rows for flags that fired.
5. **Fix and re-run** until the verdict is pass, or until the remaining warnings are ones the user accepts knowingly. Prefer the cuts in `suggested_cuts` in the order given. Never cut a `decide` item to save time; move it earlier instead.
6. **Report** in this fixed shape:

```
Verdict: <pass|warn|fail>   Slot: <length> min   Booked: <total_min> min   Free: <buffer_min> min (need <required_buffer_min>)
Fixed: <flags resolved and how>
Accepted by the user: <flags left, with the user's reason>
Cuts proposed: <item, action, minutes saved> or none
Attendee-hours: <slot and booked, or "not computed: no attendee count given">
Not checked: <e.g. whether durations are realistic for this group; room, tools, pre-reads sent>
```

## Decision tables

Time rule per item type (minutes; working values, a floor or ceiling breach is a warning):

| Type | Floor | Ceiling | Over the ceiling usually means |
|---|---|---|---|
| inform | 5 | 10 | it is a pre-read |
| discuss | 10 | 20 | the question is two questions |
| decide | 10 | 15 | the decision is undecided; split off the discussion |
| brainstorm | 15 | 30 | add a converge step instead |
| break | 5 | none | n/a |

Slot rules: items add up to at most slot minus 10 percent (rounded up); a slot over 90 minutes needs a break item; no owner above 50 percent of item minutes once there are 3 or more items; no `decide` item starting in the last 10 percent of the slot.

Purpose to structure:

| Purpose | Required shape |
|---|---|
| decide | at least one `decide` item, the first one starting in the first half |
| brainstorm | a `brainstorm` item followed by a `discuss` or `decide` item (diverge, then converge) |
| inform | if every item is `inform`, offer a written update instead of a meeting |
| review | no structural rule; the other checks still apply |

Cut or async (applied in this order when the buffer is short): an `inform` or `discuss` item marked `discussion: no` becomes a pre-read (saves all its minutes); an `inform` item above 5 minutes is trimmed to 5; `discuss` and `brainstorm` items are trimmed to their floor. `decide` items are never cut.

## Output contract

One JSON object on stdout, `schema_version` 1: `title`, `purpose`, `length_min`, `start`, `attendees`, `total_min`, `ends_at_min`, `buffer_min`, `required_buffer_min`, `items[]` (`n`, `title`, `type`, `minutes`, `owner`, `outcome`, `start_min`, `end_min`, `start`, `end`, `flags[]`), `owner_minutes`, `attendee_hours` (`slot`, `booked`, `cuts_save`, or null), `findings[]` (`code`, `severity` error|warning|info, `item` or null, `message`), `counts`, `shortage_min`, `suggested_cuts[]` (`item`, `action` move_to_preread|trim, `from_min`, `to_min`, `save_min`), `cuts_save_min`, `cuts_cover_shortage`, `verdict` (fail if any error, warn if any warning, else pass; info never changes the verdict).

## Boundaries

No calendar access and no invites: the skill reads one file and prints a report. Attendee-hours come only from a count the user gave. The skill checks the arithmetic and wording of an agenda, not whether the meeting should exist; it only suggests a written update when every item is `inform`.

## Limits

- Thresholds (5/10, 10/20, 10/15, 15/30 minutes, 10 percent buffer, 50 percent owner share, 90 minute break rule, 90 percent and 50 percent decision positions) are working values, not measured optima. A group that works well with a 25 minute decide item can accept that warning.
- An outcome check looks at wording only: a question mark for `decide`, a result verb for the rest. It cannot tell a good outcome from a plausible one.
- Owner share counts scheduled minutes, not who actually speaks.
- Clock times assume one continuous block; a time zone or a day change is not modelled (clock values wrap at midnight).
- Without Python, apply the tables above by hand and say in the report that the arithmetic was not script-checked.
