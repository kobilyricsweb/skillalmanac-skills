# practice-spacing-schedule

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when a fixed item set must be distributed across bounded sessions using supplied prerequisites, capacities, review obligations, permitted intervals, and fixed placements; partial scheduling is supported when missing constraints can be isolated. Do not use for recurring-work authorization, learning-effect claims, or inputs too incomplete to construct any checkable portion.

## Task boundary

study-and-teaching-kit creates study plans and spaced-repetition schedules from supplied learning material. practice-spacing-schedule focuses on constraint satisfaction for a fixed item set, including prerequisites, session capacities, mandatory reviews, permitted intervals, fixed placements, conflicts, and defensible deferrals.

## Try the independent synthetic example

Create the structured practice schedule and constraint audit. Items: A is tagged basics and has no prerequisite; B is tagged application and requires prior practice of A. There are 3 sessions with 2 slots each. Intervals count sessions. Every new item must receive one retrieval review exactly 1 session later. Fixed placements require A as new practice in session 1 and B as new practice in session 2. When earlier-skill work occurs in a session containing newer work, identify it as cumulative mixing. Report every unused slot and do not claim an optimal learning effect.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_c5d3b049c918c00c`:

```text
{"schedule_status":"feasible","sessions":[{"session":1,"capacity":2,"placements":[{"slot":1,"item_id":"A","skill_tag":"basics","labels":["new"],"reason":"Fixed placement introduces A in session 1.","review_of_session":null}],"unused_capacity":1,"over_capacity":0},{"session":2,"capacity":2,"placements":[{"slot":1,"item_id":"B","skill_tag":"application","labels":["new"],"reason":"Fixed placement introduces B after prior practice of prerequisite A.","review_of_session":null},{"slot":2,"item_id":"A","skill_tag":"basics","labels":["retrieval_review","cumulative_mixing"],"reason":"Required retrieval review exactly 1 session after introduction; it also mixes earlier basics work with newer application work.","review_of_session":1}],"unused_capacity":0,"over_capacity":0},{"session":3,"capacity":2,"placements":[{"slot":1,"item_id":"B","skill_tag":"application","labels":["retrieval_review"],"reason":"Required retrieval review exactly 1 session after introduction.","review_of_session":2}],"unused_capacity":1,"over_capacity":0}],"deferred_items":[],"unused_capacity_report":{"total_unused":2,"by_session":[{"session":1,"unused":1},{"session":2,"unused":0},{"session":3,"unused":1}]},"constraint_audit":{"prerequisites":"satisfied","capacities":"satisfied","review_intervals":"satisfied","conflicts":[],"unresolved_constraints":[]},"assumptions":["Each stated slot is one capacity unit."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
