# Accessibility audit: product.html (WCAG 2.2 Level AA)

File audited: `<local-path>` (121 lines, unmodified).

Method: manual source review of the markup, inline CSS and inline JavaScript. Contrast ratios were computed from the hex values with the WCAG relative-luminance formula. The page was not rendered and not tested with assistive technology, so the items marked "verify" need a browser or screen-reader check.

Severity: Critical = blocks a user group completely; High = fails an AA criterion with real user impact; Medium = fails an AA criterion with limited impact, or a likely failure; Low = advisory or hygiene that supports conformance.

## Summary

| # | Severity | Lines | Issue | WCAG 2.2 SC |
|---|---|---|---|---|
| 1 | Critical | 46-47, 50 | Carousel arrows and dots are non-focusable `<span>`s with click handlers only | 2.1.1, 4.1.2 |
| 2 | Critical | 68, 70 | Quantity +/- buttons have no accessible name | 4.1.2, 2.5.3 |
| 3 | Critical | 60-62 | Colour swatches are non-focusable `<div>`s with no name or state | 2.1.1, 4.1.2 |
| 4 | Critical | 73-74 | Shipping tooltip is mouse-only and not reachable by keyboard | 2.1.1, 1.4.13 |
| 5 | High | 88-92, 113-118 | Wishlist reorder works only by drag-and-drop, with no keyboard or single-pointer alternative | 2.1.1, 2.5.7 |
| 6 | High | 109 | Carousel auto-advances every 3 s with no pause, stop or hide control | 2.2.2 |
| 7 | High | 77 | Looping autoplay video with no controls, no captions track, and possibly audible | 2.2.2, 1.2.2, 1.4.2, 1.2.5 (verify) |
| 8 | High | 9 | Global `*:focus { outline: 0; }` removes all focus indicators | 2.4.7 |
| 9 | High | 43-45, 54 | Page content is not built on headings (no h1; product title and section titles are `<div>`s) | 1.3.1, 2.4.6 |
| 10 | High | 80-84 | Size table has no header cells, no caption | 1.3.1 |
| 11 | High | 85 | iframe has no `title` | 4.1.2 |
| 12 | High | 43-45, 77, 85, 640-960 px fixed widths | Fixed-width media and iframe overflow at 320 CSS px; carousel images are clipped | 1.4.10 |
| 13 | High | 21, 22, 27-28 | Colour contrast failures: SALE badge (2.11:1), old price (4.48:1), carousel dots (1.72:1) | 1.4.3, 1.4.11 |
| 14 | High | 43 | Image alt text is a filename | 1.1.1 |
| 15 | High | 56 | Rating image has empty alt although it conveys the rating | 1.1.1 |
| 16 | High | 54 | French passage has no `lang` attribute | 3.1.2 |
| 17 | High | 102, 112 | Cart count changes silently after "Add to cart" | 4.1.3 |
| 18 | Medium | 28-29, 68-70 | Quantity icon buttons are 20x20 px; carousel dots are 10x10 px with 16 px spacing | 2.5.8 |
| 19 | Medium | 40 | Breadcrumb is not a navigation landmark; no `<main>`, `<header>`, `<footer>` | 1.3.1 (also supports 2.4.1) |
| 20 | Medium | 55 | Price meaning is conveyed only by strike-through styling; no text for "was" and "now" | 1.3.1 (advisory) |
| 21 | Medium | 56, 95, 96 | "Read more" link text repeated and not descriptive | 2.4.4 |
| 22 | Medium | 67, 101 | Duplicate `<label for="qty">`; the second one is hidden and points at an input in a different bar | 1.3.1, 4.1.2 |
| 23 | Medium | 34, 99 | Fixed bottom bar can cover focused content | 2.4.11 (verify) |
| 24 | Low | 73-74 | Shipping info trigger is a `<span>`, not a control; tooltip not linked by `aria-describedby` | 1.3.1, 4.1.2 |
| 25 | Low | 31, 88 | `list-style: none` on the items of the wishlist can strip list semantics in some Safari/VoiceOver builds | 1.3.1 (verify) |
| 26 | Low | 40 | No skip link | 2.4.1 (advisory; page is short) |
| 27 | Low | 16, 35 | Carousel has no `role`/`aria-roledescription`/label; no reduced-motion handling | Best practice (supports 2.2.2) |
| 28 | Low | 66-71 | Quantity input has no `type`, `min` or `max`; invalid text is silently replaced with 1 | Best practice (3.3.1 not triggered) |

