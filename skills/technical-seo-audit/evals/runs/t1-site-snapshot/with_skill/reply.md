# Technical SEO audit: Northfield Kettles pre-launch snapshot

Scope: 8 template pages saved as raw HTML (home EN, home DE, category page 1, category page 2, copper product, steel product, guide, sale), plus robots.txt, sitemap.xml (9 URLs) and urls.csv. Market: not stated (EN and DE pages exist). Date: 2026-11-20. HTML taken as supplied (assumed to be the raw server response). Question: is the site ready for Monday's relaunch, and what to fix first. The page-check script was run on the folder; I then read every file by hand to confirm and to catch what it cannot see.

Verdict: NOT READY. Four pages in or around the sitemap contradict themselves (noindex, canonical, robots.txt), the guide page has no content in raw HTML, and the steel product page has two conflicting canonicals. All are fixable with small edits before Monday.

Blocking: 6  Signal conflicts: 4  Presentation: 6  Hygiene: 5

(Script totals: 7 FAIL, 13 WARN, 6 NOTE. Below, findings are grouped by effect, and related script lines are merged.)

## Fix first (in this order)

1. Decide whether /copper-kettle is meant to be noindex. It is a product page, and it is noindex and in the sitemap. If it is meant to rank, this single tag removes it from search at launch.
2. Fix the guide page (/guides/descale): empty raw body, a broken JSON-LD block and `nosnippet`.
3. Fix the steel kettle canonicals.
4. Resolve /sale (noindex + robots block + in sitemap).
5. Fix category pagination (/kettles?page=2).
6. Clean the sitemap and the robots.txt Sitemap line.
7. Presentation and hygiene items.

## Findings

### Blocking (crawl or index)

| # | Page | Finding (measured value) | Threshold | Basis | Fix |
|---|---|---|---|---|---|
| 1 | /copper-kettle | `<meta name="robots" content="noindex, follow">` and the URL is listed in sitemap.xml (script S1, R1) | 0 noindex pages in the sitemap; noindex only where intended | search-engine-doc | If it should rank, delete the robots meta line. If it should not, remove the `<loc>` from sitemap.xml. Confirm intent with the owner: a product page being noindex looks like a staging leftover. |
| 2 | /guides/descale | Raw HTML body has 5 visible words: `<h1>` plus an empty `<div id="app"></div>`, with 2 external scripts (B1) | 50+ visible words in raw HTML when scripts are loaded | search-engine-doc | Server-render or pre-render the article body into the HTML. Confirm with a rendered-DOM comparison (not checked here, see below). |
| 3 | /guides/descale | JSON-LD does not parse: `"headline": "How to descale a kettle",}` has a trailing comma (J1) | 0 parse errors | search-engine-doc | Change to `{"@context": "https://schema.org", "@type": "Article", "headline": "How to descale a kettle"}` |
| 4 | /steel-kettle | Two canonicals: `https://www.northfield-kettles.example/steel-kettle` and `http://northfield-kettles.example/steel-kettle` (different protocol and host) (C2, C7, C3) | exactly 1 distinct canonical, absolute https, own host | search-engine-doc | Delete `<link rel="canonical" href="http://northfield-kettles.example/steel-kettle">`; keep the https www one. Also check the template or a plugin that injects the second tag. |
| 5 | /sale | In sitemap, `noindex`, and `Disallow: /sale` in robots.txt (S1, S2, R3) | sitemap lists only crawlable, indexable URLs; a noindex page must be crawlable to be read | search-engine-doc | Pick one intent. To keep it out of search: remove from sitemap, remove `Disallow: /sale` until it drops out, keep noindex. To rank it: remove the noindex, remove it from the Disallow, keep in sitemap. |
| 6 | /kettles?page=2 | Canonical points to `/kettles` (page 1), and the URL is in the sitemap (S3, C4). Neither saved category page links to page 2 (no `<a href>` pagination at all in the HTML) | page 2+ has a self-canonical; plain `<a href>` links between pages | search-engine-doc (canonical, sitemap); checklist rule for pagination | Set page 2 canonical to `https://www.northfield-kettles.example/kettles?page=2`, add `<a href="/kettles?page=2">` links on page 1 (and back), or if page 2 should not exist, drop it from the sitemap. Items listed only on page 2 currently have no signalled path to discovery. |

### Signal conflicts and misdirection

