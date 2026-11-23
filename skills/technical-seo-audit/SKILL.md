---
name: technical-seo-audit
description: Audits web pages and small sites for technical SEO against a measurable checklist (titles, meta descriptions, canonicals, robots and noindex, headings, sitemaps, hreflang, raw-HTML rendering) with an offline script that cross-checks saved HTML against robots.txt and the sitemap. Use when the user asks for an SEO audit, a technical SEO check, why a page is not indexed, a pre-launch SEO review or whether a page is ready to ship. Findings separate documented search-engine rules from tool conventions. Do not use for keyword research, writing content, link building or structured-data design.
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only) and makes no network calls; it reads HTML files that were saved first. Fetching live pages uses the agent's own tools and the user's permission. Without Python, apply the checklist by hand.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.1"
  network: none
---

# Technical SEO audit

Find observed technical signals, conflicts, and evidence gaps that may affect crawling, rendering, canonicalization, indexing eligibility, or presentation. For each finding, state what was measured, the applicable documented rule or explicitly labelled local convention, and what the available evidence cannot prove. Do not turn a signal into a guaranteed indexing or ranking outcome.

## Ground rules

1. **Measure, then judge.** Every finding states the observed value and either a documented boundary, an explicitly labelled local convention ("title 78 characters; convention 30-60"), or the evidence needed when no numeric threshold exists.
2. **Label the basis.** `search-engine-doc` means a documented requirement or documented behaviour. `convention` means an audit-tool habit (title and description character ranges, one h1). Never present a convention as a rule of the search engine.
3. **Compare signals.** Contradictions between files can create mixed guidance: a URL in the sitemap that is noindex, a canonical that points to a blocked or noindex page, or robots.txt preventing a crawler from seeing a noindex directive. Report the conflict without claiming which URL Google indexed unless index evidence is supplied.
4. **Check raw and rendered evidence separately.** Start from the HTML the server returns, but do not treat content absent from raw HTML as an automatic block: Google renders JavaScript. Compare the rendered DOM when the question depends on rendered content.
5. **No ranking promises.** Fixing a defect removes an obstacle. Never forecast positions, traffic or indexing dates.
6. **Say what was not checked.** A page-level audit has not seen redirects, the link graph, field performance or the index. The report lists these every time.

## Workflow

### 1. Scope

One line: which URLs or templates, which market, and the question (pre-launch check, indexing problem, full audit). For a site, pick up to 5 URLs per template rather than every page.

### 2. Collect

Save into one folder:

- the raw HTML of each page as `<name>.html` (the server response, not the browser's rendered DOM);
- `urls.csv` with the header `file,url` mapping each file to its live URL;
- `robots.txt` and one `sitemap.xml` when the audit covers a site.

Fetch with the agent's own tools and only for sites the user asked about. If the user already supplied files, use them as given.

### 3. Run the page check

```bash
python scripts/seo_page_check.py <folder-or-file>
```

It prints FAIL, WARN and NOTE findings with a rule id and basis, then a list of what it did not check. Run it; do not edit it to make a page pass. Without `urls.csv` the cross-file checks are skipped, and the output says so.

### 4. Complete the checks the script cannot do

Open [references/checklist.md](references/checklist.md) and work through the sections that match the scope:

- "Site-level rules" when a crawl export, server logs or a list of URLs with status codes is available;
- "Performance and tool gates" when the user has lab or field data, or asks whether the site is "done";
- "Reading conflicts" whenever two signals disagree, to decide which one the search engine will follow.

Mark each rule as pass, fail (with the value), or not checked (with the reason).

### 5. Prioritise

Order findings by effect, not by count:

1. **Documented crawl or indexing-eligibility barriers**: an unqualified site-wide disallow, noindex on pages intended for Search, sitemap URLs blocked from crawling, and an unparseable sitemap.
2. **Splits or misdirects signals**: conflicting or cross-domain canonicals, duplicate titles on indexable pages, non-reciprocal hreflang, redirect chains.
3. **Needs additional evidence**: content sparse in raw HTML but potentially present after rendering, canonical preferences without selected-canonical/index evidence, and field-performance questions without field data.
4. **Presentation and hygiene**: missing or duplicate descriptions, title length conventions, missing alt text or social tags, heading order, generic anchors, and image dimensions.

### 6. Report

```
Scope: <URLs or templates, date, how the HTML was obtained>
Verdict: <ready / not ready / ready with listed risks> - one sentence
Blocking: <n>  Signal conflicts: <n>  Presentation: <n>  Hygiene: <n>

| # | Page | Finding (measured value) | Threshold | Basis | Fix |

Conflicts explained: <for each pair of disagreeing signals, which wins and why>
Not checked: <list, with what would be needed>
Re-test: <the command or tool to run after the fix>
```

Give an exact tag or line to change only when the supplied evidence supports that repair; otherwise give the verification step. After fixes, re-run the script and report the new counts without claiming indexing or ranking success.

## Limits

- The script reads static HTML. It cannot see redirects, status codes, rendered DOM, performance, the link graph, Google's selected canonical, or index status.
- Google renders JavaScript, so sparse raw HTML is a local review heuristic. Confirm rendered content and relevant resources before classifying a rendering barrier.
- Zero findings means these checks passed on these files, not that the site will rank. Thin or duplicated content passes every technical check.
- Character ranges approximate pixel width; a title inside the range can still be truncated.
- Rules follow one search engine's public documentation; other engines differ in details.