Total: 28 items (4 Critical, 13 High, 6 Medium, 5 Low). Items 1-17 each block at least one AA criterion.

## Detailed findings

### 1. Carousel arrows and dots are not operable by keyboard and have no names (Critical)

- Where: lines 46-47 (`<span class="arrow prev" onclick="move(-1)">`, `<span class="arrow next" onclick="move(1)">`) and line 50 (`<span class="dot ..." onclick="go(n)">` x3).
- Why it is a problem: `<span>` elements are not focusable and have no role. Keyboard users cannot reach or activate the controls (2.1.1 Keyboard, Level A). Screen readers announce them as plain text, or nothing, so there is no name, role or state (4.1.2 Name, Role, Value, Level A). The arrow glyphs `&#8249;` and `&#8250;` would be read as punctuation at best.
- Fix: use real buttons.
  ```html
  <button type="button" class="arrow prev" aria-label="Previous image" onclick="move(-1)">&#8249;</button>
  <button type="button" class="arrow next" aria-label="Next image" onclick="move(1)">&#8250;</button>
  ```
  Make each dot a `<button type="button" aria-label="Show image 1 of 3">` and set `aria-current="true"` on the current one. Update `go()` to toggle `aria-current` together with the `current` class. Reset the `button` default styles (`border:0; background` as needed) so the look is unchanged.

### 2. Quantity +/- buttons have no accessible name (Critical)

- Where: lines 68 and 70, `<button class="icon-btn" onclick="step(-1)">` and `step(1)`. The only content is an inline SVG with no title or aria-hidden.
- Why: the button name is empty, so screen readers say "button" with no purpose (4.1.2). Under 2.5.3 Label in Name, a visible label has to be present in the accessible name, and there is none here.
- Fix: `<button type="button" class="icon-btn" aria-label="Decrease quantity" onclick="step(-1)"><svg aria-hidden="true" focusable="false" ...>...</svg></button>` and the same for "Increase quantity". Also add `type="button"` so they never submit a form.

### 3. Colour swatches are not operable by keyboard and carry no name or state (Critical)

- Where: lines 60-62 (three `<div class="swatch" style="background:..." onclick="pickColour(this)">`), and the selected state at line 26 (`.swatch.selected` border only).
- Why: `<div>` elements are not focusable, so keyboard users cannot select a colour (2.1.1). The swatches have no text, so the colour choice has no name (1.1.1 and 4.1.2). The selected state is shown only by a border and is not exposed to assistive technology (4.1.2). Neither a `<label>` nor a group label exists for the set.
- Fix: use a native radio group that keeps the visual swatch.
  ```html
  <fieldset class="swatch-group">
    <legend>Colour</legend>
    <label><input type="radio" name="colour" value="oxblood" checked class="sr-only"><span class="swatch" style="background:#8a2b1d"></span> Oxblood</label>
    <label><input type="radio" name="colour" value="navy" class="sr-only"><span class="swatch" style="background:#1f3d5c"></span> Navy</label>
    <label><input type="radio" name="colour" value="sand" class="sr-only"><span class="swatch" style="background:#c9b68a"></span> Sand</label>
  </fieldset>
  ```
  Keep a visible focus style on the swatch when the radio has focus (`input:focus-visible + .swatch`), and show the colour name next to the swatch or in the legend. The `.selected` class can then follow `:checked` and stays a visual aid only.

### 4. Shipping tooltip is mouse-only and not reachable from the keyboard (Critical)

- Where: lines 73-74. The trigger is `<span onmouseover="...display='inline-block'" onmouseout="...display='none'">Shipping info &#9432;</span>` and the content is `<span class="tip" id="tip">`.
- Why: the tooltip opens only on mouse hover. A keyboard user cannot focus the trigger, so the shipping and returns information (free returns for 30 days) is unavailable to them (2.1.1). Under 1.4.13 Content on Hover or Focus (Level AA), hover-triggered content must also appear on focus, be dismissible without moving pointer or focus (for example with Esc), and be hoverable. None of those conditions is met. Because `.tip` is not linked to the trigger, its text is not announced (see item 24).
- Fix: make the trigger a `<button type="button" aria-describedby="shipping-tip" aria-expanded="false">`. Show the tip on `click`, `focus`, `mouseenter`, and hide it on `blur`, `mouseleave`, and Escape, as 1.4.13 requires. Add `role="tooltip"` and `id="shipping-tip"` to the tip. The simplest compliant option is to show the shipping text inline in the page, which needs no script.

