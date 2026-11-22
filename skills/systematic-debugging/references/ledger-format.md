## Contents

- Markdown layout
- JSON layout
- Field rules
- Finding codes
- Output shape

## Markdown layout

```
# Ledger: <one-line symptom>

## Reproduction
- command: <exact command or steps>
- reproduced: yes
- minimised: <the smallest failing case>
- bisect: <what was bisected (time, input, code) and the result>

## Hypotheses
### H1
- statement: <a cause, in one sentence>
- prediction: <what you will observe if it is true, and what if it is false>
- status: open | confirmed | refuted | abandoned

## Experiments
### E1
- hypothesis: H1
- changed: <the one variable>
- result: <what was observed>
- outcome: confirmed | refuted | inconclusive

## Root cause
<mechanism and location, one or two sentences>
- hypothesis: H1

## Regression test
- id: T1
- path: <test file and name>
- failed before fix: yes
- failure output: <pasted failing assertion or error>

## Fix
- description: <what changed>
- test: T1
- test passes after: yes
```

The order of the `## Regression test` and `## Fix` headings is the order of recording: the test must come first. A list of changed variables may be written as `a; b` on one line or as indented sub-bullets under `- changed:`. Separate variables with a semicolon, never a comma.

## JSON layout

An object with the same names: `reproduction` (object), `hypotheses` (array of objects), `experiments` (array; `variables_changed` is an array of strings), `root_cause` (string, or object with `text` and `hypothesis`), `regression_test` (object, or `regression_tests` array), `fix` (object). Optional integer `seq` on a test and on the fix: the test's must be smaller.

## Field rules

- Hypothesis `status` `abandoned` needs a `reason`; it removes the hypothesis from the untested count.
- An experiment settles a hypothesis only if exactly one variable is listed and the outcome is confirmed or refuted. Experiments with zero or several variables count as invalid, so a hypothesis supported only by them is untested.
- A root cause must be backed by a hypothesis with a valid confirming experiment.
- `failed before fix` accepts yes, true, y, 1, fail, failed.

## Finding codes

Errors (exit code 1):

| Code | Meaning |
|---|---|
| no_reproduction, not_reproduced | Nothing recorded, or `reproduced` is not yes |
| no_hypotheses, no_statement, no_prediction, duplicate_id | Hypothesis table incomplete |
| untested_hypothesis | No valid confirming or refuting experiment (and not abandoned) |
| status_unsupported | Status says confirmed or refuted without a matching valid experiment |
| experiment_unknown_hypothesis, experiment_no_result, experiment_bad_outcome | Experiment row incomplete |
| experiment_no_variable, multi_variable_experiment | Zero or several variables changed |
| root_cause_too_short, root_cause_not_confirmed | Root cause missing detail or unsupported |
| fix_without_root_cause | Fix with no root cause statement |
| fix_without_failing_test | No test, or not recorded as failing, or no pasted failure output |
| fix_before_test | Fix recorded before the test (section order or `seq`) |
| fix_unknown_test, fix_test_still_failing | Fix names a missing test, or the test still fails after |

Warnings (do not change the exit code): no_minimisation, no_bisect, possible_multi_variable, status_stale, abandoned_without_reason, root_cause_hedged, fix_no_description, test_without_fix.

## Output shape

One JSON object: `ok`, `counts`, `untested_hypotheses`, `multi_variable_experiments`, `experiments_without_variable`, `fix_recorded`, `fix_without_failing_test`, `findings` (array of `severity`, `code`, `where`, `message`), `file`. On usage problems: `ok` false and `error`, exit code 2.