| # | Page | Finding (measured value) | Threshold | Basis | Fix |
|---|---|---|---|---|---|
| 7 | /kettles and /kettles?page=2 | Identical title `Kettles \| Northfield stovetop and electric range` and identical description (T3, D3) | 0 duplicates among indexable pages | search-engine-doc (distinct, descriptive titles) | Page 2: `Kettles, page 2 \| Northfield enamel range` and a different description. The `<h1>` is also identical ("All kettles"); the page 2 `h2` says "More kettles". |
| 8 | / and /de/ | hreflang: home links `en` and `de`, but /de/ has only a self `de` link and no link back to `en` (X3). No x-default on either (X2) | reciprocal hreflang; x-default is recommended | search-engine-doc | On /de/ add both `en` and `de` alternates; on both add `<link rel="alternate" hreflang="x-default" href="https://www.northfield-kettles.example/">`. Without the return link the pair is ignored. |
| 9 | sitemap.xml | Contains `http://www.northfield-kettles.example/about` (http, S5). That page was not in the snapshot, so its state is unknown | sitemap lists https canonical URLs only | search-engine-doc | Change to `https://` after confirming /about is live and indexable. |
| 10 | robots.txt | `Sitemap: http://www.northfield-kettles.example/sitemap.xml` uses http (not flagged by the script, found by hand) | https, one canonical host | search-engine-doc (consistent protocol) / consistency check | Change to `Sitemap: https://www.northfield-kettles.example/sitemap.xml`. |

### Presentation

| # | Page | Finding | Threshold | Basis | Fix |
|---|---|---|---|---|---|
| 11 | /guides/descale | `<meta name="robots" content="nosnippet">` (R2) | 0 on pages meant to be quoted | search-engine-doc | Remove the tag. An informational guide with no snippet is also ineligible for AI answer features. Keep only if deliberate. |
| 12 | /copper-kettle | No meta description (D1) | 1 per page | search-engine-doc | Add one, e.g. 120-155 chars describing the 1.5 litre copper kettle. |
| 13 | / (home) | 1 of 1 images has no `alt` (`/img/hero.jpg`) (I1) | 100% | search-engine-doc | Add a descriptive alt. |
| 14 | /steel-kettle | Image loaded over http: `http://cdn.northfield-kettles.example/steel.jpg` (M1) | 0 mixed content | search-engine-doc | Serve the image over https. |
| 15 | /guides/descale | Title is 84 characters (T2) | 30-60 | convention | Shorten, e.g. `How to descale a kettle in four steps \| Northfield` (not a search-engine rule; it may be truncated, not penalised). |
| 16 | / (home) | Title is 18 characters, `Northfield Kettles` (T2) | 30-60 | convention | Optional: add a descriptor. Low priority. |

### Hygiene

| # | Page | Finding | Threshold | Basis | Fix |
|---|---|---|---|---|---|
| 17 | /kettles | Heading jumps h1 to h3 ("Stovetop") (H2) | no skipped levels | convention | Change the h3 tags to h2. |
| 18 | / (home) | Anchor text "click here" to the descale guide (A1) | descriptive anchors | search-engine-doc | `<a href="/guides/descale">How to descale a kettle</a>` |
| 19 | all pages | og:title differs from the page title on several pages; short og descriptions on /de/ (O1 passes, content is thin) | present | convention | Optional alignment. |
| 20 | sitemap.xml | All 9 `lastmod` values are 2026-11-01 (S4) | lastmod used only when consistently accurate | search-engine-doc | Emit the real last-modified date per URL, or omit lastmod. |
| 21 | /de/ | Page text under the German `<h1>` is English copy (observed in the HTML; possible placeholder) | language consistency | not a rule; flagged for review | Confirm the German body is final. |

## Conflicts explained

- **Sitemap + noindex (/copper-kettle, /sale):** the noindex wins; the page is dropped and the sitemap entry only produces a reported error.
- **noindex + robots.txt block (/sale):** the crawler cannot fetch the page, so it never reads the noindex. The URL can remain indexed with no content. Unblock until it drops out.
- **Two canonicals (/steel-kettle):** both may be ignored; the http non-www one also points at a different host.
- **Sitemap + canonical elsewhere (/kettles?page=2):** the strong canonical signal beats the weak sitemap signal, so page 2 is treated as a duplicate of page 1.
- **Hreflang without return link (/ and /de/):** the pair is ignored by the engine.

## Not checked

- Status codes, redirects, chains, http to https and www/non-www redirects (needs live requests; the canonical and sitemap mix of http/https/www/non-www makes this a priority to test).
- Rendered DOM vs raw HTML (the guide page needs a browser comparison).
- Internal link graph: orphans, click depth, broken links. Only the home page was inspected for links; it links to /kettles and the guide only.
- Core Web Vitals (field and lab), index coverage, manual actions (needs Search Console).
- Structured data eligibility beyond JSON syntax.
- Pages not in the snapshot: /about, /cart and any other URLs. The 5 URLs per template guidance was not exercised because only one page per template was supplied.
- Whether /copper-kettle and /sale noindex, and the /sale robots rule, are intended.
- Facets, parameter URLs and tracking parameters (no crawl).

No ranking or traffic effect is promised; these fixes remove obstacles only.

## Re-test

After the fixes, run:

```
python scripts/seo_page_check.py <folder>
```

from the technical-seo-audit skill folder against refreshed HTML (re-save the pages and keep urls.csv). Target: 0 FAIL. Then run a live crawl for redirects and link checks, and submit the corrected sitemap in Search Console.
