# settings.html accessibility changes

Output: `settings.fixed.html` (original `settings.html` left untouched). Layout, colors (except one), copy, and behaviour are kept.

## Focus and keyboard
- Removed `*:focus { outline: 0; }`, which hid focus on every control. Replaced with a `:focus-visible` outline (3px blue, 2px offset).
- Toggle switch, theme dropdown trigger, delete link and modal close button are now real `<button>` elements, so they are reachable with Tab and activate with Enter/Space.
- Theme dropdown: ArrowDown/ArrowUp open it and move between options, Home/End jump to first/last, Enter/Space choose an option, Escape closes and returns focus to the trigger, Tab closes it.
- Delete dialog: focus moves into the dialog on open (the name field) and returns to the delete link on close. Tab and Shift+Tab are trapped inside the dialog. Escape closes it.
- While the dialog is open, the page behind it is set `inert`, so screen readers and keyboard users cannot reach it.

## Semantics and screen reader support
- Toggle: `<div>` became `<button role="switch">` with `aria-checked`, labelled by "Email me a weekly summary". `aria-checked` is updated on each toggle.
- Theme dropdown: trigger has `aria-haspopup="listbox"`, `aria-expanded` (updated on open/close) and `aria-controls`, and is labelled "Theme" plus its current value. The list is `role="listbox"`, options are `role="option"` with `aria-selected` kept in sync with the chosen value.
- Delete link: `<span onclick>` became `<button type="button" aria-haspopup="dialog">`. Button styling keeps the link look (same color, underline, font).
- Dialog: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to the title. Title changed from `<div>` to `<h2>` (same size/weight; margin reset to match the old div).
- Close button: `<span>&times;</span>` became a `<button aria-label="Close">` with the ×  marked `aria-hidden`.
- Name input: now has an associated `<label for="confirm-name">` (the instruction text).
- Mismatch on delete: input gets `aria-invalid="true"` and an `aria-describedby` message (visually hidden) explaining the mismatch, announced assertively. The red border is kept as before.
- Toast: the visual toast is `aria-hidden`; its text is also written to a persistent `role="status"` live region so it is announced. The live region is cleared and refilled so repeated messages announce again.
- Dialog buttons are `type="button"` so they never submit an enclosing form.

## Visual changes (kept minimal)
- Toggle "off" track color changed from `#b9b9b4` to `#8a8a85` so the switch boundary reaches at least 3:1 contrast against the white card (WCAG 1.4.11). The "on" state is unchanged.
- Dropdown trigger now sets `font: inherit`, `color`, `text-align: left`, `box-sizing: border-box` and `width: 100%` so the button renders exactly like the old div.
- Added a `.sr-only` utility class (no visible change).
- Added `prefers-reduced-motion` rule that disables the switch knob transition.

## Not changed
- Copy, layout, spacing, toast timing and the delete-confirmation logic are unchanged.
- Clicking outside the dropdown does not close it, same as before.
