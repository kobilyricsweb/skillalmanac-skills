---
name: accessibility-audit
description: Audits web pages and components against WCAG 2.2 levels A and AA and fixes what it finds. Runs a bundled static checker for machine-detectable failures, then a manual pass for keyboard, focus, names, forms, media and the criteria added in 2.2, and reports each issue with its success criterion, who it blocks and the fix. Use when the user asks for an accessibility or a11y audit, a WCAG, ADA or Section 508 check, screen reader or keyboard support, or to make a page, form, modal or component accessible. Do not use for visual redesign, SEO audits, performance work or legal compliance sign-off.
license: Apache-2.0
compatibility: The checker needs Python 3.9 or newer (standard library only). No network access is used. Without Python, follow the manual checklist and say the script was not run.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Accessibility audit

Find the barriers in a page or component, say who each one blocks, and fix them. Evidence comes from two places: `scripts/a11y_static_check.py` (what can be decided from source) and a manual read in a fixed order (what cannot). Always say which of the two produced a finding and what neither covered.

## Workflow

Copy this checklist into the reply and tick items as they are done:

```
- [ ] 1. Scope set (files, level, audit only or audit and fix)
- [ ] 2. Static checker run on every HTML file
- [ ] 3. Each checker finding confirmed in the source
- [ ] 4. Manual pass done in the fixed order
- [ ] 5. Severity assigned by user impact
- [ ] 6. Fixes applied and checker re-run (only if asked to fix)
- [ ] 7. Report written, including what was not tested
```

### 1. Scope

Default target: WCAG 2.2 level AA (which includes level A). Audit only what was asked for. If the request does not say whether to fix, audit first and offer the fixes.

### 2. Run the checker

```bash
python scripts/a11y_static_check.py path/to/page.html
```

Several files may be passed; `--json` gives machine-readable output. The script reads HTML with inline or locally linked CSS. For JSX, Vue or template files, check rendered or exported HTML when it exists; otherwise read the source against step 4 and state that the script was not run. Do not edit the script or drop its findings to get a clean run.

### 3. Confirm every finding

`FAIL` is decidable from source; still open the line and confirm it. `WARN` needs judgement (for example a contrast warning that assumes the page background). Drop a finding only with a one-line reason in the report.

### 4. Manual pass, in this order

The checker cannot see behaviour. Read the source for these, in order, using [references/manual-checks.md](references/manual-checks.md) for the detailed questions and success criteria:

1. Keyboard: every action reachable, operable with Enter or Space, no trap, logical order.
2. Focus: visible on every control, not hidden under sticky or overlay content, moved and returned correctly by dialogs and menus.
3. Scripted widgets: name, role, state, and state changes reflected in attributes. For any dialog, menu, tabs, combobox, accordion, tooltip, carousel, toggle or live message, read the matching section of [references/widget-patterns.md](references/widget-patterns.md).
4. Forms: visible labels, instructions, required state, error text tied to the field and announced.
5. Meaning without sight or colour: structure, reading order, colour-only signals, link purpose.
6. Media and motion: captions, autoplay, pause control, reduced motion.
7. Zoom and reflow: fixed heights and widths that clip at 320 CSS px or 200% text size.
8. Criteria added in WCAG 2.2: 2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8.

### 5. Severity

| Severity | Test |
|---|---|
| Blocker | Some users cannot complete the task at all (unlabelled required field, keyboard trap, control with no keyboard access) |
| Serious | Task is possible but error-prone or very slow (missing error association, lost focus, low contrast body text) |
| Moderate | Friction or confusion, a workaround exists (skipped heading level, vague link text) |
| Minor | Best practice, or level AAA advisory |

### 6. Fix

- Use the native element before ARIA: `button`, `a href`, `label`, `fieldset`, `dialog`, `details`, `select`. A role without the matching keyboard behaviour is a new defect, not a fix.
- An accessible name must contain the visible label text (2.5.3). `placeholder` and `title` are not labels. `aria-label` on a `div` or `span` with no role is ignored.
- Never put `aria-hidden="true"` on, or around, something focusable. Use `inert` or remove it from the tab order.
- Errors: text next to the field, `aria-invalid="true"`, `aria-describedby` pointing at the message; messages injected after load need `role="alert"` or a live region. Colour alone is not an error state.
- Focus styles: keep or replace the outline; the indicator needs 3:1 against adjacent colours. Use `:focus-visible`.
- Do not block paste or password managers on login fields (3.3.8).
- Re-run the checker after fixing. Repeat until there is no `FAIL`.

### 7. Report

Use this format exactly:

```
## Accessibility audit: <scope>
Standard: WCAG 2.2 level AA. Method: static checker (run / not run) and manual source review.
This is not a conformance claim.

### Findings
| # | Severity | SC (level) | Where | Problem and who it blocks | Fix | Found by |
|---|---|---|---|---|---|---|
| 1 | Blocker | 4.1.2 (A) | signup.html line 41, password field | No accessible name; screen reader users hear "edit text" | Add a label tied by for and id | checker |

### Checked, no failure found
<areas from step 4 that were read and passed>

### Not tested
<always: real screen readers, real keyboard run in a browser, rendered contrast over images, user testing; plus anything skipped>

### Totals
<n> blocker, <n> serious, <n> moderate, <n> minor
```

## Rules that prevent wrong findings

- Cite the success criterion number and level for every finding; if no criterion applies, label it "best practice" and rate it Minor.
- 4.1.1 Parsing was removed in WCAG 2.2. Do not cite it. Duplicate ids matter only where they break a label or an ARIA reference (1.3.1, 4.1.2).
- Text contrast: 4.5:1, or 3:1 for text of 24px and larger, or 18.66px and larger when bold (1.4.3). Borders of inputs, icons that carry meaning and focus indicators: 3:1 (1.4.11). Placeholder text is text. Disabled controls and logos are exempt.
- Target size (2.5.8): 24 by 24 CSS px, unless the control has enough spacing, sits inline in a sentence, or an equivalent control exists. 44 by 44 is level AAA and a good default for touch.
- Never write "accessible", "compliant" or "passes WCAG" as a verdict. Write what was checked and that no failures were found in it.

## Limits

- Source review only. Nothing is rendered and no assistive technology is run, so behaviour that depends on JavaScript at runtime is inferred from code, not observed.
- The checker does not resolve the CSS cascade: contrast is measured where one rule sets both colours, or against the page background as a warning.
- Automated checks find a minority of real barriers. A clean run is a floor, not a result.
- This is not legal advice and not a conformance statement (VPAT, EN 301 549, ADA).
