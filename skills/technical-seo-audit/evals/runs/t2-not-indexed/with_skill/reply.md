Scope: https://www.acme-scheduler.example/pricing, one saved raw HTML file plus robots.txt and sitemap.xml you supplied. Question: why the page is not in Google. Date 2026-11-20. I used the offline check script and the skill checklist. No live fetch was done.

Verdict: Not ready. Lighthouse 100 does not mean the page is fine. The page tells Google to index a different site.

Blocking: 1  Signal conflicts: 1 (same root cause)  Presentation: 2  Hygiene: 0

## Root cause

pricing.html contains:

    <link rel="canonical" href="https://staging.acme-scheduler.example/pricing">

The live page at www.acme-scheduler.example/pricing says its preferred version is the staging host. Google treats rel=canonical as a strong signal. The sitemap listing the www URL is only a weak signal, so the two conflict and the canonical normally wins. The likely outcome is that Google does not index the www page and treats the staging URL as the main one. Staging is probably blocked, unreachable or unindexed, so nothing shows up.

Likely cause: a staging template or config value was copied to production. The sitemap lastmod for /pricing is 2026-10-30, about three weeks ago. That matches your timeline, but it is an inference. I cannot see when the canonical changed.

## Findings

| # | Page | Finding (measured value) | Threshold | Basis | Fix |
|---|---|---|---|---|---|
| 1 | /pricing | Canonical points to https://staging.acme-scheduler.example/pricing (script S3 FAIL, C7 WARN, C4 NOTE) | Canonical is the page's own URL on its own host | search-engine-doc | Change to `<link rel="canonical" href="https://www.acme-scheduler.example/pricing">` |
| 2 | /pricing | Robots meta has `max-snippet:0` | No nosnippet / max-snippet:0 on pages meant to be quoted | search-engine-doc | Change to `<meta name="robots" content="index, follow">`. This does not block indexing. It removes the text snippet and eligibility for AI answer features. Keep it only if intended. |
| 3 | /pricing | Title is 71 characters | Convention 30-60 | convention | Optional shortening, e.g. "Acme Scheduler pricing: Free, Team and Business plans". Not a Google rule and not related to the missing page. |
| 4 | /pricing | og:title "Pricing" and og:description "Compare plans" are very short | Present | convention | Optional; low priority. |

## Conflicts explained

- Sitemap lists the www URL, but the canonical points to staging. The canonical wins (strong versus weak signal). Fix the canonical. The sitemap is already correct.
- robots.txt is fine. It blocks only /app/ and /billing/, so /pricing is crawlable. Google can fetch the page and see the wrong canonical.
- The robots meta says index, so there is no noindex. The problem is the canonical, not a noindex.

## Why Lighthouse says 100

Lighthouse's SEO check passes a page that has a valid, crawlable canonical tag, even if it points to another host. It does not compare the canonical to the page's own URL, the sitemap or the index. The skill checklist makes the same point: a lab SEO score of 100 covers about a dozen page-level checks and says nothing about canonical conflicts or the sitemap. It is a convention-based gate, not proof of indexability.

## Not checked

- Live status code, redirects, and whether the live response matches this saved HTML (fetch the live URL and compare the canonical, in case the saved file is stale).
- Whether the staging host is reachable, blocked or indexed.
- Index status and the reason Google gives. Search Console URL Inspection on /pricing will show "User-declared canonical" versus "Google-selected canonical" and the coverage status. I cannot see it.
- Internal links to /pricing, rendered DOM, Core Web Vitals, manual actions.
- Content quality. The saved page has roughly 70 words, and the table lists Free and Team but not Business, although the text describes three plans. That is a content point and does not explain the missing page.
- Other pages: only the home page is listed in the sitemap and I was not given its HTML. Check it for the same staging canonical.

## Re-test

1. Fix the canonical (and the max-snippet if unintended), deploy, then run:
   `python scripts/seo_page_check.py <folder>` and expect S3, C7 and C4 to be gone.
2. Search Console: URL Inspection on https://www.acme-scheduler.example/pricing, Test live URL, check the user-declared canonical, then Request indexing.
3. Search the codebase and config for "staging.acme-scheduler" to catch the same value on other pages, in headers, or in the sitemap generator.

No timing or ranking is promised. Fixing the canonical removes the obstacle; Google decides when to reindex.
