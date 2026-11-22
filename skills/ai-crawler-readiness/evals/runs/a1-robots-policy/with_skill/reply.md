# robots.txt update: AI crawler policy

## Decision applied

- Model training: block (GPTBot, ClaudeBot, Google-Extended)
- Answer search (citations): allow (OAI-SearchBot, Claude-SearchBot, PerplexityBot)
- User-requested fetch: allow (ChatGPT-User, Claude-User, Perplexity-User)
- Classic search (Googlebot): unchanged, allowed

The request does not name the user-fetch choice. I allowed it because the owner wants citations, and blocking those fetchers would stop an assistant from opening a page when a person asks about it. Confirm this choice.

## Changes from a1_robots.txt

1. **GPT-Bot changed to GPTBot.** The old token was misspelled, so the group did nothing and OpenAI's training crawler was never blocked.
2. **Training group added.** GPTBot, ClaudeBot and Google-Extended now share one group with `Disallow: /`.
3. **Answer-search group added.** OAI-SearchBot, Claude-SearchBot and PerplexityBot are allowed, with the private paths repeated. Without the repeat, these bots would ignore the `*` group and could fetch `/admin/`, `/checkout/` and `/internal-search`.
4. **User-fetch group added.** ChatGPT-User, Claude-User and Perplexity-User are allowed, with the same private paths repeated. Their operators say robots.txt may not apply to these fetchers, so this group does not protect private paths on its own.
5. **anthropic-ai and CCBot kept blocked** as in the original file. Their operators' pages were not read for this review, so their rules are unverified.
6. **Private paths:** `/admin/`, `/checkout/`, `/internal-search` are closed to every crawler in every group.
7. **Sitemap line kept** unchanged.

## Check result (ai_access_check.py, offline)

- Before (a1_robots.txt): 6 FAIL, 1 WARN. GPTBot, ClaudeBot and Google-Extended were allowed everywhere, and GPT-Bot was flagged as an undocumented token.
- After (robots_new.txt): 0 FAIL, 0 WARN. Training crawlers are blocked; search and user-fetch crawlers are allowed on public paths; private paths are blocked for all.
- The script's test paths were `ROOT` and `articles/example-article`. The second is a placeholder, not a real article URL. Re-run with real article paths.

## Google's AI (legal's request): not fully achievable with robots.txt

- Google-Extended controls only Gemini training and grounding. Blocking it does not remove the site from Google Search or from AI Overviews and AI Mode. Operators' documentation says so, and the script prints the same note.
- Removing the site from AI features inside Search needs `nosnippet` or `max-snippet:0` on the pages, or blocking Googlebot. Both reduce or remove search visibility. This is an owner decision, not a robots.txt edit, and I did not make it.

## Not verified or not checked

- Crawler facts were read from the skill's reference dated 2026-11-20. No live re-read was done (no web access).
- Not checked: CDN or host "block AI bots" settings, firewall rules, login walls, page-level `noindex`/`nosnippet` tags. A CDN setting can override this file.
- Not checked: whether any assistant cites the site after this change. robots.txt does not guarantee citation, and the effect appears only after crawl and indexing. Robots.txt changes can take up to about 24 hours to take effect (per OpenAI and Perplexity).
- Server logs were not available, so no evidence of current crawler hits.

## Next steps for the owner

1. Confirm the user-fetch choice (allowed here).
2. Decide on Google AI Overviews: keep Search visibility (current file) or accept `nosnippet`/`noindex` on articles to leave AI answers in Search.
3. Check the CDN for a bot-blocking switch.
4. Verify after deploy with `curl` of the live robots.txt (plain text, status 200) and check logs for GPTBot, ClaudeBot and Google-Extended.
