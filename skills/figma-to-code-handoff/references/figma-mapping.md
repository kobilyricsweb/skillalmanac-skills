## Contents

1. Auto layout to flexbox
2. Frame, text and effect properties
3. Component properties to code props
4. Exported asset names

## 1. Auto layout to flexbox

Write `display: flex` on every auto layout frame. Then:

| Figma | CSS | Trap |
|---|---|---|
| Direction horizontal / vertical | `flex-direction: row` / `column` | |
| Spacing between items N | `gap: Npx` | |
| Spacing between items "Auto" | `justify-content: space-between` | gap is not used; with one child it pins to the start |
| Padding top, right, bottom, left | `padding: T R B L` | the four values are listed separately in the export; collapse only when equal |
| Alignment, primary axis (left/centre/right in a row, top/centre/bottom in a column) | `justify-content: flex-start / center / flex-end` | |
| Alignment, counter axis | `align-items: flex-start / center / flex-end` | the 3x3 alignment grid sets both; read the axis from the direction |
| Child "Fixed" size N | `width` or `height: Npx` | on the primary axis add `flex: none`, or the child shrinks |
| Child "Hug contents" | leave the size `auto` | do not write `width: fit-content` unless the parent stretches it |
| Child "Fill container", primary axis | `flex: 1 1 0` and `min-width: 0` | without `min-width: 0` long text overflows |
| Child "Fill container", counter axis | `align-self: stretch` | |
| Wrap | `flex-wrap: wrap`; counter-axis spacing becomes `row-gap` | |
| Child with absolute position | `position: absolute` with `top`, `right`, `bottom`, `left` from its constraints; parent gets `position: relative` | the child no longer takes part in `gap` |
| Clip content | `overflow: hidden` | also clips focus rings and shadows of children |
| Min / max width or height | `min-width`, `max-width`, and so on | |

A grid-type auto layout becomes CSS grid (`grid-template-columns` from the column definitions, `gap` from the spacing); read its properties from the export, do not infer them from flex rules.

## 2. Frame, text and effect properties

| Figma | CSS | Trap |
|---|---|---|
| Corner radius | `border-radius` | independent corners are four values, in the order top-left, top-right, bottom-right, bottom-left |
| Stroke, inside | `border` with `box-sizing: border-box` | Figma strokes sit inside by default, which is what border-box gives |
| Stroke, outside | `outline` or `box-shadow: 0 0 0 2px <stroke colour>` (spread equals the stroke width) | adding a `border` would grow the box |
| Stroke, centre | no exact equivalent | report it, do not guess |
| Fill with an alias variable | `background: var(--token)` | use the token, not the resolved hex |
| Drop shadow x, y, blur, spread, colour | `box-shadow: x y blur spread colour` | text and icon shadows use `text-shadow` or `filter: drop-shadow()` with no spread |
| Line height in px | `line-height` as a unitless ratio (px divided by font size), or the px value | state which; a ratio scales with user font size |
| Letter spacing in % | `letter-spacing` in em, percent divided by 100 | `-2%` is `-0.02em` |
| Letter spacing in px | `letter-spacing` in px | |
| Text "Hug" | text sizes to its content on one line | real content wraps; give the container a `max-width` instead of `white-space: nowrap` |
| Opacity | `opacity` | a variable stored as 0-100 must be divided by 100 |

## 3. Component properties to code props

| Figma property | Code | Rule |
|---|---|---|
| Variant property whose values are an option set (Type, Size, Intent) | one prop with a string union; property name in camelCase, values in lower-case kebab | `Size: Small / Medium / Large` becomes `size: "sm" | "md" | "lg"`; reuse the scale names of the spacing tokens and record the mapping |
| Variant property named State with Hover, Pressed, Focused, Disabled | CSS `:hover`, `:active`, `:focus-visible`, and the `disabled` attribute | not a prop. Default is the base style |
| State driven by data (Loading, Selected, Error, Checked) | a boolean prop or a native attribute | `aria-selected`, `aria-checked`, `aria-invalid` where they apply |
| Boolean property | boolean prop, default as in Figma | a boolean that only shows or hides one instance swap is dropped in favour of the slot below |
| Instance swap (Leading icon) | an optional slot prop (`leadingIcon?: ReactNode` or a named slot) | presence of the slot replaces the matching "Show leading icon" boolean |
| Text property (Label) | `children` for buttons, links and badges; a string prop when the component lays the text out itself | |
| Default values in Figma | default prop values | missing defaults are a question for the designer |
| Variant combinations that do not exist | not representable in types | list them under "Left for the designer"; do not silently allow them |

For each component list: props with types and defaults, states handled by CSS, slots, and the tokens each variant uses. Check that every variant colour is a token alias, not a hex.

## 4. Exported asset names

Rule: `<kind>-<name>[-<size>].<ext>` with `@2x` or `@3x` only on raster files. Kinds: `icon`, `logo`, `img`, `illus`. All lower-case kebab.

| Figma layer name | File name | Why |
|---|---|---|
| `Icons / Plus` | `icon-plus.svg` | slash and spaces become hyphens; the group name becomes the kind |
| `Icons / Arrow Right` | `icon-arrow-right.svg` | |
| `Logo Mark@2x` | `logo-mark@2x.png` | the scale suffix is kept on rasters only |
| `hero image final (2)` | `img-hero.webp`, and a question | "final" and "(2)" mean several versions exist; confirm which is current before naming |

- After normalising, two layers that give the same file name are a collision: rename one of them with a distinguishing word, never overwrite.
- Single-colour SVG icons: set fill and stroke to `currentColor`, keep `viewBox`, drop fixed `width` and `height`, so size and colour come from CSS.
- Photos: webp or avif; flat UI graphics with transparency: svg when vector, webp or png otherwise.
- A slash in a layer name may become a folder separator in some exports, so check the output paths before wiring imports.
