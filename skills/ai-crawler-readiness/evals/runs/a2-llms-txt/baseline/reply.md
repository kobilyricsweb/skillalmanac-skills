# Will llms.txt get us into Google AI Overviews and ChatGPT answers?

Short answer: no, not by itself. Publishing llms.txt is cheap and harmless, and it may help some tools that read it, but it is not the lever that decides whether Google or ChatGPT show us.

## What I know

- **Google AI Overviews.** Google has said publicly that it does not use llms.txt for Search or AI Overviews. Eligibility follows normal Search rules: the page must be crawlable, indexable, and eligible to appear in Google Search. Pages that rank and are useful for the query are what get pulled into AI Overviews. So the things that matter are indexing, crawl access, content quality, and matching the query intent.
- **ChatGPT answers.** I have no confirmed evidence that ChatGPT reads llms.txt when it answers questions. ChatGPT search uses OpenAI's own crawler and its search index. Whether our pages appear depends on whether that crawler can reach them (robots.txt must not block it), whether the pages are indexed, and whether they are relevant and authoritative for the question.

I could not verify either point against current documentation: this task had no web access, and my knowledge has a cutoff. Check Google's Search Central documentation on AI features and OpenAI's crawler documentation before relying on these statements.

## What the llms.txt I wrote does and does not do

- It gives a clean, curated map of the site (docs, product pages, key references) with a one-paragraph summary. That is useful for developers or tools that choose to ingest it, and for anyone who asks an assistant to read our docs.
- Docs pages are linked with the `.md` suffix, because the page list says those are served as Markdown. This is an assumption from the list: I did not check that each linked `.md` URL returns content. Verify before publishing.
- The page list gives titles and paths only. I had no page descriptions, so the one-line notes are short and based on titles. Improve them from the real page content if needed.
- I put login, sign up, legal, brand, and careers pages under "Optional", which signals that they are low priority for a reader or model.

## What would actually move the needle

1. Make sure the key pages (pricing, quick start, job file reference, API docs, FAQ, glossary, customer stories) are indexed in Google and Bing. Check Search Console and Bing Webmaster Tools.
2. Check robots.txt and any CDN or WAF rules, and confirm that OpenAI's crawler and Google's crawlers are not blocked.
3. Keep the HTML pages fully readable without JavaScript, with a clear title, a direct answer near the top, and accurate structured data where it applies.
4. Build authority: references from other sites, customer stories, and documentation that answers real questions people ask about scheduling, cron, and retries.
5. Track results directly: check whether our domain is cited in AI answers for our target queries, and compare with a baseline over several weeks.

Bottom line: llms.txt is a low-cost addition, not a route into AI Overviews or ChatGPT. Treat it as optional and spend the effort on the list above.
