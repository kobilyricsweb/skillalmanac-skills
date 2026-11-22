---
name: nextjs-practices
description: Reviews and fixes Next.js App Router code - where to put use client, data fetching and caching, loading and error files, metadata and SEO, route.ts vs server actions, next/image - using version-tagged decision tables and a scanner for client files importing server-only code, pages missing loading, error or metadata, and raw img tags. Use when the user asks to review an app/ directory, asks why a Next.js page is slow or stale, or how to cache, revalidate, add metadata or write a route handler. Do not use for generic React hooks and state, the pages/ router, or other frameworks.
license: Apache-2.0
compatibility: The scanner needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checks in step 3 by hand and say the scanner was not run.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Next.js App Router practices

Scope: choices that exist only because of the App Router (server/client boundary, caching, route files, metadata). Component state, effects, keys and memoisation are a different job; use a React skill for those.

## Step 0: pin the version

Read `package.json` for the `next` major, then check `next.config.*` for `cacheComponents`. Every rule below is tagged with the major it applies to; an untagged rule holds for 13.4 and later. If the major is not 14, 15 or 16, say so and treat version-tagged rows as unverified. Details and sources: [references/version-facts.md](references/version-facts.md) (read the section for the detected major only).

## Server or client: decide per component, bottom-up

Default is server. Add `use client` to the smallest leaf that needs one of these triggers, never to a page, layout or a wrapper around a whole section.

| Trigger found in the component | Decision |
|---|---|
| `useState`, `useEffect`, `useRef`, `useReducer`, `useContext` consumer, event handler props (`onClick`) | Client leaf |
| Browser API (`window`, `localStorage`, `IntersectionObserver`) | Client leaf |
| Library that calls hooks or touches the DOM (charts, maps, editors) | Client leaf, loaded with `next/dynamic` if over about 50 KB |
| Reads cookies, headers, a database, a secret, the filesystem | Server; add `import 'server-only'` to the data module |
| Only renders props and static markup | Server |
| Needs both (list from the database, one button inside) | Server parent fetches, passes plain serialisable props to a client leaf |
| Context provider | Client file containing only the provider; the layout stays server and passes `children` through it |

Props crossing server to client must be serialisable: no functions (except Server Actions), class instances or `Date` methods you rely on. A server component can be passed to a client component as `children` or another prop; a client file cannot import a server component.

Server-only code reached from a client file fails the build or leaks to the bundle. Mark every module that touches secrets or a database with `import 'server-only'`; mark browser-only helpers with `import 'client-only'`. The scanner finds direct imports and one level of local indirection.

## Data fetching and caching

Fetch in the server component that renders the data, not in a parent that forwards it. Three rules:

1. **Parallel by default.** Two awaits that do not depend on each other become `Promise.all`, or start both promises before the first `await`. Sequential awaits are legitimate only when the second needs the first's result. Preload with a function call before a `Suspense` boundary when a child will need the data.
2. **Cache by intent.** Pick one row; do not mix.

| Content | Choice | Majors |
|---|---|---|
| Same for everyone, changes on a schedule | `fetch(url, { next: { revalidate: N } })` or a page `export const revalidate = N`; N from the content's real refresh interval, not 60 by habit | all |
| Same for everyone, changes on an event | tag the fetch (`next: { tags: [...] }`) and call `revalidateTag` in the mutation | all (in 16 the one-argument form is deprecated, not removed: pass a cache-life profile as the second argument; verify against nextjs.org (unconfirmed)) |
| Per user (cookies, auth header) | Dynamic render; do not cache; wrap the slow part in `Suspense` | all |
| Database call, no `fetch` | wrap in `unstable_cache` (14, 15) or a `use cache` function (16 with `cacheComponents`) | 14 to 16 |
| Plain `fetch` with no option | cached by default in 14; not cached in 15 and later | 14 vs 15+ |

3. **Deduplicate shared reads.** `fetch` calls with the same URL and options are deduplicated within one render; database calls are not. Wrap shared database reads (the same row in `generateMetadata` and the page) in React `cache()`.

Client-side fetching is for data that depends on user interaction after load, or that must refresh live. Use a data library there; do not move server-renderable content into `useEffect`.

## Loading, error and not-found

For every route segment whose `page` awaits data:

- `loading.tsx` in that folder or a parent (instant shell; it wraps the page in `Suspense`). Where only part of the page is slow, a local `<Suspense fallback>` is better than a segment-wide loading file: it keeps the fast parts visible.
- `error.tsx` in that folder or a parent. It must start with `use client` and receives `error` and `reset`. It does not catch errors from the layout in the same folder; put a boundary one level up, and add `global-error.tsx` for the root layout.
- Call `notFound()` for a missing record and give the folder a `not-found.tsx`; never render an empty page with status 200 for a missing slug.

## Metadata and SEO

