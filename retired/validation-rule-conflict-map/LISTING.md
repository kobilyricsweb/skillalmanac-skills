# validation-rule-conflict-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when labeled validation rules from multiple notes overlap or contradict and implementers need a field-level compatibility analysis. Do not use for making an unstated policy choice, separating general decision evidence, or writing validation code.

## Task boundary

Nearest is decision-evidence-ledger; this analyzes operational rule compatibility rather than separating decisions, proposals, and assumptions.

## Try the independent synthetic example

Map these supplied rules. R1: field seats; scope all basic plans; seats must be at most 3, inclusive; unit seats. R2: field seats; scope all basic plans; seats must be at least 4, inclusive; unit seats. No precedence or exception is supplied. Produce a field-level conflict map with original wording, exact constraints, scope intersection, classification, precedence evidence, resolution status, unresolved questions, assumptions, and limits. Do not choose a winner or write validation code.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_4ab8e867f451`:

```text
{"conflict_map":[{"source_ids":["R1","R2"],"field":"seats","original_rules":["field seats; scope all basic plans; seats must be at most 3, inclusive; unit seats","field seats; scope all basic plans; seats must be at least 4, inclusive; unit seats"],"scope_intersection":"All basic plans","exact_constraints":["seats <= 3 seats, inclusive","seats >= 4 seats, inclusive"],"classification":"contradictory","precedence_evidence":"No precedence or exception supplied.","resolution_needed":true,"unresolved_reason":"The rules admit no common seats value; governing authority is unspecified."}],"unresolved_questions":["Which rule, if either, governs all basic plans?","Is the scope or applicability of either rule misstated?"],"assumptions":["The supplied scope and unit wording apply exactly as written."],"limits":["Compatibility analysis only; no winner, policy, or validation code is provided."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
