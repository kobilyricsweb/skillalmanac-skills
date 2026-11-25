**No. A final p of 0.04 is not ordinary confirmatory evidence here.** The p-value was computed correctly, but the procedure that produced it makes the number uninterpretable as a test result.

**What was wrong**

- **Optional stopping.** A p-value means "the probability of a result this extreme if there's no effect, with the sample size and stopping rule fixed in advance." Checking repeatedly and stopping at the first p < 0.05 breaks that guarantee. Even a few looks can push the real false-positive rate to roughly 0.10–0.15 when nominal alpha is 0.05. Checking after every addition makes it worse.
- **Outcome-dependent data collection.** Tasks were added *because* of the running p-value. The sample is now a function of the outcome, so the test no longer describes the data-generating process it assumes. "The checks never changed" doesn't help: the test was the same, but the set of tasks it was applied to was chosen by its results.
- **Trajectory.** 0.20 → 0.11 → 0.04 is a drift toward significance under continued sampling, not a stable effect. The first crossing of the threshold is the point where a noisy estimate is most likely to look impressive, so the effect size at that moment is probably inflated (winner's curse).
- **Forking paths on task selection.** If "matched" tasks were chosen after seeing results, or the matching criteria were adjusted, that is another degree of freedom the p-value doesn't account for.

**What was right**

- Recording the p-value at each step is good practice. Hiding the trajectory would have been worse.
- Using the same statistical test throughout avoids switching methods to get a result.

**Defensible next step**

1. **Treat the current result as exploratory.** Report all the looks (8, 10, 12 tasks, and any others), the stopping rule as it actually happened, and the effect estimate with a confidence interval. Don't call it confirmed.
2. **Quantify the damage.** Simulate the full adaptive procedure under the null (same task-addition rule, same looks, same test) and see how often it crosses 0.05. This gives the true false-positive rate for your process, which is more useful than a textbook multiplier.
3. **Run a confirmatory study.** Lock these before collecting data:
   - the exact task set (or the matching rule, applied mechanically),
   - a fixed final sample size from a power calculation,
   - a single primary test and alpha.
   If you want interim looks, use a group-sequential design with alpha spending (O'Brien-Fleming or Pocock) or an always-valid method (e.g., mSPRT/e-values). Those are designed for repeated looks; plain repeated t-tests are not.
4. **Use fresh tasks.** The confirmatory set should be new tasks, not the ones that produced the signal. Hypothesis-generating data can't confirm itself.
5. **Pre-register and document.** Write the hypothesis, primary endpoint, sample size, and analysis plan before the new run, with a timestamp.

If you share the task-level data and how tasks were matched, I can run the null simulation for your exact procedure and estimate the actual false-positive rate and a sample size for a confirmatory study.
