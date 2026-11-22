# Listing page content: nextjs-practices

**One line:** Reviews Next.js App Router code with version-tagged decisions and a scanner for structural mistakes.

## What it does

The skill pins the Next.js major first, then applies decision tables for server vs client components, fetching and caching, loading and error boundaries, metadata, route handlers vs server actions, and images. A scanner walks an `app/` directory and prints strict JSON: client files that import server-only code, pages that fetch with no loading or error file above them, pages without metadata, raw `<img>` tags, independent awaits that run in sequence, and `route.ts` beside `page.tsx`. A fixed fix order and report shape come with it.

## Capabilities

- `scripts/next_scan.py scan <app_dir> [--strict]`: JSON findings with rule, severity, file, line; exit 1 on errors (or warnings with `--strict`)
- Decision tables tagged with the Next major (14, 15, 16)
- `references/version-facts.md`: behaviour changes between majors and upgrade traps
- A report that states what was and was not checked

## When to use

Review an `app/` directory; "where do I put use client"; a page that is slow or shows stale data; adding metadata or canonical URLs; choosing between `route.ts` and a Server Action; build errors about server code in client components.

## When not to use

Component state, effects, keys and memoisation (that is a React skill; this one covers only the decisions the App Router adds). The `pages/` router. Other frameworks. Visual design.

## How it differs from react-best-practices

That skill reviews React component correctness (hooks, state, effects, keys). This one starts where the framework adds rules: the server/client boundary, caching per Next major, route files, metadata. Its script reads route structure and import boundaries, not component bodies.

## Requirements

Python 3.9 or newer for the scanner (standard library only). No network. Without Python, the agent applies the checks by hand and says the scanner did not run.

## Install

To be generated at publication, one pinned command per tool; installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real fixture runs (`python evals/run_fixtures.py`, 6/6 pass):

1. `python scripts/next_scan.py scan evals/fixtures/bad_site/app` exits 1 with 11 findings: 3 `client-imports-server` in `dashboard/Chart.tsx` (lines 5 to 7: a local module that imports `server-only` and `pg`, `next/headers`, `node:fs`), `route-page-conflict`, `client-at-tree-top` on `settings/page.tsx`, and on `dashboard/page.tsx` missing loading, error and metadata, one `img-tag` (line 9) and one `possible-waterfall` (line 6). `ok` is false.
2. `python scripts/next_scan.py scan evals/fixtures/good_site/app` exits 0 with no findings and `"suppressed": 1` (a raw `<img>` carrying the `no-img-element` lint comment).

No with-skill agent run exists yet, so no saved agent output is shown.

## Limits

Text-based scanner, not a TypeScript parser; sees one level of local import indirection; `missing-loading` and `missing-error` treat any `await` in a server page as fetching; does not measure runtime caching, bundle size or Core Web Vitals; version facts come from the author's knowledge of the docs and were not re-fetched.

## Evidence

Static lint 0 FAIL / 0 WARN; scanner fixtures 6/6 on Windows with Python 3.11. Everything else (trigger tests, with/without task evals, cross-tool, human review) not done. See VERIFICATION.md.

## Demo script (60 to 90 seconds)

Prompt: "Review the app/ folder of this Next.js 15 project." Beat 1: the agent reads `package.json`, names the major. Beat 2: it runs the scanner; 3 errors show. Beat 3: it moves `use client` into a leaf and adds `import 'server-only'`. Beat 4: re-scan is clean; report lists what was kept and not checked. (To be recorded from a real run.)

## FAQ seeds

- Does it need network? No.
- Does it work with the `pages/` router? No.
- Does it run my build? No; it never executes your code.
- How is it different from a React skill? See above.
- Will it say which Next version a rule applies to? Yes; rules are tagged 14, 15 or 16.
- How do I uninstall? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

0.1.0, 2026-11-21: first draft; fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
