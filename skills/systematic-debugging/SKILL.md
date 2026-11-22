---
name: systematic-debugging
description: Runs a fixed debugging procedure (reproduce, minimise, bisect, hypothesis ledger with predictions, one-variable experiments, root cause statement, failing regression test before the fix) and validates the ledger with a script that reports untested hypotheses, multi-variable experiments and a fix with no failing test first. Use when an agent or developer is guessing at a bug, a test is flaky or fails only in CI, a regression has no known commit, or the user says debug this properly, find the root cause, stop shotgun debugging. Do not use for writing new tests, code review, performance profiling, or explaining an error message.
license: Apache-2.0
compatibility: The ledger script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checklist in step 8 by hand.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  license: Apache-2.0
  version: "0.1.0"
  network: none
---

# Systematic debugging

Do not edit product code to see whether the symptom goes away. A change made before the cause is known is a guess, and a guess that happens to pass hides the bug. Keep a ledger file the whole time (`debug-ledger.md`, or `.json`) and edit product code only at step 7.

## The ledger

Create it at step 1 and append to it as you go. Layout and field rules: [references/ledger-format.md](references/ledger-format.md). Read it before writing the first entry.

## Procedure

```
- [ ] 1 Reproduce
- [ ] 2 Minimise
- [ ] 3 Bisect
- [ ] 4 Hypotheses, each with a prediction
- [ ] 5 Experiments, one variable each
- [ ] 6 Root cause statement
- [ ] 7 Failing regression test, then the fix
- [ ] 8 Validate the ledger and report
```

1. **Reproduce.** Get one command that makes the bug appear, and run it. Record the command and that it failed. If you cannot make it fail, you have no bug to fix yet: gather evidence (logs, the exact input, versions) and say so; do not hypothesise on a failure you have not seen. For a flaky failure, estimate its rate from history and use the run counts in [references/narrowing-playbook.md](references/narrowing-playbook.md) (for example 23 runs for a 1-in-8 failure).
2. **Minimise.** Shrink the input, config or steps until removing anything more makes the failure vanish or change. Keep the oracle strict: same error text or same wrong value. A different failure is a different bug; log it and move on. Record the minimised case.
3. **Bisect.** Pick the axis that fits: code (`git bisect run`), input (halving), time or environment (change one difference at a time). Before you trust the result, check the commit before it passes and the named commit fails. The mechanics, the exit-code rules for `git bisect run` and the environment checklist are in the playbook; read the section you need.
4. **Hypotheses.** Write at least two, as causes, not as fixes. Each gets a prediction in the form "if true, doing X gives R; if false, S", where R and S differ. A hypothesis with no prediction cannot be refuted and is rejected by the validator. Include one that blames the code you consider most correct.
5. **Experiments.** One experiment tests one hypothesis and changes one variable (an input, a flag, one environment difference, one stub). List the variable under `changed`. An experiment that changes two things settles nothing, even if the symptom goes away. Run it, write down what happened, mark it confirmed, refuted or inconclusive. Update the hypothesis status. Do not change product code in an experiment; use inputs, flags, logging, stubs, or a scratch copy.
6. **Root cause.** State the mechanism and where it happens, in one or two sentences, citing the confirmed hypothesis. No "probably", "might" or "seems to". The validator only warns on a hedge (`root_cause_hedged`), but a hedged root cause means the hypothesis is not confirmed, so treat that warning as blocking. If you cannot write it without a hedge, go back to step 4 with what you learned.
7. **Test, then fix.** Write a test that fails because of the root cause and run it on the unfixed code; paste the failing output into the ledger. Only then make the smallest change that removes the cause, run the test again (it must pass), and run the surrounding suite. A fix with no failing test first is a guess with a green check.
8. **Validate and report.** Run the validator, fix whatever it reports, run it again:

```bash
python scripts/ledger_check.py debug-ledger.md
```

`ok` must be `true` before you call the bug fixed. Do not edit the script to make it pass. Without Python, check by hand: every hypothesis has a prediction and a valid experiment; no experiment lists two variables; the root cause has no hedge word; the test's failing output is in the ledger and comes before the fix.

## Script

`scripts/ledger_check.py <ledger>`: run it. Reads one Markdown or JSON ledger, prints one JSON object (`ok`, `counts`, `untested_hypotheses`, `multi_variable_experiments`, `experiments_without_variable`, `fix_without_failing_test`, `findings`), exit 0 when there are no errors, 1 on errors, 2 on a missing or empty file. Finding codes are listed in the format reference. Warnings (no minimised case, no bisect, hedged root cause) do not fail the run but belong in the report.

## Traps that need a decision

| Situation | Do this |
|---|---|
| The symptom disappears after adding a sleep, retry or null check | Treat it as a mask. Record it as an inconclusive experiment and keep looking for the mechanism |
| Two hypotheses both survive | Design an experiment whose predictions differ; do not fix both |
| The cause is in code you do not own | Make the failing test at your boundary, record the upstream cause, and fix or work around it there |
| No test can be written (timing, hardware, production-only) | Write down why, record the strongest observable check, and report the validator's `fix_without_failing_test` as a known gap under "Not verified"; do not claim `ok` |
| Three hypotheses refuted in a row | Re-read the reproduction. The oracle or the minimised case is usually wrong |

## Report format

```
Bug: <symptom in one line>
Reproduced by: <command>; minimised to: <case>; bisect: <result or n/a>
Root cause: <mechanism and location>
Evidence: <the confirming experiment, the failing test output before the fix>
Fix: <what changed>; test passes after: <yes/no>; suite: <result>
Ledger check: <ok true/false, warnings>
Not verified: <e.g. other callers, production, flaky-run count>
```

## Limits

- The validator checks that the record is complete and ordered; it cannot tell whether a prediction is sensible, whether an experiment really changed one variable, or whether a root cause is true. A dishonest ledger passes.
- Variable counting relies on the semicolon-separated `changed` list; a single entry written as "A and B" gets a warning only.
- The run-count table assumes independent runs and a failure rate you estimated from history.
- Bisecting needs a known good version; the playbook covers what to do without one only in outline.
- Some bugs cannot be reproduced on demand (rare production races); the procedure then stops at step 1 and says what evidence is missing.
- The markdown reader accepts the layout in the format reference only; other headings are ignored.
