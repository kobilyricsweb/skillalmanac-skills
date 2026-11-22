# Manual checks, in audit order

Each line is a question to answer from the source. The numbers are WCAG 2.2 success criteria; A and AA are in scope by default.

## Contents

1. Keyboard
2. Focus
3. Forms and errors
4. Structure and meaning
5. Colour and contrast beyond text
6. Media, motion and timing
7. Zoom, reflow and spacing
8. Criteria added in WCAG 2.2
9. Sources

## 1. Keyboard

- Is every click handler on a natively focusable element, or on one with a role, `tabindex="0"` and Enter/Space handling? (2.1.1 A)
- Do handlers fire on `click` (which keyboards trigger on buttons and links) rather than only on `mousedown`, `mouseover` or `touchstart`? (2.1.1 A)
- Can focus leave every component (date pickers, embedded editors, modals after closing)? (2.1.2 A)
- Does DOM order match visual order? Look for `order`, `flex-direction: row-reverse`, `float: right`, absolute positioning and positive `tabindex`. (2.4.3 A, 1.3.2 A)
- Is there a way past repeated blocks: a skip link, or landmarks with one `main`? (2.4.1 A)
- Are single-key shortcuts (a letter with no modifier) remappable or active only on focus? (2.1.4 A)

## 2. Focus

- Does any rule remove `outline` without a visible replacement? Is the replacement at least 3:1 against what surrounds it? (2.4.7 AA, 1.4.11 AA)
- Can a sticky header, cookie bar or chat bubble completely cover the focused element? Look for `position: sticky/fixed` without `scroll-padding`. (2.4.11 AA)
- When content is inserted or removed (dialog, inline editor, deleted row), where does focus go? It must not fall back to the top of the page. (2.4.3 A)
- Does focus or a value change alone trigger navigation, submission or a new window? (3.2.1 A, 3.2.2 A)

## 3. Forms and errors

- Does every field have a visible label that stays visible while typing? (3.3.2 A, 1.3.1 A)
- Are related controls grouped with `fieldset`/`legend` or `role="group"` plus a label? (1.3.1 A)
- Is required state exposed (`required` or `aria-required`) and explained in text, not only by an asterisk colour? (3.3.2 A, 1.4.1 A)
- Do fields that collect the user's own data carry the right `autocomplete` token (`email`, `tel`, `given-name`, `street-address`, `new-password`, `one-time-code`)? (1.3.5 AA)
- On error: is the field marked `aria-invalid`, is the message text tied by `aria-describedby`, does it say what is wrong and how to fix it, and is it announced (focus moved to the first invalid field, or a live region)? (3.3.1 A, 3.3.3 AA, 4.1.3 AA)
- For legal, financial or data-deleting submissions: can the user review, confirm or undo? (3.3.4 AA)
- Is the visible label text contained in the accessible name (no `aria-label="Submit form"` on a button that reads "Send")? (2.5.3 A)

## 4. Structure and meaning

- One `h1`; heading levels describe the outline, not the font size. (1.3.1 A, 2.4.6 AA)
- Lists are `ul`/`ol`; data tables have `th` with `scope` and a caption; layout tables have `role="presentation"`. (1.3.1 A)
- Do instructions rely on shape, position or colour alone ("the red fields", "the button on the right")? (1.3.3 A, 1.4.1 A)
- Can each link's purpose be told from its text, or its text plus its sentence or list item? (2.4.4 A)
- Do images of text exist where real text would do? Do informative images have alt text that carries the same information; do images inside links describe the destination? (1.4.5 AA, 1.1.1 A)
- Are passages in another language marked with `lang`? (3.1.2 AA)
- Are navigation and repeated components in the same order and named the same across pages? (3.2.3 AA, 3.2.4 AA)

## 5. Colour and contrast beyond text

- Input borders, checkbox outlines, toggle tracks, icons that are the only label, chart marks, focus rings: 3:1 against the adjacent colour. (1.4.11 AA)
- Text over images or gradients: measure against the lightest and darkest area behind it; a scrim or solid backing is the usual fix. (1.4.3 AA)
- Links inside text: distinguishable without colour (underline), or 3:1 against the surrounding text plus a non-colour cue on hover and focus. (1.4.1 A)
- Status shown by colour (red/green badges, error borders) also needs text or an icon with a name. (1.4.1 A)
- Content that appears on hover or focus (tooltips, menus) must be dismissable with Escape, hoverable, and persistent. (1.4.13 AA)

## 6. Media, motion and timing

- Prerecorded video with speech: captions; audio-only: transcript; video with visual-only information: audio description or text alternative. (1.2.1 to 1.2.5)
- Sound that starts on load and lasts over 3 seconds needs a stop or mute control. (1.4.2 A)
- Anything that moves, blinks, scrolls or auto-updates for over 5 seconds beside other content needs pause, stop or hide: carousels, tickers, animated backgrounds. (2.2.2 A)
- Nothing flashes more than three times a second. (2.3.1 A)
- Session timeouts warn the user and allow an extension. (2.2.1 A)
- Motion triggered by scrolling or interaction respects `prefers-reduced-motion` (2.3.3 is AAA; report as advisory).

## 7. Zoom, reflow and spacing

- No `user-scalable=no`, no `maximum-scale` under 2. (1.4.4 AA)
- At 320 CSS px wide, is there horizontal scrolling for anything other than data tables, maps, diagrams or toolbars? Look for fixed pixel widths, `min-width`, `white-space: nowrap`, wide grids without wrapping. (1.4.10 AA)
- Do containers with fixed `height` or `overflow: hidden` clip text when line height is 1.5, paragraph spacing 2 times the font size, letter spacing 0.12 and word spacing 0.16? (1.4.12 AA)
- Is orientation locked? (1.3.4 AA)

## 8. Criteria added in WCAG 2.2

| SC | Level | What to look for |
|---|---|---|
| 2.4.11 Focus Not Obscured (Minimum) | AA | A focused control fully hidden by author content (sticky bars, banners, open panels) |
| 2.5.7 Dragging Movements | AA | Drag to reorder, sliders, drag-and-drop uploads, map panning with no click or tap alternative |
| 2.5.8 Target Size (Minimum) | AA | Controls under 24 by 24 CSS px without spacing: icon buttons, close crosses, pagination dots, table row actions |
| 3.2.6 Consistent Help | A | Help links, chat or contact details that change position between pages |
| 3.3.7 Redundant Entry | A | Asking again for information already given in the same process (shipping then billing) without auto-fill or selection |
| 3.3.8 Accessible Authentication (Minimum) | AA | Login that needs memory or a puzzle with no alternative: blocked paste, no password-manager support, image CAPTCHA only |

4.1.1 Parsing is obsolete and removed in 2.2; never report it.

## 9. Sources

- W3C, Web Content Accessibility Guidelines (WCAG) 2.2: https://www.w3.org/TR/WCAG22/
- W3C, Understanding WCAG 2.2: https://www.w3.org/WAI/WCAG22/Understanding/
- W3C, ARIA in HTML: https://www.w3.org/TR/html-aria/
