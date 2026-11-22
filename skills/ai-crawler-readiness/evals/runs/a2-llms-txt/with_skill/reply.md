# Reply: will llms.txt get Tidewater Jobs into Google AI Overviews and ChatGPT answers?

Short answer: no, not by itself. The llms.txt file is low-cost and harmless, but neither product's documentation says it is used to decide what appears in answers.

## Google AI Overviews

Google's Search documentation (changelog dated 15 June 2026, read 2026-11-20) says llms.txt files are not needed for Search and do not affect visibility or ranking. AI features in Search use pages that are indexed and eligible to show a snippet. So for AI Overviews, what matters is that the key pages are indexed, have no `noindex`, `nosnippet` or `max-snippet:0`, and have their main content in the first HTML response. The llms.txt file does none of that.

## ChatGPT answers

ChatGPT search draws on OpenAI's answer-search crawler, `OAI-SearchBot`. Per OpenAI's crawler documentation (read 2026-11-20), a site that blocks it is not shown in ChatGPT search answers. So the things that decide ChatGPT visibility are:

- `robots.txt` must allow `OAI-SearchBot` (and the site must not block it at the CDN or firewall);
- the pages must be fetchable with a 200 status and readable as text.

We did not receive the live `robots.txt` or any server logs, so we have not checked either. That is the first thing to verify.

## What llms.txt does and does not do

- It is a community proposal (llmstxt.org, read 2026-11-20), not a standard that any assistant has documented as reading it. We found no operator statement that ChatGPT, Claude or Perplexity read it.
- We wrote it as an index of entry points from the page list, with the docs linked to their `.md` versions, and the less central pages under "Optional". It lints with 0 FAIL and 0 WARN.
- Whether Markdown versions of the docs increase citations is not established either.

## What would actually move the needle

1. Check `robots.txt` and any CDN "block AI bots" setting. Decide, on purpose, whether to allow `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot` and the user-requested fetchers. Training crawlers (`GPTBot`, `ClaudeBot`, `Google-Extended`) are a separate decision.
2. Confirm the key pages are indexed in Google Search Console and Bing Webmaster Tools, and that no page carries `noindex` or `nosnippet`.
3. Check that the pricing, docs and security pages put their main facts in the raw HTML, not behind scripts or tabs.
4. Give the quotable pages a direct answer near the top, with visible dates and authors.
5. Measure: assistant referral visits per month, crawler hits by name and status code in logs, and a fixed list of 20 to 50 prompts re-run monthly. Record a baseline before changes.

## Assumptions and gaps

- The page list is taken from the sitemap extract in a2_site_pages.md. The URLs are not verified against the live site.
- We assumed every `/docs/...` page has a `.md` twin, as the page list says "docs pages". If any does not, its link in llms.txt will 404 and should be changed to the HTML URL.
- No robots.txt was edited; this task covered llms.txt only.
- The crawler facts come from the skill's reference file, read 2026-11-20. They change; re-read before relying on them.
