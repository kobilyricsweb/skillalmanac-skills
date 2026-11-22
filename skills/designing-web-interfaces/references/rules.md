# Interface design rules and audit rule names

## Contents

1. Type
2. Spacing and layout
3. Colour and contrast
4. Hierarchy
5. Interaction states
6. Empty, error and loading states
7. Responsive behaviour
8. Motion
9. Machine-made tells
10. Rule names the script reports

Read the section that matches the finding or the part of the screen you are writing. Thresholds are working values.

## 1. Type

- Pick 4 to 8 sizes on a ratio of about 1.2 to 1.333 and use only those. Two sizes closer than 1.1 apart (14 and 15) look like an accident; two steps further apart than 1.7 leave no size for secondary text.
- Body text 16px or more. Text below 12px is for legal lines and badges only. Set body size on `html` or `body` in rem so user font settings still work.
- Body line height 1.4 to 1.8 (1.5 default); headings 1.1 to 1.3. Large text with body-like line height looks loose.
- Keep paragraphs between 45 and 75 characters wide; `max-width: 65ch` is a good default. Above 80ch the eye loses the next line.
- Rank with size and weight, not with a new font. One family is enough; a second only for display or code. Use at most 3 weights in practice and never more than 4.
- Set numbers in tables with tabular figures (`font-variant-numeric: tabular-nums`) so columns align.
- Do not mix `px` and `rem` for text sizes in one file; choose rem.

## 2. Spacing and layout

- One base unit of 4px; spacing values are multiples of 4 with 2 and 6 as rare half steps. Use 8 to 12 named steps and nothing else.
- Proximity carries meaning: the gap inside a group is at most half the gap between groups. A label sits 4 to 8px from its field; sections sit 32 to 64px apart.
- Page gutters: 16px on phones, 24 to 32px on tablets, content column at most 1200px (text columns far narrower).
- Align to a small number of left edges. Centre text only for short headings, hero statements and empty states; left-align body copy, lists, forms and tables.
- Use `gap` in grid and flex layouts rather than margins on children. Use `auto-fit` with `minmax()` for card grids so they wrap without breakpoints.
- Do not set fixed pixel widths at or above 480px; use `max-width` plus fluid width.

## 3. Colour and contrast

- Contrast ratio from the WCAG relative-luminance formula: normal text 4.5:1, large text (24px, or 18.66px and bold) 3:1, borders of form controls and meaningful icons 3:1 against their surroundings. Placeholder and disabled text are also read by users; give placeholders 4.5:1 or do not rely on them.
- Palette: one accent, one neutral ramp (7 to 9 steps, slightly tinted toward the accent), three status colours. Count the distinct values in your CSS; above about 14 the palette has no system.
- Never carry meaning by colour alone: pair red errors with text and an icon, link text with an underline or weight.
- Pure black on pure white is harsh; use a near-black (`#1f2933` style) on white, and keep dark mode backgrounds off pure black.
- Dark mode is a second set of tokens, not an inversion. Re-check every text and background pair, including status colours (a red that passes on white often fails on dark grey). Redefine all of the colour variables in the dark block.
- Text on photos or gradients needs a scrim or a solid panel; the script cannot check it, look at it.

## 4. Hierarchy

- One primary action per view, styled filled; secondary actions outlined or text; destructive actions styled by consequence, not by size.
- Three emphasis levels per screen. If everything is bold, coloured or boxed, nothing is.
- One h1 per page, no skipped heading levels; headings describe, they are not styling hooks.
- Remove a box before adding one: separate by space first, by a hairline second, by a filled surface third.
- Cards earn their border: a repeated item that is one line of text is a list row, not a card.
- Tables for comparison, lists for scanning, cards for items that have an image and several attributes.
- Number of choices: a menu of more than 7 top-level items or a form of more than about 7 fields per step needs grouping or steps.

## 5. Interaction states

