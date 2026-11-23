---
name: statistical-test-selector
description: Chooses a statistical test for a described study design using a decision table on outcome type, group count, pairing, distribution shape and sample size, then lists assumptions, a fallback test, the effect size to report and claims to avoid. Use when a researcher asks which test fits a design, whether a t-test or a nonparametric alternative applies, or how to analyse grouped, paired, count, ordinal or time-to-event data. Do not use for running tests on raw data, power calculations, picking a test after seeing results, or causal claims from observational designs.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Statistical test selector

Use this procedure to recommend one primary test for one study question. Work only from the design the user describes. Do not look at results to choose the test.

## Step 1. Collect the inputs

Required before any recommendation:

- Outcome type: continuous, binary, count, ordinal, or time-to-event.
- Number of groups (or number of measurement occasions).
- Paired or independent observations.
- Sample size per group (or per pair).
- Distribution shape: a stated skewness, a plot description, or "unknown".
- Study design: randomised experiment or observational.
- Question: difference in location, difference in proportion, association, trend, or rate ratio.

If outcome type, group count, or pairing is missing, stop and list the missing fields. Do not guess.

## Step 2. Map the outcome type to a family

| Outcome type | Family | Examples |
|---|---|---|
| Continuous (interval or ratio scale) | Numeric | reaction time, weight, score sum |
| Binary (two categories) | Proportion | responded yes or no, pass or fail |
| Count (events per fixed unit) | Count model | visits per week, defects per batch |
| Ordinal (ordered categories) | Rank-based | Likert item, pain 0 to 10 rating |
| Time to event with censoring | Survival | months until relapse, censored at study end |

## Step 3. Pick the primary test from the design

| Family | Design | Primary test | Fallback |
|---|---|---|---|
| Numeric | 1 group vs fixed value | one-sample t-test | Wilcoxon signed-rank |
| Numeric | 2 independent groups | Welch t-test | Mann-Whitney U when skewed (Step 4) |
| Numeric | 2 paired measurements | paired t-test on differences | Wilcoxon signed-rank |
| Numeric | 3+ independent groups | Welch one-way ANOVA | Kruskal-Wallis, then Dunn test with Holm correction |
| Numeric | 3+ repeated measures | repeated-measures ANOVA or mixed model | Friedman test |
| Proportion | 2 independent groups | chi-square test of independence | Fisher exact test (any expected count below 5) |
| Proportion | 2 paired measurements | McNemar test | exact binomial test on discordant pairs |
| Proportion | 3+ groups | chi-square or Fisher-Freeman-Halton | logistic regression with covariates |
| Count | 1 or more groups | Poisson regression | negative binomial when overdispersed |
| Ordinal | 2 independent groups | Mann-Whitney U | ordinal logistic regression |
| Ordinal | 2 paired | Wilcoxon signed-rank | sign test |
| Ordinal | 3+ independent | Kruskal-Wallis | ordinal logistic regression |
| Survival | 2 groups | log-rank test | Cox model; restricted mean survival time if proportional hazards fails |

## Step 4. Apply the sample size and shape thresholds

These are working values chosen for this procedure. They are not published industry standards.

| Condition | Rule |
|---|---|
| Smallest group n below 15 | Prefer the nonparametric or exact option; state that power is low |
| Smallest group n from 15 to 29 | Use the t-test only when the distribution plot shows no strong skew or outliers |
| Smallest group n 30 or more | The t-test is acceptable under moderate non-normality |
| Absolute sample skewness up to 0.5 | Treat as roughly symmetric |
| Absolute sample skewness above 0.5 up to 1.0 | Moderate skew; check with a Q-Q plot |
| Absolute sample skewness above 1.0 | Skewed; choose the rank-based or permutation option |
| Ratio of group standard deviations above 2 | Use the Welch version, not the pooled t-test |
| Chi-square expected count below 5 in any cell | Use Fisher exact |

Mann-Whitney U compares rank distributions. It tests a difference in means only when the two groups have similar shape. Say so in the output whenever Mann-Whitney is recommended.

## Step 5. Specify assumptions and how to check them

Give one row per assumption that the primary test needs:

| Assumption | How to check | If it fails |
|---|---|---|
| Independence of observations | Confirm from the sampling or allocation description | Use a clustered, paired, or mixed model; do not proceed with the simple test |
| Normality of residuals | Q-Q plot; Shapiro-Wilk only as a supplement when n is below 50 | Rank-based or permutation option |
| Equal variances | Ratio of standard deviations | Welch version |
| Expected cell counts at least 5 | Count expected values from the table margins | Fisher exact |
| Proportional hazards | Log-log survival plot or Schoenfeld residuals | Restricted mean survival time |

## Step 6. Choose the effect size and interval

| Primary test | Effect size to report | Interval |
|---|---|---|
| t-test (any form) | Hedges g (use instead of Cohen d when n is below 20) | 95% CI from the noncentral t or bootstrap |
| Paired t-test | Mean difference and dz | 95% CI of the mean difference |
| Mann-Whitney U | Probability of superiority and rank-biserial r | 95% bootstrap CI, 2000 resamples (working value) |
| Wilcoxon signed-rank | Rank-biserial r | 95% bootstrap CI |
| Chi-square, 2 by 2 | Odds ratio and phi | 95% CI on the log odds ratio |
| Fisher exact, 2 by 2 | Odds ratio | 95% CI (conditional maximum likelihood) |
| ANOVA | Omega squared | 95% CI from bootstrap |
| Kruskal-Wallis | Epsilon squared | 95% bootstrap CI |
| Poisson or negative binomial | Rate ratio | 95% Wald CI |
| Log-rank | Hazard ratio from Cox model | 95% CI |

## Step 7. Write the output

Use exactly these headings in this order. Use the table columns shown.

```
## Recommendation
- Outcome type:
- Design:
- Primary test:
- Reason (one sentence tied to a table row):

## Assumptions to check
| Assumption | How to check | If it fails |

## Fallback test
- Test:
- Use when:

## Effect size and interval to report
- Effect size:
- Interval:

## Claims not to make
- (bulleted list, at least two items)

## Open questions
- (bulleted list; write "none" if empty)
```

## Refuse or stop when

- The user asks which test gives a significant result, or asks to compare tests after seeing outcomes. Refuse the selection and explain that the choice must follow the design.
- The study is observational and the user asks for causal wording such as "causes" or "effect of". Recommend the test but restrict the output to association language.
- Outcome type, group count, or pairing is missing (Step 1).
- The user has run several tests and wants the smallest p value. Refuse to rank them by p value.
- Several outcomes or comparisons are planned and no correction method is named. Stop and ask for the correction method before giving a final recommendation.
- The user asks for a sample size or power figure. Hand that off; this skill does not compute it.

## Worked check

Input: two independent groups of 14 and 16 with skewed scores.

1. Step 2 gives the numeric family.
2. Step 3 gives 2 independent groups, so the first-line test is Welch t-test.
3. Step 4 applies two rules: the smallest group (14) is below 15, and skewness above 1.0 is skewed. Both move the choice to Mann-Whitney U.
4. Step 6 gives probability of superiority and rank-biserial r, with a bootstrap interval.
