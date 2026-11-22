# Pre-relaunch SEO audit: northfield-kettles.example

Scope: the 8 template HTML files in the snapshot, urls.csv, robots.txt and sitemap.xml. I had no HTTP status codes, redirect behaviour, response headers, or the JS/image files, so anything that depends on those is flagged "unverified". Every finding below comes from the files themselves.

## Fix before Monday (blockers)

### 1. Copper kettle product page is set to noindex (copper-kettle.html)
- It carries `<meta name="robots" content="noindex, follow">` while also being self-canonical and listed in sitemap.xml. A product page being excluded and also submitted is almost certainly a leftover from staging or a template flag.
- Impact: the page will drop out of (or never enter) the index. This is the most costly item because it is a revenue page.
- Fix: remove the robots meta tag. Check the template and any staging-to-production config that sets it (steel-kettle does not have it). Re-check after deploy, and check any other product pages not in this snapshot.
- The same page has no meta description. Add one.

### 2. Steel kettle has two conflicting canonicals (steel-kettle.html)
- `https://www.northfield-kettles.example/steel-kettle` and `http://northfield-kettles.example/steel-kettle` (http, non-www) are both declared.
- Google ignores canonical hints when they conflict, so you lose control of which URL is chosen, and one of them points at an insecure non-www host.
- Fix: keep only the https www one. Probably two sources (template plus plugin or header injection) both emit a tag; find and remove the second.
- The page also loads its image over `http://cdn.northfield-kettles.example/steel.jpg`. On an https page this is mixed content (may be blocked or warned). Switch to https. Unverified: whether the CDN serves https.

### 3. Page 2 of the kettle list canonicalises to page 1 (kettles-page2.html)
- `/kettles?page=2` has canonical `/kettles`, but its content differs (the enamel range). Products linked only from page 2 may not get discovered or indexed through it, and the page is in the sitemap even though it tells Google it is a duplicate.
- It reuses the exact title and meta description of page 1.
- Fix: self-canonical `/kettles?page=2`, with a unique title (e.g. "Enamel kettles, page 2 | Northfield") and description. Page 1 correctly self-canonicals.

### 4. /sale: robots.txt block contradicts the noindex and the sitemap
- robots.txt has `Disallow: /sale`, the page has `noindex`, and sitemap.xml lists it.
- Google cannot read a noindex on a page it is not allowed to crawl, so the URL can still show in results as a bare link. Listing a blocked, noindexed URL in the sitemap is another mixed signal.
- Decide the intent:
  - Should rank: remove the Disallow and the noindex, keep it in the sitemap. (Title and description are already good.)
  - Should be hidden: keep noindex, remove the Disallow so the tag can be seen, and remove it from the sitemap.
- `Disallow: /sale` is a prefix rule and will also block any future `/sale-*` or `/sales/...` path.

### 5. Descaling guide: content only exists after JavaScript, plus broken schema and nosnippet (guide-descale.html)
- The body is an `<h1>` plus an empty `<div id="app"></div>` and two scripts. The raw HTML has no article text. Google can render JS, but later and less reliably, and many other crawlers and AI fetchers do not. Fix: server-side render or pre-render. Unverified: what guide.js outputs.
- The JSON-LD has a trailing comma (`"headline": "How to descale a kettle",}`), so it is invalid JSON and will be ignored. Fix the syntax and add the usual Article fields (author, datePublished, image).
- `<meta name="robots" content="nosnippet">` removes the snippet from results, hurting click-through on a page you want to rank. Remove it unless there is a reason.
- The title is about 87 characters and will be truncated. Shorten to about 60 (e.g. "How to descale a kettle in four steps").

## Fix soon (important, not launch-blocking)

### 6. German page and hreflang (index.html, de.html)
- index.html declares hreflang en and de, but de.html only declares itself. hreflang must be reciprocal, so Google will likely ignore the pair. Fix: put the same en + de set on both pages, plus `x-default`.
- de.html is `lang="de"` with a German title, description and H1, but the body paragraph is the English boilerplate. Translate it, or it reads as a mixed-language near-duplicate.
- /de/ is the only German URL; confirm that is intended.

### 7. Sitemap hygiene (sitemap.xml)
- It lists URLs that should not be there: /copper-kettle (noindex), /sale (noindex and blocked), /kettles?page=2 (canonical elsewhere). Sitemaps should list only indexable, self-canonical, 200 URLs.
- `http://www.northfield-kettles.example/about` is http, and is not in urls.csv or the snapshot, so I could not check it. Unverified: whether it exists, redirects or 404s. Fix the protocol and confirm a 200 with a self-canonical.
- Every lastmod is 2026-11-01, which looks auto-stamped. Search engines learn to ignore lastmod when it is unreliable. Use real dates or drop the field.
- robots.txt references the sitemap with an `http://` URL. Use https.

### 8. Same body copy on every template
- Index, kettles, page 2, copper, steel, sale and de all carry the identical English paragraph ("Northfield makes stovetop and electric kettles in small batches..."). Product pages have no price, specs or unique description beyond a name and image.
- Impact: thin and duplicate content across the site, which weakens each page. Fix: unique copy per product and category; move the boilerplate to a footer.
- No Product structured data on product pages. Add Product/Offer markup (price, availability) once real content exists.

## Minor clean-up
- index.html: hero image has no `alt`; the link text "click here" to the guide is non-descriptive (use "How to descale a kettle").
- kettles.html uses `<h3>` directly after the `<h1>` with no `<h2>`; page 2 uses `<h2>`. Make heading structure consistent.
- All pages share one og:image (`/img/og.jpg`); fine for launch. Unverified: that the file exists.
- Positives: every page has charset, viewport and a canonical (self-referencing except the two broken cases above); images have width/height, avoiding layout shift; robots.txt does not block JS/CSS or the whole site.

## Not verifiable from this snapshot
HTTP status codes and redirect chains (http to https, non-www to www, trailing slash: /de/ has one, other URLs do not), response headers (an `X-Robots-Tag` could override the meta tags), the /about page, /cart, image and JS files, page speed, internal linking beyond the home page, and whether staging is blocked.

## Suggested order of work
1. Remove noindex from copper-kettle (and check other products).
2. Remove the duplicate http canonical and the http image on steel-kettle.
3. Fix page 2 canonical, title and description.
4. Decide /sale intent and align robots.txt, meta robots and sitemap.
5. Fix the guide: server-render, valid JSON-LD, drop nosnippet, shorten title.
6. Make hreflang reciprocal with x-default; translate the de body copy.
7. Clean the sitemap and the robots.txt sitemap URL.
8. Replace the shared boilerplate and add product schema.
