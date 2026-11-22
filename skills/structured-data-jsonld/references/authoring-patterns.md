# JSON-LD authoring patterns

Read the section for the types being written. Examples use `https://www.example.com`.

## Contents

1. Graph skeleton and ids
2. Required and recommended properties by type
3. Worked example: product page with first-party reviews
4. Worked example: article with breadcrumb
5. Checks to wire into a build

## 1. Graph skeleton and ids

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "WebPage", "@id": "https://www.example.com/guides/x#webpage",
      "url": "https://www.example.com/guides/x", "name": "Page title",
      "isPartOf": { "@id": "https://www.example.com/#website" },
      "breadcrumb": { "@id": "https://www.example.com/guides/x#breadcrumb" },
      "mainEntity": { "@id": "https://www.example.com/guides/x#article" } },
    { "@type": "BreadcrumbList", "@id": "https://www.example.com/guides/x#breadcrumb", "itemListElement": [] },
    { "@type": "Article", "@id": "https://www.example.com/guides/x#article" }
  ]
}
```

| Entity | `@id` pattern |
|---|---|
| Organization | `{home}#organization` |
| WebSite | `{home}#website` |
| WebPage | `{canonical}#webpage` |
| BreadcrumbList | `{canonical}#breadcrumb` |
| Main entity | `{canonical}#article`, `#product`, `#software`, `#video`, `#question` |
| Person | `{profile URL}#person` |

- Full Organization and WebSite nodes live on the home page. Other pages refer to them with `@id` only, or `@id` plus `name` and `url`.
- A node is described fully on its own canonical page and referenced elsewhere.
- Reviews are nested under the item they review, so `itemReviewed` is not repeated.
- Ids never change when the title changes. Use the canonical URL, not a session or tracking URL.

## 2. Required and recommended properties by type

| Type | Required | Recommended |
|---|---|---|
| Article family | none | `headline`, `image` (several ratios), `datePublished`, `dateModified`, `author` with `name` and `url` |
| BreadcrumbList | 2 or more `ListItem`, each with `position`, `name`, and `item` (the last may omit `item`) | match the visible trail |
| Product | `name`, and one of `offers`, `review`, `aggregateRating` | `image`, `description`, `sku`, `brand`, `offers.price`, `priceCurrency`, `availability` |
| SoftwareApplication | `name`, `offers.price` (`0` when free), and `aggregateRating` or `review` | `applicationCategory`, `operatingSystem` |
| Review | `author`, `reviewRating.ratingValue`, `itemReviewed` unless nested | `datePublished`, `reviewBody`, `author.url` |
| AggregateRating | `ratingValue`, `ratingCount` or `reviewCount`, `itemReviewed` unless nested | `bestRating`, `worstRating` |
| VideoObject | `name`, `thumbnailUrl`, `uploadDate` | `description`, `duration`, `contentUrl` or `embedUrl` |
| QAPage | `mainEntity` Question with `name`, `answerCount`, and `acceptedAnswer` or `suggestedAnswer`, each with `text` | `author`, `datePublished`, `upvoteCount`, answer `url` |
| ProfilePage | `mainEntity` with `name` | `dateCreated`, `sameAs`, `description`, `image` |
| DiscussionForumPosting | `author.name`, `datePublished`, `text` | `headline`, `url`, `comment` |
| Organization | none | `name`, `url`, `logo` (at least 112 by 112 pixels), `sameAs` |
| WebSite | `name`, `url` | `alternateName` |
| Dataset | `name`, `description` (50 to 5,000 characters) | `creator`, `license`, `distribution` |
| LocalBusiness | `name`, `address` | `telephone`, `openingHoursSpecification`, `geo` |
| Event | `name`, `startDate`, `location` | `endDate`, `offers`, `eventStatus` |

Format rules for every type: dates as `2026-11-12T10:00:00+00:00`; absolute `https` URLs; numbers as numbers or numeric strings; no HTML inside text values; no empty strings or placeholder values.

## 3. Worked example: product page with first-party reviews

The page shows "4.6 out of 5 (38 reviews)", a price and two reviews. Markup uses exactly those values.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Product", "@id": "https://www.example.com/p/trail-lamp#product",
      "name": "Trail Lamp 300", "image": ["https://www.example.com/img/trail-lamp.jpg"],
      "description": "Rechargeable 300-lumen headlamp.",
      "offers": { "@type": "Offer", "price": "39.00", "priceCurrency": "USD",
                  "availability": "https://schema.org/InStock", "url": "https://www.example.com/p/trail-lamp" },
      "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.6", "reviewCount": "38" },
      "review": [ { "@type": "Review", "author": { "@type": "Person", "name": "R. Diaz" },
                    "datePublished": "2026-09-02", "reviewBody": "Bright and light. Strap slips a little.",
                    "reviewRating": { "@type": "Rating", "ratingValue": "4" } } ] }
  ]
}
```

If the same page also quotes a score from another site ("4.8 on a marketplace"), that number stays visible text and is not marked up.

## 4. Worked example: article with breadcrumb

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Article", "@id": "https://www.example.com/guides/descale-kettle#article",
      "headline": "How to descale a kettle",
      "image": ["https://www.example.com/img/descale-16x9.jpg"],
      "datePublished": "2026-10-02T09:00:00+00:00", "dateModified": "2026-11-11T09:00:00+00:00",
      "author": { "@type": "Person", "name": "Ana Ruiz", "url": "https://www.example.com/authors/ana-ruiz" },
      "publisher": { "@id": "https://www.example.com/#organization" },
      "mainEntityOfPage": { "@id": "https://www.example.com/guides/descale-kettle#webpage" } },
    { "@type": "BreadcrumbList", "@id": "https://www.example.com/guides/descale-kettle#breadcrumb",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Guides", "item": "https://www.example.com/guides" },
        { "@type": "ListItem", "position": 2, "name": "How to descale a kettle" } ] }
  ]
}
```

The steps and the FAQ on such a page stay as ordinary headings, lists and paragraphs. They still help readers and can be quoted in results; they need no HowTo or FAQPage markup.

## 5. Checks to wire into a build

| Check | Rule |
|---|---|
| Syntax | every template renders JSON that parses |
| Required | required properties present for each emitted type |
| Parity | rating value, counts, review text, breadcrumb names and dates in the markup equal the rendered page |
| Policy | no rating markup on list, hub or comparison templates; no rating markup under a minimum number of real ratings; no editorial score in `aggregateRating` |
| Dates and URLs | ISO 8601 with time zone; absolute canonical URLs |
| Live sample | a few URLs per template through the official rich-result test before each release |
| After release | the structured-data reports in the search console: zero invalid items |
