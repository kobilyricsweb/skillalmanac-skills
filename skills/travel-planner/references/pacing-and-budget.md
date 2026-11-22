## Contents

- Check thresholds
- Transit buffer worked examples
- Budget table layout
- Why the numbers are what they are

## Check thresholds

| Check | Value | Code |
|---|---|---|
| Activities per day: relaxed / balanced / packed | 2 / 3 / 4 | pacing_limit |
| Travel-day penalty | minus 1 activity, never below 1 | pacing_limit |
| Scheduled non-meal hours per day (activities, transit, other) | 6 / 8 / 10 | long_day |
| Minimum gap between two places in the same area | 15 min plus declared travel time | missing_transit_buffer |
| Minimum gap between two places in different areas | 30 min plus declared travel time | missing_transit_buffer |
| Extra lead time before an item (airport, timed entry) | `arrive_early_min`, added to the gap | missing_transit_buffer |
| Planned transit block between two places | counts as travel time; the 15 or 30 min buffer is still needed after it | missing_transit_buffer |
| Verified fact older than | 30 days before the first trip date | stale_check |
| Unplanned reserve | at least 10% of budget_total | thin_contingency |

Two places count as "different" when their `location` strings differ after lower-casing and trimming spaces; they count as the "same area" only when both carry an identical non-empty `area`.

## Transit buffer worked examples

- Castle ends 11:00 (area Alfama), lunch starts 11:45 (area Alfama): gap 45, needs 15. Pass.
- Museum ends 12:00 (area Baixa), harbour tour starts 12:10 (area Docks), declared travel 0: gap 10, needs 30. Fail.
- Sightseeing ends 17:00, check-in desk at the airport starts 18:30, `travel_from_previous_min` 30, `arrive_early_min` 60, areas differ: needs 30 + 30 + 60 = 120, gap 90. Fail.
- A transit block 12:00-12:40 sits between two places that end 12:00 and start 13:00: covered 40, remaining 20, needs 30. Fail, move the start to 13:10.

## Budget table layout

Use these category rows so totals match the checker: lodging, food, activities, transport, other, then "unplanned reserve" and "total budget". Report each row as amount and share of the planned total. Per-person costs are multiplied by `travelers` before they are summed. Convert to one currency before writing the file; state the rate source and date in the report because the rate is a fact to verify.

## Why the numbers are what they are

They are planning defaults chosen to make over-packed plans visible, not measured limits. A user who walks fast or wants a marathon day may raise the style; do not edit the constants. If a finding is disputed, explain the cause (for example, a 10 minute gap across areas) and let the user change the plan or accept the warning knowingly.
