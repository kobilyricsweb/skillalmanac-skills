## Verdict
do not publish as is

## Chart read
- chart_type: vertical bar chart, single series
- message: Our Q3 sales grew sharply over Q2
- message class: trend
- fit: does not fit - a trend over time fits line or zero-baseline area; bars are not in the trend row of the fit table
- missing fields: 2 (source_and_date, y_axis unit)

## Findings
| ID | Severity | Check | Problem | Fix |
|---|---|---|---|---|
| F1 | HIGH | Bar baseline | y_axis starts at 90. Q1 bar draws 6 units tall and Q3 draws 14 units tall (2.3 times), while the values are 96 and 104 (+8.3 percent). | set y_min to 0 |
| F2 | MEDIUM | Missing units | y-axis label "Sales" has no unit | author to state currency and scale |
| F3 | MEDIUM | Missing source | no publisher or date shown | author to add source and date line |

Checks not triggered: Area baseline, Dual y-axes, Claim check (qualitative "sharply", no ratio stated), 3D effect, Series count, Colour-only encoding, Pie slices, Log scale, Percent change on small base, Unsorted categories (chronological), Dense labels (10 gridlines at current spec).

## Corrected spec
```text
chart_type: vertical bar (change to line if the message stays a trend; see open question 1)
title: Our Q3 sales grew sharply over Q2 (Q3 is +6.1 percent on Q2)
x_encoding: Q1, Q2, Q3, Q4 (fiscal year 2025)
y_axis: label=Sales; unit=<missing: ask author>; min=0; max=110; gridline_step=20
series: one, blue
sort_order: chronological
colour_and_labels: value printed above each bar; no legend needed
source_and_date: <missing: ask author>
```

## Open questions
1. Is the message about a trend across quarters or a comparison of quarters? A trend fits a line chart; a comparison fits bars with a zero baseline.
2. What currency and scale does Sales use?
3. Who published the data and on what date?
4. "Grew sharply" is not quantified. Is the intended claim the 6.1 percent rise from 98 to 104?
