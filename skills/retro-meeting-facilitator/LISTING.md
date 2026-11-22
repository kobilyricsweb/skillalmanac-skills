# Retro Meeting Facilitator

## One line

Turns a missed release or a messy sprint into a timed retro agenda, a sorted capture sheet and three owned actions with due and check dates.

## What it does

The skill walks a team through one retrospective of 60 minutes, or 45 minutes for teams of three or four. It starts by checking the actions from the previous retro, so old commitments are marked done, carried or dropped before anything new is discussed. It then picks a format from a short table: Start-Stop-Continue for a routine sprint, 4Ls for a long period with mixed feelings, and a Timeline when the order of events matters, as after a missed deadline.

Pasted sticky notes are split into single ideas, de-duplicated, and rewritten so that no note blames a named person. Notes are grouped into themes that need at least two notes each, with a rule for promoting process-gap notes when there are too few themes. Dot-voting uses a fixed dot budget, and the top three themes become one action each. Every action has a verb-first text, an owner who is a role rather than a person named in a note, a due date, a check date and a yes-or-no done test.

The output is four fixed tables: carried actions, agenda, capture sheet and action list.

## When to use

Use it after a sprint, a release or a missed deadline when the team has notes but no decisions. It fits a facilitator who needs an agenda and a clean list of actions to paste into a tracker.

## When not to use

Do not use it for performance reviews, for deciding who caused a failure, for root-cause work on a production outage, or for one-to-one feedback. The refusal rules in the skill stop those requests and point to the right kind of conversation.

## Requirements

A text-capable agent and the pasted notes. No scripts, no network, no installed tools.

## Example

Smoke input: six people, a missed release, six pasted notes. Excerpt of the action list produced by following the skill:

| # | Theme | Action | Owner (role) | Due date | Check date | Done test |
|---|---|---|---|---|---|---|
| 1 | A: release ownership and scope | Name one owner for the release checklist and freeze scope before each release | Release lead (role) | D+10 working days | D+14 days | Does the checklist have a named owner and a dated freeze entry for the last release? |
| 2 | B: QA on late build and stale data | Refresh staging data and deliver the release candidate to QA by the Tuesday before each release | QA lead (role) | D+10 working days | D+14 days | Did QA receive the release candidate by the Tuesday before the last release? |
| 3 | C: standups overrun | Time-box standups to 15 minutes with a rotating facilitator who ends discussion at the limit | Scrum master (role) | D+10 working days | D+14 days | Did every standup end within 15 minutes in the last two weeks? |

## Limits

The timings, dot counts and date offsets are working values chosen for this procedure. They have not been checked against any team or any published guidance. The skill cannot see the room, so it cannot tell whether a note is accurate or whether the owner agreed. Small teams with fewer than three people are refused, and groups above twelve must be split. Output depends on the quality of the pasted notes; with very few notes the themes may be thin.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
