# reading-guide-question-ladder

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when turning a complete supplied passage and learning goal into an evidence-grounded ladder of locating, explaining, interpreting, and evaluating questions. Do not use for outlining notes, adding outside facts, or asking factual questions the passage cannot answer.

## Task boundary

classroom-quiz-builder creates assessment questions; this builds a source-linked progression of reading questions and teacher notes, preserving text boundaries and unsupported causal conclusions.

## Try the independent synthetic example

Create an ordered reading-question ladder from this complete passage.
Paragraph 1: Mina covered one tray of seedlings with a clear lid and left another tray uncovered.
Paragraph 2: After three days, the covered tray’s soil looked damp, while the uncovered tray’s soil looked dry. The passage suggests the lid may have slowed moisture loss.
Learning goal: Separate observations from the passage’s qualified interpretation.
Permitted moves: locating, explaining, evaluating.
Expected response length: one or two sentences per answer.
Reflection questions: not allowed.
For every question, give its passage location, cognitive move, expected evidence and length, answerability check, and any limit. Include a brief teacher note.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_1b97612002cf`:

```text
{"learning_goal":"Separate observations from the passage’s qualified interpretation.","question_ladder":[{"question":"What did Mina do with the two trays?","passage_location":"Paragraph 1","cognitive_move":"locating","expected_evidence":"She covered one tray with a clear lid and left the other uncovered.","expected_response_length":"One or two sentences","answerability":"supported","limits_or_reflection":null},{"question":"What difference in soil condition appeared after three days?","passage_location":"Paragraph 2","cognitive_move":"locating","expected_evidence":"The covered tray’s soil looked damp and the uncovered tray’s looked dry.","expected_response_length":"One or two sentences","answerability":"supported","limits_or_reflection":null},{"question":"How does the passage qualify its interpretation of the lid’s effect?","passage_location":"Paragraph 2","cognitive_move":"explaining","expected_evidence":"It says the lid may have slowed moisture loss, presenting this as a possibility.","expected_response_length":"One or two sentences","answerability":"supported","limits_or_reflection":null},{"question":"Does the passage establish that the lid caused the moisture difference?","passage_location":"Paragraph 2","cognitive_move":"evaluating","expected_evidence":"No; it reports an association and offers only a qualified suggestion.","expected_response_length":"One or two sentences","answerability":"supported","limits_or_reflection":"Do not claim more than the passage states."}],"teacher_note":{"status":"complete","unresolved_limits":["The passage does not establish causation beyond the qualified suggestion."]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
