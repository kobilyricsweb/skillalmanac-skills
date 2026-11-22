## Contents

1. Contrast formula and worked example
2. Contrast thresholds by use
3. Logo section checklist
4. Voice trait tests
5. Imagery section checklist
6. Sources

## 1. Contrast formula and worked example

Relative luminance L of a colour (WCAG 2.x definition):

1. Read R, G, B as 0 to 255 and divide each by 255 to get c.
2. For each channel, if c is 0.03928 or less use c / 12.92, otherwise use ((c + 0.055) / 1.055) raised to 2.4.
3. L = 0.2126 * R + 0.7152 * G + 0.0722 * B using the converted channels.

Contrast ratio = (L_lighter + 0.05) / (L_darker + 0.05). Range 1 to 21. Compare the unrounded number to the threshold: 4.499 fails.

Worked example, mid-grey #767676 on white: c = 118/255 = 0.4627; ((0.4627 + 0.055) / 1.055)^2.4 = 0.1812, the same for all three channels, so L = 0.1812. White L = 1. Ratio = 1.05 / 0.2312 = 4.54, a pass. The slightly lighter #777777 gives 4.48, a fail. This is why "light grey text" on white is the most common failure in brand palettes.

## 2. Contrast thresholds by use

| Use | Minimum ratio |
|---|---|
| Body and small text, including text on buttons | 4.5 |
| Large text: 24 px regular, or 18.66 px bold and up (18 pt and 14 pt bold) | 3 |
| Icons, input borders, focus rings that carry meaning, chart lines | 3 against their neighbour |
| Logo on its background | 3 is the working rule in this kit; the logo itself is exempt from WCAG text rules, but an unreadable wordmark is a misuse |
| Disabled controls and pure decoration | no minimum |

A brand colour that fails 4.5 as text on the background can still be used for large headings, fills and rules. Name that restriction in the palette table ("Crust: large text and fills only").

## 3. Logo section checklist

- Files: which formats exist (SVG, PNG with transparency, PDF for print), and which colour versions (full colour, one colour, reversed on dark).
- Clear space: expressed as a multiple of a part of the logo, so it scales. Include a diagram request for the designer.
- Minimum size: print width in millimetres, screen width in pixels, and the compact variant (icon only, stacked) with its own minimum.
- Backgrounds: which logo version goes on which background role. A reversed version is required if the primary colour logo fails 3:1 on dark surfaces.
- Misuse list of at least 8 items, each a single sentence in the form "Do not ..." and each paired with a request to show the bad example next to the good one.
- Co-branding: logo-to-partner-logo spacing is at least one clear-space unit, with a visual weight rule (neither dominates).
- Favicon and social avatar: the compact variant, tested at 16 px and as a circle crop.

## 4. Voice trait tests

A voice trait passes only if all three hold:

1. Opposite test: a real brand could choose the opposite ("formal" versus "casual"). "High quality" fails.
2. Line test: you can write one sentence in the trait and one in its opposite on the user's own subject.
3. Rewrite test: a neutral sentence from the user's real material can be rewritten in the trait and the rewrite is visibly different.

Tone by situation: celebration may use exclamation marks; routine info uses none; bad news states the fact in the first sentence, then the fix, then the apology if one is owed; errors give what happened, what the user can do, and what we are doing; complaint replies name the problem in the user's words before anything else. Banned patterns to list per brand: filler openers ("We are thrilled to announce"), mandatory exclamation marks, jargon the audience does not use, humour in error messages.

## 5. Imagery section checklist

- Photography: subject, setting, lighting, crop, people (real customers, staff, or models), diversity and consent line, colour treatment with a numeric cap on overlay opacity.
- Illustration: allowed or not; line weight and palette (use only palette colours).
- Iconography: one style (outline or filled), grid size such as 24 px, stroke weight, corner radius.
- Do-not list with at least 5 items.
- Accessibility: alt text 125 characters or fewer describing content and purpose; no text baked into images; if text is on an image, put it on a plate or overlay that gives 4.5:1.
- Sourcing: where images come from and who clears usage rights (a name, not "the team").

## 6. Sources

Facts here are public standards restated in the kit's own words.

- WCAG 2.1, success criterion 1.4.3 Contrast (Minimum): 4.5:1 for text, 3:1 for large text. https://www.w3.org/TR/WCAG21/#contrast-minimum
- WCAG 2.1, success criterion 1.4.11 Non-text Contrast: 3:1 for interface components and meaningful graphics. https://www.w3.org/TR/WCAG21/#non-text-contrast
- WCAG 2.1 definitions of relative luminance and contrast ratio (the formula in section 1). https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
- WCAG 2.1 definition of large-scale text (18 point, or 14 point bold). https://www.w3.org/TR/WCAG21/#dfn-large-scale
- Typographic scale ratios named after musical intervals (minor second 1.067, major second 1.125, minor third 1.2, major third 1.25, perfect fourth 1.333, perfect fifth 1.5) are conventional values, not a standard.
