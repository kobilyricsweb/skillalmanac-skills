# Formulas and worked example

## Contents

- Definitions
- Worked example (matches the fixture)
- Why median and MAD for spikes
- Optional statistical reorder point
- Sources

## Definitions

- `avg_daily`: units sold per day over the window, returns excluded.
- Lead time: days from placing the order to the goods being sellable.
- Buffer days: days of average demand the owner wants still on the shelf when the order lands.
- Reorder point (ROP): the stock level at which to place an order. Demand during lead time plus the buffer: `ceil(avg_daily x lead_time + avg_daily x buffer_days)`.
- Safety stock here means the buffer: `avg_daily x buffer_days`. Textbook safety stock built from demand variability is the optional `--z` variant below.
- Suggested quantity: the amount that brings stock back up to `ROP + cover_days x avg_daily`, never below the minimum order quantity.

## Worked example (tote-green in evals/fixtures)

Sold 2 a day for 28 days, lead time 10 days, buffer 4 days, stock 18, minimum order 12, cover 14 days.

1. avg_daily = 56 / 28 = 2
2. safety stock = 2 x 4 = 8
3. ROP = ceil(2 x 10 + 8) = 28
4. stock 18 <= 28, so action `order now`
5. days left = 18 / 2 = 9, below the 10-day lead time, so stockout before arrival is true
6. order-up-to level = 28 + 14 x 2 = 56; need = 56 - 18 = 38; 38 is above the minimum of 12, so order 38

Second example, spike handling (cap-spike): 14 days of 2, 13 days of 3, one day of 40. Median 2.5, median absolute deviation 0.5, limit 2.5 + 3 x 0.5 = 4. Only the 40 is a spike. Average with it: 107 / 28 = 3.8214. Without it: 67 / 27 = 2.4815. With lead 5 and buffer 2 the reorder point is 27 or 18. The gap is the cost of one unusual day; the owner decides which view is right.

## Why median and MAD for spikes

A standard-deviation rule is distorted by the spike it is trying to find. The median and the median of absolute distances from it barely move when one day is extreme. When more than half the days are identical the distance median is 0 and the rule would flag every different day, so the script skips the check and says so.

## Optional statistical reorder point

`ceil(avg x lead + z x std_daily x sqrt(lead))`. Larger z keeps fewer stockouts and more stock; z of about 1.28 corresponds to a 90% chance of not stocking out during one lead time, 1.65 to 95%, 2.33 to 99%, if demand is roughly normal and the lead time is exact. The user picks z. The skill reports it beside the plain reorder point and does not choose between them.

## Sources

Background definitions, restated in my own words above:

- https://en.wikipedia.org/wiki/Reorder_point
- https://en.wikipedia.org/wiki/Safety_stock
- https://en.wikipedia.org/wiki/Median_absolute_deviation
