# Answer key: text field (values from design/text-field.json)

Structure: label above input, gap 6px (OFF-TOKEN, between 4 and 8: must be reported), then hint or message, gap 6px. Component width fluid (320 is the artboard).
Label: 14px / 20px (1.429), weight 500, --color-text (#1c1b19); disabled: #72706b (--color-text-placeholder / neutral-500).
Input: height 44px (min-height acceptable), padding 10px 12px (10px is OFF-TOKEN: keeping 10px to reach 44px is the right call and must be stated), radius 8px (--radius-md), background #ffffff (--color-surface), text 16px / 24px.
Default: border 1px solid #72706b (--color-border-control); placeholder/value colour #72706b (--color-text-placeholder).
Focus: border 2px solid #0b5cad (--color-accent) plus ring 0 0 0 3px rgba(11,92,173,0.25); text #1c1b19. Must not shift layout versus the 1px state (use outline/box-shadow for the extra pixel, or compensate padding).
Error: border 1px solid #b42318 (--color-border-danger); message row: 16px alert icon + text, gap 6px, 14px / 20px, colour #b42318 (--color-text-danger): "Enter a full email address, for example dana@northwind.io". Replaces the hint.
Disabled: background #f7f6f3 (--color-surface-disabled), border #d9d7d1 (--color-border), text #72706b.
Hint: "We only use this for sign-in links." 14px / 20px, #5c5a56 (--color-text-muted).
State mapping: Focus -> :focus-visible or :focus; Error -> [aria-invalid="true"] (or equivalent attribute) with aria-describedby to the message; Disabled -> :disabled. Classes that must be toggled by hand as the only mechanism are a defect.
Accessibility: label for/id; hint tied by aria-describedby; error icon decorative or named; type=email and autocomplete are a plus.
Notes must mention: off-token 6px and 10px decisions; states not drawn (hover, placeholder vs value, read-only, focus+error together); icon asset.
