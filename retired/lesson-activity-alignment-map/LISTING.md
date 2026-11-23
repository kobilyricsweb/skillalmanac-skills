# lesson-activity-alignment-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when a lesson plan must show which supplied activities produce observable evidence for each stated learning objective and assessment criterion. Do not use for prerequisite mapping, inventing new activities or assessments, or treating topic exposure and attendance as demonstrated alignment.

## Task boundary

study-and-teaching-kit builds teaching material; this only checks supplied activities against supplied objectives and criteria for observable evidence, inventing no activity, assessment or lesson change. tutorial-prerequisite-mapper models step prerequisites.

## Try the independent synthetic example

Create an alignment map. Objective O1: learners classify two shapes as triangle or not triangle. Objective O2: learners explain why a triangle has three sides. Activity A1: learners label two supplied shape cards and submit the labels; product is a two-label card; time 3 minutes. Activity A2: teacher explains the three-side rule while learners listen; no learner product; time 2 minutes. Criterion C1: both A1 labels are correct. Criterion C2: the learner gives a reason mentioning three sides. Total lesson time is 5 minutes. Do not invent or change activities.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_51a8a20003aa`:

```text
{"connections":[{"objective":"O1: learners classify two shapes as triangle or not triangle","activity":"A1: label two supplied shape cards and submit the labels","learner_action":"Label both supplied shape cards","evidence":"Two-label card","criterion_connection":"Both labels are correct","classification":"direct_evidence","time_minutes":3,"uncertainty":[]},{"objective":"O2: learners explain why a triangle has three sides","activity":"A2: teacher explains the three-side rule while learners listen","learner_action":"No learner explanation is supplied; learners listen","evidence":"No learner product or observable explanation supplied","criterion_connection":"Criterion requires a reason mentioning three sides","classification":"exposure_only","time_minutes":2,"uncertainty":[] }],"time_accounting":{"stated_limit_minutes":5,"known_mapped_minutes":5,"status":"feasible"},"uncovered_objectives":["O2 is not demonstrated by A2"],"conflicts":[],"proposals":[]} 
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
