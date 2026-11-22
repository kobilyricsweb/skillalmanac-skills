# Structured data for the "Best standing desks 2026" page

Page: https://www.deskbench.example/best/standing-desks (from s3_category.html)   Subject: the list of five standing desks (ItemList)

## Result: review stars and carousel are not possible for this page

- **Review stars: not eligible.** The existing markup puts `aggregateRating` on the list (ItemList) and on each of the two Product items. The page is a "best of" list, and ratings on a list, category or comparison page are not allowed. The scores on the page ("our score 4.8/5") are the site's own editorial grades, not ratings from users or a named reviewer, so they cannot go in `aggregateRating` either. Adding stars here would breach the rating policy and risk a manual action.
- **Carousel: not eligible.** Carousel (ItemList) rich results are restricted to course, movie, recipe and restaurant pages. A desk list does not qualify.
- **Expected result: none (semantic only).** The corrected markup below makes the list readable to search engines. It does not produce a rich result.

## Markup: replace the existing block

Replace the whole `<script type="application/ld+json">` block in the `<head>` with the block below. This is a fix to a policy violation, not a tidy-up of working markup, so the rating nodes should be removed rather than kept.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "CollectionPage",
      "@id": "https://www.deskbench.example/best/standing-desks#webpage",
      "url": "https://www.deskbench.example/best/standing-desks",
      "name": "Best standing desks 2026: 5 tested picks",
      "mainEntity": {
        "@id": "https://www.deskbench.example/best/standing-desks#list"
      }
    },
    {
      "@type": "ItemList",
      "@id": "https://www.deskbench.example/best/standing-desks#list",
      "name": "Best standing desks 2026",
      "numberOfItems": 5,
      "itemListOrder": "https://schema.org/ItemListOrderAscending",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Altura Pro",
          "url": "https://www.deskbench.example/reviews/altura-pro"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "Stanza 2",
          "url": "https://www.deskbench.example/reviews/stanza-2"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": "Liftline S",
          "url": "https://www.deskbench.example/reviews/liftline-s"
        },
        {
          "@type": "ListItem",
          "position": 4,
          "name": "Korda Frame",
          "url": "https://www.deskbench.example/reviews/korda-frame"
        },
        {
          "@type": "ListItem",
          "position": 5,
          "name": "Pillar Mini",
          "url": "https://www.deskbench.example/reviews/pillar-mini"
        }
      ]
    }
  ]
}
```

Notes on the block:
- The five list items and the count of 5 match the visible numbered list. The positions run 1 to 5 in the visible order.
- The "our score" figures (4.8, 4.6, 4.5, 4.3, 4.2) stay as visible text in the list and are not marked up.
- The byline ("By Jonas Feld") and the updated date ("3 November 2026") are visible, but the page does not show a first-publication date, so no Article markup is emitted.

## Visible-content check

- Values compared: five item names, five URLs in the list, the list count (5), and the page title and heading.
- Result: all names and the count appear in the visible text. The URLs are the same links as in the visible list.
- Script: `jsonld_check.py --page-type list` on the existing page gave 3 FAIL (LIST-RATING on the ItemList and both Products) and 2 WARN (reviewCount values not visible). Run on the corrected markup, a copy of the page with the new block, it gave **0 FAIL, 0 WARN, 0 NOTE**.

## Left out on purpose

- **Review stars (aggregateRating on ItemList or Product):** not allowed on a list page, and the scores are the site's own editorial grades rather than user ratings.
- **Carousel (ItemList carousel rich result):** the carousel rich result is restricted to course, movie, recipe and restaurant pages.
- **Article markup:** the page has no visible first-publication date; adding it would need a date the page does not show.

## Next step that could earn stars (not done here)

Each desk has its own review page (for example /reviews/altura-pro). If one of those pages is a single-product editorial review by a named author, with a reviewRating given by that author, it can carry Product with one Review, which is eligible for review snippets. This is not done in this task: those pages were not provided, and their content and reviewer must be checked first. The rating on each review page must come from the named reviewer, not from the list.

## Still to do (by the site owner)

- Run the corrected page or its JSON-LD through the search engine's public rich-result tester and the schema.org validator before shipping. These checks were not run here: there is no web access.
- After release, watch the structured-data reports in the search console for errors.
- Decide whether the ItemList should stay on the page at all, since it has no rich result of its own. It is harmless and helps readers, so leaving it in is reasonable.
- Confirm that the visible scores and the byline are the real facts for the page. The check does not verify that.

Hand-over summary:
```
Page: https://www.deskbench.example/best/standing-desks   Subject: list of five standing desks
Markup: CollectionPage + ItemList (5 ListItems, no ratings)
Expected result: none (semantic only). Review stars not eligible; carousel restricted to course, movie, recipe, restaurant pages.
Left out on purpose: aggregateRating on list and Products (list-page rating policy; editorial scores are not user ratings); carousel (restricted type)
Visible-content check: 5 names, 5 URLs, count 5 compared; all visible
Script: existing page 3 FAIL, 2 WARN; corrected markup 0 FAIL, 0 WARN, 0 NOTE
Still to do: official rich-result test and schema.org validator; console report after release; per-desk review pages if stars are wanted
```
