## Contents
- Metric definitions
- Choosing a north star
- Decision log rules
- Investor update rules
- Worked runway example

## Metric definitions

These are this skill's conventions, chosen so two people compute the same number from the same sheet. If the founder's accountant uses another convention, state both.

| Term | Definition here |
|---|---|
| revenue | cash received from customers in the month (not invoiced, not booked) |
| cash_out | every payment out in the month: payroll, tools, tax payments, refunds, loan repayments; positive number |
| cash_balance | bank balance at month end, all operating accounts combined |
| gross burn | cash_out |
| net burn | cash_out minus revenue |
| runway | cash_balance / net burn, in months |
| MoM growth | revenue_t / revenue_t-1 minus 1 |
| CMGR 3m | (revenue_t / revenue_t-3)^(1/3) minus 1 |

Funding received in a month raises cash_balance without being revenue; the reconciliation warning will fire for that month. Record it in the review's Metrics section and the decision log, and leave revenue alone.

## Choosing a north star

One number that rises when customers get value and that the team can change in a week. Test each candidate with three questions: can it be computed from a file the team already has; does it move within 7 days of a real change; can it be gamed without helping a customer. Reject a candidate that fails the first, or that passes only the third.

| Business | Candidate north star | Definition sentence (write it exactly) |
|---|---|---|
| B2B SaaS | weekly active teams | teams with at least 3 sessions by 2 or more users in the 7 days ending Sunday |
| Marketplace | completed transactions per week | orders marked delivered or paid out in the week |
| Subscription app | paying subscribers retained at day 30 | subscribers active 30 days after first payment divided by those who paid 30 days ago |
| Services | billable hours delivered | hours invoiced for work done in the week |

The thresholds in the SaaS row are an example to replace with the founder's own. Revenue is a result, not a north star, for most early teams, because it lags the work by weeks.

## Decision log rules

A decision has a verb-first sentence, one owner who is a person, a due date, and a review date when it is hard to reverse. Reversible means undoing costs under one week of one person's time. Never rewrite a closed row; supersede it with a new row. Decisions that change the north star definition, the metrics sheet columns, pricing, or headcount always get a row. A decision the founder did not state is not logged by the agent.

## Investor update rules

Facts only from the metrics sheet or named sources. Same metrics, same order every month so readers can compare. Asks are specific and answerable in one email. No forecasts presented as facts, no valuation talk, no statements about a financing that has not closed. If the company is in a regulated offering process, the founder checks wording with counsel before sending; the agent does not give that advice.

## Worked runway example

Cash balance 152,156. Net burn in the last three months 29,690, 29,359 and 28,895.
Average = (29,690 + 29,359 + 28,895) / 3 = 29,314.67. Runway = 152,156 / 29,314.67 = 5.19 months. Last month alone: 152,156 / 28,895 = 5.27. Worst of three: 152,156 / 29,690 = 5.12. If burn stays flat, cash runs out during the 6th month after the latest month (5 whole months of runway, then part of the next): the script reports that month as cash_zero_month_at_avg_burn.
