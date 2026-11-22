# Accessibility audit: signup.html against WCAG 2.2 Level AA

Audited file: `<local-path>` (94 lines, not modified).

Method: manual review of the markup, inline CSS and inline JavaScript against the WCAG 2.2 success criteria (A and AA). Contrast ratios were calculated from the hex values in the stylesheet using the WCAG relative-luminance formula. No automated tool or assistive technology was run, so items marked "verify" should be confirmed with a screen reader and keyboard pass after the fixes.

## Summary

The page does not conform to WCAG 2.2 AA. The most serious problems are:

1. The primary submit control is an `<a>` with no `href`. It cannot be reached or activated from the keyboard, so the form cannot be submitted without a mouse (2.1.1, 4.1.2).
2. Most form fields have no programmatic label. Name, email and password inputs are not labelled for assistive technology, and the password `aria-labelledby` points to an id that does not exist (1.3.1, 3.3.2, 4.1.2).
3. Focus indicators are removed globally for inputs, selects and links (2.4.7).
4. The session auto-redirects after 2 minutes with no warning or extension, which can discard what the user typed (2.2.1).
5. The text-based captcha has no alternative, and password paste is blocked (3.3.8).
6. Several colour contrast failures: hint text, button text and the input border (1.4.3, 1.4.11).
7. Zoom is disabled in the viewport meta tag (1.4.4).

| # | Severity | Issue | WCAG SC | Location (lines) |
|---|---|---|---|---|
| 1 | Critical | Submit control is a focusable-less `<a>` with no href | 2.1.1, 4.1.2 | 81 |
| 2 | Critical | Full name has no label association | 1.3.1, 3.3.2, 4.1.2 | 42-43 |
| 3 | Critical | Email has no label; placeholder used as label | 1.3.1, 3.3.2, 1.3.5 | 47 |
| 4 | Critical | Password input has broken `aria-labelledby` and no name | 1.3.1, 4.1.2, 3.3.2 | 58 |
| 5 | Critical | Terms "checkbox" is a non-focusable div with no role or state | 1.3.1, 2.1.1, 4.1.2 | 77 |
| 6 | Critical | Session timeout with no warning or extension | 2.2.1 | 91 |
| 7 | High | Focus outline removed for inputs, selects and links | 2.4.7 | 15 |
| 8 | High | Password show/hide button has no accessible name | 4.1.2, 1.1.1 | 59 |
| 9 | High | Logo image has no alt text and the link has no name | 1.1.1, 2.4.4 | 32 |
| 10 | High | `<html>` has no `lang` attribute | 3.1.1 | 2 |
| 11 | High | Zoom disabled (`maximum-scale=1, user-scalable=no`) | 1.4.4 | 5 |
| 12 | High | Text captcha with no alternative and no audio or refresh option | 3.3.8, 1.1.1 | 70-74 |
| 13 | High | Password paste is blocked | 3.3.8 | 58 |
| 14 | High | Autocomplete tokens missing or wrong for name, email, phone, new password | 1.3.5 | 43, 47, 53, 58 |
| 15 | High | Required fields indicated by colour and asterisk only, not programmatically required | 1.4.1, 1.3.3, 3.3.2 | 36, 42, 47 |
| 16 | High | Error text "Invalid" is always visible, not linked, not announced, and not descriptive | 3.3.1, 3.3.3, 4.1.3, 1.3.1 | 47-48 |
| 17 | High | Invalid email state shown by red border only | 1.4.1 | 19, 47 |
| 18 | High | Text colour contrast failures (hint, button) | 1.4.3 | 16, 24 |
| 19 | High | Input border contrast too low | 1.4.11 | 14 |
| 20 | High | Terms link text "Click here" is not descriptive | 2.4.4, 2.4.6 | 78 |
| 21 | Medium | Plan radio group has no fieldset and legend | 1.3.1 | 63-68 |
| 22 | Medium | Heading levels skip (h1 then h3) | 1.3.1 | 35, 39, 63 |
| 23 | Medium | Positive `tabindex` values break focus order | 2.4.3 | 43, 47 |
| 24 | Medium | Password strength meter communicated by colour only, not announced | 1.4.1, 4.1.3 | 20, 60, 86-89 |
| 25 | Medium | Password requirements not stated | 3.3.2 | 57-61 |
| 26 | Medium | Phone hint not associated with the input | 1.3.1 | 52-54 |
| 27 | Medium | Sticky header can obscure a focused element | 2.4.11 | 9 |
| 28 | Medium | Terms checkbox target smaller than 24x24 px; icon button 18x18 px | 2.5.8 | 22, 25, 77 |
| 29 | Medium | Checked/unchecked state of the terms control shown by colour only | 1.4.1 | 23, 77 |
| 30 | Medium | Captcha is an image of text | 1.4.5 | 71 |
| 31 | Low | Hint text is 13px and low contrast | 1.4.3 | 16, 18 |
| 32 | Low | Eye icon overlaps typed password text (no right padding on input) | 1.4.12 (verify), usability | 14, 25 |
| 33 | Low | Error and hint text sizes below 16px base | Advisory | 16, 18 |
| 34 | Low | Plan radio group has no required or default state communicated | 3.3.2 | 63-68 |

