# robots.txt changes: AI citation allowed, training blocked

Source: a1_robots.txt. New file: robots_new.txt. No web access was available, so every crawler token below comes from my own knowledge (cutoff June 2026). Check each token against the vendor's current documentation before deploying.

## What changed

1. **Fixed a broken block.** The original file blocks `GPT-Bot`. That is not OpenAI's token, so the rule never matched and GPTBot was never blocked. The new file blocks `GPTBot`.
2. **Blocked training crawlers.** `GPTBot`, `ClaudeBot`, `anthropic-ai` (older Anthropic token, kept), `Google-Extended`, `Applebot-Extended`, `Meta-ExternalAgent`, `Bytespider`, `CCBot` (Common Crawl, kept). All get `Disallow: /`.
3. **Allowed citation and user-triggered bots.** `OAI-SearchBot` and `ChatGPT-User` (ChatGPT), `Claude-SearchBot` and `Claude-User` (Claude), `PerplexityBot` and `Perplexity-User` (Perplexity). Each has its own group repeating the original Disallow lines. A crawler with its own group ignores the `*` group, so the repeat keeps the admin, checkout and internal-search paths blocked.
4. **Unchanged.** The `*` group and the Sitemap line are as before, so Googlebot and Bingbot keep full access.

## Decisions for Legal

- **Google AI Overviews cannot be removed with robots.txt alone.** `Google-Extended` only controls use for Gemini training and grounding. AI Overviews are governed by Googlebot, and blocking Googlebot removes the site from Search. The only page-level options are `nosnippet` or `data-nosnippet` (removes snippets in Search too) or `noindex` (removes the page from Search). Either one is a product decision, so I did not add them.
- **Extra training bots.** `Applebot-Extended`, `Meta-ExternalAgent` and `Bytespider` go beyond the original list because they match the stated goal. Remove them if Legal wants only the named bots.
- **Unknown crawlers.** Any bot not listed falls under `*` and is allowed. Blocking all unknown bots would require allowlisting Googlebot and Bingbot by name, which I did not do.

## Limits

- robots.txt is a request, not enforcement. Some crawlers are reported not to honour it. Enforcement needs a CDN or WAF rule.
- Some user-triggered bots (`ChatGPT-User`, `Perplexity-User`, `Claude-User`) may not be bound by robots.txt, because they fetch on a user's behalf. Allowing them is what makes citation work, but it is not a guarantee.
- Do not deploy until the tokens above are confirmed against current vendor docs.