- Every server `page` exports `metadata` (static) or `generateMetadata` (dynamic segments, data-driven titles). Client pages cannot export either; move the page to a server file.
- Set `metadataBase` once in the root layout, or relative Open Graph and canonical URLs break.
- Use the `title.template` pattern in the root layout and a plain `title` per page; do not hand-write `<head>` tags in the App Router.
- Per page set `description` and `alternates.canonical`. Set `robots: { index: false }` for filter, search-result and private pages.
- Generate `app/sitemap.ts` and `app/robots.ts` as route files; split sitemaps when one list exceeds 50,000 URLs (`generateSitemaps`).
- Structured data goes in a `<script type="application/ld+json">` rendered from the server component, with every `<` in the serialized JSON replaced by the six-character sequence `<` (backslash, u, 0, 0, 3, c) so a string value cannot close the script tag.
- `opengraph-image.tsx` files may use raw `<img>`; they render with `ImageResponse`, not the DOM.

## Route handlers and server actions

| Need | Use |
|---|---|
| A form or button in your own UI mutates data | Server Action (`use server`); validate input on the server; revalidate the affected path or tag |
| A webhook, a mobile client, a third party, a non-HTML response | `route.ts` handler |
| Read data for your own pages | Neither: fetch in the server component |
| Streaming response, file download, cron endpoint | `route.ts` |

Rules: a folder cannot hold both `route.ts` and `page.tsx`. Treat every Server Action and handler as a public endpoint: authenticate and authorise inside it. Verify webhook signatures on the raw body (`await request.text()`) before parsing. `GET` handlers are cached by default in 14 and not in 15 and later.

## Images and fonts

Use `next/image` for content images: give `width` and `height` (or `fill` with a sized parent), and `priority` only on the single largest above-the-fold image. Remote hosts need `images.remotePatterns` (not the deprecated `domains`). Keep a raw `<img>` only for `data:` URIs, tiny inline SVG-like assets and image-generation files, and mark any other with the `no-img-element` lint disable comment so the scanner counts it as suppressed. Load fonts with `next/font`, not a stylesheet link.

## Workflow

```
- [ ] 0 Version pinned
- [ ] 1 Scan
- [ ] 2 Fix errors, then warnings, in the order below
- [ ] 3 Judge what the scanner cannot see
- [ ] 4 Re-scan
- [ ] 5 Report
```

1. Run `python scripts/next_scan.py scan <app_dir>` (use `src/app` if that is where routes live). Run it; do not edit it to make a check pass.
2. Fix in this order: `route-page-conflict` and `client-imports-server` (errors, break builds or leak code); `client-at-tree-top` (move `use client` down, then the page can export metadata); `missing-loading` and `missing-error`; `missing-metadata`; `img-tag`; `possible-waterfall` (info; confirm the second await really is independent).
3. By hand, check what the script cannot: unnecessary `use client` on a leaf with no trigger from the table; caching choice per the table; auth inside Server Actions; `Suspense` placement; canonical and robots on filter pages.
4. Re-scan until `ok` is true and nothing remains that you did not decide to keep.
5. Report in this shape:

```
Version: <next major, router, cacheComponents on/off>
Scanner: <errors>/<warnings>/<info> before, <errors>/<warnings>/<info> after
Fixed: <rule: files, one line each>
Kept on purpose: <finding and why, e.g. img in a partner widget with the lint comment>
Judgement changes: <client boundary moves, cache choices, with the table row used>
Not checked: <anything run-time: real caching behaviour, build output, Core Web Vitals>
```

## Scanner contract

`python scripts/next_scan.py scan <app_dir> [--strict]` prints one JSON object:

```
{"tool":"next_scan","version":1,"root":str,"files_scanned":int,
 "findings":[{"rule":str,"severity":"error|warn|info","file":str,"line":int,"message":str}],
 "counts_by_rule":{rule:int},"suppressed":int,"strict":bool,"ok":bool}
```

`ok` is false when any error exists, or any warn with `--strict`. Exit 0 ok, 1 findings fail the run, 2 bad usage or missing directory (message on stderr). Rules: `client-imports-server`, `client-at-tree-top`, `missing-loading`, `missing-error`, `missing-metadata`, `img-tag`, `possible-waterfall`, `route-page-conflict`. A loading or error file in any parent folder counts as covering a page. Pages under `@slot` and intercepting folders skip the metadata rule; folders starting with `_` are skipped.

## Limits

- The scanner is text-based, not a TypeScript parser. It misses imports built dynamically, path aliases other than `@/` and `~/`, and server-only code reached through two or more local modules.
- `missing-loading` and `missing-error` treat any `await` or `fetch(` in a server page as fetching; a page that only awaits `params` is flagged too. Decide by reading.
- `possible-waterfall` is a heuristic for consecutive same-indent `const x = await ...` lines; it cannot see waterfalls across components.
- Apostrophes in JSX text can hide the rest of that line from the comment stripper.
- Nothing here measures runtime caching, bundle size or Core Web Vitals; the report says so.
- Version facts were written from the author's knowledge of the docs and are not re-fetched on each run; confirm against the installed version's docs when a row is decisive.
