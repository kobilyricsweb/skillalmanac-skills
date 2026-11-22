# Listing page content: reorder-point-calculator

**One line:** Turns a sales CSV, lead times and stock levels into reorder points, quantities and stockout flags as strict JSON.

## What it does

The skill collects per item the daily sales history, supplier lead time, current stock, minimum order quantity and the owner's chosen buffer in days. A script applies fixed rules: demand is the last 28 days, an item with fewer than 14 days gets "too little data", a day above the median plus 3 times the median absolute deviation is reported as a spike (and optionally left out), and the reorder point is average daily sales times lead time plus the buffer. An action ladder sorts every item into order now, order within lead time, fine, no sales, too little data or check data. Everything is arithmetic on the supplied numbers; nothing is predicted or recommended.

## Capabilities

- `scripts/reorder_points.py`: JSON with `avg_daily`, `std_daily`, `safety_stock`, `reorder_point`, `days_left`, `days_to_reorder_point`, `stockout_before_arrival`, `suggested_order_qty`, `spike_days`, `dead_stock` and `warnings[]` per item
- Data checks: missing dates, returns recorded as negative sales, unit mismatch, lead time of zero, negative stock, unparseable rows, items with sales but no parameters
- Optional statistical reorder point from a z-score the user chooses, shown for comparison only
- A fixed report shape that lists assumptions and what was not checked
- `--out` writes the JSON to a new file and refuses any path that is an input file

## When to use

You have daily sales per product and want to know when to reorder, how much safety stock a chosen buffer implies, which items will run out before a delivery lands, or which stock has stopped selling.

## When not to use

Forecasting future demand, deciding what or from whom to buy, pricing, reconciling a physical stock count with records, or checking invoices. Difference from `inventory-count-reconciliation-plan`: that skill compares counts against records; this one computes reorder points from sales history and lead times.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent applies the table by hand using `references/formulas.md`.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from `python scripts/reorder_points.py evals/fixtures/sales.csv evals/fixtures/items.csv --buffer-days 3 --cover-days 14` (saved fixture run, as-of 2026-03-28). Summary: 2 order now, 1 order within lead time, 1 fine, 1 no sales, 1 too little data, 1 check data.

1. Tote bag: 2 a day, lead time 10, buffer 4, stock 18. Reorder point 28, action `order now`, days left 9.0 (below the lead time, so `stockout_before_arrival` is true), suggested quantity 38.
2. Mug: 4 a day, lead time 7, buffer 3, stock 50. Reorder point 40, 2.5 days until it is reached, action `order within lead time`, no quantity yet.

## Limits

- Assumes the last 28 days predict the next lead time; seasons, promotions and one-off bulk orders break that.
- Days with no sales because there was no stock look like zero demand.
- Window, minimum and spike thresholds are fixed working values.
- The optional z-score figure assumes roughly normal demand and fixed lead time.
- `moq` is a floor, not a pack size.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN and 10 script fixture cases pass with hand-checked expected values. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Show the two CSV files and say the buffer is 3 days.
2. Run the script; the summary shows two items at order now.
3. Open the tote-green record: reorder point 28, days left 9, stockout warning, quantity 38.
4. Re-run with `--exclude-spikes` on the cap item and show the reorder point drop from 27 to 18.

## FAQ seeds

- Does it need network access? No.
- Will it tell me how much to buy? It gives a quantity that follows from your buffer and cover days; whether to buy is your decision.
- Can it forecast next month? No; it only restates recent sales as a daily rate.
- What if I have weekly sales? Convert to daily rows first or the 28-day rule does not apply.
- Why does an item say "too little data"? It has under 14 days of history in the window.
- How does it differ from a stock count reconciliation? That compares counts with records; this computes when to reorder.
- Does it change my files? No; only a new `--out` file, never an input.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
