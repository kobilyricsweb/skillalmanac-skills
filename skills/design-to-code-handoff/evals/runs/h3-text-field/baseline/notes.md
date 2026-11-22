# Text field: decisions and open questions

Source: `design/text-field.json` (component set "Text field", id 12:71, states Default, Focus, Error, Disabled).
Tokens: `src/tokens.css` (semantic tokens only, no palette or raw colours in components).

## Files
- `text-field.css`: component styles, plus a small demo-page layout block (`.demo*`).
- `text-field.html`: one demo per state, links `src/tokens.css` and `text-field.css`.

## Colour mapping (design hex to token)
| Design value | Hex | Token |
|---|---|---|
| Label, Focus/Error value text | #1c1b19 | `--color-text` |
| Default/Focus/Error input border | #72706b | `--color-border-control` |
| Hint text | #5c5a56 | `--color-text-muted` |
| Input surface | #ffffff | `--color-surface` |
| Focus border | #0b5cad | `--color-accent` |
| Error border, error message | #b42318 | `--color-border-danger`, `--color-text-danger` |
| Disabled surface | #f7f6f3 | `--color-surface-disabled` |
| Disabled border | #d9d7d1 | `--color-border` |
| Disabled label/value, default value | #72706b | `--color-text-placeholder` |

## Geometry decisions
- Field height 44px, horizontal padding `--space-3` (12px), radius `--radius-md` (8px).
- Border 1px in Default/Error/Disabled, 2px in Focus (as in the design).
- Type: value 16px/24px weight 400; label 14px/20px weight 500; hint and message 14px/20px. Font `--font-sans`.
- Design spacing of 6px (label to field, field to hint, icon to message text) is not on the space scale. Built as `calc(var(--space-1) * 1.5)` so it stays token-derived and exactly 6px.
- Focus ring is the design's drop shadow (spread 3px, accent at 25% alpha, radius 0). Written as `box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-accent) 25%, transparent)`. No focus-ring token exists.

## Structure decisions
- Native `<input>` with a `<label for>`, `aria-describedby` linking hint or message, and `aria-invalid="true"` in Error.
- Error message uses `--color-text-danger`; the value stays in default text colour, as in the design.
- Default state: the design shows "name@company.com" in grey. Rendered as a `placeholder` on an empty input, which matches the placeholder token. Consequence: text a user types in a Default field is `--color-text` (dark); only the placeholder is grey. Confirm this is the intended behaviour.
- Focus, Error, Disabled use real `value` attributes, as in the design.
- Focus styling applies both to `:focus-within` (real use) and to a `.text-field--focus` modifier (static demo).

## Open questions
1. **Alert icon.** The JSON gives `Icon / Alert` only as a 10x6 stroked vector bounding box (no path data). The demo uses a placeholder circle-with-exclamation SVG (16px, `currentColor`). Replace it with the real icon asset from the icon set.
2. **Spacing scale.** The 6px gap is not a token. Either add `--space-1-5` (6px) to tokens.css or keep the `calc` form. Preferred: add the token.
3. **Focus ring token.** Add something like `--shadow-focus-ring` or `--color-focus-ring` (accent at 25%) so the rgba-equivalent is not derived in the component.
4. **Border width on focus.** The 2px border is inside the 44px box, so the content box shifts by 1px on focus. The design (strokeAlign INSIDE) suggests no shift, so the content may need `padding` compensation. Not checked against the Figma render.
5. **Components.css.** The shared `.icon` class is 20px; the design icon is 16px, so the field uses its own `.text-field__icon` rather than `.icon`.
6. **Font.** Inter is not loaded by the demo (tokens name it, fallback is system-ui). Add the font link if the demo must match the design rendering exactly.
7. **Dark mode.** tokens.css has no dark theme, so none is implemented.
8. **Not verified in a browser.** The HTML was not opened or screenshotted, so visual match against the Figma frames is unconfirmed.
