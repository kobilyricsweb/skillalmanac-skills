# Hero section: implementation notes

Files: `hero.html` (markup), `hero.css` (styles). Shared CSS is loaded from `src/tokens.css` and `src/components.css`, not copied.

Source: `design/hero.json`, frames `Hero / Desktop` (1440x592) and `Hero / Mobile` (375x760). Script run: `node_to_css.py --tokens src/tokens.css`, plus `--diff` between the two frames.

## Structure and reuse

- Section `.hero` with an `h1` headline, `p` eyebrow and body, and an actions group. The two actions are `<a>` links (`#demo`, `#pricing` are placeholders), because "Book a demo" and "See pricing" navigate.
- Buttons reuse `components.css`: `.btn .btn--lg .btn--primary` and `.btn .btn--lg .btn--secondary`, plus `.btn--block` for the mobile full-width stack. The design's Button instances (Primary/Secondary, Large) match `.btn--lg`: 14px/24px padding, 16px/600/1.5 label, 8px radius, 1px control border on secondary. No button styles were written locally.
- Wrapper layers from the export (`Copy`, `Actions`) are kept only where layout needs them.
- Colours and sizes use tokens only. Raw values are limited to the layout values listed under decisions.

## Decisions

1. **Off-token padding 14px (buttons).** Kept as in `.btn--lg` (component value, same as spec). Nearest tokens are 12px and 16px. Removing 14px would change the button height from 52px, so it is a fixed size that depends on it.
2. **Off-token padding 120px (desktop side inset).** Not a token. Implemented as `padding-inline: max(48px, calc((100% - 1200px) / 2))`. At 1440 this gives exactly 120px (content 1200px, matching the design). Below 1440 it shrinks to 48px; above 1440 the content stays 1200px and centres, with the background full width. This follows the artboard-to-max-width rule.
3. **Desktop vertical padding 96px** = `--space-24`, exact token.
4. **Button box model.** `box-sizing: border-box` on `.hero .btn`, so the 1px border sits inside the 52px height as in Figma (strokes inside by default).
5. **Breakpoints.** Mobile-first, base = 375 frame. Chosen where the layout stops fitting, not at the artboard widths:
   - `>= 640px` tablet: stacked still, larger type, buttons in a row (no full-width buttons), media max 520px wide at 13:10.
   - `>= 1120px` two columns. Below this the 520px media plus a readable headline column does not fit. Headline 48px here, inset 48px.
   - `>= 1280px` headline 56px (design desktop size). Headline sizes: 36 (mobile), 48 (640-1279), 56 (1280+).
6. **Media height.** Export has fixed sizes (520x400, 335x240). Built as `aspect-ratio` (13/10 desktop/tablet, 335/240 mobile) with width that flexes. Height is not fixed, so it scales between frames.
7. **Off-token mobile copy gap / type.** Mobile values are exact tokens: 16px copy gap, 12px action gap, 32px section gap, 48px / 20px padding.
8. **Image fill.** The media is a FILL image frame, but the export has no image asset. Built as an empty `aria-hidden` box with `--color-accent-subtle` background and 16px radius (`--radius-xl`). Replace with a real `<img>` (`object-fit: cover`) once the asset is exported.
9. **Eyebrow and case.** Source text stays in sentence case; `text-transform: uppercase` applied in CSS (from the text style).
10. **Tablet values not drawn.** At 640-1119 the design gives no frame. Used desktop body type (18/28), desktop eyebrow and copy gap (24px), tablet headline 48px with 1.167 line-height (56px), and desktop-equivalent padding `64px 32px`. Not verified against the designer.
11. **`body` rule.** Set `margin: 0` and background in `hero.css` so the file renders as a standalone page. Remove if the page shell already does this.

## Fidelity check (spec = export value, code = value in CSS at the matching frame)

| layer | property | spec | code | match |
|---|---|---|---|---|
| Hero / Desktop | padding | 96px 120px | 96px / 120px at 1440 | yes (120px via calc) |
| Hero / Desktop | gap | 64px | `--space-16` | yes |
| Hero / Desktop | background | neutral-50 | `--color-bg-page` | yes |
| Copy | gap | 24px | `--space-6` | yes |
| Copy | width | 616px | 1200 content minus 520 media minus 64 gap = 616 at 1440 | yes |
| Eyebrow | size / lh / ls | 14 / 20 / 0.04em | `--font-size-sm` / 1.429 / 0.04em | yes |
| Headline (desktop) | size / lh / ls / weight | 56 / 64 / -0.02em / 700 | `--font-size-5xl` / 1.143 / -0.02em / 700 | yes |
| Body (desktop) | size / lh / colour | 18 / 28 / neutral-600 | `--font-size-lg` / 1.556 / `--color-text-muted` | yes |
| Actions (desktop) | gap | 16px | `--space-4` | yes |
| Button | height / radius | 52px / 8px | 14+24+14 (+1px border, border-box) / `--radius-md` | yes |
| Button primary | colour | accent / on-accent | `--color-accent` / `--color-text-on-accent` | yes |
| Button secondary | border / colour | 1px neutral-500 / neutral-900 | 1px `--color-border-control` / `--color-text` | yes |
| Media (desktop) | size / radius | 520x400 / 16px | 520 wide, 13:10 (400 tall at 520) / `--radius-xl` | yes at 1440 |
| Hero / Mobile | padding | 48px 20px | `--space-12` / `--space-5` | yes |
| Hero / Mobile | gap | 32px | `--space-8` | yes |
| Copy (mobile) | gap | 16px | `--space-4` | yes |
| Headline (mobile) | size / lh / weight | 36 / 44 / 700 | `--font-size-3xl` / 1.222 / 700 | yes |
| Body (mobile) | size / lh | 16 / 24 | `--font-size-md` / 1.5 | yes |
| Actions (mobile) | gap / layout | 12px, column, full width | `--space-3`, column, `.btn--block` | yes |
| Media (mobile) | size / radius | 335x240 / 16px | 335:240 ratio / `--radius-xl` | yes at 375 |

## States and breakpoints not in the design

- Hover, focus-visible, active, disabled for the two buttons: reused from `components.css` (`:hover`, `:focus-visible` outline, `:disabled`). Not drawn in the export.
- Breakpoints 640px, 1120px, 1280px and the layout between 375 and 1440 (including the 1280 headline step) are not in the export; they are decisions above.
- Behaviour beyond 1440: content capped at 1200px, centred; background full width.
- Empty/loading/error states: not applicable to a static hero.

## Open questions for the designer

1. Hero image: which asset, and should it be a real `<img>` with `object-fit: cover` on mobile? Current build uses an empty placeholder.
2. Tablet (640-1119) layout and type: none drawn. Confirm stacked with row buttons, or two columns earlier?
3. Desktop headline at 1120-1279 (48px) and mobile-to-tablet headline step: confirm.
4. Are "Book a demo" and "See pricing" links or buttons that open a dialog? Current markup uses links.
5. Does the 14px button padding stay (matches the component), or should buttons move to 12px/16px?

## Not verified

- No browser render, so no visual or pixel comparison, at any width.
- Fonts: `Inter` is in the token stack but not loaded here; the page uses the fallback font until the project loads it.
- Real content length: sample copy only. Headline and body wrapping at other lengths and translations is not tested.
- Focus order and keyboard behaviour of the links were not tested.
- The breakpoint choices (640 / 1120 / 1280) were worked out from the frame sizes and column arithmetic, not checked in a browser.
