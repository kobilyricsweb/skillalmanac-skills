# Are we done at health score 96? No.

The 96 is the crawler's own score. It is a tool convention, not a search-engine measure. The export has 28 URLs, and I count about 10 distinct defects in it. Several of them waste crawl budget or send mixed signals. The skill's "done" rule says every row in sections 1 and 2 of the checklist must pass on the same day. Many site-level rows fail here, so the site is not done.

Scope: `t3_crawl_export.csv`, 28 URLs on www.fernbank-outdoor.example. The question is whether the site is done and what to fix first. This is a crawl-export review only (checklist section 2). I had no raw HTML, robots.txt or sitemap file, so the page-level script (`seo_page_check.py`) was not run. It needs saved HTML plus `urls.csv`.

Verdict: not ready. Fix the sitemap, redirect and link problems below first.
Blocking: 5  Signal conflicts: 4  Presentation: 1  Hygiene: 2 (counts are by finding group, not by URL)

## Top fixes, in priority order

| # | Page(s) | Finding (measured value) | Threshold | Basis | Fix |
|---|---|---|---|---|---|
| 1 | /guides/pitching-in-wind, /guides/seam-sealing, /guides/stove-fuel-types | 3 orphan indexable pages: 0 inlinks, no depth. /stove-fuel-types is also missing from the sitemap, so nothing leads to it. | 0 orphans; 0 indexable pages missing from the sitemap | search-engine-doc (discovery through links and sitemap) | Link all three from the /guides hub. Add /stove-fuel-types to the sitemap. |
| 2 | /packs/trek-65 | Returns 404, has 4 internal inlinks, and is listed in the sitemap. | 0 broken internal links; sitemap holds only 200 URLs | search-engine-doc | Remove the 4 links and the sitemap entry. If the product has a successor, 301 it once to the successor. Otherwise leave it 404 or 410. |
| 3 | /stoves/discontinued-x1 | Soft 404: returns 200 with title "Page not found". It is indexable, in the sitemap and has 2 inlinks. | Removed pages return 404 or 410 | search-engine-doc | Return 404 or 410, or 301 it to /stoves. Remove it from the sitemap and from the 2 links. |
| 4 | /old-tents, /tents-2024, /tents-sale | Redirect chain of 3 hops: /old-tents to /tents-2024 to /tents-sale to /tents. /old-tents has 12 internal inlinks and is in the sitemap. The other two have 1 inlink each. | At most 1 hop; 0 internal links to redirected URLs; sitemap holds only final URLs | search-engine-doc (redirects as a strong signal) and conv (hop limit) | Make all three 301 straight to /tents. Change the 14 internal links to point at /tents. Remove /old-tents from the sitemap. |
| 5 | /tents?sort=price, /tents?sort=price&colour=green, /packs?sort=weight | Facet and sort URLs found by crawling from the home page. They carry 30, 14 and 30 inlinks, so site navigation links to them. They are non-indexable and canonicalised to the base page, so this wastes crawl effort and does not hurt rankings directly. | 0 parameter URLs discovered by the crawl | search-engine-doc (faceted-navigation guidance) | Stop linking to these URLs, or render sort controls without plain `<a href>`. Block the parameters in robots.txt once links are removed. Keep the canonicals meanwhile. |
| 6 | /sleeping-bags/down-800 | Canonical points to /down-600, yet the page is in the sitemap and has 5 inlinks. | Sitemap lists only self-canonical URLs | search-engine-doc | If it is a distinct product, give it a self-canonical. If it is a duplicate, drop it from the sitemap and relink to /down-600. Check which was intended. |
| 7 | /api/stock.json | Returns 500 with 6 internal inlinks. | 0 broken internal links; 0 5xx | search-engine-doc | Fix the endpoint or remove the links. Better, stop linking the API to crawlable pages and disallow /api/ in robots.txt. |
| 8 | /guides/archive/2019/winter/layering/base, /mid | Depth 6, with 1 inlink each. They are indexable and in the sitemap. /tents-sale, another redirect, sits at depth 4. 3 of the 25 URLs that have a depth (12%) exceed 3 clicks. | At most 3 clicks for 95% of pages | conv | Link the archive from the /guides hub, or flatten the URL and link structure. If the pages are not wanted in search, decide on noindex. |
| 9 | /checkout | Indexable, in the sitemap, and has 45 inlinks. | Intent check (R1) | search-engine-doc | Confirm it should be indexed. Normally set `noindex` and drop it from the sitemap. Cannot confirm from this export. |
| 10 | Most titles | Several titles are 5 to 7 characters ("Tents", "Packs", "Stoves"). Product titles are auto-built from the URL path ("Tents/Ridge 2", "Packs/Day 22"). | 30 to 60 characters | conv | Write descriptive titles such as "Ridge 2 Backpacking Tent | Fernbank Outdoor". This is a presentation point, not a block. |

Sitemap summary: at least 4 listed URLs should not be there (/old-tents, /packs/trek-65, /stoves/discontinued-x1, /sleeping-bags/down-800), and /checkout needs confirming. This is a bigger problem than the score suggests.

## Conflicts explained
- Sitemap plus 301, 404, soft-404 or canonical elsewhere (rows 2, 3, 4, 6): the redirect, 404 or canonical is the stronger signal. The sitemap entry is wasted and flagged as an error in the console.
- The parameter URLs canonicalise to the base page, which is correct. The real defect is that they are linked and crawled in volume.

## Why the score hides this
The score weights page-level hygiene. It says nothing about orphans, redirect chains, sitemap contents, soft 404s or crawl waste. That makes it a poor proxy for "done".

## Not checked
- Raw HTML, titles and descriptions beyond what is in the export, headings, JSON-LD, hreflang.
- robots.txt, the sitemap file itself, and noindex tags (the `indexable` column does not say why a URL is non-indexable).
- Field performance (LCP, INP, CLS), server logs and index status in the console.
- Whether the crawl was complete, and how the tool computes 96.
- No ranking or traffic effect is promised from these fixes.

## Re-test
Re-crawl after fixes and require: 0 orphans, 0 redirect hops beyond 1, 0 broken internal links, 0 sitemap URLs that are not 200 and self-canonical, 0 parameter URLs discovered. Then run `python scripts/seo_page_check.py <folder>` on saved HTML plus `urls.csv`, robots.txt and the sitemap.
