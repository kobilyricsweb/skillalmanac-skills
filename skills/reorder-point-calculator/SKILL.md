---
name: reorder-point-calculator
description: Works out when to reorder each product from a sales history CSV, supplier lead times and current stock, using stated formulas, and returns strict JSON with average daily sales, reorder point, safety stock, days of stock left, a suggested order quantity, stockout risk and dead-stock flags. Use when a shop owner or market seller asks when to reorder, how much safety stock to keep, what the reorder point is, which items will run out, or which stock has stopped selling. Do not use for demand forecasting, purchasing or pricing decisions, reconciling physical counts against records, or checking invoices.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in references/formulas.md.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Reorder point calculator

Arithmetic on numbers the user supplied. The output says what the sales history implies if the recent rate continues; it is not a forecast, not purchasing advice, and not financial advice. Say so in the final reply.

## Inputs to collect

Per item, all from the user (ask for what is missing, never invent):

| Input | Where | Note |
|---|---|---|
| Sales per day | sales CSV: `item,date,qty` (+ optional `unit`) | `date` is `YYYY-MM-DD`; several rows per day are summed. Weekly totals must be turned into daily rows first, or the 28-day rule is meaningless. |
| Supplier lead time in days | items CSV: `lead_time_days` | Order placed to goods on the shelf, counted by the user. |
| Current stock | items CSV: `stock` | Same unit as sales. |
| Minimum order quantity | items CSV: `moq` (default 1) | A floor, not a pack size. |
| Buffer days | `--buffer-days` or per item `buffer_days` | The user's choice: how many days of demand they want left when the order arrives. Do not suggest a number; if asked, explain that more days means more stock held and fewer stockouts. |
| Extra cover days | `--cover-days` (default 0) | Days of demand to order beyond the reorder point. The user's choice. |

## Decision rules (fixed; the script applies them)

| Rule | Value |
|---|---|
| Demand basis | The last 28 calendar days up to the as-of date (latest date in the sales file unless `--as-of` is given). If the item's history is shorter, use what exists. |
| Too little data | Fewer than 14 days in the window: action `too little data`, no reorder point. Do not extrapolate. |
| Missing days | A day with no row counts as zero sales (`--missing-days zero`, default) and is reported; `--missing-days skip` leaves such days out instead. Ask which fits: zero for shops that log only days with sales, skip for logs with gaps. |
| Returns | Negative quantities are left out of demand and counted in a warning. |
| Spike | A day above median + 3 x median absolute deviation is listed in `spike_days`. It stays in the average unless `--exclude-spikes` is passed. When most days are identical (MAD 0) the check is skipped and the item says so. |
| Average | `avg_daily` = sum of demand in the window / days counted. `std_daily` = sample standard deviation. |
| Safety stock | `avg_daily x buffer_days` |
| Reorder point | `ceil(avg_daily x lead_time_days + safety stock)` |
| Days left | `stock / avg_daily` |
| Days to reorder point | `max(0, (stock - reorder_point) / avg_daily)` |
| Order quantity | Only for `order now`: `max(ceil(reorder_point + cover_days x avg_daily - stock), moq)` |
| Optional | `--z Z` adds `reorder_point_statistical = ceil(avg x lead + Z x std_daily x sqrt(lead))` for comparison only; it never drives the action. |

Action ladder, first match wins:

| Action | Condition |
|---|---|
| `check data` | Unit mismatch, lead time or stock not a number, negative lead time or stock, bad buffer or moq. Fix the input first. |
| `too little data` | Fewer than 14 days counted. |
| `no sales` | Average is zero. With stock above zero the item is also flagged `dead_stock`. |
| `order now` | Stock at or below the reorder point. |
| `order within lead time` | Above the reorder point but it will be reached within `lead_time_days`. |
| `fine` | Anything else. |

Independent warnings: `stockout_before_arrival` is true when days left is below the lead time (an order placed today arrives too late); more than 180 days of stock is a slow mover; lead time 0 means the reorder point is the buffer only.

## Workflow

```
- [ ] 1 Collect inputs and write them to two CSV files
- [ ] 2 Check units and lead times by eye
- [ ] 3 Run the script
- [ ] 4 Read warnings before actions
- [ ] 5 Report
```

1. Save the sales and the item parameters as CSV in the user's workspace; never edit the originals. Header names are case-insensitive; `sku` works for `item`, `quantity` or `units_sold` for `qty`.
2. Confirm that sales and stock use the same unit (pieces, kg, cases) and that no lead time is a guess you have filled in. A lead time of 0 usually means "unknown".
3. Run, never edit the script to change a result:

```bash
python scripts/reorder_points.py sales.csv items.csv --buffer-days 5 [--cover-days 14] [--exclude-spikes] [--as-of 2026-03-28] [--out report.json]
```

   Prints JSON: `as_of`, `assumptions`, `summary` (count per action), `file_warnings`, and `items[]` with `item, action, stock, lead_time_days, buffer_days, window_days, days_observed, avg_daily, std_daily, safety_stock, reorder_point, days_left, days_to_reorder_point, stockout_before_arrival, suggested_order_qty, spike_days, spikes_excluded, dead_stock, warnings[]`. Exit 0 on a report, 2 on unusable input with a message on stderr. `--out` writes the JSON to a new file; it refuses any path that is the sales or items file even with `--force`, needs `--force` to replace another existing file, and `--dry-run` writes nothing.
4. Read `file_warnings` and each item's `warnings` first: unmatched items, skipped rows, returns, spike days, missing days. A spike that drives the average is a question for the user (one-off wholesale order or real demand?), not a decision for you; show both runs if it matters.
5. Report in this shape, items needing attention first:

```
As of <date>, <N> items. Order now: <list with qty>. Order within lead time: <list>. Stockout before arrival: <list>.
Dead stock: <list>. Too little data / check data: <list and what to fix>.
Assumptions: buffer <n> days, cover <n> days, spikes <kept|excluded>, missing days <zero|skip>.
Not checked: supplier reliability, seasonality, price breaks, promotions, cash available. Arithmetic on supplied numbers, not a forecast.
```

Without Python, apply the table by hand to each item using [references/formulas.md](references/formulas.md), which has a worked example to check your arithmetic against.

## Limits

- It assumes the last 28 days predict the next lead time. Seasons, promotions, stock-outs that suppressed sales and one-off bulk orders all break that, and the script cannot see them.
- A day with no sales caused by having no stock looks like zero demand and lowers the average.
- The 28-day window, 14-day minimum and 3 x MAD spike rule are fixed working values, not measured optima.
- The optional `--z` figure assumes demand is roughly normal and lead time is fixed; it is shown for comparison only.
- Quantities are not rounded to pack sizes; `moq` is only a floor.
- Dates must be ISO `YYYY-MM-DD`; other formats are skipped and reported.
- One decimal for days, three for quantities; very small averages can round to zero in the display.
- Does not touch purchasing, suppliers, prices or accounts.
