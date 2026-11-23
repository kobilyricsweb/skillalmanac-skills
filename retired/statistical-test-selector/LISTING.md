# statistical-test-selector

## One line

Maps a described study design to one primary statistical test, with the assumptions to check, a fallback, the effect size to report and the claims to avoid.

## What it does

The skill works through a fixed procedure. It first requires the outcome type, the number of groups, whether observations are paired, the sample size per group, the distribution shape and the study design. It then maps the outcome to a family (numeric, proportion, count, ordinal or time-to-event) and looks up the primary test in a design table. Sample size and skewness thresholds can move the choice toward a rank-based or exact option. The output is a fixed set of headings: recommendation, assumptions with checks, fallback, effect size and interval, claims not to make, and open questions. The procedure also refuses to pick a test after seeing results and refuses causal wording for observational designs.

## When to use

Use it when a study has been designed and the analyst needs a defensible first test before looking at the numbers. Typical cases are two independent groups with skewed scores, paired before and after measurements, yes or no outcomes compared across sites, count data per unit of time, ordinal survey items, and survival comparisons between two arms.

## When not to use

Do not use it to run calculations on a dataset, to compute power or sample size, to rank tests by their p values, or to write causal conclusions from an observational study. It does not replace a statistician for multi-level models or for designs with many correlated outcomes.

## Requirements

A text-capable agent. No scripts, no network access and no installed packages. The user supplies the design description in plain text.

## Example

Excerpt from the smoke run, where the input was two independent groups of 14 and 16 with skewed scores:

```
## Recommendation
- Outcome type: continuous (ratio scale, 0 to 100)
- Design: two independent groups, randomised experiment, n = 14 and 16
- Primary test: Mann-Whitney U (two-sided, or one-sided if the direction was fixed before data collection)
```

## Limits

The thresholds for sample size, skewness and standard deviation ratio are working values set for this procedure. They are not published standards. The skill does not see raw data, so skewness and variance statements rest on what the user reports. Bootstrap settings are a working choice. The skill covers common designs only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
