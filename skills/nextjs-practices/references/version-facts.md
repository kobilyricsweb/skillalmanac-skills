## Contents

- Next.js 14
- Next.js 15
- Next.js 16
- Upgrade traps by direction
- Where to confirm

Facts are stated in our own words. Each section lists what changes behaviour the skill depends on. Confirm decisive rows against the docs of the installed version.

## Next.js 14

- App Router is stable (since 13.4). Server Actions are stable.
- `fetch` with no cache option is cached (treated as `force-cache`). Opt out with `cache: 'no-store'` or `export const dynamic = 'force-dynamic'`.
- `GET` route handlers that do not read the request are cached as static by default.
- `params` and `searchParams` are plain objects; `cookies()` and `headers()` are synchronous.
- Client-side router cache keeps visited dynamic pages for about 30 seconds and static ones for about 5 minutes.
- Database and non-`fetch` data: `unstable_cache` is the caching tool.
- Partial prerendering is experimental.

## Next.js 15

- `fetch` with no option is not cached; set `cache: 'force-cache'` or a `revalidate` value to cache. `GET` route handlers are not cached by default; opt in with `export const dynamic = 'force-static'`.
- `params`, `searchParams`, `cookies()`, `headers()` and `draftMode()` return promises. Synchronous access still works with a warning in 15 and is removed in 16; use `await`, or `use()` in a client component. A codemod exists.
- The client router cache no longer reuses page segments by default (stale time 0 for dynamic pages); it can be raised with `experimental.staleTimes`.
- React 19 is the supported React for the App Router.
- `after()` (run work after the response is sent) is stable from 15.1; it was `unstable_after` in 15.0.
- `next/dynamic` with `ssr: false` is not allowed inside a Server Component; put it in a client file.
- `next/form` gives a form that navigates with prefetching and progressive enhancement.
- Turbopack for `next dev` is stable.

## Next.js 16

- Turbopack is the default bundler for dev and build.
- `cacheComponents: true` in config enables the `use cache` directive (file, component or function level) and replaces the older experimental flags for dynamic IO and partial prerendering. With it on, uncached dynamic access outside `Suspense` is reported as a build error (exact wording and behaviour: verify against nextjs.org (unconfirmed)). Cache lifetime is set with `cacheLife`, invalidation with `cacheTag`; the built-in `cacheLife` profile names and their durations: verify against nextjs.org (unconfirmed).
- `revalidateTag` takes a second argument naming a cache-life profile; the one-argument form is deprecated, not removed (exact deprecation status: verify against nextjs.org (unconfirmed)). For read-your-writes inside a Server Action use `updateTag`; `refresh()` re-renders the current page without touching the cache.
- `middleware.ts` is renamed `proxy.ts` (export `proxy`); it runs on the Node runtime. The old name still works with a deprecation notice during the transition.
- Synchronous access to `params`, `searchParams`, `cookies()` and `headers()` no longer works; `await` is required.
- The `next lint` command is removed; run the linter directly.
- Image defaults changed: `images.minimumCacheTTL` defaults to four hours, `images.qualities` defaults to a single value (75), and local images with query strings need `images.localPatterns`. `images.domains` is deprecated in favour of `remotePatterns`.
- Parallel route slots require an explicit `default.tsx`.

## Upgrade traps by direction

| From to | Silent change to look for |
|---|---|
| 14 to 15 | Pages that were cached through plain `fetch` become dynamic and slower; add `revalidate` or `force-cache` where staleness is acceptable. Static `GET` handlers become dynamic. |
| 14 or 15 to 16 | Code that read `params` synchronously breaks; `revalidateTag('x')` without a profile is deprecated; middleware file name; local images with query strings fail. |
| 16 with `cacheComponents` | A page with an uncached `await` and no `Suspense` may fail at build rather than at run time (verify against nextjs.org (unconfirmed)). |

## Where to confirm

- https://nextjs.org/docs/app (App Router docs, version selector at the top)
- https://nextjs.org/docs/app/guides/upgrading (per-major upgrade guides and codemods)
- https://nextjs.org/blog/next-15 and https://nextjs.org/blog/next-16 (release notes for the changes above)
- https://nextjs.org/docs/app/getting-started/caching (caching model per version)
- https://nextjs.org/docs/app/api-reference/functions/generate-metadata (metadata fields)
