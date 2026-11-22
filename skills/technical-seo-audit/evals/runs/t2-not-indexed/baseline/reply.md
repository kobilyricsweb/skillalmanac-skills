# Why the pricing page is not in Google

**Short answer: no, SEO 100 does not mean the technical side is fine. The page tells Google to index a different URL, the staging one.**

## The cause (high confidence)

In `pricing.html`:

```html
<link rel="canonical" href="https://staging.acme-scheduler.example/pricing">
```

The page is served at `https://www.acme-scheduler.example/pricing` (per `urls.csv`), but its canonical points at the **staging host**. That is almost certainly a leftover from a staging build or template. Google treats the canonical as a strong hint that the staging URL is the preferred version, so it will usually:

- consolidate the www page into the staging URL and not show the www page, or
- if staging is not publicly reachable, blocked or noindexed, find no valid canonical to index, so nothing ranks.

Either way, the page you want to appear is not the one being nominated. Your sitemap lists the www URL, so the sitemap and the canonical contradict each other. Google gives the canonical more weight than a sitemap entry.

## Why Lighthouse still says 100

Lighthouse only checks that the page is crawlable and well-formed. It does not know which host you meant to be canonical, and it cannot see how Google has indexed the page. A well-formed, absolute canonical URL passes. A fix-then-pass score does not prove the page is indexable. (I cannot see your Lighthouse report, so I can't say how it handled the cross-domain canonical. Some versions flag it, some do not. Either way, treat the score as a basic hygiene check, not an indexing guarantee.)

## What I checked and found fine

- `robots.txt`: only `/app/` and `/billing/` are blocked, so `/pricing` is crawlable. The sitemap is declared.
- `sitemap.xml`: lists `/pricing` on the www host with a `lastmod` of 2026-10-30.
- Meta robots is `index, follow`. There is no `noindex`.
- Title and description are present and a reasonable length. The H1 is present. The page has real body text.

## Secondary issues (not why it is missing, but worth fixing)

1. `max-snippet:0` in the meta robots tag tells Google to show **no text snippet**. It does not block indexing, but if the page does appear it will show as a bare title and URL, which cuts clicks. Remove it unless it was deliberate.
2. The comparison table lists only Free and Team. Business is described in the text but missing from the table, and the image alt text promises a comparison chart. Add the Business row.
3. `og:title` ("Pricing") and `og:description` ("Compare plans") are much thinner than the real title and description. Align them for better social previews.
4. The page is very short. That is not a problem for a pricing page, but it means there is little else to signal relevance.

## What to do

1. Change the canonical to `https://www.acme-scheduler.example/pricing`. Better still, fix the template so the canonical is built from the production host. Check the other pages for the same bug, including the home page.
2. Check what the staging host serves. If it is public and duplicates the site, put it behind authentication or `noindex` it. Do not rely on robots.txt for that.
3. Deploy, then in Search Console run **URL Inspection** on the www `/pricing` URL. Compare "User-declared canonical" with "Google-selected canonical". The live test should show the new canonical. Click **Request indexing**.
4. Wait. Recrawl and reselection usually take days to a couple of weeks. Check the **Pages** report for "Duplicate, Google chose different canonical than user" or "Alternate page with proper canonical tag". Those statuses would confirm this diagnosis.

## Limits of this review

I only had one saved HTML file, `robots.txt`, the sitemap and `urls.csv`. I could not see Search Console, server headers (an `X-Robots-Tag` header or a redirect would also matter), the live site, or the staging host. The staging canonical is the only clear defect in the files, so it is the most likely cause. Search Console URL Inspection will confirm it.