- Elements: default, hover (pointer only, never the sole cue), `:focus-visible` (2px outline, 2px offset, 3:1 against its surroundings), active (pressed), disabled (reduced contrast, `cursor: not-allowed`, still readable, plus the reason nearby when it is not obvious), loading (control keeps its width, label replaced or spinner added, disabled to stop double submit), selected/current (nav item, tab, row).
- Removing the default outline is allowed only when a visible replacement exists in the same or a `:focus-visible` rule. `outline: none` alone is a FAIL.
- Controls are at least 44px tall on touch layouts (24px is the lowest WCAG 2.2 AA size; 40 is the script's warning line). Space neighbouring targets by at least 8px.
- Links inside text are underlined or otherwise distinguishable without colour; visited state optional.
- Inputs show a visible label (not placeholder-only), the value, a focus state, an error state and a help text slot.

## 6. Empty, error and loading states

- **Empty**: say what belongs here, why it is empty (new, filtered, cleared), and give one action ("Create your first invoice"). Do not use a sad illustration instead of a sentence. A filtered-empty state offers "Clear filters".
- **Error, field level**: message under or beside the field, in words that say how to fix it ("Use a date after 3 March"), linked by `aria-describedby`, `aria-invalid="true"` on the input, never colour alone. Validate on blur, re-validate on input after the first error, keep what the user typed.
- **Error, page or request level**: what failed, whether data is safe, a retry action, and a way out. Use `role="alert"` for errors that appear after an action. No raw codes as the only content.
- **Loading**: skeleton shapes for page regions that load longer than about 300ms, spinner inside the button for actions, progress bar when the length is known. Reserve space so content does not jump. Mark the region `aria-busy="true"` while loading.
- **Partial**: some data loaded, some failed: show what exists and a retry for the rest.
- **Success**: confirm in place (inline message or changed button label), not only a toast that vanishes in 3 seconds.
- Write every state's copy in the product's voice and check it fits at 360px.

## 7. Responsive behaviour

- Include `<meta name="viewport" content="width=device-width, initial-scale=1">`. Never disable zoom (`user-scalable=no`, `maximum-scale=1`).
- Design at 360px first, then add `min-width` queries only where the layout breaks. Use at most 5 breakpoints; 640, 1024 and 1280 cover most products. Use content-driven breakpoints when a component needs one.
- Prefer intrinsic layout (`flex-wrap`, `auto-fit`/`minmax`, `clamp()`) before a query.
- Navigation: collapse to a menu button below the width where links no longer fit on one line; keep the primary action visible.
- Tables: allow horizontal scroll inside a wrapper or reflow to stacked rows; never let the page scroll sideways.
- Test at 360, 768 and 1280px, and with text enlarged to 200%.

## 8. Motion

- 100 to 200ms for hover and focus feedback, 200 to 300ms for panels and dialogs. Animate `opacity` and `transform`, not layout properties.
- List the properties in `transition`; `transition: all` animates everything and causes layout work.
- Provide a `@media (prefers-reduced-motion: reduce)` block that removes or shortens movement. No autoplaying motion over text.

## 9. Machine-made tells

Each is a default that appears when no decision was made. Replace it with a decision.

| Tell | Why it reads as machine-made | Replace with |
|---|---|---|
| Violet or indigo gradient hero or buttons | The statistical default of generated UI | One brand colour, flat; a gradient only if the brand has one |
| Gradient text in headings | Decoration that lowers contrast | Solid text colour with weight |
| Several blurred translucent cards | Imitation of an effect, rarely a real overlay | Solid surfaces; blur for one real overlay |
| Everything centred | No alignment logic | Left-aligned body, forms, lists |
| Three identical feature cards with an emoji | Template layout | A list, a table or screenshots of the real product |
| Emoji as icons | Mixed styles, inconsistent rendering across systems | One icon set, one stroke weight |
| 5 or more radii, 5 or more shadows | No tokens | 2 or 3 radii, 2 or 3 elevations |
| Stock copy ("unlock", "seamless", "elevate", "next-generation", "welcome to our") | Says nothing | A sentence that says what the product does and for whom |
| Lorem ipsum or placeholder names left in | Unfinished | Real or realistic copy |
| `transition: all`, `!important` everywhere | Cascade not understood | Listed properties, fixed specificity |

## 10. Rule names the script reports

FAIL means a defect that is almost always wrong. WARN means usually wrong, check it. INFO means a limit of the check.

| Rule | Severity | Meaning |
|---|---|---|
| `viewport-meta` | fail | HTML has no viewport meta, or it lacks `width=device-width` |
| `viewport-zoom` | fail | Viewport blocks pinch zoom |
| `contrast-text` | fail, or warn when the background was assumed from `body` | Text pair below 4.5:1 (3:1 for large text); also used for tokens pairs |
| `focus-outline-removed` | fail | Outline removed, no replacement focus style |
| `state-hover`, `state-focus` | warn | Interactive elements with no hover or focus rule |
| `state-disabled` | info | No disabled style found |
| `touch-target` | warn | Control height under 40px |
| `type-min-size`, `type-body-size` | warn | A size under 12px; a body size under 16px |
| `type-scale-count` | warn | More than 8 sizes (tokens: also fewer than 4) |
| `type-near-duplicates`, `type-scale-jump` | warn | Neighbouring sizes under ratio 1.1 or over 1.7 |
| `type-weights`, `type-families` | warn | More than 4 weights, more than 3 families |
| `type-line-height`, `type-measure` | warn | Line height outside range; paragraph column over 80ch |
| `type-fluid` | info | `clamp()` or `calc()` sizes not checked |
| `space-grid`, `space-distinct` | warn | Off-grid spacing (more than 20% and at least 3 values); more than 12 distinct values (tokens: fewer than 5 or more than 12) |
| `palette-size`, `palette-hues` | warn | More than 14 colours; tokens with more than 4 hue families |
| `responsive-fixed-width` | warn | Width of 480px or more without `max-width` |
| `responsive-none` | warn | Fixed or multi-column layout with no media queries and no intrinsic layout |
| `responsive-breakpoints` | warn | More than 5 breakpoints, or not ascending (tokens) |
| `responsive-desktop-first` | info | Only `max-width` queries |
| `motion-reduced`, `transition-all` | warn | Motion without a reduced-motion block; `transition: all` |
| `heading-h1`, `heading-skip` | warn | Not exactly one h1; a level skipped |
| `states-empty`, `states-error`, `states-loading` | warn | List, form or fetch present, no matching state markup or class found (keyword check on markup, classes and script text) |
| `tell-purple-gradient`, `tell-gradient-text`, `tell-glass` | warn | Violet gradient; `background-clip: text`; 3 or more blurred surfaces |
| `tell-shadow-sprawl`, `tell-radius-sprawl`, `tell-center-everything` | warn | More than 4 shadows; more than 4 radii; 6 or more centring rules |
| `tell-emoji-icons`, `tell-filler-copy` | warn (filler: fail for Lorem ipsum) | Three or more emoji in headings, buttons, links or list items; stock phrases |
| `important-overuse` | warn | More than 5 `!important` |
| `external-stylesheet`, `css-none` | info | Linked stylesheet not followed; no CSS in the HTML file |
| `tokens-missing`, `tokens-unknown-keys`, `tokens-color-invalid`, `tokens-size-invalid`, `contrast-pairs-missing`, `contrast-pair-invalid` | warn or info | Problems with the tokens file itself; see tokens-schema.md |
