# Verification — claim-evidence-map

Status: unpublished free candidate; no Platform Score or native verification.

The earlier instruction and reference text occurs verbatim in the retained with-skill prompt. The later licence/tier metadata revision was not exercised in that historical trial.
The retained v013 trial contains 5 cases. A fresh model graded anonymized A/B outputs
against author-designed factual assertions; the mapping and raw outputs are retained.

- Baseline assertions: 19 pass, 1 fail, 0 unclear.
- With-skill assertions: 20 pass, 0 fail, 0 unclear.
- Trial author/executor: gpt-5.6-luna, low effort; blind grader: gpt-5.6-sol, low effort.
- Raw evidence: sprint `agents/baseline_v013`, `agents/with_skill_v013`,
  `agents/blind_smoke_grade_v013`, `private-grading-map-v013.json`.

These are batched inline manual smoke trials, one repetition per task, with visible supplied
instructions. They do not establish automatic skill routing, successful native loading, portability,
statistical efficacy, real customer outcomes, or a 10/10 rating. Assertions are test specifications,
not independent ground truth. A stronger baseline often already performs well.

The v0.1.2 source failed to split compound claims; v0.1.3 explicitly fixes this. Its follow-up
includes three original cases and two newly added holdouts. Raw with-skill output had invalid outer
JSON (five stray empty-string fragments). `syntax-normalization.json` records syntax-only removal,
retains the raw hash, and changes no answer text. The semantic grade uses that normalized copy.
**Strict outer-JSON protocol failed**, despite passing semantic assertions. No all-protocol pass is
claimed; fresh native execution and strict output validation are still required.

Initial and revised source reviews found real defects; the shared batch report records repairs
and boundaries. Native execution is blocked in the current Windows registered-Core runtime,
including the matching installed-app CLI. The owner approved Apache-2.0 and Global Media Holdings as copyright holder. Cross-tool and human review and the existing house release gates remain open.

## Cross-review correction

Claude identified a flawed expected answer or missing attachment in the original ordinary case.
The current eval prompt/expectations are corrected; the raw earlier trial and grade remain unchanged.
The numbers above describe the OLD cases only and do not validate the corrected suite. Claim-map
now preserves the ambiguous period as a separate case; it must not infer whole-trial duration.
Read the sprint `EVAL_CORRECTIONS.md`. Fresh execution of the corrected cases remains OPEN.

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

`python content/review/tools/replay_package.py content/review/batch_03_free/claim-evidence-map --mode agent-cases`

Prints corrected task prompts/assertions only; it does not run a model or establish native efficacy.
