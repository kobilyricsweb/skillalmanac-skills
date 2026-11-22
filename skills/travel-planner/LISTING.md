# Listing page content: travel-planner

**One line:** Builds a paced, budgeted trip itinerary and lists every hour, price and visa fact still to verify before booking.

## What it does

The skill gives an agent a six-step trip-planning procedure: collect the missing facts, pick a pace (relaxed 2 activities a day, balanced 3, packed 4), draft the days as an itinerary JSON file, add budget lines and a document checklist, run a checker, and report in a fixed format. A verify-before-booking rule forbids stating any opening hour, price or visa rule as fact; each goes in as unverified with the kind of source to check. The bundled script reads the itinerary file and prints one strict JSON report: overlapping time blocks, days over the pacing limit, missing transit buffers (15 minutes inside an area, 30 across areas, plus travel time and arrive-early time), unverified or unsourced facts, stale checks, and budget totals by category and day.

## Capabilities

- `scripts/itinerary_check.py`: strict JSON report with `ok`, `findings[]`, `to_verify[]` and `budget`; exit 0, 1 or 2
- Pacing table by trip style, with a travel-day penalty and a scheduled-hours cap
- A fixed report: day table, budget table, document checklist, to-verify list, assumptions
- A document checklist by trip type and a table of where each fact kind is verified
- An itinerary template file

## When to use

You ask to plan a trip, build or fix an itinerary, budget a holiday, or check whether a plan is too packed.

## When not to use

Booking, live flight or hotel prices, legal visa advice, turn-by-turn navigation, or non-travel schedules such as a project plan or a meeting agenda.

## Requirements

Python 3.9 or newer, standard library only, for the checker. No network. Without Python the skill gives a manual check.

## Install

Copy the folder to `.claude/skills/travel-planner/` or `.agents/skills/travel-planner/`. No version is pinned yet; this is a draft.

## Examples

Prompt: "Here is my weekend plan. Will it fit my budget, and what do I need to check before I book anything?" with `evals/files/t3-over-budget.json`.

Checker output (real run, abridged):

```
"ok": false
"summary": {"days": 1, "items": 3, "activities": 1, "errors": 1, "warnings": 4, "facts_to_verify": 4}
error   over_budget     planned spend 530 exceeds budget 500 EUR by 30
warning unverified_fact hotel   unverified price fact: 300 EUR for the night
warning unverified_fact tour    unverified hours fact: Tour departs 10:00
warning unverified_fact tour    unverified price fact: 90 EUR per person
warning unverified_fact dinner  unverified price fact: Set menu 25 EUR
"budget": {"total": 530.0, "budget_total": 500.0, "remaining": -30.0}
```

Prompt: "This plan feels too packed" with `evals/files/t2-packed-day.json`. Real run: 3 errors (`pacing_limit`: 3 activities on a relaxed day, allowed 2; two `missing_transit_buffer` for 5-minute gaps across areas), 7 warnings, 75 GBP planned of 400.

The skill's report text for these prompts has not been run with a model; only the checker output above is from a saved run.

## Limits

The script checks internal consistency only. It cannot know opening days, real transfer times or visa rules. One currency, no overnight blocks. It does not book, search live prices or navigate. Visa and health rules are not legal or medical advice.

## How it differs from nearby skills

There is no other trip skill in the registry. `task-breakdown-coach` and `plan-stress-test` plan work and decisions, not travel; this skill is limited to itineraries and carries a travel-specific checker.

## Evidence

Static lint: 0 FAIL, 0 WARN (see VERIFICATION.md). Checker fixtures: 6 of 6 cases pass on Python 3.11. Trigger, efficacy, cross-tool and human review: not done.

## Demo script (60 to 90 seconds)

1. Prompt: "Plan 4 relaxed days in Rome for two, 2400 EUR." The agent asks at most four questions, states assumptions.
2. The agent writes trip.json with 2 activities per day and every hour and price marked unverified.
3. The checker runs; one `missing_transit_buffer` error appears; the agent moves a start time and re-runs to `ok: true`.
4. The final reply shows the day table, the budget table, the document checklist and a to-verify list of hours and prices with where to check each.

Before: a confident plan with invented opening hours. After: a plan that says what to confirm.

## FAQ seeds

- Does it need network? No.
- Does it book anything or look up prices? No; it lists what you must check.
- Why are all hours marked unverified? The agent cannot know them for your date; you or a fetched official page must supply them.
- Does it work in tool X? Only a file-reading agent with Python is needed; cross-tool runs have not been done.
- Can I change the pacing limits? Pick another trip style; the constants are not meant to be edited.
- What data leaves my machine? None from the script; it reads one file.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; lint and fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
