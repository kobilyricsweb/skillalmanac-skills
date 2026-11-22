---
name: responsive-breakpoint-test-plan
description: Plans responsive layout tests from CSS breakpoints. Use when a user needs a viewport test matrix, asks which widths to check before a layout ships, or reports bugs that appear only at in-between widths. Derives widths at, one below and one above each breakpoint, plus 320 and 1920, then adds content stress cases and per-width pass criteria. Do not use for writing CSS, running browser tests, or declaring a layout responsive from CSS alone.
license: Apache-2.0
compatibility: "Type B: none beyond a text-capable agent; no scripts and no network."
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Responsive breakpoint test plan

Use this procedure to turn a site's media queries into a fixed list of viewports, content stress cases and pass criteria. The output is a plan plus a result matrix. A plan alone is not evidence that a layout works; see the verdict rules.

## Inputs

- Every media query in the CSS that changes layout (min-width and max-width values). Accept the stylesheet files or a pasted list.
- The page or component under test, with its real content: at least one text block, one group of links or buttons, one form control set, and any list or table.
- Base font size in px (default 16 px if the user does not say; state the assumption in the output).

## Workflow

1. Collect breakpoints. Read every media query. Record each value in px with its direction (min or max) and its source file and line. Convert em or rem at the base font size. Sort ascending and remove duplicates. If two values differ by less than 2 px, keep both and mark them near-duplicate for review. Required output: the BREAKPOINTS table (columns: value_px, direction, source, note).
2. Derive test widths using Table 1. Required output: the WIDTHS list, sorted, with no duplicates and each entry tagged with its origin (B-1, B, B+1, fixed).
3. Set viewport heights. Every width is tested at height 800 px. Only the widths in the landscape row of Table 1 also run at height 600 px. Required output: the VIEWPORTS list.
4. Build the cell list from Table 2. A cell is one width crossed with one stress case. Required output: the cell count per stress case and the total. The total must equal the sum in Table 2.
5. Run the checks in Table 3 for each cell. Record measured values (px, counts, booleans), not impressions. If a check cannot be measured in the environment, record result not_run and the reason. Do not estimate a value.
6. Apply the pass criteria in Table 3 and the verdict rules in Table 4. A cell passes only when every required check passes.
7. Write the output contract below. Include the assumptions from step 1 and the list of cells that were not run.

## Table 1: width rule

| Source | Widths added | Origin tag |
|---|---|---|
| each breakpoint B | B-1, B, B+1 | B-1, B, B+1 |
| fixed floor and ceiling | 320 and 1920 | fixed |
| landscape pass | none added, only height 600 applied at 899, 900, 1199 | n/a |

Worked example, breakpoints 600, 900, 1200: widths are 320, 599, 600, 601, 899, 900, 901, 1199, 1200, 1201, 1920 (11 widths). Landscape cells are 899, 900 and 1199 at height 600.

## Table 2: stress cases and cell counts

| Case | Setup | Widths | Cells |
|---|---|---|---|
| base | content exactly as shipped | all 11 | 11 |
| long_word | one 40-character unbroken string placed in every text block | all 11 | 11 |
| zoom_200 | effective width = width / 2, which stands in for 200 percent text zoom | all 11 | 11 |
| rtl | dir set to rtl on the html element | 320, 600, 900, 1200, 1920 | 5 |
| empty | every list, table and result area with zero items | 320, 900, 1920 | 3 |
| long_list | 200 items in each list | 320, 600, 900, 1200 | 4 |
| landscape | height 600 px | 899, 900, 1199 | 3 |

Total cells: 48 for the worked example. Effective width 160 px at width 320 under zoom_200 is a stress floor, not a supported size. A failure in that one cell is advisory.

## Table 3: checks and pass criteria

| Check | How it is measured | Pass threshold | Required |
|---|---|---|---|
| horizontal_scroll_px | page scroll width minus viewport width | 0 px | yes |
| min_target_px | smallest width or height of any link, button or form control | 24 px or more (WCAG 2.2 SC 2.5.8 minimum). Working value 44 px for primary actions | yes at 24 px |
| clipped_text | text blocks whose content is larger than their box | 0 | yes |
| overlap | pairs of interactive elements whose boxes intersect | 0 | yes |
| keyboard_reachable | every control appears in the tab order at this width | all reachable | yes |
| avg_line_chars | average characters per line in the main body text | 45 to 90. Working value, not a published standard | no, advisory |

## Table 4: verdict rules

| Condition | Verdict |
|---|---|
| every required check passes in every cell | PASS |
| any required check fails in a cell with stress case base, long_word, rtl, long_list or empty | FAIL |
| any required check fails in a zoom_200 cell at a width other than 320, or in a landscape cell | FAIL |
| a required check fails only in the zoom_200 cell at 320 | PASS WITH ADVISORY |
| any cell is not_run, or no measured run exists | NOT VERIFIED |

A CSS reading alone never produces PASS. Use NOT VERIFIED when only the plan was produced.

## Output contract

Write these sections in this order.

1. Heading "Breakpoints" with the BREAKPOINTS table and the assumed base font size.
2. Heading "Widths and viewports" with the WIDTHS list (each tagged with origin) and the VIEWPORTS list.
3. Heading "Cell matrix" with a table whose columns are: width, height, stress, horizontal_scroll_px, min_target_px, clipped_text, overlap, keyboard_reachable, avg_line_chars, result, note.
4. Heading "Summary" with a JSON object using exactly these keys: slug, breakpoints, widths, cells_total, pass, fail, not_run, verdict.
5. Heading "Not run" listing each cell that has result not_run and its reason.

Example summary object for a plan with no measured run:

{"slug": "responsive-breakpoint-test-plan", "breakpoints": [600, 900, 1200], "widths": [320, 599, 600, 601, 899, 900, 901, 1199, 1200, 1201, 1920], "cells_total": 48, "pass": 0, "fail": 0, "not_run": 48, "verdict": "NOT VERIFIED"}

## Refuse / stop when

- No media queries are supplied or the CSS cannot be read. Stop and ask for the stylesheet or the list of breakpoints. Do not guess breakpoints.
- The user asks to call the layout responsive from CSS alone or without a measured run. Refuse and report NOT VERIFIED.
- The user asks for a claim that the layout works on all devices. Refuse. The matrix covers only the listed widths and stress cases.
- Breakpoints are in em or rem and no base font size is known. Stop and ask for it.
- The user asks you to write or change CSS. This procedure is out of scope.
- A stress case needs content the user has not supplied. Mark those cells not_run. Do not invent content.
- Any measured value is missing for a required check. Record not_run for that cell and do not fill the value.
