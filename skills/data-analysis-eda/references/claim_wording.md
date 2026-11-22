## Contents

- Rewrites from claim to description
- Three traps with numbers
- Background reading

# Claim wording for EDA findings

Read this when you are not sure whether a sentence in your report states more than the data shows.

## Rewrites from claim to description

| Overreach | Acceptable finding (claim + evidence + caveat) |
|---|---|
| "Discounts increase order size." | "Orders with a discount have a median value of 84, against 61 without (n = 410 and 2,950). Discounts were applied mostly to returning customers, who also order more; not separated here." |
| "Churn is driven by support tickets." | "Accounts with 3 or more tickets churned in 31% of cases (62 of 200) against 9% (180 of 2,000). Tickets may follow the decision to leave; timing was not checked." |
| "The data is clean apart from a few outliers." | "17 of 4,096 order values exceed 3 IQR above the third quartile; the largest is 61 times the median. Owner to confirm whether they are real." |
| "Revenue is flat." | "Monthly revenue in the file ranges 1.1M to 1.3M with no run of more than 2 rising months. Two of 14 months have under half the usual row count, so they may be incomplete." |
| "Age does not matter for spend." | "No strong straight-line association was found (r = 0.03 on 3,400 rows). Curved or group-specific effects were not examined." |
| "Missing incomes are random." | "Income is missing for 22% of rows; the rate is 35% in region B and 14% in region A (n = 600 and 1,400). The missingness is related to region." |
| "Country is a useless column." | "Country has the single value US in all 22,000 rows." |

Pattern: say what was computed, on how many rows, and which check was not done.

## Three traps with numbers

1. **Reversal under splitting.** A treatment can win in each of two groups and lose in the pooled table when the groups differ in size and base rate (Simpson's paradox). Rule used here: any group comparison you plan to report is repeated within the largest categorical column; if the direction flips, the finding is `suggestive` at best.
2. **Same summary, different data.** Four datasets can share the same mean, variance and correlation and look completely different when plotted (Anscombe's quartet). Rule used here: do not report a correlation without checking the group medians table or a scatter of the two columns.
3. **Many looks.** Testing k independent patterns at a 5% threshold gives about 0.05 times k false hits (multiple comparisons). Rule used here: write the number of columns and splits you examined into the report, and mark isolated hits as `suggestive`.

## Background reading

- NIST engineering statistics handbook, chapter on exploratory data analysis: https://www.itl.nist.gov/div898/handbook/eda/eda.htm (the case for looking at data before modelling).
- Anscombe's quartet: https://en.wikipedia.org/wiki/Anscombe%27s_quartet
- Simpson's paradox: https://en.wikipedia.org/wiki/Simpson%27s_paradox
- Multiple comparisons problem: https://en.wikipedia.org/wiki/Multiple_comparisons_problem
- Outliers and the interquartile-range fences: https://en.wikipedia.org/wiki/Outlier

The numbers in the rewrite table are invented for illustration; they are not results from any file.
