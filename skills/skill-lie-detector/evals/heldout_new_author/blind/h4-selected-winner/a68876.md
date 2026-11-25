**Justified conclusion:** One skill showed a nominally significant gain in an exploratory screen. That makes it a candidate worth confirming, not a proven winner.

**Why the result doesn't support "proven":**

- **Multiple comparisons.** With 20 tests, a p of 0.03 is unremarkable. If none of the skills worked, the chance that at least one clears p < 0.05 is about 1 − 0.95²⁰ ≈ 64%. Bonferroni needs p < 0.05/20 = 0.0025, and Holm and Benjamini-Hochberg also fail at p = 0.03 for the top-ranked result. Under any standard correction, this result is not significant.
- **Selection bias (winner's curse).** Picking the largest of 20 observed gains guarantees the 7-point figure is inflated, even if a real effect exists. The true effect is probably smaller.
- **The 19 non-significant results don't mean "no effect."** They mostly reflect limited power with 12 tasks per arm. Some could be real, smaller effects.
- **Missing information.** I don't have the per-task variance, whether the comparison was paired, the scoring scale (is 7 points on a 100-point scale?), or a confidence interval. Without those, I can't say how precise the 7-point estimate is or how likely it is to replicate. I won't assume values for them.

**What to do next:**

1. **Report the full picture.** Show all 20 results with effect sizes, CIs, and raw p-values, and say that the top one was selected after the fact. Don't label it the winner.
2. **Confirm on fresh tasks.** Choose the one candidate (or a short pre-specified shortlist, with a correction for the shortlist size). Lock in the primary metric, the comparison, and the analysis before running. Use tasks that were not used to select it.
3. **Size the confirmation study.** Use a power calculation based on a conservative effect, meaning something well below 7 points, and on the observed variance. Twelve tasks is probably too few to detect a modest effect reliably.
4. **Check robustness.** Look at whether the gain is consistent across tasks or driven by a few, and whether it holds under a paired analysis.
5. **Decide with the manager on that basis.** If they need a decision now, the defensible framing is: "one candidate skill looks promising; we're running a confirmatory test before adopting it." If the confirmation holds up, you can then call it a winner.
