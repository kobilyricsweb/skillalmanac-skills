---
name: structured-data-jsonld
description: "Writes and validates JSON-LD structured data (schema.org markup) for web pages: picks the type that fits the page, says whether it still earns a rich result, enforces rating and review policy, and checks syntax, required properties and visible-content parity with an offline script. Use when the user asks to add schema markup, structured data, JSON-LD, rich snippets, review stars, breadcrumbs or FAQ schema, or to fix structured-data errors. Do not use for a full SEO audit, for writing page content, or for Open Graph and meta tags."
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only) and makes no network calls. The final confirmation uses the search engine's public rich-result tester, run by the user or the agent's own browser tools. Without Python, check required properties by hand against the reference tables.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.1"
  network: none
---

# Structured data (JSON-LD)

Describe what is on the page, in the vocabulary search engines read, without claiming anything the page does not show. Markup that validates but misstates the page (stars the site awarded itself, an FAQ block that earns nothing, ratings copied from another site) is a failed job and can cost the site its rich results.

## Ground rules

1. **Mark up only what a visitor can see.** Every value in the markup (rating, count, price, author, date, answer text) appears in the page's visible content and comes from the same data.
2. **One page, one subject.** Pick the single main entity the page is about. Everything else is a reference to it or a supporting node.
3. **Be honest about the payoff.** For each type say one of: earns a rich result, restricted, retired, or semantic only. Check [references/rich-result-status.md](references/rich-result-status.md) rather than memory; features are retired every year.
4. **Ratings are opinions about one item.** `aggregateRating` holds only ratings given by the site's own users. A site's own verdict on one product may be marked up as a single `Review` by its named author, with the scale stated in `bestRating`, when the page is that review; it is never placed in `aggregateRating`. Never mark up ratings gathered from other sites, a star count from a code host, ratings on a list or category page, or a business's reviews of itself.
5. **Valid is not shown.** Correct markup makes a page eligible; it does not promise a rich result. Say so in the hand-over.
6. **Do not delete working markup to tidy up.** Retired types are harmless; remove them only when the user wants less to maintain.

## Workflow

### 1. Read the page

From the HTML or the template, list: the page's subject, the facts that are visible (name, dates, author, price, ratings and their count, breadcrumb trail, video, questions), and any existing JSON-LD. If a fact needed by the markup is not visible, it is either added to the page first or left out of the markup.

### 2. Choose types

Use the decision table in [references/rich-result-status.md](references/rich-result-status.md): find the row for the page kind, take the main type, and note the status. When the user asks for a type that is retired (FAQ, how-to) or not allowed for the page (ratings on a list), say so plainly, name what the page can use instead, and continue with that.

### 3. Write the graph

Follow [references/authoring-patterns.md](references/authoring-patterns.md) for the node layout and required properties of each type. In short:

- one `<script type="application/ld+json">` with `"@context": "https://schema.org"` and an `@graph` array;
- stable absolute `@id` values (`{canonical URL}#fragment`); describe a node fully once, refer to it by `@id` elsewhere;
- absolute URLs; ISO 8601 dates with a time zone;
- server-rendered in the first HTML response.

### 4. Check

```bash
python scripts/jsonld_check.py page.html
python scripts/jsonld_check.py page.html --page-type list   # category, list and comparison pages
```

The script reports FAIL (broken syntax, missing required property, bad date or rating, rating on a list page), WARN (retired type, value not visible on the page, relative URL, self-serving rating) and NOTE (recommended property missing). Fix every FAIL, decide each WARN, and re-run until the output is clean or each remaining line is explained. Run it on the whole page, not only the snippet, so the visible-content comparison works. Do not edit the script to silence a finding.

### 5. Confirm outside

The script does not replace the search engine's own tester. Tell the user to run the page or the code through the public rich-result test and the schema.org validator before shipping, and to watch the structured-data reports in the search console after. If browser tools are available and the user agrees, run the test and report the result.

### 6. Hand over

```
Page: <URL or template>   Subject: <main entity>
Markup: <types emitted>
Expected result: <rich result name / restricted to X / none (semantic only) / retired>
Left out on purpose: <requested markup not emitted, with the reason>
Visible-content check: <values compared, result>
Script: <FAIL/WARN/NOTE counts, or "not run">
Still to do: <official tester, console report, facts to add to the page>
```

Then the JSON-LD block itself, ready to paste.

## Limits

- The script checks structure and a fixed table of required properties. It does not know every schema.org type or every feature rule, and its tables age.
- The visible-content comparison is a text search; it can miss a value shown as an image or flag one formatted differently.
- Eligibility rules follow one search engine's public documentation on the date in the reference file. Other engines publish less and may differ.
- Markup does not improve ranking by itself and cannot make thin content eligible.
