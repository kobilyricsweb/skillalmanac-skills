# Answer key: plan card (values from design/plan-card.json)

Card: vertical flex, gap 24px (--space-6), padding 32px (--space-8), background #ffffff (--color-surface), border 1px solid #d9d7d1 (--color-border), stroke INSIDE (no size growth),
radius 12px (--radius-lg), shadow 0 8px 24px 0 rgba(28,27,25,0.08) (--shadow-card). Frame is 360 wide: must become max-width (or parent-controlled), not a fixed width.
Badge: hug width, padding 4px 12px, pill radius (--radius-pill), background #e6f0fb (--color-accent-subtle); text "Most popular" 12px / 16px line (1.333), weight 600, letter-spacing 0.48px = 0.04em, uppercase via CSS, colour #0b5cad (--color-accent). Badge must not stretch full width (align-items flex-start on the card).
Header: vertical, gap 6px (OFF-TOKEN: between --space-1 4px and --space-2 8px) : must be reported with the decision. "Pro" 20px / 28px (1.4), 600, --color-text.
Price row: horizontal, gap 4px, align-items BASELINE. "$29" 48px / 56px (1.167), 700, letter-spacing -0.96px = -0.02em. "/ month" 16px / 24px, 400, colour #5d5b57 (OFF-TOKEN: nearest --color-text-muted #5c5a56) : must be reported.
"Old price $39" is a hidden layer: must NOT be rendered.
Divider: 1px high, full width, #d9d7d1 (--color-border).
Features: vertical gap 12px (--space-3), full width; each row horizontal gap 12px, align centre; icon 20x20 (existing .icon class), not shrinking; text 16px / 24px --color-text, fills the row. Texts: "Unlimited projects", "Priority support within 4 hours", "Export to CSV and PDF". Should be a list.
Button: INSTANCE of Button, Variant=Primary, Size=Large, full width, label "Start 14-day trial". Must reuse .btn .btn--primary .btn--lg .btn--block from components.css (which already gives padding 14px 24px, radius 8px, 16px/600). Restyling the button locally is a defect.
Tokens: semantic tokens (--color-*, --space-*, --radius-*, --font-size-*, --shadow-card, --font-sans); palette tokens (--palette-*) and raw hex in the card CSS are defects.
Notes must mention: the two off-token values and what was done; hidden layer skipped; states not in the design (hover/focus come from .btn); icon asset needed.