### 5. Wishlist reorder is drag-and-drop only (High)

- Where: lines 88-92 (`<li draggable="true">`), the instruction "Your wishlist (drag to reorder)" at line 87, and the script at lines 113-118.
- Why: the list items cannot be focused or reordered by keyboard (2.1.1, Level A). Under 2.5.7 Dragging Movements (Level AA, new in 2.2), any functionality that uses dragging must also work with a single pointer click or tap and no dragging. None exists. The move is not announced (4.1.3).
- Fix: add move-up and move-down `<button>`s to each item, with names such as "Move Atelier Dumont canvas tote up", and move the `<li>` in the DOM on click. Announce the new position in a live region. Keep drag as an extra option if wanted. Change the heading text to say the buttons are available as well.

### 6. Carousel auto-advances with no pause control (High)

- Where: line 109, `setInterval(function () { move(1); }, 3000);`.
- Why: the carousel moves on its own every 3 seconds. It has no pause, stop or hide mechanism (2.2.2 Pause, Stop, Hide, Level A). Users with cognitive or attention needs and screen-reader users may be disrupted, and the change is not announced.
- Fix: either remove the auto-advance, or add a visible pause/play `<button>` that is on by default for a moving carousel and stops the timer. Also stop the timer when the carousel receives hover or focus, and do not start it if `window.matchMedia('(prefers-reduced-motion: reduce)').matches` is true. Note that this is a 2.2.2 requirement, not optional.

### 7. Autoplaying looping video has no controls and no captions (High)

- Where: line 77, `<video src="/video/tote-story.mp4" width="640" height="360" autoplay loop></video>`.
- Why:
  - 2.2.2 Pause, Stop, Hide (Level A): the video plays automatically, loops, and runs longer than 5 seconds, and no control is provided. There is no `controls` attribute.
  - 1.4.2 Audio Control (Level A): if the video has an audio track, it plays automatically with no mechanism to pause it or control its volume beyond the browser's own. `muted` is absent. Verify whether the file has an audio track.
  - 1.2.2 Captions (Prerecorded) (Level A): if the video has speech or important sound, there is no `<track kind="captions">`.
  - 1.2.5 Audio Description (Prerecorded) (Level AA): if the story is conveyed only visually, an audio description or equivalent is needed. Verify.
- Fix: add `controls`, remove `autoplay` (or add `muted` and `playsinline` and keep a visible pause control), remove `loop` or keep the pause control, and add `<track kind="captions" srclang="en" label="English" src="...vtt" default>`. Provide a text description or audio description for the visual content.

### 8. Focus indicators are removed (High)

- Where: line 9, `*:focus { outline: 0; }`.
- Why: this removes the focus indicator for every focusable element. Keyboard users cannot see where they are (2.4.7 Focus Visible, Level AA). Nothing replaces it, so the page also has no focus style on the swatches, the quantity input or the Add to cart button.
- Fix: delete the rule. If a custom style is wanted, use `:focus-visible` with a clearly visible indicator, for example `outline: 3px solid #1c1c1c; outline-offset: 2px;`, which gives 3:1 against white. The 2.4.13 Focus Appearance criterion is Level AAA and is not required here, but this is a good target.

### 9. No heading structure (High)

- Where: line 53 (`<div class="title">Atelier Dumont canvas tote</div>`), lines 58, 65, 76, 79, 87, 94 (`<div class="section-title">`).
- Why: the page has no `<h1>`. Product title and section titles are plain divs, so screen-reader users cannot navigate by heading (1.3.1 Info and Relationships, Level A). Headings are not used to describe the sections, which fails the purpose of 2.4.6 Headings and Labels (Level AA).
- Fix: `<h1 class="title">Atelier Dumont canvas tote</h1>`, then `<h2 class="section-title">` for Colour, Quantity, See it in use, Size guide, Your wishlist, and Reviews (keep the `id="reviews"` on the h2). Keep the existing CSS classes so the appearance does not change.

### 10. Size table has no header cells and no caption (High)

