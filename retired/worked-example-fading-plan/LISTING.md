# worked-example-fading-plan

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when an educator needs a staged progression from demonstration to independent performance for one supplied procedure, including explicit handling of missing inputs and retained prompts. Do not use for redesigning example collections, diagnosing misconceptions, creating assessments, or broadening coverage across cases.

## Task boundary

study-and-teaching-kit builds teaching material and classroom-quiz-builder creates questions; this sequences diminishing support for one supplied procedure, building no lesson, quiz or assessment. example-set-diversifier selects varied rule examples.

## Try the independent synthetic example

Create a fading plan. Target procedure: compare two numbers by (1) read both numbers, (2) compare their values, (3) write >, <, or =. Complete worked example: compare 2 and 3; read 2 and 3; determine 2 is less than 3; write 2 < 3. Prerequisites: the learner can read digits 0–5, but there is no evidence that symbol meanings are secure. Common error: reverses < and >. Final independent task: "Compare 4 and 1 using >, <, or =." Return stages, support changes, retained prompts and their basis, independence evidence, rationale, exact final-task treatment, assumptions, conflicts, and limits.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_a2068c39e77d`:

```text
{"planning_status":"complete","missing_fields":[],"stages":[{"stage":"Demonstration","learner_task":"Follow comparison of 2 and 3.","shown_reasoning":["Read both numbers: 2 and 3.","Compare their values.","Write 2 < 3."],"prompts":["Check which number is smaller."],"removed_support":[],"independence_evidence":"Learner identifies the smaller number and selects a comparison symbol with support.","rationale":"All steps remain visible while the symbol-direction prompt addresses the supplied reversal error."},{"stage":"Prompted completion","learner_task":"Compare two supplied digits.","shown_reasoning":["Read both numbers."],"prompts":["Compare their values.","Choose >, <, or = and check its direction."],"removed_support":["Demonstrated comparison result","Demonstrated written symbol"],"independence_evidence":"Learner compares values and writes the appropriate relation after prompts.","rationale":"Reading is supported as a stated prerequisite; comparison and symbol choice become active tasks."},{"stage":"Independent task","learner_task":"Compare 4 and 1 using >, <, or =.","shown_reasoning":[],"prompts":[],"removed_support":["All demonstrated reasoning","Symbol-direction prompts"],"independence_evidence":"Learner independently reads 4 and 1, compares them, and writes a correct relation.","rationale":"The exact final task is reserved for independent completion."}],"retained_prompts":[{"prompt":"Check the direction of < or > before finalizing.","basis":"Supplied common error: reversing < and >."}],"final_task_treatment":"Use the final task exactly as supplied; do not provide its answer.","assumptions":[],"conflicts":[],"limits":["No mastery or learning gain is claimed; symbol security is not established beforehand."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
