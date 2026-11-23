---
name: ui-animation-timing-spec
description: Writes a UI animation timing and easing spec for a set of interface transitions. Use when a product team needs consistent durations, easing curves, stagger timing and reduced-motion fallbacks for drawers, toasts, modals, menus or list entries. Do not use for writing CSS or JavaScript animation code, for choosing a brand motion style, or for video, 3D or game animation.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# UI Animation Timing Spec

This skill turns a list of interface transitions into one timing and easing spec. It sets durations by size tier, easing by role, stagger for groups, and a reduced-motion variant for every row. It works from the transition list alone and runs no code.

## Workflow

1. **Intake.** Read the transition list. Each transition needs three facts: element, trigger and purpose (confirm, orient, warn or reveal). A purpose outside those four values counts as missing. Output: one intake row per transition, numbered T1, T2 and so on. If a fact is missing, apply the stop rule below.
2. **Tier.** Estimate the element's end-state area as a share of the viewport, then read the tier from the Duration tiers table. A modal dialog with a backdrop is always large. Output: one tier name per transition.
3. **Enter duration.** Take the tier's default value. Use another value only if it falls inside the tier's enter range and the reason is stated in one sentence. A move transition uses the same enter ms as its tier. Output: enter ms, and the same value for each move transition.
4. **Exit duration.** Exit ms = enter ms x 0.7, rounded to the nearest 10 ms, never below 100 ms. The 0.7 factor and the 100 ms floor are working values, not a published standard. Output: exit ms for each exit transition.
5. **Easing.** Pick the keyword from the Easing by role table: enter, exit or move. Output: one keyword per transition.
6. **Stagger.** Only for a transition that reveals two or more items of one group. Output: step in ms, or n/a.
7. **Reduced motion.** Write the variant for every row using the Reduced-motion rules. Output: one short phrase per row.
8. **Refusal check.** Apply the Refuse rules. A refused transition gets no summary row. Output: the refused list.
9. **Summary.** Write the Output contract sections in order: status, summary table, refused list, and questions when status is partial.

## Duration tiers (working values)

These ranges are working values. They are not a published standard.

| Tier | Choose when | Enter range | Default enter |
|---|---|---|---|
| micro | State feedback with no travel: hover, press, toggle color | 100-150 ms | 120 ms |
| small | Element covers under 25% of the viewport and enters or leaves: toast, tooltip, small menu | 150-250 ms | 200 ms |
| medium | Element covers 25% to under 60% of the viewport: drawer, popover, side panel | 250-400 ms | 300 ms |
| large | Element covers 60% or more of the viewport, or is a modal dialog | 300-500 ms | 400 ms |

The enter range applies to enter transitions only. Exit values come from step 4 and can fall outside the range.

## Easing by role (working values)

| Role | Keyword | Working cubic-bezier | Apply to |
|---|---|---|---|
| enter | ease-out | (0, 0, 0.2, 1) | Element appears or arrives |
| exit | ease-in | (0.4, 0, 1, 1) | Element leaves the screen |
| move | ease-in-out | (0.4, 0, 0.2, 1) | Element changes position and stays visible |

The keywords are the spec. The cubic-bezier values are working values to be replaced by the team's own curves if it has them.

## Stagger rules (working values)

- Step: 30 ms to 60 ms. Default 40 ms.
- At most 6 items are staggered. Item 1 starts at 0 ms; item n starts at (n - 1) x step. Items 7 and later start with item 6.
- Example: six items at 40 ms start at 0, 40, 80, 120, 160 and 200 ms. Item 9 also starts at 200 ms.
- The reduced-motion variant sets stagger to 0 ms, so all items change together.

## Reduced-motion rules

Every row gets this variant unless the transition is refused:

- Opacity only: 0 to 1 on enter, 1 to 0 on exit, 100 ms (working value), ease-out for enter or ease-in for exit.
- No translation, scale or rotation.
- Stagger 0 ms.
- Repeating or looping motion stops and shows its end state.

## Refuse rules

Mark the transition refused and leave it out of the summary table when:

- The motion is the only carrier of information, for example a warning shown only by a shake, with no text, icon or color change. Required fix: add a non-motion cue and resubmit.
- The motion flashes more than 3 times in any one second, the general flash threshold in WCAG 2.3.1. Required fix: reduce the flashes to 3 or fewer per second, or remove the flash.

## Stop rule for missing intake facts

- A transition missing element, trigger or purpose is left out of the summary table.
- Write one numbered question per missing fact, for example "1. What starts the toast?", and list them under Questions.
- Set status to partial. Do not guess a missing fact.
- If no transition has enough facts, the summary table has zero rows and the output is the Questions list with the status line.

## Output contract

Write these sections in this order.

1. `Status: complete`, `Status: partial` or `Status: refused`.
   - complete: every transition has a summary row and none is refused.
   - refused: every transition is refused.
   - partial: any other outcome.
2. `## Summary`: one table with these columns, in this order:
   `| ID | Element | Transition | Trigger | Tier | Duration ms | Easing | Stagger ms | Reduced-motion alternative |`
   Transition is enter, exit or move. Duration ms is an integer. Stagger ms is an integer or n/a.
3. `## Refused`: one bullet per refused transition in the form `ID: reason; required fix`. Write `None.` when empty.
4. `## Questions`: a numbered list. Include this section only when status is partial.

## Shipped files

- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text for this skill.