- Where: lines 80-84.
- Why: the first row and first column use `<td>`, so the relationship between each value and its column and row header is not exposed (1.3.1, Level A). Screen readers cannot announce "Width, Medium: 38 cm".
- Fix:
  ```html
  <table>
    <caption>Size guide (dimensions in cm)</caption>
    <thead><tr><th scope="col">Size</th><th scope="col">Width</th><th scope="col">Height</th><th scope="col">Strap drop</th></tr></thead>
    <tbody>
      <tr><th scope="row">Medium</th><td>38 cm</td><td>34 cm</td><td>24 cm</td></tr>
      <tr><th scope="row">Large</th><td>46 cm</td><td>40 cm</td><td>26 cm</td></tr>
    </tbody>
  </table>
  ```
  The caption replaces the visual section title for this table and removes the need for "Size guide" to be the only description.

### 11. iframe has no title (High)

- Where: line 85, `<iframe src="/embed/size-calculator" width="400" height="200"></iframe>`.
- Why: frames must have an accessible name so users know what they contain (4.1.2, Level A). Without `title`, screen-reader users hear "frame" or the file path.
- Fix: `<iframe src="/embed/size-calculator" title="Size calculator" width="400" height="200"></iframe>`. Also set `max-width:100%` on it (see item 12).

### 12. Content does not reflow at 320 CSS px (High)

- Where: the carousel images (lines 43-45) have `width="960"` and the carousel is `overflow:hidden` (line 13). The video (line 77) has `width="640"`. The iframe (line 85) has `width="400"`. No `max-width:100%` rule exists for any of them. The `.wrap` padding is 16px.
- Why: at a 320 CSS px viewport, the available width is about 288 px. The video and iframe are wider than that, so the page scrolls horizontally in two directions. That fails 1.4.10 Reflow (Level AA). The carousel images are not scaled: a 960 px image inside a 288 px box is clipped by `overflow:hidden`, so part of the product photo is hidden. This is loss of information, not only a scroll problem. No 2D-layout exception applies to these items.
- Fix: add `img, video, iframe { max-width: 100%; height: auto; }` (and `.carousel img { width: 100%; height: 100%; object-fit: cover; }` if the carousel stays a fixed height). Remove the fixed pixel `width` on the video and iframe, or keep it as a max. Verify at 320 px and at 400% zoom.

### 13. Colour contrast failures (High)

- SALE badge, line 21: `background:#ff9a3c; color:#ffffff; font-size:13px; font-weight:700`. Contrast 2.11:1. 13 px bold is not "large text" (that requires 14 pt bold, about 18.66 px), so 4.5:1 applies. Fails 1.4.3 Contrast (Minimum). Fix: darken the background, for example `#b34700` (5.5:1 with white), or use a dark text colour on the orange.
- Old price, line 22: `.old { color:#777 }` on `#fff`. Contrast 4.48:1, just below the 4.5:1 required for 16 px text. Fails 1.4.3. Fix: `color:#767676` (4.54:1) or darker. The struck-through text is still text and must meet the ratio.
- Carousel dots, lines 19-20: inactive `background:#c9c5ba` on white. Contrast 1.72:1. Fails 1.4.11 Non-text Contrast (Level AA, 3:1 minimum), because the dot is the only indicator of which slide is current. Fix: inactive dot `#767676` (4.54:1 against white, which also clears 3:1), and keep the current dot `#1c1c1c`.
- Passing for reference: body text `#1c1c1c` on white (about 16:1); `.new` `#c0271b` on white (about 5.9:1); `.buy` and `.tip` white on `#1c1c1c`; `.icon-btn` and quantity input border `#777` on white (4.48:1, above the 3:1 needed for a component boundary, so 1.4.11 passes).

### 14. Carousel image alt text is a filename (High)

- Where: line 43, `alt="tote-front.jpg"`.
- Why: the alt text is a file name, not a description. It fails 1.1.1 Non-text Content (Level A) because the user gets no information about the product photo.
- Fix: `alt="Atelier Dumont canvas tote, front view"`.

### 15. Rating image has empty alt although it conveys the rating (High)

- Where: line 56, `<img src="/img/stars-4.png" alt="" width="100" height="20">`.
- Why: `alt=""` marks an image as decorative. These stars convey the rating, so the information is lost to screen-reader users (1.1.1, Level A). The rating is shown only as an image.
- Fix: `alt="Rated 4 out of 5 stars"`. Alternatively, put the rating in text next to the image and keep `alt=""`.

### 16. French passage has no language attribute (High)

- Where: line 54, `<p>Fabriqué à la main à Lyon, en toile de coton épaisse.</p>`. The page is `lang="en"` (line 2).
- Why: a passage in a different language needs its own `lang` so that screen readers pronounce it correctly (3.1.2 Language of Parts, Level AA).
- Fix: `<p lang="fr">Fabriqué à la main à Lyon, en toile de coton épaisse.</p>`.

