# nurture-sequence-logic-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when approved messages, audience states, permitted transitions, timing constraints, exclusions, and terminal conditions must be organized into an auditable logic map. Do not use for defining an entire campaign, predicting engagement, sending messages, or inventing entry rules, destinations, or transitions absent from the supplied design.

## Task boundary

email-marketing-sequences writes email sequences; this maps entry conditions, states, transitions, prerequisites and exclusions of a supplied sequence, writing no emails, cadence or automation.

## Try the independent synthetic example

Create a sequence logic map from this complete synthetic design. Initial entry rule: start in S0 when the audience is new. Approved messages: M1, purpose "welcome", prerequisite "none"; M2, purpose "explain setup", prerequisite "M1 sent". Audience states: S0="new"; S1="welcomed"; S2="setup explained". Transition rules: R1 moves S0 to S1 when M1 is completed; R2 moves S1 to S2 when M2 is completed. Timing constraints: M1 may occur immediately; M2 must be at least one day after M1. Exclusions: opted-out people receive no later message. Terminal conditions: opt-out from any state ends every branch; reaching S2 completes the sequence. Produce the documentary map only; do not schedule or send anything.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_03fe0d916dda`:

```text
{"missing_inputs":[],"paths":[{"branch_id":"main-1","entry_state":"S0","destination_state":"S1","entry_condition":"Audience is new, per the initial entry rule.","message_id":"M1","purpose":"welcome","prerequisite":"none","cited_transition":"R1","transition_condition":"M1 is completed.","timing":"immediately","terminal_behavior":null,"placement_status":"placed","gap":null},{"branch_id":"main-2","entry_state":"S1","destination_state":"S2","entry_condition":"S1 is reached through R1.","message_id":"M2","purpose":"explain setup","prerequisite":"M1 sent","cited_transition":"R2","transition_condition":"M2 is completed.","timing":"at least one day after M1","terminal_behavior":null,"placement_status":"placed","gap":null},{"branch_id":"stop-opt-out","entry_state":"any state","destination_state":null,"entry_condition":"opt-out","message_id":null,"purpose":null,"prerequisite":null,"cited_transition":null,"transition_condition":null,"timing":null,"terminal_behavior":"Stop the sequence; no later message is permitted.","placement_status":"terminal","gap":null},{"branch_id":"stop-complete","entry_state":"S2","destination_state":null,"entry_condition":"S2 is reached","message_id":null,"purpose":null,"prerequisite":null,"cited_transition":null,"transition_condition":null,"timing":null,"terminal_behavior":"The sequence is complete.","placement_status":"terminal","gap":null}],"exclusions":[{"exclusion_text":"Opted-out people receive no later message.","scope":"opted-out people","condition":"opt-out","effect":"No later message is permitted."}],"unplaced_messages":[],"unreachable_states":[],"conflicts":[],"open_gaps":[]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
