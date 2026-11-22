---
name: chart-readability-review
description: Reviews a described chart or chart spec for readability and misleading design choices, such as truncated bar axes, dual y-axes, 3D effects, colour-only encoding, too many series, unsorted bars and missing units or sources. Use when the user has a text description, mock-up notes or spec of a chart and asks whether it is clear, honest or ready to publish, or wants a corrected spec. Do not use for an image the agent cannot read, for writing chart code, for choosing a charting library, or for checking whether the underlying data is correct. Refuses to judge an undescribed chart.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Chart readability review

Use this procedure to review one chart at a time. The input is a text description or spec of the chart. The output is a verdict, a findings table with severity, and a corrected spec. Work only from what the user wrote. Do not invent axis ranges, values or sources.

## Required input fields

Check the input for these fields before any review. Record each as present or missing.

| Field | Example of a usable value |
|---|---|
| chart_type | "vertical bar", "line", "pie", "scatter" |
| message | the one sentence the title or author wants the reader to take away |
| x_encoding | category names or time axis with unit |
| y_axis | label, unit, minimum, maximum |
| series | count and names; how each series is distinguished |
| values | the numbers, or "not provided" |
| sort_order | "descending by value", "chronological", "alphabetical", "none" |
| source_and_date | publisher and date of the data |

If `chart_type`, `message` or `y_axis` is missing, stop and ask for it (see Refuse / stop when).

## Workflow

1. **Confirm the description is usable.** Output: the field table above with present or missing for each row, and the count of missing fields.
2. **Classify the message.** Output: one of comparison, trend, part-to-whole, distribution, relationship. Use the fit table in the next section. If the message fits more than one, pick the one the title states.
3. **Fit check.** Output: "fits" or "does not fit", with the reason from the fit table.
4. **Run the checks.** Go through every row of the check table. Record each row as "triggered" or "not triggered". Do not skip a row because the chart looks fine. A check that cannot be decided because a field is missing is recorded as "unknown" and goes into Open questions.
5. **Assign severity** to each triggered check using the severity definitions. Set the verdict using the verdict rule.
6. **Write the corrected spec.** Change only what a finding requires. Keep the author's message and data. Output: the spec block in the contract below.
7. **List open questions.** Output: a numbered list, one question per missing field or unknown check. Ask for underlying numbers whenever the title or message makes a quantitative claim.

## Chart-type fit table

| Message | Fits | Does not fit |
|---|---|---|
| comparison between categories | vertical bar (up to 12 categories), horizontal bar (long labels or more than 12 categories), dot plot | pie with more than 5 slices, 3D bar, any bar with a non-zero baseline |
| trend over time | line, area only when the baseline is zero | pie, stacked area with more than 4 series |
| part-to-whole | 100% stacked bar with up to 4 segments, single stacked bar, pie with up to 5 slices | donut with more than 3 slices, pie that must show small differences |
| distribution | histogram, box plot, strip plot | bar chart of averages only |
| relationship between two numeric variables | scatter plot | dual-axis line chart |

## Check table

Each row gives the trigger, the severity when triggered and the fix to write into the corrected spec. The thresholds are working values chosen for this procedure. They are not published standards.

| Check | Trigger | Severity | Fix in corrected spec |
|---|---|---|---|
| Bar baseline | bar chart and y_axis minimum is above 0 | HIGH | set y_min to 0; if the message is about small differences, switch to dot plot and say so |
| Area baseline | area chart and y_axis minimum is above 0 | HIGH | set y_min to 0 or change to line chart |
| Dual y-axes | two y-axes with different units or scales | HIGH | split into two panels with a shared x-axis |
| Claim check | title or message states a ratio, change or "doubled" that the values do not show | HIGH | ask for values; rewrite title to the numbers given |
| 3D effect | bar, pie or area drawn with depth or perspective | HIGH | flat version of the same chart type |
| Series count | more than 5 series on one chart | MEDIUM | group the smallest into "Other" or use small multiples |
| Colour-only encoding | series told apart only by colour, with no direct label or pattern | MEDIUM | direct labels at line ends or bar ends; add a pattern or marker |
| Pie slices | pie with more than 5 slices, or slices not stated to sum to 100 percent | MEDIUM | bar chart sorted by value |
| Missing units | any axis or value label without a unit | MEDIUM | add unit to axis title, e.g. "USD millions" |
| Missing source | source_and_date missing | MEDIUM | add publisher and date line under the chart |
| Log scale | log scale used without the word "log" on the axis | MEDIUM | label axis "log scale" and add a reference value |
| Percent change on small base | percent change reported where the base value is under 10 units (working value) | MEDIUM | show absolute change next to the percent |
| Unsorted categories | categories with no natural order and sort_order is "none" | LOW | sort descending by value |
| Dense labels | more than 20 gridlines or data labels on one axis (working value) | LOW | reduce gridlines to 4 to 6 and label only key values |

Colour-blind safety is a MEDIUM concern when the spec names a red and green pair as the only distinction. Record it under Colour-only encoding.

## Severity definitions

- HIGH: the chart can make a reader believe something the data does not show.
- MEDIUM: the reader has to work to decode the chart, or a number cannot be verified from the spec.
- LOW: cosmetic; no change to what the reader concludes.

## Verdict rule

- Any HIGH finding: verdict is "do not publish as is".
- No HIGH and at least one MEDIUM: verdict is "revise before publishing".
- Only LOW findings: verdict is "ready with minor fixes".
- No findings and no unknowns: verdict is "ready".
- Any unknown check forces at least "revise before publishing" until the open question is answered.

## Output contract

Produce exactly these five headings in this order, in Markdown.

```
## Verdict
<one of the four verdict phrases>

## Chart read
- chart_type: <value>
- message: <value>
- message class: <comparison | trend | part-to-whole | distribution | relationship>
- fit: <fits | does not fit> - <reason>
- missing fields: <count> (<comma-separated names or "none">)

## Findings
| ID | Severity | Check | Problem | Fix |
|---|---|---|---|---|
| F1 | HIGH | Bar baseline | y_axis starts at 90 | set y_min to 0 |

## Corrected spec
```text
chart_type: <value>
title: <value>
x_encoding: <value>
y_axis: label=<value>; unit=<value>; min=<value>; max=<value>
series: <value>
sort_order: <value>
colour_and_labels: <value>
source_and_date: <value>
```

## Open questions
1. <question>
```

If there are no findings, write "None." under Findings and still produce the corrected spec with the unchanged values.

## Refuse / stop when

- The input is only an image, a file path or a link. Stop and ask for a text description or spec. Do not guess at the chart.
- chart_type, message or y_axis is missing. Stop and ask for the missing field before any finding is written.
- The title or message claims a change, ratio or ranking and no values are given. Ask for the underlying numbers. Do not confirm the claim.
- The user asks you to invent or fill in values, a source or a date. Refuse that part and list the value under Open questions.
- The user asks for a misleading presentation, such as a truncated axis meant to exaggerate a difference. Decline that version and offer the baseline fix or a dot plot instead.
- The user asks whether the data itself is accurate. That is outside this review. Say so and stop that part.

## Smoke check

The offline smoke task is a described vertical bar chart whose y-axis starts at 90. The procedure must flag the Bar baseline check as HIGH and write y_min to 0 in the corrected spec. Input and output files for the smoke run are kept in the fixtures folder of this package.
