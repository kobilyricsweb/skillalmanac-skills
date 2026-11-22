# Making content readable and quotable for assistants

Read the sections for the parts in scope at step 5.

## Contents

1. First checks: indexed and in the raw HTML
2. Quotable page pattern
3. llms.txt format
4. Markdown versions of pages
5. Measuring
6. What is established and what is not

## 1. First checks

| Check | Pass |
|---|---|
| The page is indexed by the main search engines | present in the engine's console or a `site:` query |
| No `noindex`, `nosnippet`, `max-snippet:0` | on every page meant to be quoted |
| Main content in the server's first HTML response | view the raw response; the key paragraphs and tables are there |
| No content behind a click, tab, accordion script or login | all panels in the HTML |
| Status 200, one canonical URL per topic | no parameter or duplicate variants |
| Pages load without consent or bot walls for crawlers | check a crawler user agent in the logs for 200s |

## 2. Quotable page pattern

- The question the page answers is in the title and the first heading.
- A direct answer in the first 100 words, in plain sentences that stand alone when lifted out.
- Facts as text and HTML tables, with units and dates. No facts only in images.
- One topic per URL; stable URLs; a visible "updated" date that matches the real last change.
- Named author or organisation, and how the facts were obtained. Original numbers with their method earn mentions; restated common knowledge does not.
- Definitions, comparisons and steps under descriptive headings, so a passage can be cited by section.
- Outbound sources linked. Claims an assistant can verify elsewhere are safer to repeat.

Not tactics: text written for bots and hidden from people, pages mass-produced to match prompts, or different content for crawlers than for visitors. Search spam policies apply to AI answers as well.

## 3. llms.txt format

Location: `/llms.txt` at the site root (a sub-path file may cover its own section). Markdown, in this order:

1. One H1 with the site or project name. The only required element.
2. An optional blockquote with a short summary.
3. Optional plain paragraphs or lists with detail (no headings).
4. Zero or more H2 sections, each a list of links: `- [Name](https://absolute.url): optional note`.
5. By convention an H2 named `Optional` holds links a reader may skip when short of context.

Example:

```
# Example Docs

> Documentation for Example, a tool for scheduling data jobs. Covers install, the job file format and the HTTP API.

Versions before 2.0 use a different job format; see the migration guide.

## Docs

- [Quick start](https://www.example.com/docs/quick-start.md): install and first job in five minutes
- [Job file reference](https://www.example.com/docs/job-file.md): every field with defaults
- [HTTP API](https://www.example.com/docs/api.md): endpoints, auth, rate limits

## Optional

- [Changelog](https://www.example.com/changelog.md)
```

Rules of thumb: an index of entry points, not a copy of the sitemap; link to Markdown versions when they exist; absolute URLs; keep it in step with the site in the same release process. Advertise it from pages with `<link rel="describedby" href="/llms.txt">` if wanted.

## 4. Markdown versions of pages

- Serve a clean Markdown version at the page URL plus `.md` (or `index.html.md` for directory URLs): title, summary, the facts, then the body. No navigation, ads or scripts.
- The HTML page points to it: `<link rel="alternate" type="text/markdown" href="...">`.
- The Markdown response points back and stays out of the search index: `Link: <html-url>; rel="canonical"` and `X-Robots-Tag: noindex`.
- Same facts as the HTML page. Generate both from one source and test that key values match.
- Optional: answer `Accept: text/markdown` on the HTML URL with the Markdown version, using a separate cache key.
- Text taken from third parties (user posts, repository files) is labelled as such in the Markdown, because an agent reading it may otherwise treat instructions inside it as the site's own.

## 5. Measuring

| Signal | How |
|---|---|
| Crawler access | Requests per crawler token per day with status codes, from server or CDN logs; verify tokens against published IP ranges |
| Referral visits | Sessions whose referrer is an assistant's domain, per month |
| Citations | A fixed list of 20 to 50 prompts the site should answer, run monthly by hand or with a tracking tool; record whether the site is cited |
| Search-engine AI answers | Counted inside normal web search totals in the engine's console; there is no separate report |
| Index health | Indexed pages against submitted pages in each engine's console |

Give a baseline before changes and a date for the re-check. One reading proves nothing.

## 6. What is established and what is not

Established by operators' documentation (read 2026-11-20): which token does what; that blocking an answer-search crawler removes the site from that assistant's search answers; that the main search engine needs indexing and snippet eligibility and no special file for its AI answers, and does not use llms.txt.

Not established: that any assistant reads llms.txt; that Markdown versions increase citations; any ranking factor inside an assistant. The llms.txt format itself is a community proposal (`llmstxt.org`, read 2026-11-20). Present these as low-cost options, not as fixes.
