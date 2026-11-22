# Answer key: hero (values from design/hero.json)

Differences Desktop (1440) -> Mobile (375), each must be implemented:
1. Direction: row -> column
2. Cross-axis alignment: center -> flex-start (stretch children)
3. Gap between copy and media: 64px (--space-16) -> 32px (--space-8)
4. Padding: 96px 120px -> 48px 20px (--space-24 / 120px is OFF-TOKEN, must be reported; --space-12 / --space-5)
5. Copy block gap: 24px -> 16px
6. Headline: 56px / 64px (1.143) -> 36px / 44px (1.222); letter-spacing -0.02em at both sizes; weight 700
7. Body: 18px / 28px (1.556) -> 16px / 24px (1.5); colour #5c5a56 (--color-text-muted)
8. Actions: row gap 16px -> column gap 12px, full width
9. Buttons: hug -> full width (.btn--block or equivalent)
10. Media: fixed 520x400 -> full width, height 240px; radius 16px (--radius-xl) both; image fill = cover, clipped
Shared: background #f7f6f3 (--color-bg-page); eyebrow "Field service software" 14px / 20px, 600, letter-spacing 0.56px = 0.04em, uppercase via CSS, colour --color-accent; headline "Dispatch the right technician the first time"; buttons "Book a demo" (primary, large) and "See pricing" (secondary, large) reusing .btn classes.
Responsiveness: no fixed 1440 or 375 width; content max-width or fluid; copy flexes (flex 1, min-width 0) beside the 520px media; a stated breakpoint chosen where the row stops fitting (roughly 768 to 1024px), not at 1440 or 375.
Semantics: section, h1 or h2 for the headline, img with alt (not a background) or a justified background with text alternative; links or buttons for actions.
Notes must mention: the off-token 120px; breakpoint choice; what is unspecified (tablet layout, wider than 1440, image asset and alt text, hover/focus from .btn).