## Detailed findings

### Critical

**1. Submit button is not keyboard operable (lines 81)**
- Where: `<a class="btn" onclick="document.getElementById('signup').submit()">Create account</a>`
- Why: An `<a>` without `href` is not a link and is not in the tab order. Keyboard users cannot reach it, and Enter does not activate it. The control has no role, so screen readers may not announce it as a button. This also means the form cannot be completed by keyboard alone. Calling `form.submit()` also bypasses native constraint validation and the submit event.
- Fix: Use a real button: `<button type="submit" class="btn">Create account</button>` and remove the `onclick`. Let the native submit handle it. Adjust the CSS for `button` (reset border, font, and set `cursor: pointer`).
- SC: 2.1.1 Keyboard (A), 4.1.2 Name, Role, Value (A).

**2. Full name is not labelled (lines 42-43)**
- Where: `<span>Full name <span class="req">*</span></span>` followed by `<input id="fullname">`.
- Why: The visible text is a `<span>`, so the input has no accessible name. Screen reader users hear an unnamed text field. Clicking the text also does not focus the field.
- Fix: `<label for="fullname">Full name <span class="req" aria-hidden="true">*</span></label>` and add `required` (and `aria-required` if you prefer) to the input. Keep the required meaning in text as well (see item 15).
- SC: 1.3.1 Info and Relationships (A), 3.3.2 Labels or Instructions (A), 4.1.2 (A).

**3. Email has no label; placeholder used as the label (line 47)**
- Where: `<input type="text" name="email" id="email" class="invalid" placeholder="Work email *">`
- Why: The only text is a placeholder. Placeholders are not reliably announced as names, disappear when typing, and have low default contrast. The input type is also `text` rather than `email`.
- Fix: Add a visible `<label for="email">Work email <span aria-hidden="true">*</span></label>`, set `type="email"`, `autocomplete="email"`, `required`, and remove the `*` from the placeholder (or drop the placeholder).
- SC: 1.3.1 (A), 3.3.2 (A), 1.3.5 Identify Input Purpose (AA).

**4. Password field has a broken label reference and no name (line 58)**
- Where: `<input type="password" ... aria-labelledby="pw-label" ...>`. No element with `id="pw-label"` exists in the document.
- Why: `aria-labelledby` points to nothing, so the field has no accessible name. The password field has no visible label at all, so sighted users also have no label.
- Fix: Add a visible `<label for="password">Password</label>` and remove the `aria-labelledby` attribute. Add `autocomplete="new-password"`, `required`, and a visible requirements hint linked with `aria-describedby` (see item 25).
- SC: 1.3.1 (A), 4.1.2 (A), 3.3.2 (A).

**5. Terms agreement control is a fake checkbox (lines 77-78)**
- Where: `<div class="check" id="terms" onclick="this.classList.toggle('on')"></div>` followed by text and a link.
- Why: A `div` with a click handler is not focusable and has no role or state. Keyboard users cannot toggle it. Screen readers do not know it is a checkbox or whether it is checked. It is also not associated with its text ("I agree to the terms."). The `on` class is not exposed to assistive technology.
- Fix: Use a native checkbox inside a label: `<label><input type="checkbox" name="terms" id="terms" required> I agree to the <a href="/terms">Terms of Service</a></label>`. Style the native input with `accent-color` or a custom visual that keeps a visible boundary and checked state. Remove the `onclick`.
- SC: 1.3.1 (A), 2.1.1 (A), 4.1.2 (A).

