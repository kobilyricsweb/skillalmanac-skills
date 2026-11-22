# Plan card / Pro: handoff notes

Files: `plan-card.html`, `plan-card.css`. Source: `design/plan-card.json` (frame "Plan card / Pro", 360x423, node 12:25). Tokens: `src/tokens.css`. Shared components: `src/components.css`.

## Reused

- Tokens: colours, spacing, radii, shadow, type sizes and font family all written as `var(--...)`.
- `.btn .btn--primary .btn--lg .btn--block` for the CTA. `.btn--lg` already is `padding: 14px var(--space-6)`, so the design's 14px vertical padding matches the shared component exactly. No local restyling of the button.
- `.icon` for the check icons (20x20, flex-shrink 0).

## Deviations and decisions

| Item | Spec | Built | Why |
|---|---|---|---|
| Header gap | 6px | 6px (raw) | Off-token. Nearest tokens are 4px and 8px, equally far away, so snapping is a visible change. Kept the spec value. Consider adding a `--space-1h` or accepting 8px. |
| Period colour | #5d5b57 | `var(--color-text-muted)` (#5c5a56) | Off-token by 1 to 4 per channel. Nothing depends on the exact value, so the semantic token is used. |
| Top-level width | 360px artboard | `max-width: 360px; width: 100%` | Artboard is not a width. Card shrinks on narrow screens. |
| Check icon path | Vector 14x10 at (3,5) in 20x20, stroke 2, #0b5cad | Approximate path `M4 10 L8 14 L16 6`, stroke `currentColor`, colour from `--color-accent` | The export has no path geometry for the vector (no vectorPaths/fillGeometry), so the shape is inferred from its bounding box. Needs the real SVG from the designer. Round caps and joins are assumed. |
| Hidden layer "Old price" | `visible: false` under Header > Price row | Not built | Hidden in export. |
| Badge label case | Text style gives uppercase | Source text "Most popular", `text-transform: uppercase` in CSS | Per skill rule. Badge and label merged into one element (`.badge`) since the badge has no other content. |
| Page scaffold | not in design | body padding and background on `plan-card.html` | Only for previewing the card. Not part of the component. |

## Element choices

- Card: `article`. Plan name: `h2` (level assumed; adjust to the page outline). Price: spans inside a `p`.
- Divider: `hr` with `border: 0` and a 1px background, so it keeps the design colour.
- Features: `ul` with `list-style: none`, one `li` per row. The check SVG is `aria-hidden`.
- CTA: `button type="button"`. If it navigates to a trial sign-up, change it to `a` and keep the same classes.

## States and breakpoints

Not in the design (not built as variants):
- Hover, focus-visible, active and disabled on the CTA. The shared `.btn` styles apply: hover and focus-visible come from `components.css`. Disabled is also covered there.
- Card hover or selected state.
- Narrower and wider layouts: only one frame exists, so the card is fluid up to 360px. Narrow widths were not specified.
- Empty, loading or error states: none.

## Open questions for the designer

1. Real check-icon SVG path (the export has no geometry). Please provide the SVG for the "Icon / Check" component.
2. Header gap: 6px is off the spacing scale. Should it be 4px, 8px, or stay 6px?
3. Is the "Old price" layer meant to be shown in some state (e.g., a discount)? It is hidden in this export, so it is not built.
4. Should the card be a `button`-based selectable option or static? This affects the markup.

## Not verified

- Not rendered in a browser. No visual or pixel comparison against the design.
- Fonts: `Inter` is named in the tokens but not loaded anywhere in this work folder, so the fallback stack is what renders.
- Real content: lengths of plan names, prices, and feature text were not tested with longer strings or translations.
- Fidelity was checked value by value against the script output (padding 32px, gap 24px, radius 12px, border 1px, shadow, 20px / 48px / 16px / 12px type, line heights and letter-spacing), not visually.
