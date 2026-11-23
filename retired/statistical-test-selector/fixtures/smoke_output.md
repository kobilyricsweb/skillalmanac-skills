## Recommendation
- Outcome type: continuous (ratio scale, 0 to 100)
- Design: two independent groups, randomised experiment, n = 14 and 16
- Primary test: Mann-Whitney U (two-sided, or one-sided if the direction was fixed before data collection)
- Reason (one sentence tied to a table row): Step 4 applies because the smallest group is below 15 and sample skewness is above 1.0 in both groups, so the rank-based option replaces the Welch t-test.

## Assumptions to check
| Assumption | How to check | If it fails |
|---|---|---|
| Independence of observations | Random allocation with one score per participant, as described; confirm no participant appears in both groups | Use a paired or mixed model; do not run either simple test |
| Similar distribution shape (needed for a mean-difference reading) | Compare histograms or Q-Q plots of the two groups; the stated skewness values are about 1.4 and 1.2 | Report the result as a difference in rank distributions only, not as a difference in means |
| Equal spread | Standard deviation ratio is about 2.6, above the working threshold of 2 | Not needed for Mann-Whitney; it is the reason the Welch version is the fallback |

## Fallback test
- Test: Welch t-test on the raw scores, reported as a secondary sensitivity analysis
- Use when: the researcher needs a difference in group means and the Q-Q plots show the skew is driven by a few extreme scores that are confirmed as valid, or when the sample is later increased to 30 or more per group.

## Effect size and interval to report
- Effect size: probability of superiority (training score higher than control score) and rank-biserial r
- Interval: 95% bootstrap CI, 2000 resamples (working value), for both effect sizes

## Claims not to make
- That the training group has a higher mean score, because the distributions are not similar in shape.
- The size of the average gain in score points, because the fallback mean analysis has not been run and the groups are small.
- That a non-significant result shows no effect; with 14 and 16 participants the test has low power.
- Any statement that the sample represents a wider population unless the recruitment method supports it.

## Open questions
- Was the direction of the comparison fixed before data collection (decides one-sided or two-sided)?
- Is the skew caused by valid extreme scores or by a recording error?
