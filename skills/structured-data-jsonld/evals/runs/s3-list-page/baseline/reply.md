# JSON-LD for the "Best standing desks 2026" page

Paste this into the `<head>` in place of the existing `<script type="application/ld+json">` block. The page's visible text already contains each score ("our score 4.8/5") and the byline (By Jonas Feld), so every value below is backed by the page.

```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Best standing desks 2026: 5 tested picks",
  "url": "https://www.deskbench.example/best/standing-desks",
  "dateModified": "2026-11-03",
  "numberOfItems": 5,
  "itemListOrder": "https://schema.org/ItemListOrderDescending",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "url": "https://www.deskbench.example/reviews/altura-pro",
      "item": {
        "@type": "Product",
        "name": "Altura Pro",
        "url": "https://www.deskbench.example/reviews/altura-pro",
        "review": {
          "@type": "Review",
          "author": {"@type": "Person", "name": "Jonas Feld"},
          "publisher": {"@type": "Organization", "name": "DeskBench", "url": "https://www.deskbench.example"},
          "reviewRating": {"@type": "Rating", "ratingValue": "4.8", "bestRating": "5", "worstRating": "1"},
          "name": "Altura Pro review",
          "reviewBody": "Most stable at full height."
        }
      }
    },
    {
      "@type": "ListItem",
      "position": 2,
      "url": "https://www.deskbench.example/reviews/stanza-2",
      "item": {
        "@type": "Product",
        "name": "Stanza 2",
        "url": "https://www.deskbench.example/reviews/stanza-2",
        "review": {
          "@type": "Review",
          "author": {"@type": "Person", "name": "Jonas Feld"},
          "publisher": {"@type": "Organization", "name": "DeskBench", "url": "https://www.deskbench.example"},
          "reviewRating": {"@type": "Rating", "ratingValue": "4.6", "bestRating": "5", "worstRating": "1"},
          "name": "Stanza 2 review",
          "reviewBody": "Best value."
        }
      }
    },
    {
      "@type": "ListItem",
      "position": 3,
      "url": "https://www.deskbench.example/reviews/liftline-s",
      "item": {
        "@type": "Product",
        "name": "Liftline S",
        "url": "https://www.deskbench.example/reviews/liftline-s",
        "review": {
          "@type": "Review",
          "author": {"@type": "Person", "name": "Jonas Feld"},
          "publisher": {"@type": "Organization", "name": "DeskBench", "url": "https://www.deskbench.example"},
          "reviewRating": {"@type": "Rating", "ratingValue": "4.5", "bestRating": "5", "worstRating": "1"},
          "name": "Liftline S review",
          "reviewBody": "Quietest motor."
        }
      }
    },
    {
      "@type": "ListItem",
      "position": 4,
      "url": "https://www.deskbench.example/reviews/korda-frame",
      "item": {
        "@type": "Product",
        "name": "Korda Frame",
        "url": "https://www.deskbench.example/reviews/korda-frame",
        "review": {
          "@type": "Review",
          "author": {"@type": "Person", "name": "Jonas Feld"},
          "publisher": {"@type": "Organization", "name": "DeskBench", "url": "https://www.deskbench.example"},
          "reviewRating": {"@type": "Rating", "ratingValue": "4.3", "bestRating": "5", "worstRating": "1"},
          "name": "Korda Frame review",
          "reviewBody": "Best frame-only kit."
        }
      }
    },
    {
      "@type": "ListItem",
      "position": 5,
      "url": "https://www.deskbench.example/reviews/pillar-mini",
      "item": {
        "@type": "Product",
        "name": "Pillar Mini",
        "url": "https://www.deskbench.example/reviews/pillar-mini",
        "review": {
          "@type": "Review",
          "author": {"@type": "Person", "name": "Jonas Feld"},
          "publisher": {"@type": "Organization", "name": "DeskBench", "url": "https://www.deskbench.example"},
          "reviewRating": {"@type": "Rating", "ratingValue": "4.2", "bestRating": "5", "worstRating": "1"},
          "name": "Pillar Mini review",
          "reviewBody": "Best for small rooms."
        }
      }
    }
  ]
}
```

## What changed and why

1. **Removed the page-level and per-product `aggregateRating`.** The old block set `reviewCount` to 5 on the list and to 1 on each product. Those numbers are not user ratings; they are DeskBench's own editorial scores. Google does not allow star ratings that the publisher invents or that are not based on real ratings, so this markup would put the page at risk of a manual action and would not earn stars.
2. **Replaced them with a `Review` per product.** The scores are a critic's review of third-party desks, which is the case the Review snippet is built for. The `Review` names the product in `item.review` and carries `reviewRating` with `bestRating` 5, so Google can show stars.
3. **Kept `ItemList` as the outer structure** with `position` and `url` on each `ListItem`, which is what list and carousel features read.
4. **Added `dateModified` (2026-11-03)** from "Updated 3 November 2026". I did not add `datePublished` because the page does not give one.

## Things you need to check or decide

- **Carousel is not guaranteed.** I could not check Google's current carousel rules (no web access in this task). Google's carousel features cover specific content types, and I do not know of one for "best of" product lists. Treat the ItemList markup as necessary but not sufficient.
- **`worstRating` is an assumption.** The page does not state a scale floor. I used 1; change it if your scale differs.
- **`reviewBody` uses the one-line verdicts from the page.** These are short. Google prefers a full review text, so consider writing a longer `reviewBody` from the review pages (`/reviews/...`) if they are on the same scale.
- **Product images are missing.** Google's Product snippet expects an `image`. I did not invent URLs. Add one per product, using a real image that appears on the page.
- **Product `review` on the same page as the list.** Google's guidelines are strict about a Review being about the main entity of the page. This page is a list of five items, so check the result in the Rich Results Test. If the test rejects it, the fallback is to put each Review on its own `/reviews/<slug>` page and keep only the ItemList here.
- **Validate before shipping.** I could not run the Rich Results Test or Schema Markup Validator here. The JSON was parsed locally to confirm it is valid JSON.
- **Visible-content match.** Each rating in the markup matches the score shown in the page's list ("our score X/5"). Keep them in sync if scores change.
