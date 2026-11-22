# Structured data for the Vortiq B7 review

Page: https://www.kitchenbench.example/reviews/vortiq-b7-blender   Subject: Vortiq B7 blender (one editorial review)
Markup: Product (with one Review by Maya Okonkwo), BreadcrumbList
Expected result: Review snippet (stars) for the product, if Google chooses to show it. Breadcrumb trail on desktop results only. FAQ dropdowns: none.
Left out on purpose:
- FAQPage: Google no longer shows FAQ rich results for this kind of site (limited to government and health sites in 2023, no longer shown from 7 May 2026). The three questions stay as visible HTML.
- HowTo for the three cleaning steps: retired since 2023. The steps stay as the visible ordered list.
- Amazon rating (4.8, 2,314 ratings): another site's ratings cannot be marked up.
- The 8.7 score is not in aggregateRating (it is the site's own editorial grade, not an aggregate of user ratings). It is the Review's reviewRating, with bestRating 10, because the page is this one review.
- Offers / price ($179.00): the price was "when tested", not a current offer, and no current shop URL or availability is shown. Add an offer only once the current price and shop link are on the page.
Visible-content check: review score 8.7 of 10, author name, published 14 Oct 2026, updated 9 Nov 2026, review sentence, product name, hero image, breadcrumb names and URLs. All match the page. Checked by hand; the script's text search is not run on the copy below beyond structure.
Script: 0 FAIL, 0 WARN, 0 NOTE on the candidate page (s1_blender_review_with_schema.html in the same folder). The `--page-type list` run fails as expected, because this is a product review, not a list page.
Still to do:
- Replace the datePublished and dateModified times (T00:00:00+00:00) with the CMS's real publish and update timestamps and time zone.
- Run the page through Google's Rich Results Test and the schema.org validator before shipping.
- After release, check the search console's structured-data report for zero invalid items. Expect a delay before any change appears.
- No guarantee of stars: valid markup only makes the page eligible.

## JSON-LD to paste (in the <head>, server-rendered)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Product",
      "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#product",
      "name": "Vortiq B7 blender",
      "image": ["https://www.kitchenbench.example/img/vortiq-b7-hero.jpg"],
      "review": {
        "@type": "Review",
        "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#review",
        "url": "https://www.kitchenbench.example/reviews/vortiq-b7-blender",
        "headline": "Vortiq B7 blender review: six weeks of smoothies and soup",
        "author": {
          "@type": "Person",
          "name": "Maya Okonkwo",
          "url": "https://www.kitchenbench.example/authors/maya-okonkwo"
        },
        "datePublished": "2026-10-14T00:00:00+00:00",
        "dateModified": "2026-11-09T00:00:00+00:00",
        "reviewBody": "The B7 crushes ice evenly and is quieter than its rivals, but the lid is fiddly.",
        "reviewRating": {
          "@type": "Rating",
          "ratingValue": "8.7",
          "bestRating": "10"
        }
      }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#breadcrumb",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.kitchenbench.example/" },
        { "@type": "ListItem", "position": 2, "name": "Reviews", "item": "https://www.kitchenbench.example/reviews" },
        { "@type": "ListItem", "position": 3, "name": "Vortiq B7 blender", "item": "https://www.kitchenbench.example/reviews/vortiq-b7-blender" }
      ]
    }
  ]
}
</script>
```

The complete page with this block inserted is at `<local-path>`. The original page was not changed.
