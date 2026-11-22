# user-story-splitter

## One line

Breaks one large user story into three to six thin slices, each with Given/When/Then acceptance criteria, an S or M size label, and a first slice that finishes one outcome.

## What it does

The skill takes a single user story and works through a fixed procedure. It first checks that the text names who is acting and what they want. It restates the story as Who, What and Why, and it writes "not stated" when the reason is missing rather than inventing one. It then lists every workflow step, rule, data kind, screen, path and action the story names in its own words, plus any implied item that a stated rule or step cannot work without. That list is the only source for slices. A bare umbrella verb such as "manage" with no named actions stops the run with status `needs-input`, asking one question per missing action.

Six splitting axes (workflow steps, business rules, data variations, interface, happy versus edge path, operations) are each marked Used or Not used. The Used axes become three to six slices. Each slice gets two to four acceptance criteria in Given/When/Then form, a size label, and a dependency field. A size L result is not allowed; the skill splits such a slice again. The first slice is the smallest one that lets a single user finish one happy-path outcome.

A final scope check removes anything that is not on the original scope list and reports it under Not added, so the output never grows past what the story says.

## When to use

- A story is too large to finish in one cycle and the team needs a thin first delivery.
- A product manager wants acceptance criteria for each piece of a feature, written in one consistent format.
- A story mixes several actions, such as view, change and end, and needs them separated.

## When not to use

- You need new requirements written from a vague idea. The skill splits existing text and does not invent scope.
- You need hour estimates, story points, owners, dates or a ranking across several stories.
- The input is a bug report or a task list with no user outcome.

## Requirements

A text-capable agent and the SKILL.md file. There is no script, no network access and no file output. The input is the story text itself, usually one or two sentences.

## Example

```
# Story split: subscription management
Status: needs-input
Who: customer
What: manage their subscription
Why: not stated

1. Can the customer view their current subscription? If so, what should the view show?
2. Can the customer change to a different plan? If so, how is the change confirmed?
3. Can the customer end the subscription? If so, when does access stop?
4. Is there any failure, cancel or reversal the story should cover?
```

The story says "manage" but names no actions, so the intake check stops the run. No scope list, splitting table or slices are produced, and nothing is invented. The four questions are the missing actions plus the edge-path question.

## Limits

- Splits only what the story says. A story that is vague will yield vague slices, and the skill reports gaps rather than filling them.
- Thresholds (slice count 3 to 6, two to four criteria, the S and M rules) are working values chosen for readability. They are not an industry standard.
- Output is Markdown only. The skill does not create tickets, read issue trackers or estimate effort.
- The Why line is often "not stated". The skill does not infer business value.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
