# ui-animation-timing-spec

## One line

Turns a list of interface transitions into one timing and easing table, with durations by size tier, easing by role, stagger for groups and a reduced-motion variant for every row.

## What it does

The skill takes a list of UI transitions for a product screen, such as a settings drawer, a toast or a modal dialog. For each transition it needs the element, the trigger and the purpose. From those facts it picks a size tier by how much of the viewport the element covers, assigns an enter duration from that tier, and derives the exit duration as 70 percent of the enter value, rounded to 10 ms. Easing follows the role of the motion: enter uses ease-out, exit uses ease-in, and position changes use ease-in-out. Lists of two or more items receive a stagger step between 30 and 60 ms, capped at six staggered items. Every row carries an opacity-only reduced-motion variant lasting 100 ms. The output is a status line, one summary table, and a refused list. Transitions that rely on movement alone to convey meaning, or that flash more than three times a second, are refused with a required fix.

## When to use

Use it when a team has several transitions that were timed by feel and needs one consistent table to hand to a front-end developer. It suits a settings drawer, notification toasts, dialogs, popovers and list reveals on a single product. The output is a table of numbers and keywords, so a developer can apply it directly in any animation system.

## When not to use

Do not use it to write CSS, JavaScript or framework animation code. Do not use it to pick a brand motion style or to decide how expressive an interface should be. It does not cover video, 3D, game or physics-based motion, and it does not measure real frame timing on a device.

## Requirements

A text-capable agent that can read a list and write a Markdown table. No scripts, no network access, no packages, and no files beyond the transition list.

## Example

Input: five transitions for a settings drawer, a toast and a modal dialog, each with element, trigger and purpose.

```
Status: complete

## Summary

| ID | Element | Transition | Trigger | Tier | Duration ms | Easing | Stagger ms | Reduced-motion alternative |
|---|---|---|---|---|---|---|---|---|
| T1 | Settings drawer | enter | Settings button press | medium | 300 | ease-out | n/a | Opacity 0 to 1, 100 ms, ease-out, no travel |
| T2 | Settings drawer | exit | Close button or scrim click | medium | 210 | ease-in | n/a | Opacity 1 to 0, 100 ms, ease-in, no travel |
| T3 | Toast | enter | Save action completes | small | 200 | ease-out | n/a | Opacity 0 to 1, 100 ms, ease-out, no travel |
| T4 | Toast | exit | Five-second timer ends or dismiss control | small | 140 | ease-in | n/a | Opacity 1 to 0, 100 ms, ease-in, no travel |
| T5 | Modal dialog | enter | Confirm button on a destructive action | large | 400 | ease-out | n/a | Opacity 0 to 1, 100 ms, ease-out, no travel |

## Refused

None.
```

## Limits

The tier ranges, the 70 percent exit rule, the easing cubic-bezier values, the stagger step and the 100 ms reduced-motion duration are working values. They are not a published standard, and a team with its own motion tokens should replace them. The tier is an estimate from the viewport share the author supplies, not a measurement. The skill does not check how a transition looks on a device, and it does not know the rendering performance of the target platform.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
