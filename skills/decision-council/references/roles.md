# Council role cards

## Contents
- Output format shared by every role
- Sceptic
- Operator
- Finance
- Customer
- Long-term
- Traps that make a council worthless

Read only the card of the role you are about to run, plus the shared format and the traps.

## Output format shared by every role

Each role writes exactly this block, one per role, covering every option (including "do nothing"):

```
ROLE: <name>
Stance per option: <option>: favour | oppose | neutral (one line of reason each)
Top findings: 1-3 items, each tagged [given] (the user said it), [assumed] (the role's guess) or [unknown] (cannot be known from here)
Needs to know: the single fact that would change this role's stance most, and how to get it
Confidence: low | medium | high, with one phrase of why
```

Rules: roles are allowed to disagree and should. A role may not end on "it depends" without naming what it depends on. A number that the user did not give is tagged [assumed] and shown as a range, never as a point. Three findings at most; depth goes into the "Needs to know" line.

## Sceptic

Job: find how the leading option fails. Does not propose an alternative.

Required outputs:
1. Pre-mortem: for each of the top two options, write the sentence "It is 18 months later and this failed because ..." three different ways. Each failure story has a trigger (what happens first) and an early signal (what the user would see in the first 90 days).
2. The load-bearing assumption: the one belief that, if false, breaks the option. State how it could be tested cheaply before committing.
3. Optimism check: which numbers or promises in the user's notes come from someone who benefits from the user saying yes.

Questions to ask yourself: what is being counted that is not yet real (verbal promises, forecasts, "likely")? What is the downside if this goes wrong in the worst plausible way, not the average way?

## Operator

Job: make the option real. Thinks in weeks, people, dependencies.

Required outputs:
1. First 30 days: the 5 concrete actions in order, who does each, what it needs.
2. Hidden work: tasks nobody listed (handover, migration, approvals, paperwork, learning curve) with a rough effort range.
3. Capacity: what the decider will stop doing to make room. If nothing, say the option is not yet resourced.
4. Single point of failure: the person, system or approval that everything waits on.

## Finance

Job: money in, money out, timing, and what the choice costs by not being taken.

Required outputs:
1. Three cases (low, base, high) for the main money lines, each with its assumptions written beside it. Never one number.
2. Break-even or payback: the month when the option has returned what it consumed, or the statement that it never does under the base case.
3. Cash floor: the lowest point of cash during the first 12 months and whether fixed obligations stay covered there.
4. Sunk costs named and set aside (money or time already spent that no option can recover).
5. Cost of delay: what waiting one month costs or saves.
6. Opportunity cost: what the money or time would do under the best other option.

Not a licensed adviser: no tax, investment or legal conclusions; flag where a specialist is needed.

## Customer

Job: the people on the receiving end. "Customer" means whoever lives with the outcome: buyers, users, team members, family, patients, voters.

Required outputs:
1. Who is affected, split into at most four groups, with what each gains and loses.
2. Evidence quality per group: observed behaviour, stated preference, or guess. Observed beats stated beats guess.
3. Reaction and switching: how each group will react in the first 90 days and what it costs them to leave or object.
4. The silent group: whoever is affected but not in the user's notes.

## Long-term

Job: the view from three and ten years out.

Required outputs:
1. Where each option leaves the decider at 3 years and at 10 years: skills, assets, relationships, options still open.
2. Lock-in and optionality: what becomes harder or impossible later, and what new choices open up.
3. Compounding: whether the option's benefits grow, flatten or decay, and its costs likewise.
4. Regret test: five years on, which choice would be most regretted if it failed, and which if it succeeded.

## Traps that make a council worthless

- Five voices that all agree: re-run the dissenting role with the instruction to argue against the emerging favourite.
- Roles that restate the user's notes. A finding must add something not in the notes (an implication, a risk, a missing number, a question).
- Invented precision: percentages and probabilities nobody supplied. Use ranges and tags.
- Averaging away a veto: if one role names a failure the decider cannot survive (cash floor below fixed costs, legal bar, safety), that is a gate, not a score. Treat it as a constraint in the recommendation.
- Leaving out "do nothing" and "delay": the status quo is always an option and usually the baseline others are scored against.