### 17. Cart count changes are not announced (High)

- Where: lines 100 and 112. `addToCart()` sets `c.textContent` on the `#cart-count` span, which is not a live region.
- Why: the update is silent for screen-reader users, who get no confirmation that the item was added (4.1.3 Status Messages, Level AA).
- Fix: `<span role="status">Cart: <span id="cart-count">0</span> items</span>`, or add `aria-live="polite"` to `#cart-count`. Consider a short message such as "Added 1 to cart" in the same live region.

### 18. Touch target sizes too small (Medium)

- Where: lines 28 and 70 (`.icon-btn` 20 x 20 px). Lines 19 (`.dot` 10 x 10 px, with 3 px margin on each side, so about 16 px centre-to-centre spacing).
- Why: 2.5.8 Target Size (Minimum, Level AA) requires at least 24 x 24 CSS px, unless the spacing exception applies. The 20 px buttons fail. The dots fail, because their 24 px spacing circles overlap neighbouring targets.
- Fix: make `.icon-btn` at least 24 x 24 px (ideally 44 px). Make the dot targets at least 24 x 24 px with padding or a larger `::before` hit area while keeping the visual size. The swatches (32 px) and the arrow buttons (about 40 px tall) already pass.

### 19. Page landmarks and breadcrumb are missing (Medium)

- Where: line 40 (`<a href="/">Northgate Goods</a> / <a href="/bags">Bags</a>` in a plain div), and the page as a whole.
- Why: there are no `<main>`, `<header>`, `<nav>` or `<footer>` landmarks. The breadcrumb is not identified as navigation. This is a 1.3.1 structure issue and it limits 2.4.1 Bypass Blocks (see item 26).
- Fix: wrap the breadcrumb as `<nav aria-label="Breadcrumb"><ol><li><a href="/">Northgate Goods</a></li><li><a href="/bags">Bags</a></li></ol></nav>`. Wrap the product content in `<main>` and the buy bar in `<footer>` or `<div role="region" aria-label="Purchase">`.

### 20. Price meaning is conveyed only by styling (Medium, advisory)

- Where: line 55, `<span class="old">$80</span> <span class="new">$60</span>`.
- Why: the strike-through and colour show the sale price, but a screen reader reads "$80 $60" with no meaning. Strike-through is not text meaning. This is not a clear 1.4.1 failure, since bold and strike-through are used, but the meaning is not in the text.
- Fix: use semantic markup and visually hidden text, for example `<del><span class="sr-only">Was </span>$80</del> <ins><span class="sr-only">Now </span>$60</ins>`, or `Was $80, now $60` in a visually hidden element. Add the `sr-only` class to the stylesheet.

### 21. "Read more" links are not descriptive (Medium)

- Where: line 56 (`<a href="#reviews">Read more</a>`), lines 95-96 (`<a href="/reviews/1">Read more</a>`, `/reviews/2`).
- Why: three links share the text "Read more" and go to different places. 2.4.4 Link Purpose (In Context, Level A) is met only if the surrounding sentence gives the purpose. The one at line 56 goes to the review section, not to a review, so its purpose is unclear.
- Fix: make the text descriptive, for example "Read more reviews" at line 56 and "Read the full review by ..." at lines 95-96, or add visually hidden text such as `<span class="sr-only"> review 1</span>`.

### 22. Duplicate and misplaced labels for the quantity input (Medium)

- Where: line 67 (`<label for="qty">Quantity</label>`), line 69 (`<input id="qty">`), and line 101 (`<label for="qty" style="display:none">Qty</label>`) inside the buy bar.
- Why: the input has two labels, so its accessible name combines both ("Quantity Qty" in most browsers, even though one is hidden). The second label is hidden but still contributes to the name. It is also in a different part of the page from the input it points to, which makes the markup misleading (1.3.1, 4.1.2). The "Quantity" section heading at line 65 duplicates the visible label.
- Fix: delete line 101. Keep one label. If the buy bar needs a quantity control, put its own input with its own label there. Replace the section-title "Quantity" with a fieldset legend if one is kept.

### 23. Fixed buy bar may cover focused content (Medium, verify)

