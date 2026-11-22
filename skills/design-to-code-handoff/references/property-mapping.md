# Node properties to CSS

The node shape is the REST export used by Figma and tools that copy it. Field names below are as they appear in the JSON.

## Contents

- Auto layout container
- Child sizing
- Position and constraints
- Fills, strokes, radius, effects
- Text
- Node types
- Units and conversions that go wrong
- Sources

## Auto layout container

| Node field | Value | CSS |
|---|---|---|
| `layoutMode` | `HORIZONTAL` / `VERTICAL` | `display: flex` / plus `flex-direction: column` |
| `layoutMode` | `NONE` or absent | Not a flex container: children are placed by coordinates. Infer the flow |
| `layoutMode` | `GRID` | `display: grid`; read the row and column counts and track sizes |
| `itemSpacing` | n | `gap: npx` (ignored when the primary axis is `SPACE_BETWEEN`) |
| `layoutWrap` | `WRAP` | `flex-wrap: wrap`; `counterAxisSpacing` becomes `row-gap` |
| `primaryAxisAlignItems` | `MIN` / `CENTER` / `MAX` / `SPACE_BETWEEN` | `justify-content: flex-start` (default) / `center` / `flex-end` / `space-between` |
| `counterAxisAlignItems` | `MIN` / `CENTER` / `MAX` / `BASELINE` | `align-items: flex-start` / `center` / `flex-end` / `baseline` |
| `paddingTop` `paddingRight` `paddingBottom` `paddingLeft` | n | `padding` |
| `clipsContent` | true | `overflow: hidden` |
| `itemReverseZIndex` | true | First child paints on top: reverse the stacking with `z-index` or `isolation` |

`MIN` on the counter axis means children keep their own size. CSS defaults to `stretch`, so `align-items: flex-start` must be written out.

## Child sizing

Newer exports carry `layoutSizingHorizontal` and `layoutSizingVertical` on each layer.

| Value | Along the parent's main axis | Across it | No auto-layout parent |
|---|---|---|---|
| `FIXED` | `width`/`height` in px, plus `flex-shrink: 0` | `width`/`height` in px | px size |
| `HUG` | No size: content decides | No size | No size |
| `FILL` | `flex: 1 1 0` and `min-width: 0` (or `min-height: 0`) | `align-self: stretch` | `100%` |

Older exports use `layoutGrow: 1` (fill along the main axis) and `layoutAlign: "STRETCH"` (fill across), and on the container `primaryAxisSizingMode` / `counterAxisSizingMode` with `FIXED` or `AUTO` (hug).

`minWidth`, `maxWidth`, `minHeight`, `maxHeight` map directly. `min-width: 0` on a filling child is what lets long text truncate or wrap instead of pushing the layout wider.

## Position and constraints

- `layoutPositioning: "ABSOLUTE"`: the child is taken out of the flow; the parent needs `position: relative`. Offsets come from the two `absoluteBoundingBox` rectangles: left is child x minus parent x, and so on.
- `constraints.horizontal`: `LEFT` pin left, `RIGHT` pin right, `LEFT_RIGHT` pin both (stretches), `CENTER` centre, `SCALE` percentages. `constraints.vertical`: `TOP`, `BOTTOM`, `TOP_BOTTOM`, `CENTER`, `SCALE`.
- `absoluteBoundingBox` is in canvas coordinates. It is a measurement, not a layout instruction: never emit `left`/`top` from it for in-flow layers.
- `rotation` in REST exports is in radians.

## Fills, strokes, radius, effects

| Node field | CSS | Notes |
|---|---|---|
| `fills[]` of type `SOLID` | `background-color`; on text, `color` | Channels are 0 to 1 floats: multiply by 255 and round. Effective alpha is `color.a` times the paint's `opacity`. Skip paints with `visible: false`. The last visible paint is on top |
| `fills[]` of type `GRADIENT_LINEAR` | `linear-gradient(angle, stops)` | Angle from the first two `gradientHandlePositions`; stop positions are 0 to 1 |
| `fills[]` of type `IMAGE` | `img` or `background-image` | `scaleMode` `FILL` is `cover`, `FIT` is `contain`, `TILE` is `repeat`. The export holds a reference, not the file |
| `strokes[]` with `strokeWeight` | `border: w solid colour` | `strokeAlign` `INSIDE` equals a border under `box-sizing: border-box`. `OUTSIDE` adds to the box: use `outline` or a spread shadow. `CENTER` straddles the edge |
| `individualStrokeWeights` | `border-top` and the rest | For dividers on one side |
| `strokeDashes` | `border-style: dashed` | Exact dash lengths need SVG |
| `cornerRadius` | `border-radius` | A radius of half the height or more is a pill: use a large value such as 9999px |
| `rectangleCornerRadii` | four values | Order is top-left, top-right, bottom-right, bottom-left, the same as CSS |
| `effects[]` `DROP_SHADOW` | `box-shadow: x y blur spread colour`; on text, `text-shadow` without spread | Several shadows are comma-separated, first on top |
| `effects[]` `INNER_SHADOW` | `box-shadow: inset ...` | |
| `effects[]` `LAYER_BLUR` / `BACKGROUND_BLUR` | `filter: blur()` / `backdrop-filter: blur()` | The design radius is about twice the CSS blur radius |
| `opacity` | `opacity` | Applies to the whole subtree, unlike a paint's opacity |
| `blendMode` other than `NORMAL` or `PASS_THROUGH` | `mix-blend-mode` | Check the result by eye |

