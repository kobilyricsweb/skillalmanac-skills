# concept-contrast-table

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when supplied definitions, examples, nonexamples, and learner confusions must become a focused comparison with evidence-backed boundaries. Do not use for terminology standardization, general glossary work, unsupported distinctions, or a discriminating question the inputs cannot establish.

## Task boundary

study-and-teaching-kit builds teaching material and classroom-quiz-builder creates questions; this contrasts supplied concepts from their supplied definitions, examples and nonexamples, building no lesson, quiz or flashcards.

## Try the independent synthetic example

Create a decision-focused contrast for novice editors. Concept A, “draft,” means content still open to substantive change. Approved example: a memo awaiting author review. Nonexample: a memo formally released to staff. Concept B, “published,” means content formally released to its intended audience. Approved example: a memo emailed to all staff after approval. Nonexample: a memo saved privately. Known confusion: learners think polished formatting makes a document published. Use only the supplied facts, identify the classification cues, and determine whether the evidence supports an either-or discriminating question.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_exec_medium_2f0d65f81819`:

```text
{"orientation":"Decide from change status and formal release, not formatting.","concepts":[{"name":"draft","defining_features":["Still open to substantive change"],"non_features":["Polished formatting alone does not establish draft status","A memo formally released to staff is not a draft"],"support_status":"supported"},{"name":"published","defining_features":["Formally released to its intended audience"],"non_features":["Polished formatting alone does not establish publication","A privately saved memo is not published"],"support_status":"supported"}],"boundary_cases":[{"case":"Memo awaiting author review","classification":"draft","basis":"Approved draft example."},{"case":"Memo emailed to all staff after approval","classification":"published","basis":"Approved published example."}],"recognition_cues":["Ask whether substantive changes remain open.","Ask whether the content was formally released to its intended audience.","Ignore formatting polish as proof of publication."],"discriminating_question":null,"evidence":[{"claim":"A memo awaiting author review is a draft.","source_input":"Approved draft example."},{"claim":"An approved memo emailed to all staff is published.","source_input":"Approved published example."}],"unresolved_ambiguities":["The evidence does not rule out content satisfying both definitions.","The evidence does not establish that every item must satisfy one definition, so an either-or question is unsupported."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
