## Contents

- Run counts for flaky failures
- Minimising an input
- Bisecting code with git
- Bisecting time and environment
- Choosing the next experiment
- Sources

## Run counts for flaky failures

If a failure shows up in a fraction p of runs, the number of consecutive runs you need to be 95% sure you would have seen it at least once is `n = ceil(ln(0.05) / ln(1 - p))`. The same number of consecutive clean runs is the bar for saying a fix worked at the original rate.

| Failure rate p | Runs for 95% |
|---|---|
| 0.50 | 5 |
| 0.25 | 11 |
| 0.20 | 14 |
| 0.125 (5 in 40) | 23 |
| 0.10 | 29 |
| 0.05 | 59 |
| 0.01 | 299 |

Rule of thumb: about 3 divided by p. Three green runs of a 1-in-8 failure prove nothing (the chance of three clean runs without any fix is about 67%). Estimate p from history first (failures divided by runs). If p is below 0.05, do not try to prove the fix by repetition; prove the mechanism instead, or make the failure deterministic (fixed seed, injected delay, forced ordering) and test that.

## Minimising an input

Goal: the smallest input that still fails the same way. "The same way" means the same error text or the same wrong value; a different failure means you found a different bug, so log it separately.

1. Fix the oracle first: one command that exits non-zero only for this failure (grep the error text, compare the wrong value).
2. Halve: drop half of the input (lines, records, config keys, request fields). If it still fails, keep the smaller one. If not, restore that half and drop the other half. When halves no longer work, drop quarters, then eighths, then single elements, until no single removal keeps the failure.
3. Then simplify values: replace long strings with "a", large numbers with 0 or 1, nested structures with flat ones. Keep each change only if the oracle still fails.
4. Record the final input in the ledger under `minimised`, with its size before and after.

Do this by hand or with a short loop. It is a search for a cause, not for a fix: the minimised input often names the bug by itself (a lone empty string, a single negative number, one record with a null).

## Bisecting code with git

Use it when you have a known good commit and a known bad one. The number of test runs is `ceil(log2(commits))`: 100 commits is 7 runs, 200 is 8, 1,000 is 10.

```
git bisect start
git bisect bad            # the current checkout fails
git bisect good <ref>     # a commit where the oracle passed
git bisect run <command>
git bisect reset          # always finish with this
```

Exit codes of the command given to `bisect run`: 0 means good; 1 to 127 except 125 means bad; 125 means this commit cannot be tested, skip it (for example it does not build); 128 and above abort the whole bisect. Wrap your oracle so that "the build is broken" exits 125 and "the failure appeared" exits 1; otherwise a build error is misread as the bug and the bisect names the wrong commit.

Before trusting the result: check out the commit before the named one and confirm the oracle passes, check out the named commit and confirm it fails. If the failure is flaky, run the oracle the number of times from the table above at each step, or the bisect will land on noise. Then read the diff of that commit: it names where to look, not yet why.

If there is no known good commit, bisect on the version axis instead: released versions, dependency versions, or the date of the first bug report.

## Bisecting time and environment

When the failure depends on the machine and not the code (it fails in CI, not on a laptop), list every difference you can find and change one at a time on the failing side: operating system and version, interpreter or compiler version, dependency lockfile, environment variables, locale and time zone, clock, CPU count, parallelism level, file system case sensitivity, network access, data volume. Halve the list: apply half of the laptop values to CI, see if the failure goes, and keep halving. A run that applies several differences at once is a multi-variable experiment and does not count.

When the failure depends on time (only at midnight, only on the 31st, only after 49 days), set the clock explicitly to a failing value instead of waiting, and confirm it fails, then move it one step toward a passing value.

## Choosing the next experiment

Pick the hypothesis whose prediction is cheapest to test and would remove the most remaining possibilities. Write the prediction as: "if the hypothesis is right, then changing X to Y gives result R; if it is wrong, the result is S". If R and S are the same, the experiment is worthless; redesign it. Prefer experiments that do not change product code (a flag, a log line, a different input, a stub). Never edit the code that you suspect to see whether the symptom goes: that is a fix attempt, not an experiment, and it hides the mechanism.

## Sources

- git-bisect manual page, exit-code rules for `git bisect run`: https://git-scm.com/docs/git-bisect (restated in own words; check the manual for your git version).
- Delta debugging (halving an input to find a minimal failing case): Zeller and Hildebrandt, "Simplifying and Isolating Failure-Inducing Input", IEEE Transactions on Software Engineering, 2002, DOI 10.1109/32.988498. Cited from memory, not re-fetched when this skill was written.
- The run-count formula is the standard probability of n independent clean runs, (1 - p) to the power n, set equal to 0.05. It assumes runs are independent.
