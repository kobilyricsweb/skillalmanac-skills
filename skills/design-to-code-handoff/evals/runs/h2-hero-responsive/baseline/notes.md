# Hero section: notes

## Files
- `hero.html`: markup; loads `src/tokens.css`, `src/components.css`, `hero.css`.
- `hero.css`: all hero layout. Mobile-first, breakpoints at 640px and 960px.

## Decisions
- **Breakpoints.** Base (375 frame) is a single column with 20px gutters and 48px vertical padding. From 640px the buttons sit in a row and the media ratio widens to 16:9. From 960px the layout is two columns with 96px vertical padding.
- **Desktop columns.** The content is capped at 1200px (1440 minus 2 x 120px). Columns are `616fr / 520fr` with a 64px gap, which gives the 616px copy and 520px media at 1440 and keeps the same ratio at other widths. Above 1440 the content stays 1200px and centres, so the gutters grow.
- **Gutters.** Side padding is `clamp(32px, 8.333vw, 120px)` at 960px and up, which equals 120px at 1440.
- **Headline.** Fluid `clamp(36px, 13px + 2.98vw, 56px)`. It reaches 36px at 768px and below and 56px at 1440px. Line-height 1.18, letter-spacing -0.02em, weight 700.
- **Body.** 16px on phones and tablet, 18px from 960px, matching the two frames.
- **Eyebrow.** 14px, weight 600, uppercase, 0.04em tracking, accent colour.
- **Buttons.** Existing `.btn--lg .btn--primary` and `.btn--lg .btn--secondary` from `components.css`. Only width is set by the hero (full width on phones, auto from 640px). Button styling is not changed.
- **Colours.** Only semantic tokens are used: `--color-bg-page`, `--color-text`, `--color-text-muted`, `--color-accent`, `--color-accent-subtle`. I checked the export's hex values against the palette and they match.
- **Radius.** Media uses `--radius-xl` (16px).
- **Spacing.** Gaps use `--space-*` tokens (24, 32, 12, 16, 64, 96, 48 and 20 px).

## Deviations from the design tokens
- The 1200px content cap, 520px and 616px column widths, 13/10 and 16/9 and 7/5 media ratios, and 1.18 / 1.55 line-heights have no matching token. They are layout values, not colour or spacing values.
- The 120px gutter is written as `calc(var(--space-24) + var(--space-6))` so it still uses tokens.
- The 56px and 36px font sizes come from the `--font-size-5xl` and `--font-size-3xl` tokens.

## Discrepancies in the export (open questions)
1. **Desktop vertical alignment.** The frame sets `counterAxisAlignItems: CENTER`, but the Copy node is at y=96 (top). The 300px copy against the 400px media would centre at y=146. I followed the measured position (`align-items: start`). Confirm which is intended.
2. **Mobile heights.** The frame is 760px tall, but Copy (y 48, h 300) overlaps Actions (y 338 to 454). The Media node reports y=0. Its size is 335x240, and I set it below the copy in the flow. The frame's bottom padding and the copy/actions spacing are not reliable in the export, so the page height comes from the content (about 668px at 375).
3. **Gap inconsistencies.** Measured gaps do not match the declared `itemSpacing` values (desktop copy gaps read as 18px and 16px where 24px is declared; mobile copy-to-actions is about 28px). I used a uniform 24px copy gap.
4. **Image.** The media fill uses `imageRef: a1b2c3`, and the file is not in the export. The media box is a placeholder in `--color-accent-subtle` with `aria-hidden`. Need the asset, the crop focal point, and whether the image should have alt text.
5. **Button labels.** The "Book a demo" and "See pricing" hrefs (`#demo`, `#pricing`) are placeholders.
6. **Wider than 1440 and narrower than 375.** Not in the export. The design covers 1200px content centred above 1440 and 1-column down to 320px (the headline stays at 36px). Confirm the 320px case and the 768 to 959px stacked layout, which I inferred.
7. **Font.** Inter is declared in the export and in `--font-sans`, but no font file or `@font-face` is provided. The page relies on the system fallback unless Inter is loaded.

## Not verified
- Not rendered in a browser. The layout was written from the export geometry and tokens and has not been checked at 375, 768, 960, 1440 or 1920 px.
