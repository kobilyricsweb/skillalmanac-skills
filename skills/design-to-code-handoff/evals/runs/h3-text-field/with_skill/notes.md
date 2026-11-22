# Text field: build notes

Source: `design/text-field.json` (COMPONENT_SET "Text field", 360x520; variants State=Default, Focus, Error, Disabled; each 320x96). Tokens: `src/tokens.css`. Shared components checked: `src/components.css` (buttons and `.icon` only; no input or alert-icon component exists, so the text field is new).

Files: `text-field.html` (demo of all four states), `text-field.css` (component).

## Decisions

| Item | Spec | Built | Why |
|---|---|---|---|
| Stack gap (label, input, hint/message) | 6px | 6px, no token | Off-token, equidistant from --space-1 (4px) and --space-2 (8px). Kept the spec value so the stack matches the 96px component height. |
| Icon-to-message gap | 6px | 6px, no token | Same as above. |
| Input vertical padding | 10px | Replaced by `height: 44px` with vertical centring; horizontal padding `--space-3` (12px) | 10px padding plus a 24px line in a 44px control does not fit once the 1px border is counted. A single-line input centres its text, so height governs. |
| Input height | 44px fixed | `height: 44px` on the `<input>` | Fixed control height is part of the design. A single-line input scrolls rather than grows, so the skill's min-height guidance does not apply to it. |
| Input border width | 1px default, 2px focus | Always 1px; focus adds `inset 0 0 0 1px` accent shadow | Avoids a 1px layout shift on focus. Visual result is the same 2px accent edge. |
| Focus ring | `0 0 0 3px rgba(11,92,173,0.25)` | Same value, raw | No accent-alpha token exists. The colour is palette-blue-600 at 25%. |
| Error ring | not in design | Danger ring on `aria-invalid="true"` + `:focus-visible` | The design has no focused-error frame. This is a decision; see open questions. |
| Text element | design "Value" is a text layer | `<input type="email">` | A text field needs a real input for editing, labels and validation. |
| Label and hint | TEXT layers | `<label for>`, `<p>` linked with `aria-describedby` | Accessible association. |
| Placeholder | design shows the value text in placeholder colour | `placeholder` attribute, styled with `--color-text-placeholder` | Default has an empty value with a placeholder. |
| Disabled label colour | design shows label in placeholder colour | `:has(> .text-field__input:disabled)` selector on the label | Keeps the disabled state on real selectors without a toggle class. |
| Component width | 320px artboard child | `width: 100%; max-width: 320px` | Skill: artboard width becomes a max, not a fixed width. |
| Font weights (500 label, 400 body, 600 headings) | literal values | Literal values | No weight tokens exist. |
| Line heights | 20/24px | Unitless 1.429 and 1.5 | Matches the handoff rule: unitless line-height. |
| Demo static focus | Focus frame | `.is-focus` class on the demo input | The static specimen has no real focus. Real focus uses `:focus-visible`. The class exists only for the demo; remove it if the page is not a showcase. |

## Structure and states

- Built: Default, Focus, Error, Disabled, each mapped to a real selector: `:focus-visible` (plus `.is-focus` for the demo), `[aria-invalid="true"]`, `:disabled`.
- Error message: the design's message row (icon + text) replaces the hint in the Error state, as drawn.
- Not in the design and not built: hover, loading, read-only. No input styles exist in `src/components.css` to reuse for these, so they are left for a later pass. The focused-error ring is the one state added beyond the design (see Decisions).

## Open questions for the designer

1. **Alert icon geometry.** The design's icon is an instance "Icon / Alert" (16x16) containing a single VECTOR 10x6 with a 2px red stroke at (3,5). The export has no path data, so the exact shape is unknown. The demo uses a placeholder chevron (`M3 6 L8 11 L13 6`). Please send the SVG export of the alert icon, and check whether a shared alert icon exists in the design system.
2. **Focused error state.** Is the focus ring red when the field is invalid, or stays blue? The CSS uses red. This is a decision, not from the design.
3. **Vertical padding.** Confirm that 44px fixed height with centred text (10px padding dropped) matches the intent, versus a 46px total with the border.
4. **Gap values.** Should 6px become a token (add `--space-1-5`), or should the design use 4px or 8px?
5. **Real content.** Is the input type always `email` here, or should the component take a generic type?

## Not verified

- Not rendered in a browser; no pixel comparison. Values were checked against the script output, not visually.
- Fonts: `Inter` is named in tokens but not loaded anywhere; fallback fonts are what the demo shows.
- The `:has()` selector for the disabled label needs a modern browser; older browsers keep the default label colour.
- Real validation behaviour (when the error shows) is not built; the demo only shows the static state.
- Dark mode: no dark tokens exist in `src/tokens.css`, so none were built.