- Where: line 34, `.buybar { position: fixed; bottom: 0; ... height: 72px }`, with `padding-bottom: 80px` on body (line 8).
- Why: 2.4.11 Focus Not Obscured (Minimum, Level AA) requires that a focused element is not entirely hidden by author content. A focused control scrolled under the 72 px bar can be fully hidden, depending on scroll position. Partial cover is allowed. Verify by tabbing through the page at 320 px and 1280 px height.
- Fix: add `scroll-padding-bottom: 80px` on `html`, so focused elements scroll above the bar. Alternatively, make the bar a normal block at the end of the page on narrow screens.

### 24. Shipping trigger is not a control and the tip is not linked (Low)

- Where: lines 73-74.
- Why: the trigger is a `<span>`, so it has no role or name. The tip text is not associated with it (`aria-describedby`), so it is not announced. This is part of 1.3.1 and 4.1.2. The fix for item 4 covers it.

### 25. List semantics may be removed (Low, verify)

- Where: line 31, `.wishlist li { ...; list-style: none; }`.
- Why: when `list-style: none` is applied to a list, some Safari/VoiceOver versions drop the list role, so the list is announced as plain items. This is a known WebKit behaviour and needs a check in the target browser.
- Fix: add `role="list"` to the `<ul class="wishlist">`, or remove the `list-style` declaration and set `list-style: none` on the `ul` with `padding: 0` and keep the bullets hidden by other means.

### 26. No skip link (Low, advisory)

- Where: line 39 (start of the page content).
- Why: 2.4.1 Bypass Blocks (Level A) needs a way to skip repeated blocks. This page has few repeated blocks, so it likely passes. A skip link to the main content is still recommended, especially once a site header is added.
- Fix: `<a class="skip" href="#main">Skip to content</a>` as the first element in `body`, with `id="main"` on `<main>`.

### 27. Carousel has no structure or announcement (Low, best practice)

- Where: line 42 (`<div class="carousel" id="carousel">`).
- Why: the carousel has no name, no role description and no live state. Combined with item 6, a screen-reader user does not know that a set of slides exists or which one is shown.
- Fix: `<section class="carousel" aria-roledescription="carousel" aria-label="Product images">`. Give each slide `role="group" aria-roledescription="slide" aria-label="1 of 3"`. Use `aria-live="off"` while auto-advance is paused and `polite` while it runs.

### 28. Quantity input has no constraints (Low, best practice)

- Where: line 69, `<input id="qty" value="1" inputmode="numeric">`, and `step()` and `addToCart()` in lines 111-112.
- Why: invalid input such as "abc" is silently changed to 1 by `parseInt(...) || 1`. Nothing tells the user that the value was corrected. This is not a 3.3.1 failure because no error is detected by the page, but users who type a value they expect to be kept will not be warned. The input also has no `min` or `max`.
- Fix: `<input id="qty" type="number" min="1" max="99" value="1" inputmode="numeric">` and validate on `change`, showing a visible message next to the field in a live region if the value is out of range.

## Criteria checked and not failed (for reference)

- 2.4.2 Page Titled: the `<title>` describes the page (line 6).
- 3.1.1 Language of Page: `lang="en"` is set (line 2).
- 1.4.4 Resize Text and the viewport meta (line 5): zoom is not disabled.
- 2.5.1 Pointer Gestures: no multipoint or path-based gesture is required outside the wishlist drag (covered by item 5).
- 2.5.2 Pointer Cancellation: click handlers are used, which fire on release, so this passes.
- 2.2.1 Timing Adjustable and 2.3.1 Three Flashes: no time limits and no flashing content.
- 2.4.3 Focus Order: DOM order matches the visual order, apart from the fixed bar (item 23).
- 3.2.1 On Focus and 3.2.2 On Input: changing a swatch or quantity does not change context unexpectedly.
- 3.3.8 Accessible Authentication: no login.
- 1.4.12 Text Spacing: no fixed-height text containers, except the carousel box and the 72 px buy bar, which hold single short items. Verify with a text-spacing bookmarklet.

## Recommended order of fixes

1. Items 1-4 and 5, which block keyboard and screen-reader use of the controls.
2. Items 6, 7 and 8, which cover motion, media and focus visibility.
3. Items 9-17, which cover structure, names, language, contrast and status messages.
4. Items 18-28, which cover target size, landmarks and the remaining advisories.

Re-test after the fixes with a keyboard-only pass (Tab, Shift+Tab, Enter, Space, Esc, arrow keys), a screen reader (NVDA with Chrome or Firefox, VoiceOver with Safari), a 320 px viewport and 400% zoom, and an automated scan (axe or Lighthouse) as a second check. Automated tools miss items 4, 5, 7, 20 and 23, so those need manual testing.
