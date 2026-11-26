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
| C1 | Explicit `rel=canonical` preference where duplicate/very similar URLs or a preferred URL make it useful | project scope | NOTE | conv; Google does not require an explicit canonical on every page |
| C2 | No conflicting canonicals | 1 distinct target | FAIL | doc |
| C3 | Canonical uses an absolute URL; HTTPS is preferred when equivalent HTTP and HTTPS versions exist | absolute URL | WARN | doc |
| C4 | Canonical to another URL | intended only | NOTE | doc |
| C5 | No `noindex` together with a canonical to another URL | 0 | FAIL | doc (noindex is not a canonicalisation method) |
| C6 | Canonical target does not carry a conflicting noindex signal | 0 known conflicts | FAIL | doc (the selected canonical remains Google's decision) |
| C7 | Canonical stays on the page's own host unless a cross-domain canonical is intended | 0 unintended | WARN | doc |
| R0 | robots.txt does not block the whole site | - | FAIL | doc |
| R1 | `noindex` is intended | confirm | NOTE | doc |
| R2 | No `nosnippet` / `max-snippet:0` on pages meant to be quoted | 0 | WARN | doc |
| R3 | A `noindex` page is crawlable | not blocked in robots.txt | WARN | doc |
| S0-S4 | Sitemap parses; uses absolute preferred canonical URLs; avoids known noindex, blocked, or conflicting-canonical entries; `lastmod` values are accurate | 0 known conflicts | FAIL / WARN | doc (HTTP is supported; HTTPS is preferred for equivalent URLs) |
| L1, V1 | `lang` on `<html>`; viewport meta | present | WARN | conv / doc |
| O1 | Open Graph title, description, image | present | NOTE | conv |
| I1, I2 | `alt` on images; width and height set | 100% | WARN / NOTE | doc |
| J1 | JSON-LD parses | 0 errors | FAIL | doc |
| B1 | Sparse raw HTML on a scripted page prompts rendered-DOM comparison | fewer than 50 visible words (local heuristic) | NOTE | conv; Google renders JavaScript |
| M1 | No http resources on https pages | 0 | WARN | doc |
| A1 | Descriptive anchor text | no "click here" | NOTE | doc |
| X1-X3 | hreflang: self-reference, x-default, return links | reciprocal | WARN / NOTE | doc |

## 2. Site-level rules

Check these from a crawl export, a URL list with status codes, or server logs. If none is available, list them under "Not checked".

| Area | Rule | Threshold | Basis |
|---|---|---|---|
| Host | Preferred protocol and host signals are consistent; redirects, canonicals, internal links and sitemap entries do not conflict | project-defined acceptance; minimize redirect hops | doc for signal consistency; hop count is conv |
| Redirects | Chains and loops | 0 loops; chain-length target is conv | mixed |
| Status | URLs intended for Search returning 5xx | report observed share; target is project-defined | doc behaviour; zero target is conv |
| Status | Removed pages | 404 or 410 rather than a 200 response whose content says the page is missing | doc |
| Links | Broken internal links (4xx, 5xx) | project-defined; enumerate observed failures | conv target |
| Links | Internal links to redirected URLs | project-defined; enumerate | conv target |
| Links | Pages intended for Search with no discovered internal inlink | enumerate; verify crawl scope before calling orphaned | conv audit rule |
| Depth | Clicks from a starting URL | report distribution; any cutoff is project-defined | conv |
| Sitemap | Valid supported format; absolute preferred canonical URLs; no known signal conflicts; 50,000 URLs and 50 MB maximum per file | documented limits plus 0 known conflicts | mixed |
| Sitemap | Preferred URLs intentionally omitted from the sitemap | report against the declared sitemap scope; not every indexable URL must be listed | doc |
| Pagination | Each list page has a crawlable URL and links; canonical decisions reflect whether pages are duplicate or distinct | evidence-based | doc |
| Facets | Filter and sort parameter URLs discovered by a crawl | inventory and apply a site-specific crawl strategy; do not prescribe blanket blocking | doc guidance; count target is project-specific |
| Parameters | Tracking parameters in internal links | report count; target is project-defined | conv |
| Rendering | Material differences between raw and rendered content | compare and verify crawlable resources; raw absence alone is not failure | doc |
| Logs | Search-crawler requests to non-indexable URLs | report share and trend; no universal 5% requirement | conv |
| Logs | Crawler requests receiving 5xx | report share and trend; no universal 0.5% requirement | conv |
| Security | HTTPS preferred for equivalent pages; mixed-content findings evaluated separately | evidence-based | doc |

## 3. Performance and tool gates

| Metric | Pass | Source of threshold |
|---|---|---|
| Largest Contentful Paint | 2.5 s or less at the 75th percentile of field page loads, segmented by mobile and desktop | doc |
| Interaction to Next Paint | 200 ms or less at the 75th percentile of field page loads, segmented by mobile and desktop | doc |
| Cumulative Layout Shift | 0.1 or less at the 75th percentile of field page loads, segmented by mobile and desktop | doc |
| Time to first byte | under 800 ms | conv |
| Lab audit, SEO category | 100 | conv |
| Lab audit, performance, mobile profile | 90 or more, median of 3 runs | conv |
| Lab audit, accessibility | 95 or more | conv |
| Site crawler "errors" | 0, warnings triaged one by one | conv |
| Search engine console | 0 manual actions, 0 security issues, 0 invalid structured-data items | doc |

Field data (real users) is used for Core Web Vitals assessment; lab measurements are diagnostic proxies and cannot directly measure field INP. A lab SEO score of 100 covers a bounded set of page checks and says nothing by itself about duplicates, canonical conflicts, orphan pages, redirects, sitemap scope, selected canonicals, or index status. There is no universal technical-SEO definition of "done": define acceptance criteria for the stated scope, record not-checked areas, and re-check after changes.

## 4. Reading conflicts

| Conflict | What happens | Fix |
|---|---|---|
| In sitemap + `noindex` | Conflicting intent: the sitemap suggests a preferred URL while noindex requests exclusion; actual index status needs index evidence | Remove from the sitemap, or remove the noindex, according to intent |
| In sitemap + canonical elsewhere | Sitemap inclusion is a weak canonical signal against a stronger one; mixed signals | List only the canonical target |
| `noindex` + blocked in robots.txt | The crawler cannot fetch the page, so it never sees the noindex; the URL can stay indexed without content | Unblock until the page is dropped, then block if needed |
| `noindex` + canonical to another URL | Contradiction: one says "drop me", the other "count me as that page" | Canonical only, for duplicates; noindex only, for pages with no equivalent |
| Canonical to a redirecting, 404 or noindex URL | Signals conflict; this audit cannot prove which canonical Google selects | Point it at a stable, crawlable target consistent with intent |
| Two canonicals (tag and header, or two tags) | Conflicting canonical signals; selection outcome is not proven offline | Keep one consistent preference |
| Redirect + canonical disagree | The redirect is the stronger signal | Make them agree |
| hreflang without return link | The pair is ignored | Add the reciprocal link; each language page keeps a self-canonical |
| Canonical on page 2+ pointing to page 1 | Items on later pages lose their path to discovery | Self-canonical per page |

## 5. Sources and the date they were read

Primary Google documentation re-read on 2026-11-23:

- `appearance/snippet`: no length limit for meta descriptions; snippets come mainly from page content; programmatic descriptions are acceptable; `nosnippet`, `max-snippet`, `data-nosnippet`.
- `https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec`: URL-pattern examples include query-bearing URLs; the longest matching rule wins and equal-length conflicts use the least restrictive rule; `/$` applies only to the root.
- `https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics`: Google crawls, renders, and indexes JavaScript pages; blocked pages or resources are not rendered.
- `https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls`: redirects and `rel=canonical` are strong signals, sitemap inclusion a weak one; Google makes the final canonical selection; absolute URLs are recommended and HTTP/HTTPS preference has documented exceptions.
- `https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap`: 50 MB or 50,000 URLs per file; `priority` and `changefreq` ignored; `lastmod` must reflect significant updates; URLs are absolute and represent preferred URLs the publisher wants surfaced, not a requirement to list every indexable URL.
- `https://developers.google.com/search/docs/appearance/core-web-vitals` and linked `https://web.dev/articles/vitals`: LCP, INP and CLS thresholds; field assessment at the 75th percentile, split by mobile and desktop; inclusive good boundaries.
- `appearance/ai-features`: a page must be indexed and snippet-eligible to appear in AI answer features; no extra files or markup are required.
- `specialty/ecommerce/pagination-and-incremental-page-loading` and `crawling-indexing/crawling-managing-faceted-navigation`: read by the research this checklist was built from, not re-opened for this version.

Title and description character ranges, the h1 count, time to first byte, crawl-depth and log-share cutoffs, redirect-hop targets, and all lab-score gates are conventions. Re-read the sources before relying on a threshold that matters to a decision. Remaining uncertainty: this offline checklist cannot observe Google's selected canonical, rendering result, or index state without the corresponding live or Search Console evidence.
