# Technical SEO checklist with thresholds

## Contents

1. Page-level rules (the script's rule ids)
2. Site-level rules (need a crawl, logs or live requests)
3. Performance and tool gates
4. Reading conflicts: which signal wins
5. Sources and the date they were read

Basis column: `doc` = documented by the search engine; `conv` = audit-tool convention.

## 1. Page-level rules

| Id | Rule | Threshold | Level | Basis |
|---|---|---|---|---|
| T1 | One `<title>` with text | exactly 1 | FAIL | doc |
| T2 | Title length | 30-60 characters | WARN | conv |
| T3 | Titles unique among indexable pages | 0 duplicates | FAIL | doc (descriptive, distinct titles) |
| D1 | Meta description present | 1 per page | WARN | doc |
| D2 | Description length | 120-155 characters | NOTE | conv (no documented limit; snippets are truncated to fit) |
| D3 | Descriptions unique among indexable pages | 0 duplicates | WARN | doc |
| H1 | One `<h1>` | exactly 1 | WARN | conv |
| H2 | Heading levels do not skip | 0 skips | WARN | conv (accessibility practice) |
| C1 | `rel=canonical` present | 1 per indexable page | WARN | doc |
| C2 | No conflicting canonicals | 1 distinct target | FAIL | doc |
| C3 | Canonical is absolute and https | 100% | WARN | doc |
| C4 | Canonical to another URL | intended only | NOTE | doc |
| C5 | No `noindex` together with a canonical to another URL | 0 | FAIL | doc (noindex is not a canonicalisation method) |
| C6 | Canonical target is indexable | 100% | FAIL | doc |
| C7 | Canonical stays on the page's own host unless a cross-domain canonical is intended | 0 unintended | WARN | doc |
| R0 | robots.txt does not block the whole site | - | FAIL | doc |
| R1 | `noindex` is intended | confirm | NOTE | doc |
| R2 | No `nosnippet` / `max-snippet:0` on pages meant to be quoted | 0 | WARN | doc |
| R3 | A `noindex` page is crawlable | not blocked in robots.txt | WARN | doc |
| S0-S5 | Sitemap parses; lists only https, indexable, self-canonical, crawlable URLs; `lastmod` values are real | 0 violations | FAIL / WARN | doc |
| L1, V1 | `lang` on `<html>`; viewport meta | present | WARN | conv / doc |
| O1 | Open Graph title, description, image | present | NOTE | conv |
| I1, I2 | `alt` on images; width and height set | 100% | WARN / NOTE | doc |
| J1 | JSON-LD parses | 0 errors | FAIL | doc |
| B1 | Main content in raw HTML | 50+ visible words when scripts are loaded | WARN | doc |
| M1 | No http resources on https pages | 0 | WARN | doc |
| A1 | Descriptive anchor text | no "click here" | NOTE | doc |
| X1-X3 | hreflang: self-reference, x-default, return links | reciprocal | WARN / NOTE | doc |

## 2. Site-level rules

Check these from a crawl export, a URL list with status codes, or server logs. If none is available, list them under "Not checked".

| Area | Rule | Threshold |
|---|---|---|
| Host | One protocol and host; every variant (http, www or non-www, upper case, trailing slash) reaches the canonical URL | 1 hop, 301 or 308 |
| Redirects | Chains | at most 1 hop; 0 loops |
| Status | Indexable URLs returning 5xx | 0 |
| Status | Removed pages | 404 or 410, never 200 with an error message (soft 404) |
| Links | Broken internal links (4xx, 5xx) | 0 |
| Links | Internal links to redirected URLs | 0 |
| Links | Orphan indexable pages (no internal inlink) | 0 |
| Depth | Clicks from the home page to any indexable page | at most 3 for 95% of pages |
| Sitemap | Only canonical, indexable, 200 URLs; under 50,000 URLs and 50 MB per file | 100% |
| Sitemap | Indexable pages missing from the sitemap | 0 |
| Pagination | Each page of a list has its own URL and a self-canonical; page 2 and later do not canonicalise to page 1; plain `<a href>` links between pages | 100% |
| Facets | Filter and sort parameter URLs discovered by a crawl from the home page | 0 (block in robots.txt, or keep out of links) |
| Parameters | Tracking parameters in internal links | 0 |
| Rendering | Sections present in the rendered DOM but missing from raw HTML | 0 on indexable templates |
| Logs | Share of search-crawler requests spent on non-indexable URLs | under 5% |
| Logs | 5xx share of crawler requests | under 0.5% |
| Security | https everywhere, no mixed content | 100% |

## 3. Performance and tool gates

| Metric | Pass | Source of threshold |
|---|---|---|
| Largest Contentful Paint | within 2.5 s | doc |
| Interaction to Next Paint | under 200 ms | doc |
| Cumulative Layout Shift | under 0.1 | doc |
| Time to first byte | under 800 ms | conv |
| Lab audit, SEO category | 100 | conv |
| Lab audit, performance, mobile profile | 90 or more, median of 3 runs | conv |
| Lab audit, accessibility | 95 or more | conv |
| Site crawler "errors" | 0, warnings triaged one by one | conv |
| Search engine console | 0 manual actions, 0 security issues, 0 invalid structured-data items | doc |

Field data (real users) decides Core Web Vitals; a lab score is a proxy. A lab SEO score of 100 covers about a dozen page-level checks and says nothing about duplicates, canonical conflicts, orphan pages, redirects or the sitemap. "Done" means every row here and in sections 1 and 2 passes on the same day, and stays that way on a re-check.

## 4. Reading conflicts

| Conflict | What happens | Fix |
|---|---|---|
| In sitemap + `noindex` | The page is dropped; the sitemap entry is wasted and reported as an error | Remove from the sitemap, or remove the noindex |
| In sitemap + canonical elsewhere | Sitemap inclusion is a weak canonical signal against a stronger one; mixed signals | List only the canonical target |
| `noindex` + blocked in robots.txt | The crawler cannot fetch the page, so it never sees the noindex; the URL can stay indexed without content | Unblock until the page is dropped, then block if needed |
| `noindex` + canonical to another URL | Contradiction: one says "drop me", the other "count me as that page" | Canonical only, for duplicates; noindex only, for pages with no equivalent |
| Canonical to a redirecting, 404 or noindex URL | The canonical is ignored | Point it at a 200, indexable URL |
| Two canonicals (tag and header, or two tags) | Both may be ignored | Keep one |
| Redirect + canonical disagree | The redirect is the stronger signal | Make them agree |
| hreflang without return link | The pair is ignored | Add the reciprocal link; each language page keeps a self-canonical |
| Canonical on page 2+ pointing to page 1 | Items on later pages lose their path to discovery | Self-canonical per page |

## 5. Sources and the date they were read

All under `developers.google.com/search/docs/`, read on 2026-11-20:

- `appearance/snippet`: no length limit for meta descriptions; snippets come mainly from page content; programmatic descriptions are acceptable; `nosnippet`, `max-snippet`, `data-nosnippet`.
- `crawling-indexing/consolidate-duplicate-urls`: redirects and `rel=canonical` are strong signals, sitemap inclusion a weak one; absolute URLs; do not use noindex or robots.txt to canonicalise; do not give different canonicals by different methods; hreflang pages need a canonical in the same language.
- `crawling-indexing/sitemaps/build-sitemap`: 50 MB or 50,000 URLs per file; `priority` and `changefreq` ignored; `lastmod` must reflect the last significant update; absolute URLs.
- `appearance/core-web-vitals`: the three thresholds above.
- `appearance/ai-features`: a page must be indexed and snippet-eligible to appear in AI answer features; no extra files or markup are required.
- `specialty/ecommerce/pagination-and-incremental-page-loading` and `crawling-indexing/crawling-managing-faceted-navigation`: read by the research this checklist was built from, not re-opened for this version.

Title and description character ranges, the h1 count, time to first byte and all lab-score gates are conventions. Re-read the sources before relying on a threshold that matters to a decision.
