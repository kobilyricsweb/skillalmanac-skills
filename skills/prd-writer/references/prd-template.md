# PRD template

Keep the section names; the check script looks for them. Aim for two pages.

```markdown
# PRD: <feature name>

Status: Draft. Source: <where the notes came from>. Author: <name>.

## Decisions needed
<The two to five open questions that block the build, each with who should decide. Readers see these first.>

## Problem
<Who has the problem, what happens today, and the evidence, with its source. Two to five sentences. No solution here.>

## Users
<Who it is for, and who it is not for in this version.>

## Success metrics
- <Metric>: baseline <figure from the notes>, target <figure> [proposed], measured by <how>, checked <when>.
- <Metric with no baseline yet> [needs data]

## Non-goals
- <Thing a reader would assume is included, and why it is out for now.>

## Requirements
- **R1 (Must)** <observable behaviour> (Source: <who in the notes>; <legal / contractual, if stated>). Accept: <what a tester does and sees>.
- **R2 (Must)** ...
- **R3 (Should)** ...
- **R4 (Could)** ...

## Risks and assumptions
- Risk: <what could go wrong> - <what reduces it, if the notes say>.
- [assumption] <something taken as true that nobody confirmed>.

## Open questions
- <Question?> Positions: <A, said by ...> / <B, said by ...>. Decider: <name or role>.
```

## Writing each part

**Problem.** Test: could a reader who has never seen the product explain why this matters? If the only evidence is "people asked for it", say exactly that and how many people.

**Success metrics.** A metric names something countable that moves if the feature works. Give the baseline from the notes. If the notes hold no target, either propose one on a `[proposed]` line and say what it is based on, or write `[needs data]`. Do not present a proposed target as agreed.

**Non-goals.** Write the ones somebody will ask about: the platform not covered, the user group excluded, the nearby feature left for later. Include every exclusion the notes state.

**Requirements.** One behaviour per requirement, each with a Source naming who asked for it; a legal, contractual or "not optional" statement is recorded as such and is Must. No source line in the notes, no requirement. Rewrite examples:

| Weak | Testable |
|---|---|
| The export should be fast | R4 (Must) An export of 500 invoices finishes in under 2 minutes [proposed; today it takes 14]. Accept: start an export of 500 invoices, time it |
| Users can easily find saved items | R2 (Must) The cart icon shows the count of saved items on every page. Accept: save 3 items, open any page, the icon shows 3 |
| Support reminders on all channels | R5 (Could) Reminder sent by a second channel. Accept: see Open questions (channel not decided) |

**Open questions.** Each is a question a named person can answer. For a conflict, give both positions and who holds them. Never restate an open question as a requirement.

## What stays out of a PRD

Database tables, endpoints, component names, effort estimates, and the sprint plan. A constraint stated in the notes ("guest carts cannot be supported in the first version") is recorded as a non-goal or a risk with its source.
