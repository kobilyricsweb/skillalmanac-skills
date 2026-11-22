# newsletter-issue-planner

## One line

Plans a single marketing newsletter issue from three source items you supply: angle, word-budgeted sections, five subject lines, a link audit and a pre-send checklist.

## What it does

The skill takes a short intake (audience, goal, three source items, one call to action) and turns it into a written plan rather than a finished email. It picks an angle from a four-row table keyed to the goal (inform, convert, retain, announce), then lays out a fixed section order with word budgets for the opening, each of the three items, and the call-to-action block. It writes exactly five subject lines in a fixed set of types, each with preview text, and counts the characters so the budgets can be checked. It lists the four links the issue will contain, flags missing or duplicated ones, and ends with a checklist in which the items a language model cannot verify, such as whether links open or whether the unsubscribe link renders, are marked for you to confirm. Facts come only from what you supply; statistics, quotes and dates you did not give are replaced with a visible placeholder.

## When to use

Use it when one issue has to be ready soon and the material is already in hand: three items, a named readership, one action you want readers to take. The planning step is where last-minute issues usually go wrong, because the lead item, the subject line and the single call to action get decided under time pressure. The output gives you those decisions in a fixed layout you can review in a few minutes.

## When not to use

Do not use it for a multi-issue sequence, a drip campaign, an automation or a welcome series; it plans one issue at a time. It does not write the issue body, so use it before drafting, not in place of drafting. It does not test links, read a live inbox, or check the rendering of a send.

## Requirements

Any text-capable agent that can follow a numbered procedure and produce markdown tables. No scripts, no network access and no extra packages are needed.

## Example

Excerpt from the offline smoke run (monthly gardening newsletter, goal retain, three items):

```
| # | Type | Subject | Subject chars | Preview | Preview chars |
|---|---|---|---|---|---|
| 1 | curiosity | The date that decides when seed trays go out | 44 | One date from our first item, and two more steps. | 49 |
| 2 | specific benefit | Start seeds indoors and move them out on time | 45 | Timing for seed trays, a soil tip, and a watering check. | 56 |
```

## Limits

- Budgets and character ranges are working values chosen for this skill, not published standards.
- The plan counts budgets and characters; it does not measure how a mail client truncates a subject line.
- The retain goal needs the reader's most-used item from you; without it the plan stops at intake.
- Output quality depends on the source items: vague facts produce thin sections.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
