# state-machine-transition-table

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when plain-text behavior notes define states, events, guards, and effects but leave permitted transitions unclear. Do not use for comparing document assertions, implementing code, or inferring forbidden transitions from silence.

## Task boundary

architecture-diagrams creates visual architecture or state diagrams; this extracts a transition table with supplied guards, effects, unknown destinations and conflict rows from notes, and draws no diagram.

## Try the independent synthetic example

Create a transition table from these complete notes. States: Draft, Submitted, Approved. Events: submit means a user requests submission; approve means a reviewer accepts a submission. N1: From Draft, submit with guard "title is present" moves to Submitted and records submitted=true. N2: From Submitted, approve moves to Approved and records approved=true. N3: Any state/event combination not listed is explicitly unspecified, not forbidden. Include evidence, status, unresolved cases, and assumptions. Do not implement code, run tests, or authorize system changes.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_3b1bbe1c52ba`:

```text
{"transitions":[{"source_state":"Draft","event":"submit","guard":"title is present","destination":"Submitted","effect":"records submitted=true","evidence":["N1"],"status":"conditional"},{"source_state":"Submitted","event":"approve","guard":null,"destination":"Approved","effect":"records approved=true","evidence":["N2"],"status":"documented"}],"unresolved_cases":["All other state/event combinations are unspecified, not forbidden, because no default rule is supplied.","No additional guards or effects are defined."],"normalization_assumptions":[],"scope_exclusions":["Code implementation","Testing","System changes or authorization"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