**6. Session auto-redirects after 2 minutes with no warning (lines 90-91)**
- Where: `setTimeout(function () { window.location.href = '/signup/timeout'; }, 120000);`
- Why: The page redirects regardless of user activity after 120 seconds. Users who are slow or who rely on assistive technology lose everything they typed, with no warning and no way to extend the time. The comment says this is a security measure, but the same security goal can be met without discarding input.
- Fix: Either remove the timer, or warn the user at least 20 seconds before expiry in an accessible dialog or status region, let them extend the session with one action, and keep the entered data. Reset the timer on user activity. If the timeout is kept, reconsider whether it is needed for a sign-up form at all.
- SC: 2.2.1 Timing Adjustable (A). The criterion is Level A, so it also blocks AA conformance.

### High

**7. Focus indicators removed (line 15)**
- Where: `input:focus, select:focus, a:focus { outline: none; }`
- Why: Keyboard users cannot see which control has focus on text inputs, radio buttons, or links. Nothing else in the stylesheet provides a replacement, so focus is invisible.
- Fix: Remove the `outline: none` rule, or replace it with a visible indicator of at least 2 px with at least 3:1 contrast against adjacent colours, for example `:focus-visible { outline: 3px solid #1a4fd6; outline-offset: 2px; }`.
- SC: 2.4.7 Focus Visible (AA).

**8. Show/hide password button has no accessible name (line 59)**
- Where: `<button type="button" class="icon-btn" onclick="togglePw()"><svg ...></svg></button>`
- Why: The button contains only an SVG with no title and no `aria-hidden`. Screen readers announce an unnamed button. The pressed state is not exposed either. The button is also 18x18 px (line 25), which is below the 24 px target minimum (see item 28).
- Fix: Add `aria-label="Show password"` (and toggle to "Hide password" in the script) or use `aria-pressed` with a constant label such as "Show password". Mark the SVG `aria-hidden="true" focusable="false"`. Increase the size to at least 24x24 px.
- SC: 4.1.2 (A), 1.1.1 (A), 2.5.8 (AA).

**9. Logo has no alt text and the link has no accessible name (line 32)**
- Where: `<a href="/"><img src="/img/larkspur-logo.svg" width="120" height="28"></a>`
- Why: The image has no `alt` attribute. The link therefore has no accessible name, and screen readers may read the file name.
- Fix: `<img src="/img/larkspur-logo.svg" width="120" height="28" alt="Larkspur Payroll home">`. If the logo is decorative beside a text name, use `alt="Larkspur Payroll"` on the link and `alt=""` elsewhere, but do not leave the attribute missing.
- SC: 1.1.1 Non-text Content (A), 2.4.4 Link Purpose (A).

**10. Missing page language (line 2)**
- Where: `<html>`
- Why: Without `lang`, screen readers may use the wrong pronunciation rules for the entire page.
- Fix: `<html lang="en">`.
- SC: 3.1.1 Language of Page (A).

