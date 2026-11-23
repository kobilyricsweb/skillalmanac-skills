# Verification — document-consistency-check

Status: unpublished free candidate; no Platform Score or native verification.

The earlier instruction and reference text occurs verbatim in the retained with-skill prompt. The later licence/tier metadata revision was not exercised in that historical trial.
The retained v012 trial contains 3 cases. A fresh model graded anonymized A/B outputs
against author-designed factual assertions; the mapping and raw outputs are retained.

- Baseline assertions: 9 pass, 3 fail, 0 unclear.
- With-skill assertions: 12 pass, 0 fail, 0 unclear.
- Trial author/executor: gpt-5.6-luna, low effort; blind grader: gpt-5.6-sol, low effort.
- Raw evidence: sprint `agents/baseline_v012`, `agents/with_skill_v012`,
  `agents/blind_smoke_grade_v012`, `private-grading-map-v012.json`.

These are batched inline manual smoke trials, one repetition per task, with visible supplied
instructions. They do not establish automatic skill routing, successful native loading, portability,
statistical efficacy, real customer outcomes, or a 10/10 rating. Assertions are test specifications,
not independent ground truth. A stronger baseline often already performs well.

Initial and revised source reviews found real defects; the shared batch report records repairs
and boundaries. Native execution is blocked in the current Windows registered-Core runtime,
including the matching installed-app CLI. The owner approved Apache-2.0 and Global Media Holdings as copyright holder. Cross-tool and human review and the existing house release gates remain open.

## Reproduce

From the shared sprint evidence directory, use Python 3.9+:

`python "reproduction_tools/replay_package.py" "<absolute-skill-folder>" --mode agent-cases`

For instruction-only skills, agent-cases prints the exact prompts/assertions and executes no model.
For scripted skills, fixtures replays all retained script cases and compares exit/JSON against the
saved observed results; it is a regression replay, not independent truth. Original expected checks
remain in the evaluation specifications. Native discovery must be tested separately.

## Owner licence and commercial decision,2026-11-21

Apache-2.0 is approved for this package. The unmodified standard text is included at the batch root in LICENSE and per package in LICENSE.txt; NOTICE.txt carries Copyright 2026 Global Media Holdings (skillalmanac.com). Historical raw evidence is retained unchanged and does not define current terms.

Editorial metadata tier: `free`. Tier is not computed from Platform Score or User Score. Licence approval does not close native, cross-tool or human review gates. No public launch or score is inferred.

## Portable review command

From the skillalmanac repository root:

`python content/review/tools/replay_package.py content/review/batch_03_free/document-consistency-check --mode agent-cases`

Prints corrected task prompts/assertions only; it does not run a model or establish native efficacy.
