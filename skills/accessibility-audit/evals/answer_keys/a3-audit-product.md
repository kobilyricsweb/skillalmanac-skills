# Answer key: product.html (20 seeded defects)

S = the bundled static checker can see it. B = needs reading behaviour or meaning.

1. B  Carousel auto-rotates every 3 seconds with no pause or stop control (2.2.2 A)
2. S  Carousel arrows are spans with onclick: no role, name or keyboard access (2.1.1 A, 4.1.2 A)
3. B  Carousel dots: spans with onclick, no names, 10x10px (2.1.1, 4.1.2, 2.5.8 AA)
4. S  First slide alt is the file name "tote-front.jpg" (1.1.1 A)
5. S  Product title is a div, no h1; section titles are divs, so no heading structure (1.3.1 A, 2.4.6 AA)
6. B  French sentence not marked with lang="fr" (3.1.2 AA)
7. S  SALE badge white on #ff9a3c about 2.2:1 (1.4.3 AA)
8. B  Old and new price distinguished only by strikethrough and colour; screen readers hear "$80 $60" (1.3.1 A, 1.4.1 A)
9. B  Star rating image has empty alt, so the rating is not available as text (1.1.1 A)
10. S  "Read more" links, three of them, same text different targets (2.4.4 A)
11. S  Colour swatches: divs with onclick, no names, no keyboard access (2.1.1, 4.1.2, 1.1.1)
12. B  Selected swatch shown only by a border; state not exposed (4.1.2 A, 1.4.1 A)
13. S  Quantity plus and minus buttons have no accessible names (4.1.2 A) and are 20x20px (2.5.8 AA)
14. S  Duplicate label for="qty" (a hidden second label) / id reference problem; and the buttons default to type submit is not an issue here. Count the duplicate or conflicting label if reported, otherwise ignore this item
15. S  Shipping info tooltip appears on mouse hover only; trigger not focusable (2.1.1 A, 1.4.13 AA)
16. S  Video autoplays with sound, loops, has no controls and no captions (1.4.2 A, 2.2.2 A, 1.2.2 A)
17. S  Size guide table has no header cells (1.3.1 A)
18. S  iframe has no title (4.1.2 A)
19. S  Wishlist reorder is drag only, no keyboard or single-pointer alternative (2.5.7 AA, 2.1.1 A)
20. B  Cart count changes on Add to cart with no live region (4.1.3 AA)

Also valid (bonus, not counted): focus outline removed globally (2.4.7 AA) [this one is important; count it as a 21st if found]; fixed bottom bar can cover focused elements (2.4.11 AA); no main landmark / skip link (2.4.1); breadcrumb not in nav.
False claims to penalise: missing lang or title on the page (both exist); missing alt on slides 2 and 3; saying quantity input has no label.
