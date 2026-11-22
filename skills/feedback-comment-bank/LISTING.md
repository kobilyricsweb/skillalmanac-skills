# feedback-comment-bank

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when evaluators need concise formative comments tied to supplied rubric criteria and observable response patterns. Do not use for customer-service replies, grading absent work, trait judgments, or feedback based on evidence not provided.

## Task boundary

study-and-teaching-kit builds teaching materials and classroom-quiz-builder creates questions; this builds rubric-grounded formative comments from supplied criteria and observed patterns, producing no lesson plan, quiz, score or gradebook update.

## Try the independent synthetic example

Build a reusable formative comment bank. Rubric criterion: Evidence—each claim should be linked to one supplied observation. Observable pattern: a response states “The lid reduced heat loss” and cites the observation “covered cup: 42°C; uncovered cup: 35°C,” but does not explain the link. Tone: neutral and encouraging. Revision opportunity: learners may revise by adding one sentence connecting the temperatures to the claim. Comment limit: 35 words. Do not assign a score. Return structured JSON.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_9e28321510bd`:

```text
{"entries":[{"criterion":"Evidence","observable_pattern":"The response claims that the lid reduced heat loss and shows temperatures of 42°C for the covered cup and 35°C for the uncovered cup, but does not connect them.","comment":"You supplied relevant temperatures. Add one sentence explaining how the higher covered-cup temperature supports the claim.","next_action":"Explain the link between the two temperatures and the heat-loss claim.","prohibited_overclaim":"Do not assign a score or infer the learner’s understanding, effort, or intent; do not claim the evidence is absent.","status":"supported"}],"missing_inputs":[],"conflicts":[]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
