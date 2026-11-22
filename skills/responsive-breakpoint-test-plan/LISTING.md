# responsive-breakpoint-test-plan

## One line

Turns a site's CSS breakpoints into a fixed viewport matrix, content stress cases and per-width pass criteria, with a verdict that cannot be PASS from CSS reading alone.

## What it does

The skill reads every media query that changes layout and records each breakpoint with its source. It then derives test widths: each breakpoint plus one pixel below and one pixel above, and two fixed edges at 320 and 1920 px. The width list is the base of a matrix. Each width is crossed with seven content stress cases: the content as shipped, a 40-character unbroken word, a 200 percent text zoom modelled as half the viewport width, right-to-left direction, empty states, a 200-item list, and a landscape height of 600 px at three widths. The worked example in the skill has 11 widths and 48 cells.

For every cell the skill names six checks: horizontal scroll, minimum target size, clipped text, overlapping interactive elements, keyboard reachability, and average line length. Five of these are required. The pass thresholds are written in a table, with the source of each threshold stated: the 24 px target minimum comes from WCAG 2.2, and the 45 to 90 character line range is marked as a working value.

The output is a fixed set of sections, a cell matrix with named columns, and a JSON summary object. Verdict rules separate a full pass, a pass with an advisory for the extreme zoom cell, and NOT VERIFIED. Cells that were not measured are listed by name with a reason.

## When to use

- Before a layout change ships and you need to know which widths to test.
- When a bug is reported only at widths between two breakpoints, and the plan must cover the edges on both sides.
- When a reviewer wants a written matrix of widths, stress cases and pass criteria to hand to whoever runs the browser checks.
- When the stylesheet has three or more breakpoints and manual choice of widths is error-prone.

## When not to use

- To write or edit CSS. The skill only plans the tests.
- To run a browser or take measurements. The skill defines what to measure and records what was reported to it.
- To claim that a layout is responsive. The verdict rules make that claim impossible without a measured run.
- For native mobile apps or for designs without a media-query breakpoint model.

## Requirements

No scripts, no network, and no packages. Any text-capable agent can follow the procedure. The user must supply the media queries, a description or copy of the page content, and ideally the base font size. Measurement needs a browser or a test tool that the user runs; the skill does not provide one.

## Example

Input: breakpoints 600, 900 and 1200 pixels, no browser run. The Summary section of the output reads:

    {"slug": "responsive-breakpoint-test-plan", "breakpoints": [600, 900, 1200], "widths": [320, 599, 600, 601, 899, 900, 901, 1199, 1200, 1201, 1920], "cells_total": 48, "pass": 0, "fail": 0, "not_run": 48, "verdict": "NOT VERIFIED"}

The skill derives those 11 widths and 48 cells across seven stress cases. Because nothing was measured, every cell is listed in the Not run section with a reason.

## Limits

- The stress cases are generic. Content that the plan does not describe, such as embedded maps or third-party widgets, is not covered until the user adds it.
- The 200 percent zoom is modelled by halving the viewport width. It does not replicate the browser text-zoom engine.
- Working values such as the 44 px primary-action target and the line length range are not industry standards.
- The matrix covers only the widths listed. It says nothing about widths between the chosen ones.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