**11. Zoom disabled (line 5)**
- Where: `<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">`
- Why: `maximum-scale=1` and `user-scalable=no` stop users from pinch-zooming, which low-vision users depend on.
- Fix: `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- SC: 1.4.4 Resize Text (AA).

**12. Text captcha without an alternative (lines 70-74)**
- Where: `<img src="/captcha/7f3a.png" alt="captcha">` with a text entry field.
- Why: The challenge is a distorted text image that requires perception and transcription. There is no audio alternative, no alternative method, and no way to request a new challenge. The alt text "captcha" does not describe the content. The image URL also uses a fixed id, so the same challenge is served each time.
- Fix: Use a captcha that does not rely on cognitive function tests, such as a managed/invisible challenge, passkey, or email verification, or provide an audio alternative plus a refresh control. Give the image descriptive alt text ("Captcha: type the characters shown") or move the requirement to a non-image method.
- SC: 3.3.8 Accessible Authentication (Minimum) (AA), 1.1.1 (A).

**13. Password paste is blocked (line 58)**
- Where: `onpaste="return false"`
- Why: Blocking paste prevents password managers from filling the field, which is a common accessibility need for people with motor or memory difficulties. Users are forced to type a password they must remember.
- Fix: Remove `onpaste="return false"`.
- SC: 3.3.8 Accessible Authentication (Minimum) (AA).

**14. Autocomplete tokens missing or wrong (lines 43, 47, 53, 58)**
- Where: Name has no `autocomplete`; email has none; phone has none; password has `autocomplete="off"`.
- Why: The purpose of each field must be programmatically determinable so that browsers and assistive tools can fill it. `autocomplete="off"` on a new-password field also blocks password managers from suggesting a strong password.
- Fix: `fullname` -> `autocomplete="name"`; `email` -> `type="email" autocomplete="email"`; `phone` -> `type="tel" autocomplete="tel"`; `password` -> `autocomplete="new-password"`.
- SC: 1.3.5 Identify Input Purpose (AA).

**15. Required fields indicated by colour and asterisk only (lines 36, 42, 47)**
- Where: "Fields marked in red are required." (line 36); red `*` on line 42; `*` inside placeholder on line 47.
- Why: The instruction depends on colour and is not programmatically announced. Only the full name field shows a marker; the email marker is inside the placeholder, and the password and plan fields show no marker at all. Requiredness is not set via `required` or `aria-required`, so assistive technology does not report it.
- Fix: Write the instruction as text: "All fields marked with * are required." Use `required` on every required input and a consistent visible `*` in each label, with the asterisk marked `aria-hidden` if the instruction is also given in text. Apply `required` to the plan radio group if it is mandatory.
- SC: 1.4.1 Use of Color (A), 1.3.3 Sensory Characteristics (A), 3.3.2 (A).

**16. Error message always visible, unlinked, not announced, and unhelpful (lines 47-48)**
- Where: `<span class="err">Invalid</span>` after the email input.
- Why: The error is shown on page load before the user has typed anything. It is not associated with the input, so screen readers do not read it when the field is focused. Dynamic errors would also need a live region, which is absent. "Invalid" does not say what is wrong or how to fix it.
- Fix: Show errors only after submission or blur, and describe the problem. Example: "Enter a work email address, such as name@company.com." Link it with `aria-describedby="email-err"` and set `aria-invalid="true"` on the field. Put the message in a region that is announced, or move focus to an error summary at the top of the form. Consider adding `novalidate` only if you provide an accessible error summary.
- SC: 3.3.1 Error Identification (A), 3.3.3 Error Suggestion (AA), 4.1.3 Status Messages (AA), 1.3.1 (A).

**17. Invalid state shown by colour only (lines 19, 47)**
- Where: `.invalid { border-color: #d00 !important; }` on the email field, present from load.
- Why: The only sign of an error is a red border, which colour-blind users may not perceive. The state is also shown on page load.
- Fix: Pair the red border with the text message from item 16 and an icon or text prefix such as "Error:", and set `aria-invalid` on the field.
- SC: 1.4.1 Use of Color (A).

**18. Text contrast failures (lines 16, 24)**
- Where: `.hint { color: #9a9a9a }` on white, and `.btn { color: #ffffff; background: #5fa8ff }`.
- Why: `#9a9a9a` on white is about 2.8:1, below the 4.5:1 minimum for normal text. White on `#5fa8ff` is about 2.5:1, which also fails. The button text is 16px bold (600 weight), which is below the 18.66px bold threshold for large text, so 4.5:1 applies.
- Fix: Use a hint colour of at least 4.5:1 on white, such as `#595959` (about 7:1). Use a darker button background, for example `#1a5fd1` with white text (about 5.5:1), or keep the brand blue and use dark text of at least 4.5:1.
- SC: 1.4.3 Contrast (Minimum) (AA).

**19. Input border contrast too low (line 14)**
- Where: `input[type=text], input[type=password] { border: 1px solid #ccc; }`
- Why: `#ccc` on white is about 1.6:1. The border is the only visual boundary of the text input, so it is needed to identify the control and must reach 3:1.
- Fix: Use a border colour of at least 3:1 against white, for example `#767676` (about 4.5:1).
- SC: 1.4.11 Non-text Contrast (AA).

**20. Non-descriptive link text (line 78)**
- Where: `I agree to the terms. <a href="/terms">Click here</a>`
- Why: "Click here" does not describe the destination. Screen reader users navigating by links hear a list of "Click here" entries.
- Fix: `I agree to the <a href="/terms">Terms of Service</a>.` (or the actual document title).
- SC: 2.4.4 Link Purpose (In Context) (A), 2.4.6 Headings and Labels (AA).

### Medium

**21. Plan radio group not grouped (lines 63-68)**
- Where: `<h3>Plan</h3>` followed by three `<label>` elements wrapping radio inputs in a plain `div`.
- Why: The radios have no group name for screen readers. Users hear "Starter, radio button, 1 of 3" without knowing the question being answered.
- Fix: `<fieldset><legend>Plan</legend> ... </fieldset>`. Remove the separate `h3` for this group, or nest it inside the legend.
- SC: 1.3.1 Info and Relationships (A).

**22. Heading levels skip (lines 35, 39, 63)**
- Where: `h1` then `h3` used for "Your details" and "Plan".
- Why: The heading structure skips level 2. Screen reader users navigating by heading get an inconsistent outline.
- Fix: Change both `h3` elements to `h2`, and adjust styling with CSS if the visual size should stay the same.
- SC: 1.3.1 (A).

**23. Positive tabindex values (lines 43, 47)**
- Where: `tabindex="1"` on full name and `tabindex="2"` on email.
- Why: Positive tab index values force these fields to the front of the tab order, ahead of the logo link and any other controls. This makes the focus order unpredictable and different from the visual order. Positive values are also fragile when elements are added.
- Fix: Remove both `tabindex` attributes. Use source order, which already matches the visual order.
- SC: 2.4.3 Focus Order (A).

**24. Password strength conveyed by colour only (lines 20, 60, 86-89)**
- Where: `.meter` background changes from red to amber to green in the script (line 88). The meter `div` has no role or text.
- Why: Strength is conveyed only by colour and width. Users who cannot see the colour, or screen reader users, get no information. The change is also not announced.
- Fix: Add a text status such as "Weak", "Fair", or "Strong" that updates in a `role="status"` or `aria-live="polite"` region, and use `role="meter"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax` and an accessible name if you keep the bar.
- SC: 1.4.1 Use of Color (A), 4.1.3 Status Messages (AA).

**25. Password requirements not stated (lines 57-61)**
- Where: No hint text is shown near the password field.
- Why: Users cannot know the rules before submitting, and the meter does not say what is required. Errors are then discovered only after a failed attempt.
- Fix: Add a visible hint (for example "At least 10 characters") and link it with `aria-describedby`. Note that the script treats 6 characters as the lower boundary; state the actual minimum the server enforces.
- SC: 3.3.2 Labels or Instructions (A).

**26. Phone hint not associated with the input (lines 52-54)**
- Where: `<span class="hint">We only call about payroll deadlines.</span>` is a sibling of the input.
- Why: The hint is not programmatically connected, so screen readers do not read it with the field.
- Fix: Add `id="phone-hint"` to the span and `aria-describedby="phone-hint"` to the input. Also set `type="tel"` (item 14).
- SC: 1.3.1 (A), 3.3.2 (A).

**27. Sticky header can obscure focus (line 9)**
- Where: `.topbar { position: sticky; top: 0; height: 64px; }`
- Why: When a focused element scrolls under the 64 px header, it is partly or fully hidden. This is the situation 2.4.11 targets.
- Fix: Add `scroll-padding-top: 80px;` (header plus margin) on `html`, or `scroll-margin-top` on focusable elements. Verify by tabbing through the form while scrolled.
- SC: 2.4.11 Focus Not Obscured (Minimum) (AA, new in WCAG 2.2).

**28. Target size below 24x24 px (lines 22, 25, 77)**
- Where: `.icon-btn { width: 18px; height: 18px }`, `.check { width: 18px; height: 18px }`.
- Why: The password toggle and the terms checkbox are 18x18 px, below the 24x24 px minimum. Neither has spacing from other targets that would meet the exception.
- Fix: Make both targets at least 24x24 px, or add enough spacing to meet the 24 px spacing exception. The terms control is fixed by item 5 if it becomes a native checkbox with a label that covers the text.
- SC: 2.5.8 Target Size (Minimum) (AA).

**29. Checked state shown by colour only (lines 23, 77)**
- Where: `.check.on { background: #2a6df4; }`
- Why: Even after item 5 is fixed, a colour-only checked state is not enough. A checkmark or text is needed.
- Fix: Use a native checkbox (item 5). If a custom style is kept, add a visible checkmark glyph in addition to the background colour.
- SC: 1.4.1 Use of Color (A).

**30. Captcha is an image of text (line 71)**
- Where: `<img src="/captcha/7f3a.png" alt="captcha">`
- Why: The characters are presented as an image of text, which 1.4.5 discourages unless the presentation is essential. A text captcha is not essential in the criterion's sense because it can be replaced with an accessible method (see item 12).
- Fix: Remove the text-image captcha as described in item 12. If it stays, provide an audio alternative and text-based option.
- SC: 1.4.5 Images of Text (AA).

### Low

**31. Small hint and error text (lines 16, 18)**
- Where: `.hint` and `.err` are `font-size: 13px`.
- Why: Small text is harder to read, especially for users with low vision. The contrast issue is covered in item 18.
- Fix: Use at least 14px, and preferably 16px, for helper and error text.
- SC: Advisory; contributes to 1.4.4 readability and 1.4.12 usability.

**32. Eye icon overlaps typed password (lines 14, 25)**
- Where: `.icon-btn` is absolutely positioned at `right: 10px` inside an input with `padding: 10px` and no extra right padding.
- Why: Long passwords can run under the icon, so the user cannot see the end of what they typed. This is a usability and visibility issue; verify it at 200% zoom.
- Fix: Add right padding to the password input, for example `padding-right: 40px`, to reserve space for the icon.
- SC: 1.4.12 Text Spacing (AA) (verify), usability.

**33. Plan has no required or default state communicated (lines 63-68)**
- Where: No radio is pre-selected and no requirement is stated.
- Why: If a plan is required, the form gives no indication and no error. If it is optional, that is not stated either.
- Fix: Decide whether the plan is required. If it is, mark the fieldset as required in text and handle the missing-selection error per item 16.
- SC: 3.3.2 Labels or Instructions (A).

**34. Password toggle does not announce state change (line 85)**
- Where: `togglePw()` changes `type` but no state is announced.
- Why: Users who cannot see the field do not know whether the password is now visible.
- Fix: Covered by item 8 (update the button label or `aria-pressed`).
- SC: 4.1.2 (A).

## Items checked and passing

- 2.4.2 Page Titled (A): the `<title>` describes the page.
- 1.4.10 Reflow (AA): the layout is a single column with `max-width: 480px`, so it should reflow at 320 CSS px. Verify with a 320 px viewport.
- 1.4.12 Text Spacing (AA): no fixed heights on text containers except the 64px topbar, which holds no text. Verify with user-applied spacing overrides.
- 1.4.3 for error text: `#d00` on white is about 5.7:1 and passes.
- 2.4.1 Bypass Blocks (A): the page is short and the header holds one link, so no skip link is required.
- 3.2.1 On Focus and 3.2.2 On Input: no context changes on focus; the password meter updates in place without moving focus.
- 3.3.7 Redundant Entry (A): no fields are asked for twice.
- 2.5.7 Dragging Movements (AA): no drag interactions.

## Verification needed

The following should be checked with a keyboard pass and a screen reader (NVDA or VoiceOver) after the fixes: focus order and visibility, announced names and states for every control, error announcements, the timeout behaviour, and reflow and zoom at 200-400%.

## Priority order for fixes

1. Replace the `<a>` submit control with a real `<button type="submit">` (item 1).
2. Add labels, `required`, `autocomplete`, and fix the password `aria-labelledby` (items 2, 3, 4, 14).
3. Replace the fake terms checkbox with a native checkbox (item 5).
4. Remove the focus outline override and the zoom restriction (items 7, 11).
5. Fix the session timeout (item 6) and the captcha and paste restrictions (items 12, 13).
6. Fix colour contrast and target sizes (items 18, 19, 28).
7. Fix errors, instructions, and fieldset grouping (items 15, 16, 21, 25).
8. Fix headings, tabindex, language, logo alt and link text (items 9, 10, 20, 22, 23).
