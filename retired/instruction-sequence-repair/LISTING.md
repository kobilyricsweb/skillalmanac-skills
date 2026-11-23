# instruction-sequence-repair

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when a complete set of written instructions has explicit dependencies, hidden prerequisites, forward references, or late verification steps and needs a dependency-supported reordering. Do not use for general prerequisite mapping, rewriting immutable actions, inventing missing steps, or changing an instruction sequence without supplied dependency evidence.

## Task boundary

Nearest is tutorial-prerequisite-mapper; this repairs sequence order rather than merely identifying prerequisite relationships.

## Try the independent synthetic example

Repair this instruction sequence while preserving every step exactly: 1. “Verify the blue tag is attached.” 2. “Open the empty case.” 3. “Attach the blue tag.” 4. “Place the card in the case.” Dependencies: opening the case must precede placing the card; attaching the blue tag must precede verifying it; placing the card must occur after the case is open. The verification step targets attachment of the blue tag and should immediately follow that action. Starting state: the case is closed and empty; the tag and card are available. Expected end state: the open case contains the card and the tag attachment has been verified. All step text is immutable.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_75178eb4c9c6`:

```text
{"repaired_steps":[{"original_position":2,"new_position":1,"text":"Open the empty case."},{"original_position":3,"new_position":2,"text":"Attach the blue tag."},{"original_position":1,"new_position":3,"text":"Verify the blue tag is attached."},{"original_position":4,"new_position":4,"text":"Place the card in the case."}],"move_log":[{"step_text":"Open the empty case.","original_position":2,"new_position":1,"supporting_dependency":"Opening must precede placing the card."},{"step_text":"Attach the blue tag.","original_position":3,"new_position":2,"supporting_dependency":"Attaching must precede verifying."},{"step_text":"Verify the blue tag is attached.","original_position":1,"new_position":3,"supporting_dependency":"Verification immediately follows the attachment action."},{"step_text":"Place the card in the case.","original_position":4,"new_position":4,"supporting_dependency":"Placement occurs after the case is open."}],"verification_notes":[{"checkpoint":"Verify the blue tag is attached.","target_action":"Attach the blue tag.","placement":"Immediately after attachment, at position 3.","status":"supported"}],"unresolved_issues":[],"reachability_status":"supported"}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
