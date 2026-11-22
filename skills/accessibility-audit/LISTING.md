## תקציר

- תוכן עמוד ה-skill: ביקורת נגישות לפי WCAG 2.2 ברמות A ו-AA, עם בודק סטטי מצורף ומעבר ידני בסדר קבוע.
- אין שימוש ברשת; ה-script קורא קבצי HTML ו-CSS מקומיים בלבד.
- הראיות הן מריצה אחת לכל תא, מודל אחד (haiku), כלי אחד. טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: accessibility-audit

**One line:** Audit a page or component against WCAG 2.2 A and AA with a static checker plus a fixed manual pass, and fix what is found.

## What it does

The skill gives an agent a seven-step audit: set scope, run `a11y_static_check.py` on the HTML, confirm each finding in source, do a manual pass in a fixed order (keyboard, focus, scripted widgets, forms, meaning without colour, media, reflow, the six criteria added in WCAG 2.2), rate severity by who is blocked, fix with native elements first, and report in a fixed table that names the success criterion and what was not tested. Two reference files hold the manual questions and the contract for each scripted widget (dialog, menu, tabs, combobox, tooltip, live messages, carousel, switch, drag list).

## Capabilities

- `a11y_static_check.py`: about 45 static checks mapped to success criteria (names of fields, buttons and links, broken ARIA references and misspelt ARIA attributes, invalid roles, focusable content under aria-hidden, zoom blocking, blocked paste on password fields, positive tabindex, table headers, media autoplay and captions, text contrast where one rule sets both colours, removed focus outlines, target size, sticky bars without scroll padding).
- A manual checklist ordered by impact, with the criterion for each question.
- Widget contracts: what a custom dialog, menu, tabs, combobox, tooltip, toast, carousel, switch and sortable list must do.
- A fixed report: finding, severity, criterion and level, location, who is blocked, fix, found by checker or by reading; plus what was not tested.

## When to use

Accessibility or a11y audits; WCAG, ADA or Section 508 checks; making a form, modal, menu or component work with keyboard and screen reader.

## When not to use

Visual redesign, SEO audits, performance work, PDF accessibility, legal conformance statements (VPAT).

## Requirements

Python 3.9+ for the script (standard library only). No network access. Without Python the written workflow still applies and the script step is reported as not run.

## Install

To be generated at publication: one pinned command per tool, writing to `.agents/skills/accessibility-audit/` and `.claude/skills/accessibility-audit/`.

## Examples (from saved eval runs)

1. Prompt: "Audit signup.html for accessibility against WCAG 2.2 level AA..." Saved output: `evals/runs/a1-audit-signup/with_skill/audit.md` (30 findings; the blind grader marked all 22 seeded defects found and preferred it to the baseline for more accurate criterion citations).
2. Prompt: "Make settings.html accessible for keyboard and screen reader users. Keep the look and the behaviour..." Saved output: `evals/runs/a2-fix-settings/with_skill/settings.fixed.html` (checker went from 9 FAIL to 0 FAIL; the blind grader preferred the baseline here because the skill run replaced the custom theme list with a native select, which changed the look).

## Limits

- Source review only: nothing is rendered and no assistive technology is run.
- The checker does not resolve the CSS cascade; contrast is measured where one rule sets both colours, or against the page background as a warning.
- Automated checks find a minority of real barriers; a clean run is a floor.
- Not legal advice and not a conformance statement.
- When asked to keep the look, the skill's preference for native elements can change the appearance (seen in eval a2).

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one small model, Claude Code only; a blind grader preferred the with-skill output in 2 of 3 (a2 lost to baseline). Not tested: any other tool, native triggering, human review.

## Demo script (60 to 90 seconds)

1. Show signup.html and the prompt "audit this for WCAG 2.2 AA".
2. The agent runs the checker: 16 FAIL, 9 WARN on the saved run; it opens each line to confirm.
3. The manual pass adds what the script cannot see: the two-minute redirect, the colour-only strength meter, the image-only CAPTCHA.
4. Close on the report table and its "Not tested" section.

## FAQ seeds

- Does it need internet access? No.
- Does a clean run mean the page is WCAG compliant? No. The skill forbids that claim; it reports what was checked.
- Does it work on React or Vue files? The manual pass does; the checker needs rendered or exported HTML.
- Which WCAG version? 2.2, levels A and AA, including the six criteria added in 2.2.
- How is it different from a browser extension scanner? It adds a manual pass and widget contracts, and it can fix the code. No comparison run has been done.
- Which tools is it verified on? Claude Code only so far.
- What data leaves my machine? None.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
