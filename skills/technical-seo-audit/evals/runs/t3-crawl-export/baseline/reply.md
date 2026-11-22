# Are we done at 96? No.

The score is an average over many checks. Most of the 28 URLs pass most checks, so one broken page barely moves it. The export has real problems, and several hit pages that matter: a money page that is being de-indexed, a checkout page in the sitemap, and a soft 404. The fixes are mostly small.

Caveat: this export is only 28 URLs, and it has no h1, meta description, response time or structured data columns. I could only audit what is in the CSV. If the site is larger, check that the crawl was complete.

## Top fixes, in priority order

**1. /sleeping-bags/down-800 canonicalises to /down-600 (5 inlinks, in sitemap).**
This is a separate product page. Its canonical points at a different product, so Google will probably drop it from the index in favour of down-600. It is also listed in the sitemap while being non-indexable.
Fix: set its canonical to itself. If it really is a duplicate of down-600, merge the pages with a 301 instead and remove it from the sitemap. Check the CMS template for other pages that copy a canonical.

**2. /stoves/discontinued-x1 is a soft 404 (200 status, title "Page not found", 2 inlinks, in sitemap, indexable).**
It tells Google the page is fine while showing an error. Fix: return a real 404 or 410, or 301 it to /stoves or a replacement product. Remove it from the sitemap and update the 2 internal links.

**3. /packs/trek-65 returns 404 (4 inlinks, in sitemap).**
Internal links and the sitemap send users and crawlers to a dead page. Fix: if the product has a successor (probably trek-55), 301 to it. Otherwise leave the 404 and remove the 4 links and the sitemap entry.

**4. Redirect chain: /old-tents -> /tents-2024 -> /tents-sale -> /tents (3 hops, 12 inlinks, /old-tents is in the sitemap).**
Each hop loses speed and crawl efficiency, and long chains risk Google giving up. Fix: point /old-tents and /tents-2024 straight at /tents with one 301. Update the 12 internal links to /tents and take /old-tents out of the sitemap, since sitemaps should only list final 200 URLs.

**5. Three orphaned guides with 0 inlinks and no click depth: pitching-in-wind, seam-sealing, stove-fuel-types.**
The crawler found them only through the sitemap (stove-fuel-types is not even in the sitemap, so it is found some other way or is invisible to Google). The /guides hub has 30 inlinks but evidently does not link to them. Fix: link them from /guides and from related product pages (tents, stoves). Add stove-fuel-types to the sitemap if it should rank.

**6. /checkout is indexable and in the sitemap (45 inlinks).**
It is a transactional page with no search value. Fix: add noindex (not a robots.txt block, so the tag can be seen) and remove it from the sitemap. Do the same for cart and account pages if they exist.

**7. /api/stock.json returns 500 (6 inlinks, not in sitemap).**
A failing endpoint that 6 pages reference. If a page fetches it for live stock, product pages may be showing wrong stock or breaking. Fix: repair the endpoint or the 6 references. Block /api/ from crawling and make sure it is not linked as a normal href.

## Medium priority

- **Sort and filter URLs get heavy internal linking.** /tents?sort=price has 30 inlinks and /packs?sort=weight has 30 (so every page links them). /tents?sort=price&colour=green is at depth 3 with 14 inlinks. The canonicals point to the clean URL and they are not in the sitemap, so this is not an indexing problem yet. It does waste crawl on a site that could multiply these URLs. Fix: make sort controls non-crawlable (buttons or JS, or rel="nofollow"), and disallow the parameters in robots.txt once the canonicals are confirmed.
- **Deep archive pages.** /guides/archive/2019/winter/layering/base and /mid are at depth 6 with 1 inlink each, but sit in the sitemap. Either flatten the path and link them from the guides hub, or decide they are not worth indexing and remove them.
- **Titles are weak.** Product titles look auto-generated from the URL path ("Tents/Ridge 2", "Packs/Day 22", "Sleeping Bags/Down 600"). Category titles are one word ("Tents", "Packs"). The faceted URLs duplicate the "Tents" title. Rewrite them to say what the page is and who it is for, for example "Ridge 2 two-person tent | Fernbank Outdoor". Do the hub and top products first.

## What looks fine

- All five main category pages and the home page are 200, self-canonical, indexable and in the sitemap, with 30-40 inlinks each.
- Product pages are all at depth 2 with 6 inlinks, so they are well linked.
- Canonicals on the faceted URLs point to the clean page, which is correct.

## Suggested order

Fixes 1 to 4 are quick and can ship together, mostly in redirect rules and the sitemap. Then 5 and 6. Then re-crawl and compare the counts of 404s, soft 404s, chains, orphans and non-indexable sitemap URLs. Track those, not the health score. In this export, 5 of the 21 sitemap URLs should not be there (old-tents, trek-65, discontinued-x1, down-800 and /checkout). The sitemap should contain only canonical, indexable, 200 URLs that you want ranked.
