# Why saltmarsh-guides.example does not appear in ChatGPT or Claude answers

## Short answer

The robots.txt is not the cause. It allows everything, and the offline check finds no FAIL or WARN. The block happens at the CDN. The dashboard export shows the managed rule "Block AI bots" switched On since 2026-07-02 (ticket OPS-311, "reduce scraper load"). The CDN checks requests before they reach the origin, so the robots.txt file never gets a say. The access log from 17 Nov 2026 confirms it: the answer-search crawlers that build the index for ChatGPT and Claude get 403 responses.

## Decision (assumed, owner has not confirmed)

- Answer search (OAI-SearchBot, Claude-SearchBot, PerplexityBot, and the user-requested fetchers): allow. This is assumed from the goal of appearing in assistant answers.
- Model training (GPTBot, ClaudeBot, Google-Extended): not decided. Left to the owner.
- Classic search (Googlebot): allow.

## Evidence

Log sample, 17 Nov 2026, status codes by crawler:

| Crawler | Kind | Path | Status | Hits |
|---|---|---|---|---|
| OAI-SearchBot | answer search | /guides/tide-tables-explained | 403 | 6 |
| Claude-SearchBot | answer search | /guides/tide-tables-explained | 403 | 3 |
| ClaudeBot | training | /guides/reading-a-chart | 403 | 4 |
| PerplexityBot | answer search | /guides/reading-a-chart | 403 | 1 |
| GPTBot | training | /guides/tide-tables-explained | 200 | 2 |
| Googlebot | search | both pages | 200 | 5 + 1 (robots.txt) |

The 403 responses are 512 bytes each, which looks like a CDN block page, not the guide.

Per OpenAI's documentation (read 2026-11-20 in the skill reference), a site that blocks OAI-SearchBot is not shown in ChatGPT search answers. Anthropic's documentation says blocking Claude-SearchBot may reduce visibility in search results.

## Other problems found

1. **Mixed blocking, unexplained.** GPTBot gets 200 on the same guide while OAI-SearchBot gets 403. The export does not show the managed rule's match criteria, so the cause of the split cannot be confirmed from these files. Ops should read the rule's scope.
2. **Page is marked nosnippet.** The tide-tables page has `<meta name="robots" content="index, follow, nosnippet">`. That stops Google from showing snippets for the page, which Google's AI features need. This is a page-level setting that the owner should decide on, separately from the CDN.
3. **Content is not in the first HTML response.** The saved raw HTML has an empty `<main id="root">` and loads two JavaScript bundles. Crawlers that do not run JavaScript see no guide text. Fix by rendering the guide content on the server.
4. **The raw HTML export does not match the logged responses.** The saved HTML file is 511 bytes, but the 200 responses in the log are 4180 bytes for the same guide. Either the export is partial or bots are served a different version. This needs checking on the live server.
5. **robots.txt size differs.** The log shows a 96-byte robots.txt response, while the saved file is 102 bytes. The file may have changed since the log was taken. Not a cause of the problem, but worth confirming.
6. **Crawler identity not verified.** The IP ranges in the log (20.171.207.x for OAI-SearchBot, 160.79.104.x and 160.79.105.x for Anthropic bots) cannot be checked offline. Verify them against the operators' published IP lists before trusting the log lines or writing firewall rules.

## What to change (owner decision needed)

1. **CDN (the main fix).** Turn off the managed "Block AI bots" rule, or scope it to training crawlers only (GPTBot, ClaudeBot, Google-Extended) if the owner wants training blocked. OAI-SearchBot, Claude-SearchBot, PerplexityBot, ChatGPT-User and Claude-User should not be blocked. If the goal of OPS-311 was load, use the existing per-IP rate limit (120 req/min) or a bot-score rule instead of a blanket block. OpenAI and Perplexity say changes can take about 24 hours to take effect.
2. **Page template.** Remove `nosnippet` from pages that should be quoted. Check whether other guide pages carry the same tag; only the tide-tables page was in the sample.
3. **Server rendering.** Put the guide text into the first HTML response.
4. **robots.txt.** No change needed. The current file is correct for the decision above. The full file as it stands:

```
User-agent: *
Allow: /
Disallow: /account/

Sitemap: https://www.saltmarsh-guides.example/sitemap.xml
```

If the owner wants the intent written down, add one comment per group. Do not add AI-specific groups, because they are not needed for this decision.

5. **llms.txt.** Not needed for ChatGPT or Claude visibility. Google states it does not use llms.txt. No operator documentation read for this task shows that any assistant reads it. Optional only.

## Not checked

- The CDN rule's match criteria (only the on/off state is in the export).
- Live robots.txt and the live guide HTML (only the saved copies were available).
- Other crawlers in the list: Claude-User, ChatGPT-User and Perplexity-User do not appear in the sample.
- Microsoft, Apple, Meta, Amazon and Common Crawl crawlers were not read for this task.

## Unproven

- Whether unblocking the CDN brings citations. Being indexed and snippet-eligible comes first; the index state of these pages is not in the export.
- Whether the empty HTML shell limits what assistants can quote.

## Measure

- Crawler status codes per token per day from the CDN or server logs, before and after the CDN change. Expect 200s from OAI-SearchBot, Claude-SearchBot and PerplexityBot about a day after the change.
- Referral visits from chatgpt.com, claude.ai and perplexity.ai per month.
- A fixed list of 20 to 50 prompts the guides should answer, re-run monthly. Record a baseline first.

Facts read on: crawler facts reference dated 2026-11-20 (no live re-read; no web access for this task).

Files used: robots.txt, cdn_settings.md, guide_page_raw.html and access_log_sample.txt from the a3_pack folder in the work folder.
