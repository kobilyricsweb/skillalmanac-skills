# Sources for the numeric rules

Facts behind the thresholds, in the skill author's own words. Pages were not re-fetched while writing this skill; the figures are well-known public standards. Check the pages when a figure matters.

- Text contrast of 4.5:1, or 3:1 for large text, and 3:1 for interface components: WCAG 2.2, success criteria 1.4.3 and 1.4.11. Large text means 24 CSS px, or about 18.66 px when bold. https://www.w3.org/TR/WCAG22/
- A visible keyboard focus indicator: WCAG 2.2, criterion 2.4.7; a minimum pointer target of 24 by 24 CSS px: criterion 2.5.8. https://www.w3.org/TR/WCAG22/
- Pinch zoom must not be blocked: WCAG 1.4.4 (resize text) and the viewport guidance in MDN. https://developer.mozilla.org/en-US/docs/Web/HTML/Viewport_meta_tag
- Relative luminance and contrast ratio formulas are defined in WCAG 2.2 under "relative luminance" and "contrast ratio". The script implements them.
- Touch targets of about 44 points (Apple) or 48 dp (Material) are the common platform guidance; the skill uses 44 as the target and 40 as the warning line. https://developer.apple.com/design/human-interface-guidelines/
- The `ch` unit, used for line length, is the width of the "0" glyph in the current font. https://developer.mozilla.org/en-US/docs/Web/CSS/length
- Reduced motion: the `prefers-reduced-motion` media feature. https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion
- The 4px spacing unit, the 1.25 type ratio and the 45 to 75 character line length are widespread design-system conventions, not standards; the script treats them as working values.
