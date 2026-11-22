# chart-readability-review

## One line
Reviews a text description of a chart for misleading axes, unlabelled units, missing sources and poor chart-type choices, then returns a severity-ranked findings table and a corrected spec.

## What it does
The skill takes a written description or spec of one chart and works through a fixed procedure. It first checks that the required fields are present: chart type, the message the title is trying to make, the y-axis range and unit, the series, the sort order and the source. It then classifies the message as comparison, trend, part-to-whole, distribution or relationship, and tests whether the chart type fits that message.

Next it runs a fixed list of checks. These include a bar or area chart whose y-axis does not start at zero, dual y-axes, 3D effects, more than five series, series told apart only by colour, pies with too many slices, missing units or sources, log scales without a label, and unsorted categories. Each triggered check gets a HIGH, MEDIUM or LOW severity, and the verdict follows from the highest severity found.

The output is a fixed set of five Markdown sections: verdict, chart read, findings, corrected spec and open questions. The corrected spec changes only what a finding requires and keeps the author's message and values.

## When to use
Use it when a person has a chart in mind, in a draft, a slide or a mock-up, and can describe it in text. Typical cases are a bar chart headed for a report, a dashboard panel described in a ticket, or a chart in a blog draft whose axis may start away from zero. It is also useful before a chart is built, when the spec is still a sketch and the risks are cheap to fix.

## When not to use
Do not use it for an image or screenshot that the agent cannot read, for generating chart code, for picking a charting library or colour palette, or for checking whether the underlying numbers are correct. The skill refuses to judge a chart that has not been described and asks for the underlying values before it confirms any claim about change or growth.

## Requirements
Any text-capable agent. No scripts, no network access and no extra packages. The input is plain text of a few lines. The output is Markdown.

## Example
The smoke run used a described bar chart with the y-axis starting at 90. The first lines of the review, copied from the fixture output, are:

```
## Verdict
do not publish as is

## Chart read
- chart_type: vertical bar chart, single series
- message: Our Q3 sales grew sharply over Q2
- message class: trend
- fit: does not fit - a trend over time fits line or zero-baseline area; bars are not in the trend row of the fit table
```

The Findings table in the same output flags the baseline as HIGH: the Q3 bar draws 14 units tall against 6 for Q1, while the values differ by 8.3 percent.

## Limits
The thresholds, such as the 10-unit base for percent change and the 5-series limit, are working values chosen for this procedure. They are not published standards. The skill checks only what the description states, so a description that omits the y-axis range cannot show a truncated axis. It does not evaluate colour contrast beyond the single colour-only rule, and it does not judge whether a chart is attractive. It was run once on one fixture.

## Status
Provisional. Lint-clean, one smoke run. Not independently verified.
