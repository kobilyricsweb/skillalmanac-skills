**Justified conclusion:** The data don't establish that this skill is a proven winner. They show one nominally significant result among 20 comparisons, and that is about what chance alone would produce.

**Why the manager's claim doesn't hold**

- **Multiple comparisons.** Testing 20 skills gives 20 chances to get a p-value under 0.05 by luck. If none of the skills does anything, the chance that at least one of 20 tests reaches p ≤ 0.03 is about 1 − 0.97²⁰ ≈ 46%. The result is well within what noise produces.
- **Correction removes the significance.** Bonferroni gives 0.03 × 20 = 0.60, far from significant. Holm's step-down procedure also won't reach significance for the top result. Even a looser false-discovery-rate correction would need the other results to be considered too.
- **Selection inflates the estimate.** Picking the largest of 20 observed gains means the 7-point figure is probably an overestimate of the true effect, even if some effect is real. This is the winner's curse.
- **The other 19 results point the same way.** None were significant, so there is no pattern of several skills helping that would make this one more believable.
- **Twelve tasks is a small sample.** Without the variance across tasks, I can't tell whether a 7-point mean difference is stable or driven by a few tasks. I don't have the per-task numbers, so I can't check this.

**What to say to the manager**

"None of the 20 skills showed a significant improvement after correcting for multiple testing. One looked promising at p = 0.03 before correction, and that is the kind of result we'd expect from chance across 20 tests. It's a candidate for follow-up, not a winner."

**What to do next**

1. **Pre-register the candidate.** Name one skill and one primary metric, and write down the test (paired or unpaired, two-sided, alpha, stopping rule) before collecting new data.
2. **Confirm on fresh tasks.** Run the chosen skill against the same baseline on new tasks that were not used to choose or develop it. Don't reuse the 12 selection tasks as the confirmation set.
3. **Size the confirmation study.** Use the observed per-task variance from the first run to estimate how many tasks are needed to detect a smaller effect than 7 points with reasonable power. Expect the true effect to be smaller than 7.
4. **Report the full set.** Include all 20 results with effect sizes and confidence intervals, not only the winner. Say how many were tested and how the winner was selected.
5. **Check consistency.** For the confirmation run, report the fraction of tasks where the skill beats the baseline, not only the average gain.
6. **Keep the 19 others as exploratory.** Any follow-up on them should be labeled as hypothesis-generating.

If the confirmation run is significant after correction and the effect holds on fresh tasks, the manager's claim becomes reasonable. Until then, the honest label is "promising, unconfirmed."
