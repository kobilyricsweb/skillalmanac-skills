# Plan card (Pro) implementation notes

Source: `design/plan-card.json`, root node 12:25 "Plan card / Pro" (360 x 423).
Files: `plan-card.html`, `plan-card.css`. Links `src/tokens.css`, `src/components.css`, then `plan-card.css`.

## Token mapping (design value -> token)

| Design property | Value | Token used |
|---|---|---|
| Card fill | #ffffff | `--color-surface` |
| Card stroke, divider | #d9d7d1 | `--color-border` |
| Card shadow (0 8 24, 8%) | rgba(28,27,25,0.08) | `--shadow-card` |
| Card radius | 12 | `--radius-lg` |
| Card padding | 32 | `--space-8` |
| Card item gap | 24 | `--space-6` |
| Badge fill | #e6f0fb | `--color-accent-subtle` |
| Badge label, check icons | #0b5cad | `--color-accent` |
| Badge radius, padding | pill, 4 / 12 | `--radius-pill`, `--space-1` / `--space-3` |
| Plan name, price, feature text | #1c1b19 | `--color-text` |
| Period text | #5c5a56 | `--color-text-muted` |
| CTA fill / label | #0b5cad / #ffffff | `.btn--primary` (existing component) |
| CTA size (296 x 52, 14/24 padding, 16px 600) | Large | `.btn--lg .btn--block` (existing component) |
| Feature row gap | 12 | `--space-3` |
| Price to period gap | 4 | `--space-1` |
| Font size 12 / 16 / 20 / 48 | | `--font-size-xs` / `-md` / `-xl` / `-4xl` |

## Values with no token (literal, flagged for the designer)

- Header gap between plan name and price row is 6px. The spacing scale has 4 and 8 and no 6, so it is a literal `6px`.
- Line heights (16, 24, 28, 56px) and letter-spacing (0.04em badge, -0.02em price) are literal. The token file has no line-height or tracking tokens. The price letter-spacing -0.96px equals -0.02em at 48px, and the badge 0.48px equals 0.04em at 12px.
- Font weights 400, 600, 700 are literal (the token file has no weight tokens; `.btn` sets 600 itself).
- Feature text is 16px, so it uses `--font-size-md`. Plan name is 20px (`--font-size-xl`).

## Decisions and deviations

- **Hidden "Old price" ($39, strikethrough) is omitted.** The node has `visible: false`. If the design later shows it, add a `<s class="plan-card__old-price">` next to the price with `--color-text-placeholder`, which matches its #72706b fill.
- **Period colour uses `--color-text-muted`** (#5c5a56). The design fill is #5d5b57, which is visually the same. The old price fill (#72706b) equals `--color-text-placeholder`, but that token is only used as a placeholder colour in this design system.
- **No `--color-accent` text token exists for the badge label.** The badge uses `--color-accent` directly, which is the same value as the design.
- **Card width.** The design is 360px wide. The card is `max-width: 360px; width: 100%` so it fits phones. Below 400px the outer page and card padding drop to 16px and 24px. The 24px card padding at phone width is a judgement call and is not in the design. Remove the media query if the designer wants the fixed 32px padding at all widths.
- **Check icon path is reconstructed.** The JSON `Vector` node (14 x 10, 2px stroke, accent) has no path geometry, only bounds. The inline SVG path `M3 10 L7.5 14.5 L17 5` in a 20 x 20 `.icon` viewBox approximates that box. The designer should confirm the check shape against the component `9:1` in the design file.
- **Button is a `<button>`.** The design does not say whether it is a link or a button. It uses `<button type="button">` because no URL is given. Change it to `<a>` with the same classes if it navigates to checkout.
- **Font.** `tokens.css` names Inter but no Google Fonts link exists in the project files, so the page falls back to `system-ui` unless the host page loads Inter. The design uses Inter 400/600/700.
- **Export data quirk.** The `Feature row` frames have absolute y positions (300, 336, 372) that do not match the parent `Features` frame (y 319). The spacing between rows (36px per 24px row, 12px gap) is consistent, so the CSS uses the gap rule, not the absolute positions.
- The Figma-style `Badge` and `Header` frames have no fills or strokes beyond those listed, so no extra surfaces were added.

## Not verified

- No browser render or pixel comparison was done against the design export. Visual match is by token mapping and measured spacing from the JSON bounds.
