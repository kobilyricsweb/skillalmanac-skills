## Contents

- Break-even in four lines
- Three worked examples
- Learning-phase thresholds
- Match types and negatives
- First-month split worked through
- Review rhythm

## Break-even in four lines

```
profit per conversion = price x gross margin               (one-off sale)
profit per lead       = close rate x profit per sale        (lead gen)
max affordable CPA    = profit per conversion (spending more loses money on the first sale)
target CPA            = 0.7 x max affordable CPA            (house rule)
```

If customers come back, add expected repeat profit to the first sale only with a number the user can defend (for example a repeat rate from their own records); otherwise leave it out and say that the plan is conservative.

## Three worked examples

1. Product sale. Price 120, margin 50 percent, profit 60, target CPA 42. Budget 1,260 a month, cpc 1.40, cvr 3 percent: clicks 900, conversions 27, CPA 46.67, above 42 by 4.67. Needs cvr 3.34 percent or cpc 1.26 to hit the target.
2. Lead gen. Close rate 20 percent, profit per sale 900, profit per lead 180, target CPA 126. Budget 2,000, cpc 4.00, cvr 8 percent: clicks 500, leads 40, CPL 50, well under 126, so there is room to bid higher or widen keywords.
3. Subscription with 60 percent margin and a 3-month average life at 30 per month: profit 54, target CPA 37.8.

Always print the arithmetic in the report in this form: `budget / cpc = clicks; clicks x cvr = conversions; budget / conversions = CPA`.

## Learning-phase thresholds

Heuristics from public platform guidance, verify (unconfirmed, as of 2026-11):

| Platform | Rule of thumb | Consequence for the plan |
|---|---|---|
| Google and Microsoft search, automated bidding | About 30 conversions per campaign over 30 days before target CPA or ROAS is reliable | Under that, start on manual cpc or max clicks; merge campaigns |
| Meta | About 50 optimisation events per ad set in a week to exit learning | Small budgets: one ad set, optimise for the highest-volume event (for example add to cart or lead form) not the rarest |
| LinkedIn | Enough budget for the audience size; audience under about 50,000 gets thin delivery | Widen the audience or accept low volume |
| TikTok | Several dozen conversions per ad group in the first week | Use fewer ad groups |

The validator uses 30 conversions as the single threshold for its `bid_learning_data_thin` warning.

## Match types and negatives

- Exact `[term]`: tightest; use for the 70 percent proven-intent share.
- Phrase `"term"`: the term in order with extra words allowed around it; good second layer.
- Broad: only with automated bidding and a long negative list; otherwise expect wasted spend.
- A negative that equals a positive keyword blocks it. The validator flags this as `negative_blocks_keyword`.
- Same keyword in two ad groups makes them bid against each other; the validator warns with `keyword_overlap`.
- Negatives are not retroactive: after launch, read the search terms report weekly for the first month and add irrelevant queries as negatives.

## First-month split worked through

Budget 3,000, one platform, target CPA 50. Spend 2,100 on proven intent (exact and phrase on the top 2 ad groups), 600 on expansion (phrase and broad on adjacent themes, or a second audience), 300 on experiments (one new offer or one new ad angle). Check the test floor for each ad group: with cpc 2.50, 100 clicks costs 250, so 2,100 supports up to 8 ad groups but 2 or 3 is the right number to reach conclusions.

## Review rhythm

Daily: check spend is on pace and nothing was disapproved. Weekly: search terms, negatives, kill rule (3 x target CPA spent with no conversion). Monthly: recompute CPA from real numbers and replace the forecast; change one thing per campaign at a time so the effect is readable.