## Text

Fields are under `style` on `TEXT` nodes; the string is `characters`.

| Field | CSS | Notes |
|---|---|---|
| `fontFamily`, `fontWeight`, `italic` | `font-family`, `font-weight`, `font-style` | Use the project's font stack variable; confirm the weight is actually loaded |
| `fontSize` | `font-size` | px in the export; convert to rem if the project uses rem (divide by 16 unless the root differs) |
| `lineHeightPx` with `lineHeightUnit: "PIXELS"` | `line-height: lineHeightPx / fontSize` | Unitless, so it scales with the font size |
| `lineHeightPercentFontSize` with `"FONT_SIZE_%"` | `line-height: value / 100` | |
| `lineHeightUnit: "INTRINSIC_%"` | `line-height: normal` | "Auto" in the design tool |
| `letterSpacing` | `letter-spacing: letterSpacing / fontSize` in `em` | The REST value is in px. A design-panel percentage of 2% is `0.02em` |
| `textAlignHorizontal` | `text-align` | `JUSTIFIED` is `justify` |
| `textCase` | `text-transform` | `UPPER`, `LOWER`, `TITLE`. Keep the source string in natural case |
| `textDecoration` | `text-decoration` | `UNDERLINE`, `STRIKETHROUGH` |
| `textAutoResize` | sizing behaviour | `WIDTH_AND_HEIGHT`: single line that hugs. `HEIGHT`: fixed width, wraps. `NONE`: fixed box. `TRUNCATE`: ellipsis |
| `maxLines` with truncation | `-webkit-line-clamp` | |
| `paragraphSpacing` | margin between paragraphs | |
| `characterStyleOverrides` and `styleOverrideTable` | inline spans | A bold word inside a sentence lives here |

The text box height in the export includes the line-height, so vertical gaps between text layers already account for it. Do not add extra margin.

## Node types

| Type | Treat as |
|---|---|
| `FRAME`, `GROUP`, `SECTION` | Container. A `GROUP` has no layout of its own |
| `COMPONENT`, `COMPONENT_SET` | A component definition and its variants. Variant names look like `Property=Value, Property=Value` |
| `INSTANCE` | A use of a component: reuse the code component. `componentProperties` holds the variant and text props |
| `TEXT` | Text |
| `RECTANGLE`, `ELLIPSE` | A box (an ellipse with equal sides is `border-radius: 50%`); often a divider or an image holder |
| `VECTOR`, `BOOLEAN_OPERATION`, `STAR`, `LINE`, `REGULAR_POLYGON` | An icon or illustration asset: export as SVG |

A layer with `visible: false` is not part of the design to build.

## Units and conversions that go wrong

- Colour floats: `0.043` is 11, not 4. Round after multiplying by 255.
- An 8-digit hex or a paint opacity is alpha: keep it (`rgba` or the 8-digit form), do not drop it.
- A `strokeWeight` of 1 with `CENTER` alignment renders half a pixel each side: designers usually mean `INSIDE`. Ask or note it.
- Shadows: design tools give offset, blur, spread and a colour with alpha. CSS order is x, y, blur, spread, colour.
- Sub-pixel sizes (`23.99998`) are export noise: round to the nearest whole px, or half px for hairlines.
- Font weights map to numbers; names such as "Semi Bold" are 600, "Medium" 500.
- The canvas x and y of the top frame are meaningless outside the design file.

## Sources

- Figma REST API, node types and properties: https://developers.figma.com/docs/rest-api/file-node-types/
- Figma REST API, property types (Paint, Effect, TypeStyle, LayoutConstraint): https://developers.figma.com/docs/rest-api/file-property-types/
- MDN, CSS flexible box layout: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout
