# Reading a keyword trend without fooling yourself

Read this at step 5, when the user asks whether a topic is growing, or when a number such as "up 300%" has to be checked.

## The four readings

Always give all four that the data allows, with the months named.

| Reading | How | What it answers |
|---|---|---|
| Recent direction | mean of the last 3 months against the mean of the 3 before | Is it moving now |
| Year on year | mean of the last 3 months against the same 3 months a year earlier (needs 15 months); with 13 months, last month against the same month a year earlier | Is it bigger than a year ago, with the season held equal |
| Distance from peak | last month against the highest month, and when the peak was | Is this the way up or the way down |
| Level | 12-month average and the last month | How big is it |

Labels used by the script: `rising` above +15% in recent direction, `falling` below -15%, `flat` between. The band exists because neighbouring volume buckets differ by 20 to 25%, so a smaller move can be one bucket step.

## Traps

- **A huge year-on-year figure on a young topic.** If the year-ago value was near zero, the percentage is arithmetic, not growth. Say "new in the last 12 months" and give the absolute numbers.
- **Growth quoted from the wrong pair of months.** "Up 300%" against a year ago and "down 40% from the peak" can both be true. Report both and say which one matters for the decision: a content plan cares about the next 6 to 12 months, so recent direction and distance from peak carry more weight than year on year.
- **One month of rebound.** A single up month after several falling months is flagged `one-month-rebound-after-decline`. Write "one month, not a trend" and say which later month would confirm it.
- **Season.** A peak in the same calendar month two years running is a season. With under 24 months only one cycle is visible, so write "possible season, one cycle seen".
- **A one-off spike.** A single month several times above the median (an event, a launch, news) inflates the 12-month average. Give the average with and without that month.
- **Totals hide composition.** A flat total can be a falling head and a rising tail. Check the largest clusters separately.
- **The last month may be incomplete or revised.** Note the provider's "data available to" date.
- **Bucket steps.** A keyword that moves from 480 to 590 moved one bucket. Do not write "+23%" as a finding for a single small keyword.

## Wording

Say: "Falling: August to October 2026 averaged 12,400 against 16,800 in May to July (-26%). Still 3.1 times October 2025. Peak was March 2026; October is 56% below it. October rose 18% on September: one month, not a trend."

Do not say: "Explosive growth", "trending", "dying", or any direction without the two periods.
