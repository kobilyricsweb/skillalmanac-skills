# Schema for the Vortiq B7 review page

## Short answer

Add the JSON-LD below to the `<head>` of `s1_blender_review.html`. It describes the page as a Review of the Vortiq B7 blender, with the 8.7/10 editorial score and the author, dates and breadcrumb trail that are already visible on the page.

What to expect: the review page can become eligible for **review stars** in results. **FAQ dropdowns will not appear**, because Google limits FAQ rich results to well-known government and health sites. The FAQ and cleaning steps on this page do not need markup for anything Google will show.

## JSON-LD to paste

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Review",
      "@id": "https://www.kitchenbench.example/reviews/vortiq-b7-blender#review",
      "url": "https://www.kitchenbench.example/reviews/vortiq-b7-blender",
      "name": "Vortiq B7 blender review: six weeks of smoothies and soup",
      "description": "We used the Vortiq B7 blender daily for six weeks. Our verdict, test results, noise measurements and who should buy it.",
      "datePublished": "2026-10-14",
      "dateModified": "2026-11-09",
      "image": "https://www.kitchenbench.example/img/vortiq-b7-hero.jpg",
      "author": {
        "@type": "Person",
        "name": "Maya Okonkwo",
        "url": "https://www.kitchenbench.example/authors/maya-okonkwo"
      },
      "publisher": {
        "@type": "Organization",
        "name": "KitchenBench",
        "url": "https://www.kitchenbench.example/"
      },
      "itemReviewed": {
        "@type": "Product",
        "name": "Vortiq B7 blender",
        "brand": {
          "@type": "Brand",
          "name": "Vortiq"
        },
        "image": "https://www.kitchenbench.example/img/vortiq-b7-hero.jpg"
      },
      "reviewRating": {
        "@type": "Rating",
        "ratingValue": "8.7",
        "bestRating": "10",
        "worstRating": "1"
      }
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Home",
          "item": "https://www.kitchenbench.example/"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "Reviews",
          "item": "https://www.kitchenbench.example/reviews"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": "Vortiq B7 blender"
        }
      ]
    }
  ]
}
</script>
```

Notes on the markup:

- **Review rating:** the 8.7 score is the editorial score shown on the page ("Our score: 8.7 out of 10"), so it is the `reviewRating`. The visible text matches the markup, which Google requires.
- **Amazon rating left out on purpose:** the "4.8 stars on Amazon (2,314 ratings)" line is a third-party rating. Do not mark it up as `aggregateRating`. Google expects ratings collected on the marked-up site itself, and marking up another site's ratings risks the markup being ignored or the page being flagged.
- **No `offers`:** the $179 price is "price when tested" and may be out of date. Add an Offer only if you can keep the price current.
- **No FAQPage or HowTo markup:** see below.

## What to expect

1. **Review stars: possible, not guaranteed.** Google decides whether to show stars. Expect a delay of days to weeks after the page is recrawled. Check the Rich Results Test and the Review snippets report in Search Console after deployment.
2. **FAQ dropdowns: will not appear.** Google restricted FAQ rich results to well-known, authoritative government and health websites in August 2023. A kitchen review site does not qualify. The FAQ section is still useful to readers; it just will not produce a dropdown.
3. **Cleaning steps: no rich result.** HowTo rich results were removed from Google Search in 2023, so the three-step cleaning list does not need markup for a display benefit.
4. **Breadcrumbs: may show in results** as the path under the URL. Google chooses when to display them.
5. **Self-review rule:** Google's review-snippet policy excludes reviews written by the business selling the product. This page is an independent review, so it should qualify, provided the reviewer is not the manufacturer or the seller. If the site earns affiliate commissions, that does not disqualify it, but the review must be genuine.

## Checks before publishing

- Validate with the Schema Markup Validator and the Rich Results Test after deployment.
- Confirm the publisher name. "KitchenBench" is inferred from the domain `kitchenbench.example`, not from anything on the page. Change it if the brand name differs.
- Confirm `datePublished` (2026-10-14) and `dateModified` (2026-11-09) against the CMS.
- Confirm the hero image URL loads publicly.

## Limits of this review

- No web access was available, so I could not check Google's current documentation or the live page. The eligibility points above come from my knowledge, which may be out of date. Confirm the rich-result rules in Google's Search Central documentation before relying on them.
- I did not test the markup against a validator.
