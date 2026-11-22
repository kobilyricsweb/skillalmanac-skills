# assessment-accommodation-translation

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when an exact approved accommodation statement must become concrete assessment logistics while preserving supplied construct, item content, response demand, scoring, format, and constraints, including partial analysis when baselines are missing. Do not use for eligibility decisions, diagnosis, legal judgments, private profiling, or unapproved assessment changes.

## Task boundary

study-and-teaching-kit prepares instructional plans, while schedule-conflict-check evaluates timing and resource clashes. assessment-accommodation-translation instead converts an exact approved accommodation into bounded assessment logistics while preserving supplied construct, content, response demand, scoring, and format and exposing missing or conflicting implementation conditions.

## Try the independent synthetic example

Prepare assessment logistics from these facts. Assessment: 20-minute paper vocabulary quiz, 10 written items, scored for word meaning; standard materials are pencil and printed quiz; standard room R1 at 09:00. Exact approved accommodation: “50% additional time and a low-distraction room.” Available: room R2 from 09:00–09:40 and one proctor. Preserve item content, written response format, and scoring target. Identify the baseline, map the approved changes, calculate timing, and distinguish implementation from authorization.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_096b9e70ab26d779`:

```text
{"baseline":{"format":"paper vocabulary quiz","construct":null,"item_content":"10 vocabulary items","response_demand":"written responses","scoring_target":"word meaning","standard_minutes":20,"materials":["pencil","printed quiz"],"instructions":null,"room":"Room R1","staffing":null,"equipment":null,"session_constraints":"Standard start 09:00; Room R2 available 09:00–09:40; one proctor available","conditions":"Standard Room R1 at 09:00"},"implementations":[{"approval_text":"50% additional time","operational_change":"Add 10 minutes, making the assessment duration 30 minutes.","status":"implementable","source":"exact approved accommodation"},{"approval_text":"a low-distraction room","operational_change":"Administer the quiz in a room confirmed to be low-distraction for the full 30-minute period beginning at 09:00.","status":"unresolved","source":"exact approved accommodation"}],"calculated_timing":{"standard_minutes":20,"additional_minutes":10,"total_minutes":30,"calculation":"20 × 0.50 = 10; 20 + 10 = 30"},"preserved_elements":["10-item content","written response demand","word-meaning scoring target","paper format","pencil and printed quiz"],"unresolved":[{"issue":"Room R2 is available from 09:00–09:40, but it is not confirmed to be low-distraction.","needed_decision":"The responsible assessment authority must confirm that R2 has the approved low-distraction property or authorize another qualifying room."},{"issue":"Availability of Room R1 beyond the standard period was not supplied.","needed_decision":"Confirm the assigned qualifying room for the complete 09:00–09:30 assessment window."},{"issue":"The assessed construct was not supplied; the word-meaning scoring target alone does not establish it.","needed_decision":"Supply the intended construct before evaluating construct fidelity."},{"issue":"Standard instructions were not supplied.","needed_decision":"Supply the instructions before claiming preservation or completing fidelity review."},{"issue":"Standard staffing was not supplied.","needed_decision":"Confirm whether one proctor satisfies standard staffing requirements."},{"issue":"Equipment requirements were not supplied.","needed_decision":"Confirm whether standard equipment is required."}],"assumptions":[],"traceability":[{"change":"10 additional minutes, total duration 30 minutes","approval_source":"50% additional time","construct_status":"unverified"},{"change":"Use a room confirmed as low-distraction","approval_source":"a low-distraction room","construct_status":"unverified"},{"change":"Any alteration to items, written responses, scoring, or paper format","approval_source":"No authorization supplied","construct_status":"authorization_required"}]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
