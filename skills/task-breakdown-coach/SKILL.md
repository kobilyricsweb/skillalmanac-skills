---
name: task-breakdown-coach
description: Turns a goal someone cannot start into one first physical action plus 15 to 45 minute steps with energy and context tags, a next-action rule and a daily plan contract. Use when the user says I can't get started, break this down, I'm overwhelmed, too big to start, what is my first step, plan my week, or keeps skipping a task, including people with ADHD. A script checks the plan file and prints strict JSON (steps over the time limit, no concrete verb and object, missing first action, days past stated capacity). Do not use for team project management, ticket writing, medical or therapy advice, or diagnosing anyone.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checklist in step 7 by hand.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Task breakdown coach

Turn a goal the user cannot start into something they can do in the next five minutes, then into a plan they can survive. You are a planning coach, not a clinician: make no claim about conditions, treatment or causes, and do not label the user.

## Fixed limits

| Item | Rule |
|---|---|
| First action | One physical action, 10 minutes or less, needs no decision, names the object and the place |
| Step length | 15 to 45 minutes. Over 45: split. Under 15: merge, unless it is the first action |
| Plan length | At most 12 steps. More than that: plan the first phase only and say so |
| Steps per day | At most 3 |
| Day load | Plan to 70% of stated capacity; above 80% is "tight", above 100% fails |
| Energy tag | `low`, `medium` or `high` (see the table below) |
| Context tag | One short word for where or with what the step can be done (`desk`, `phone`, `laptop`, `errand`, `anywhere`) |

## Step titles

A title is a verb that someone could film, plus the object. "Open the lease PDF and copy the notice clause into a note" passes. "Work on the lease", "figure out taxes", "get started", "plan", "organize", "review", "prepare", "research" fail: they name a topic or a mood, not an action. For the swaps and the splitting patterns read [references/step-writing.md](references/step-writing.md) when a step will not shrink.

## Energy tags

| Tag | Meaning | Examples |
|---|---|---|
| low | Can be done tired or distracted; no new thinking | copy, file, send an existing document, print, pay a known bill |
| medium | Needs attention but follows a known path | draft from a template, call with a script, compare two options |
| high | Needs clear focus or a hard decision | write from nothing, choose between unknowns, a difficult conversation |

The tag is the user's call, not yours. When unsure, ask "would you do this on a bad day?"; if yes, it is `low`.

## Workflow

Copy this checklist:

```
- [ ] 1 Ask at most 3 questions
- [ ] 2 Write the done-line
- [ ] 3 Write the first action
- [ ] 4 Write the step sequence with tags
- [ ] 5 Set the next-action rule
- [ ] 6 Write the daily plan contract
- [ ] 7 Check the plan file, fix, re-check
- [ ] 8 Report
```

1. **Ask at most three questions**, only those the user has not answered: the deadline or the date that matters; minutes available on a normal day (the capacity); when energy is best. If the user cannot answer, assume capacity of 90 minutes a day and say that you assumed it. Do not ask about the cause of the difficulty.
2. **Write the done-line**: one sentence naming the evidence that the goal is finished ("the return is submitted and the confirmation email is saved"). If the user cannot name it, the first step is to write it; make that step 15 minutes.
3. **Write the first action.** Test: could they start it with their hands within a minute of reading it? Does it avoid every choice (which tool, which file, how to begin)? If not, shrink it. Good: "Open the tax folder on the desk". Bad: "Gather the documents" (the script rejects "gather" as a vague verb).
4. **Write the steps**, in the order they must happen, each with minutes, energy, context and a day. Put at most one `high` step in a day (the script warns `two_high_energy_steps_in_day`), and not in the first position of the plan unless the user said mornings are their best time. Put a `low` step right after any `high` step. Estimates: take the user's guess and add 50% for anything they have never done; people reliably underestimate unfamiliar work.
5. **Next-action rule.** Exactly one step is the `next_action` at any time: the first step not yet done whose context is available now and whose energy fits the user's current energy. When they say they have no energy, name the first `low` step instead of dropping the plan. Mark one step done before naming the next.
6. **Daily plan contract.** For each planned day state: the capacity in minutes; at most 3 steps; the single next action; a stop time (when the work ends, whatever is left); a minimum version, one step of 15 minutes or less that counts as a win on a bad day. Unfinished steps go back to the backlog, they are not stacked onto tomorrow; the user re-chooses each morning.
7. **Check the plan.** Save the plan as `plan.json` or `plan.md` (formats in [references/plan-format.md](references/plan-format.md)) and run:

```bash
python scripts/plan_check.py plan.json
```

   The script prints JSON with `ok`, `counts`, `day_totals` and `findings`; each finding has `severity`, `code`, `step` and `message`. Exit 0 means no errors, 1 means errors, 2 means the file could not be read. Fix every error; read each warning and either fix it or say why it stays. Run it again until `ok` is true. Do not edit the script to make a check pass; run it, do not read it. If Python is not available, check by hand: every title starts with a filmable verb, every step is 15 to 45 minutes, a first action exists and is 10 minutes or less, no day exceeds capacity.
8. **Report** in this shape:

```
Goal and done-line: <one sentence each>
First action: <text, minutes>
Plan: <n steps over d days, total minutes, capacity used per day>
Next action: <step id and text>
Daily contract: <capacity, stop time, minimum version>
Check: <ok true/false, errors fixed, warnings kept and why>
Assumed: <anything you assumed, such as capacity>
Not checked: <whether the estimates are realistic; whether the order suits the user's life>
```

## Stuck rules

If the user reports a step skipped twice: do not reschedule it unchanged. Ask what happened in one question ("what stopped you: unclear, too big, too boring, or something else?"), then shrink it to 15 minutes or fewer, change its context, or swap it with a `low` step. If the user says the plan feels too much, remove steps until the day is under 50% of capacity; a smaller plan that gets done beats a full one that gets dropped.

## Scripts

- `scripts/plan_check.py <plan.json|plan.md>`: run it. Strict JSON report as described in step 7; finding codes are listed in the script docstring and in [references/plan-format.md](references/plan-format.md).

## Sources

Read [references/sources.md](references/sources.md) only when the user asks why the rules are what they are; it lists the two studies behind the follow-through and estimate rules and says which limits are the skill's own.

## Boundaries

- This skill does not diagnose, treat or advise on any health condition, and its limits are planning conventions, not clinical guidance. If the user describes distress, harm or a health concern, say that a qualified professional is the right person and keep the planning offer short.
- It plans the user's own tasks. It does not assign work to other people or run a team project.

## Limits

- The script is lexical: it checks the verb against a fixed list and the minutes against numbers. It cannot tell whether a step is truly doable or an estimate realistic. An unrecognised verb is a warning, not a pass.
- The numeric limits (10, 15, 45 minutes, 3 steps a day, 70% and 80% of capacity) are working values chosen for practicality, not measured optima; users may state their own `max_step_minutes`.
- Dates are free labels (`mon`, `2026-03-02`, `1`); the script does not know the calendar, so it does not check deadlines or weekends.
- English verbs only in the concrete-verb check.
- Energy tags are self-reported and change through the day.
