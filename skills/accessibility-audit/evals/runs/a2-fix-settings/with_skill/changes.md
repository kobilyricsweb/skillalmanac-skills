# Changes: settings.html to settings.fixed.html

Standard: WCAG 2.2 level AA. Method: static checker (run, before and after) and manual source review. Not a conformance claim.

## Checker result

- Before (settings.html): 9 FAIL, 1 WARN
- After (settings.fixed.html): 0 FAIL, 1 WARN
- The remaining WARN (1.3.5 autocomplete on `#confirm-name`) is dropped: the field asks for a workspace name, which is not the user's personal data, so no autocomplete token applies.

## Changes

| # | Where | SC (level) | Problem | Change |
|---|---|---|---|---|
| 1 | Email summary switch | 2.1.1 (A), 4.1.2 (A) | `div onclick` could not be reached or operated by keyboard; screen readers heard nothing | Now `<button type="button" role="switch" aria-checked="true" aria-labelledby="weekly-label">`. The label span has an id. `toggleSwitch()` updates `aria-checked` on every toggle. Visual size and colours unchanged; button border and padding reset. |
| 2 | Theme control | 2.1.1 (A), 4.1.2 (A), 1.3.1 (A) | Custom div list with click handlers; no roles, no keys, no name | Replaced with a native `<select id="theme-select">` with System, Light, Dark options and a `<label for>`. `onchange` shows the same "Theme set to X" toast. Same box width (200px), border, radius and padding. Native arrow now shown (affordance for sighted users). |
| 3 | "Delete this workspace" | 2.1.1 (A), 4.1.2 (A) | `span onclick` not focusable | Now a `<button type="button" class="link">`, styled to look the same (underlined blue text, no button chrome). |
| 4 | Delete dialog container | 4.1.2 (A), 2.4.3 (A) | Plain div; no dialog role, name or modal state | `role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby="confirm-help"`. |
| 5 | Dialog heading | 1.3.1 (A) | Title was a styled div | `<h2 id="modal-title" class="modal-title">`. Font size, weight and margin kept (margin set to 0 top to match the old look). |
| 6 | Dialog focus | 2.4.3 (A), 2.1.2 (A) | Focus stayed on the opener or went nowhere; Tab could reach the page behind | On open, focus moves to the name input and `main` gets `inert`. Tab and Shift+Tab cycle inside the dialog. On close (Cancel, close button, Escape or successful delete), focus returns to the opener. |
| 7 | Escape key | 2.1.1 (A) | Dialog could only be closed with the mouse | Escape closes the dialog. |
| 8 | Close button | 4.1.2 (A), 2.5.8 (AA) | `span` with `&times;` and no name | `<button type="button" class="close" aria-label="Close">`, 32 by 32 px, glyph kept in the same corner position. |
| 9 | Name field label | 3.3.2 (A), 1.3.1 (A) | Placeholder was the only label; it vanished on typing | Visible `<label for="confirm-name">Workspace name</label>` above the field. Placeholder removed (it duplicated the label). Field margins adjusted for the label. |
| 10 | Confirmation text | 1.3.1 (A) | Instruction text not tied to the field | `aria-describedby="confirm-help confirm-error"` on the input. |
| 11 | Mismatch error | 3.3.1 (A), 3.3.3 (AA), 4.1.3 (AA), 1.4.1 (A) | Only a red border; no text, nothing announced | Text error in `#confirm-error` (role="alert", present in the DOM before use): "The name does not match. Type tallybird-hq to confirm." Input gets `aria-invalid="true"`. Focus stays in the input. The error clears on close. Red border kept. |
| 12 | Focus indicator | 2.4.7 (AA), 1.4.11 (AA) | `*:focus { outline: 0 }` removed all focus rings | Replaced with `:focus-visible { outline: 2px solid #1558d6; outline-offset: 2px }`. Blue on white and on the page background is well above 3:1. |
| 13 | Toast announcements | 4.1.3 (AA) | Toasts appended to body with no live region | Toasts go into `#toasts` with `role="status" aria-live="polite"`, which exists before any toast is added. Same text, timing and look. |
| 14 | Buttons | 4.1.2 (A) | Dialog buttons and inline controls had no type | Added `type="button"` where a button is not a submit. Visual unchanged. |

Unchanged: colours, layout, sizes, copy, toast messages and timing, the Delete flow (name must equal tallybird-hq), the save behaviour of the switch, and the page structure (one h1, card h2s, main landmark). The inline onclick handlers were kept.

## Visible look changes (small, for the owner to accept or reject)

- The Theme control is a native select with a native arrow, not the old custom list.
- The dialog now has a visible "Workspace name" label above the input.
- The close button's hit area is 32 by 32 px. The glyph sits in the same corner.
- Focus rings are now visible (blue outline) when using the keyboard. They were hidden before.

## Not tested

- Real screen readers (NVDA, JAWS, VoiceOver, TalkBack) and their announcements of the switch state, the select, the dialog and the toast.
- Real keyboard run in a browser: Tab order, Escape, focus return, and the Tab trap in the dialog. These were written from source and not run.
- Focus indicator visibility over the danger button and at narrow widths.
- Contrast of the #b9b9b4 switch track against white (1.4.11, the off state of a control). The static checker does not measure it. The off track is roughly 1.9:1 against the white card. This was not fixed. Consider a darker off colour if the owner wants 3:1.
- Reflow at 320 CSS px and 200% text size (the dialog max-width is 420px, so it should reflow, but this was not rendered).
- Not rendered in a browser at all; only the static checker and source reading were used.
