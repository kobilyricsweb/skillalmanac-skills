## Contents

1. Contrast
2. Trademark search starting points
3. Copyright of machine-made artwork
4. Icon grids
5. SVG viewBox

Each entry states the fact used, in our own words, and the page that backs it. None of these pages was re-fetched while this package was written; re-check them at each re-verification.

## 1. Contrast

- Page: https://www.w3.org/TR/WCAG22/ (success criterion on non-text contrast, 1.4.11).
- Fact used: graphical objects needed to understand content should have at least a 3:1 contrast ratio with adjacent colours. Text that is part of a logo is exempt from the text contrast rule, but we apply 3:1 to the whole logo as a practical floor. The luminance and ratio formulas in construction.md section 6 come from the same document.

## 2. Trademark search starting points

- Page: https://www.uspto.gov/trademarks/search (United States federal trademark search).
- Page: https://www.tmdn.org/tmview/ (TMview, a combined search across the EU and many national offices).
- Page: https://branddb.wipo.int/ (WIPO Global Brand Database, international registrations and many national records).
- Fact used: these are free public databases that let a person check registered and pending marks. A search of them is a first filter, not a clearance: it does not cover unregistered marks in use, similar-sounding or similar-looking marks judged by an examiner, or every country. A trademark attorney judges the risk.

## 3. Copyright of machine-made artwork

- Page: https://www.copyright.gov/ai/ (United States Copyright Office, artificial intelligence and copyright).
- Fact used: in the United States, material generated entirely by an AI tool without sufficient human authorship is not registrable; human selection, arrangement and modification may be. Other countries differ. This is why the skill tells the user to confirm ownership with a lawyer instead of asserting it.

## 4. Icon grids

- Page: https://m2.material.io/design/iconography/system-icons.html
- Fact used: a widely used icon system draws on a 24-unit grid with 2-unit padding and keyline shapes (a square 18 units, a circle 20 units, rectangles 16 by 20 and 20 by 16). The keyline sizes in construction.md section 1 are scaled from these ratios to a 64-unit grid.

## 5. SVG viewBox

- Page: https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/viewBox
- Fact used: the viewBox defines the coordinate system that is scaled to the element size; without it a file does not scale with its container, which is why its absence is a failure in the audit.
