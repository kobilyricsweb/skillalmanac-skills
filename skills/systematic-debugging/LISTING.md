# Listing page content: systematic-debugging

**One line:** Makes an agent debug by evidence, with a ledger that a script checks before any bug is called fixed.

## What it does

The skill gives an agent a fixed eight-step procedure: reproduce, minimise, bisect, record hypotheses each with a prediction, run single-variable experiments, state the root cause, write a failing regression test, then fix. Everything goes into one ledger file. A validator script reads the ledger (Markdown or JSON) and prints strict JSON listing hypotheses that were never validly tested, experiments that changed more than one variable, and a fix recorded without a failing test first. A reference gives the numbers agents tend to get wrong: how many runs prove a flaky fix (23 runs for a 5-in-40 failure), how many bisect steps a commit range needs, and the exit codes of `git bisect run`.

## Capabilities

- `scripts/ledger_check.py <ledger>`: JSON report with `ok`, counts, untested hypotheses, multi-variable experiments, `fix_without_failing_test` and per-finding codes; exit 0, 1 or 2
- A ledger format in Markdown and JSON with a field-by-field rule list
- A narrowing playbook: run-count table, input halving, bisect and environment-difference method
- A decision table for the common traps (sleep that hides the bug, two surviving hypotheses, no testable seam)
- A fixed final report that includes what was not verified

## When to use

An agent is guessing at a bug; a test fails only in CI or intermittently; a regression has no known commit; you say debug this properly, find the root cause or stop shotgun debugging; you want to check a debugging record someone wrote.

## Compared with `engineering:debug`

The installed `engineering:debug` plugin skill gives a general debugging session flow. This skill adds a hypothesis ledger with a validator script (one-variable experiments, predictions before runs, a failing regression test before the fix), run-count and bisect tables, and a fixed report.

## When not to use

Writing new tests, code review, performance profiling, or explaining what an error message means. Difference from `reviewing-code-changes` (batch 1): that skill reviews a finished diff; this one governs how a cause is found before any diff exists. Difference from `perf-investigation`-type skills: this one needs a deterministic pass/fail oracle, which profiling usually does not have.

## Requirements

Python 3.9 or newer for the validator (standard library only). No network. Git for the bisect step when a good commit is known. Without Python the agent applies the checklist in step 8 by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from saved fixtures; no with-skill agent run exists yet.

1. A ledger written by a developer who is about to apply a fix (`evals/fixtures/draft_t2.md`):

   `python scripts/ledger_check.py evals/fixtures/draft_t2.md` gives `ok: false`, exit code 1, 8 errors and 3 warnings, among them:

   ```
   error multi_variable_experiment E1 - 2 variables changed (SMTP timeout 10 s to 30 s; retry count 3 to 1). One experiment changes one variable.
   error untested_hypothesis H2 - Hypothesis is untested (no experiment).
   error status_unsupported H1 - Status is confirmed but no valid single-variable experiment has that outcome.
   error fix_without_failing_test fix - A fix is recorded but no regression test is.
   warning root_cause_hedged root_cause - Root cause contains a hedge word; a root cause is something an experiment confirmed.
   ```

2. A complete ledger (`evals/fixtures/ledger_good.json`): `ok: true`, exit code 0, 0 errors, 0 warnings.

## Limits

- The validator checks that the record is complete and ordered, not that it is true; a dishonest ledger passes.
- Variable counting relies on a semicolon-separated list.
- The run-count table assumes independent runs.
- Bisecting needs a known good version.
- Bugs that cannot be reproduced on demand stop at step 1.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 7 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Bug report: orders page 1 shows items 11 to 20. The agent starts a ledger instead of editing `paginate`.
2. Two hypotheses with predictions: `paginate` is off by one; the caller passes the wrong base. One experiment each.
3. The `paginate` hypothesis is refuted (the users screen uses it correctly); the caller is confirmed.
4. A failing test is pasted into the ledger; then the one-line fix.
5. `ledger_check.py` prints `ok: true`; the report lists what was not verified.

## FAQ seeds

- Does it need network access? No.
- Does it work without Python? The agent follows the manual checklist in step 8; the check is then by eye.
- Does the validator prove my bug is fixed? No. It proves the record has the required parts in the required order.
- Why is a fix without a failing test an error and not a warning? A test that never failed cannot show the fix did anything.
- What if I cannot write a test? The skill says to report the validator's finding as a known gap and not to claim `ok`.
- Does it work for flaky tests? Yes; the playbook gives the run counts and the CI-versus-laptop difference method.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
