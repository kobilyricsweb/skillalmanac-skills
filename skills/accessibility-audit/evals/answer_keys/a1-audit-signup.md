# Answer key: signup.html (22 seeded defects)

S = the bundled static checker can see it. B = needs reading behaviour or meaning.

1. S  html has no lang (3.1.1 A)
2. S  viewport blocks zoom: maximum-scale=1, user-scalable=no (1.4.4 AA)
3. S  logo image has no alt, so the home link has no name (1.1.1 A / 2.4.4 A)
4. S  Full name field has no programmatic label (text in a span) (1.3.1 / 4.1.2 / 3.3.2 A)
5. S  Email field labelled only by placeholder (3.3.2 A / 4.1.2 A)
6. S  Positive tabindex 1 and 2 (2.4.3 A)
7. B  Email error: text "Invalid" does not say what is wrong or how to fix; not tied to the field (no aria-invalid / aria-describedby); error shown by red border (3.3.1 A, 3.3.3 AA, 1.4.1 A)
8. B  Required fields indicated by red colour / asterisk only: "Fields marked in red are required" (1.4.1 A, 1.3.3 A, 3.3.2 A); no required attribute
9. S  Email and phone and name lack autocomplete tokens (1.3.5 AA); email uses type=text
10. S  Password: aria-labelledby points at id pw-label that does not exist, so no label (1.3.1 / 4.1.2 A)
11. B/S Password blocks paste (onpaste return false) and autocomplete=off (3.3.8 AA)
12. S  Show-password icon button has no accessible name (4.1.2 A)
13. S  Show-password button is 18x18px (2.5.8 AA)
14. B  Password strength meter: colour and width only, no text, not announced (1.4.1 A, 4.1.3 AA, 1.1.1)
15. S  Plan radio buttons not grouped: no fieldset/legend (1.3.1 A)
16. B  CAPTCHA: image-only test with alt "captcha", no alternative method (1.1.1 A, 3.3.8 AA)
17. S  Terms checkbox is a div with onclick: no role, state or keyboard access, no label association (2.1.1 A, 4.1.2 A)
18. S  "Click here" link text (2.4.4 A)
19. S  Submit is an anchor without href: not keyboard focusable (2.1.1 A, 4.1.2 A)
20. S  Contrast: button white on #5fa8ff about 2.5:1; hint #9a9a9a on white about 2.8:1 (1.4.3 AA). Either counts
21. S  Focus outline removed on inputs, selects, links with no replacement (2.4.7 AA)
22. B  Timed redirect after 2 minutes with no warning or extension (2.2.1 A)

Also valid (bonus, not counted): heading skip h1 to h3 (1.3.1); sticky header may hide focused element, no scroll-padding (2.4.11 AA); no main landmark (2.4.1); input border #ccc under 3:1 (1.4.11); meter/err not live.
False claims to penalise: missing page title (there is one); missing charset; claims about images that do not exist; saying the Phone field has no label (it has one).
