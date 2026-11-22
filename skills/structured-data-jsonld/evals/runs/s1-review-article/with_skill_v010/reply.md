# Structured data for the Vortiq B7 review

Page: https://www.kitchenbench.example/reviews/vortiq-b7-blender (from s1_blender_review.html)   Subject: Vortiq B7 blender (reviewed by Maya Okonkwo)
Markup: Article (with WebPage, Person author, Thing for the subject), BreadcrumbList
Expected result: no star rating and no FAQ dropdowns. The page can earn Article enhancements (headline, image, dates, author in Google's article features) and the breadcrumb trail on desktop results. Valid markup makes the page eligible; it does not guarantee either.
Left out on purpose:
- Stars (Review or Product with reviewRating or aggregateRating): the only score on the page is the site's own editorial score, 8.7 out of 10. The skill's rules do not allow an editorial score in markup, and the review-snippet rules want user ratings or a named reviewer's rating. The 4.8 Amazon score (2,314 ratings) is another site's rating and is never marked up. Both stay as visible text.
- FAQPage: retired. Google stopped showing FAQ results from 7 May 2026 and removed the documentation on 15 June 2026. The three questions stay as visible headings and paragraphs.
- HowTo for the three cleaning steps: retired since September 2023. The numbered list stays as HTML.
- Product with offers: the $179.00 is a price "when tested", not a current offer, so it is not marked up as an offer.
- Publisher: the page shows no organisation name, so no publisher node is emitted. Add the site's Organization node on the home page if you want one.

Decision for you: the skill's decision table lists "editorial review of one product" as Review snippet, which needs a reviewRating. The skill's own ground rules forbid marking up an editorial score, so I followed the ground rules and emitted no stars. If you want stars, the two routes are (a) add a visible section of first-party user ratings with a count and mark up a Product with aggregateRating from those, or (b) decide that the editorial score may go into a Review's reviewRating. Option (b) breaks the skill's policy and is your call, not mine.

Visible-content check: headline, hero image URL, published date (14 October 2026), updated date (9 November 2026), author name and URL, and the breadcrumb names and URLs were compared against the page. All match. Dates have no time zone on the page; I used 00:00:00+00:00 as a placeholder, so confirm the times before shipping.
Script: jsonld_check.py on the test copy (s1_blender_review_with_jsonld.html): 0 FAIL, 0 WARN, 0 NOTE. On the original page: no JSON-LD block found (1 NOTE).
Still to do: run the page through Google's rich-result test and the schema.org validator before shipping (not run here; no web access). Watch the structured-data reports in Search Console after release. Consider adding the visible site name and the Organization node on the home page.

## JSON-LD to paste (in the page head, server-rendered)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebPage",
      "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#webpage",
      "url": "https://www.kitchenbench.example/reviews/vortiq-b7-blender",
      "name": "Vortiq B7 blender review: six weeks of smoothies and soup",
      "breadcrumb": { "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#breadcrumb" },
      "mainEntity": { "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#article" }
    },
    {
      "@type": "Article",
      "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#article",
      "headline": "Vortiq B7 blender review: six weeks of smoothies and soup",
      "image": ["https://www.kitchenbench.example/img/vortiq-b7-hero.jpg"],
      "datePublished": "2026-10-14T00:00:00+00:00",
      "dateModified": "2026-11-09T00:00:00+00:00",
      "author": {
        "@type": "Person",
        "name": "Maya Okonkwo",
        "url": "https://www.kitchenbench.example/authors/maya-okonkwo"
      },
      "about": { "@type": "Thing", "name": "Vortiq B7 blender" },
      "mainEntityOfPage": { "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#webpage" }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#breadcrumb",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.kitchenbench.example/" },
        { "@type": "ListItem", "position": 2, "name": "Reviews", "item": "https://www.kitchenbench.example/reviews" },
        { "@type": "ListItem", "position": 3, "name": "Vortiq B7 blender" }
      ]
    }
  ]
}
</script>
```
