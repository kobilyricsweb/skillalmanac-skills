# Scripted widget patterns: what must be true

Read only the section for the widget in front of you. Each section lists the native option first, then the minimum contract for a custom build. A widget that misses a line in its contract has a defect, usually under 4.1.2 (name, role, value) or 2.1.1 (keyboard).

## Contents

- Modal dialog
- Disclosure and accordion
- Menu button and dropdown
- Tabs
- Combobox, autocomplete and custom select
- Tooltip
- Status messages and toasts
- Carousel
- Toggle and switch
- Sortable or drag list
- Sources

## Modal dialog

Native: `dialog` opened with `showModal()` gives focus containment, Escape and an inert background for free.

Custom contract:
- Container has `role="dialog"` (or `alertdialog`), `aria-modal="true"`, and a name from `aria-labelledby` pointing at its heading.
- On open, focus moves into the dialog: to the first meaningful control, or to the heading with `tabindex="-1"` when the content must be read first.
- Tab and Shift+Tab cycle inside. Content behind is `inert` (or `aria-hidden` with nothing focusable in it).
- Escape closes. So does a visible close button with a name.
- On close, focus returns to the control that opened it; if that control is gone, to a logical neighbour.
- Background scroll is locked without removing zoom.

## Disclosure and accordion

Native: `details` and `summary`.

Custom contract:
- The trigger is a `button` with `aria-expanded="true|false"` and, when useful, `aria-controls`.
- The panel is hidden with `hidden` or `display: none` when collapsed, not only with height 0 or opacity 0 (otherwise its links stay in the tab order).
- In an accordion, each trigger sits inside a heading of the right level.

## Menu button and dropdown

Decide first: a list of links for navigation is a disclosure (above), not a menu. Use menu roles only for application-style commands.

Menu contract:
- Trigger: `button` with `aria-haspopup="menu"` (or `true`) and `aria-expanded`.
- Popup: `role="menu"`; items `role="menuitem"`, `menuitemcheckbox` or `menuitemradio`.
- Keys: Enter, Space or Down opens and focuses the first item; Up and Down move; Home and End jump; Escape closes and returns focus to the trigger; Tab closes.
- Only one item is in the tab order at a time (roving `tabindex`), or focus stays on the menu with `aria-activedescendant`.

## Tabs

Contract:
- Container `role="tablist"` with a label; each tab `role="tab"`, `aria-selected`, `aria-controls`; each panel `role="tabpanel"` with `aria-labelledby`.
- Only the selected tab has `tabindex="0"`; the rest `-1`. Left and Right move between tabs; Home and End jump.
- Tab key moves from the selected tab into its panel. A panel with no focusable content gets `tabindex="0"`.
- Hidden panels use `hidden`.

If the "tabs" load new pages, they are navigation links with `aria-current="page"`, not tabs.

## Combobox, autocomplete and custom select

Native: `select`, or `input` with `datalist`. Prefer them unless the design cannot work with them.

Custom contract:
- The input has `role="combobox"`, `aria-expanded`, `aria-controls` pointing at the popup, and `aria-autocomplete` (`list` or `both`).
- The popup is `role="listbox"`; options are `role="option"` with `aria-selected`.
- DOM focus stays on the input; the active option is referenced by `aria-activedescendant` and scrolled into view.
- Keys: Down opens and moves, Up moves, Enter selects, Escape closes (a second Escape clears).
- The number of results is announced through a polite live region.
- A visible label is tied to the input.

A `div` that opens a list on click with no roles and no key handling fails 2.1.1 and 4.1.2: recommend the native element.

## Tooltip

- Appears on both hover and keyboard focus; the trigger is focusable.
- The tooltip has `role="tooltip"` and the trigger points at it with `aria-describedby` (or `aria-labelledby` when the tooltip is the only name).
- Escape dismisses it without moving focus; the pointer can move onto it; it stays until hover or focus leaves (1.4.13).
- Never put interactive content in a tooltip; use a disclosure or dialog.

## Status messages and toasts

- Messages that do not take focus (saved, 3 results, added to cart, form error summary) sit in a live region that exists in the DOM before the text is inserted: `role="status"` (polite) or `role="alert"` (assertive, errors only). (4.1.3)
- A toast with an action needs enough time, or must persist until dismissed (2.2.1), and its action must be reachable by keyboard.
- Loading states: `aria-busy="true"` on the region, or a status message.

## Carousel

- A visible pause or stop control when it rotates on its own, placed before the slides in DOM order; rotation also stops on focus and hover. (2.2.2)
- Previous and next are `button` elements with names; slide pickers are named ("Slide 2 of 5") and at least 24 by 24 CSS px. (4.1.2, 2.5.8)
- Slides that are not visible are hidden from the tab order and from assistive technology.
- Swipe is not the only way to move. (2.5.1, 2.5.7)

## Toggle and switch

- A two-state button: `button` with `aria-pressed`. A setting that applies at once: `role="switch"` with `aria-checked`, or a native checkbox styled as a switch.
- The label does not change with the state (not "Mute" then "Unmute" with `aria-pressed`): either change the label or expose the state, never both.
- State is not shown by colour alone.

## Sortable or drag list

- Every drag action has a single-pointer alternative with no dragging: move up and move down buttons, or a "move to" menu. (2.5.7)
- The same alternative works from the keyboard. (2.1.1)
- After a move, the new position is announced through a live region ("Item moved to position 2 of 5").

## Sources

- W3C, ARIA Authoring Practices Guide, patterns: https://www.w3.org/WAI/ARIA/apg/patterns/
- W3C, WAI-ARIA 1.2: https://www.w3.org/TR/wai-aria-1.2/
- WHATWG HTML, the dialog element and the inert attribute: https://html.spec.whatwg.org/multipage/interactive-elements.html
