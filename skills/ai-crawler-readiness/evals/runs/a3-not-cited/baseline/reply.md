# Why saltmarsh-guides.example never appears in ChatGPT or Claude answers

## Short answer

robots.txt is not the problem. It allows everything except /account/, so it is not what keeps the AI answer engines away. The block happens at the CDN edge: the Cloudflare-style managed rule "Block AI bots", switched on 2026-07-02 (ticket OPS-311, "reduce scraper load"), returns HTTP 403 to the AI search and answer crawlers before the request ever reaches the origin. Those crawlers never get a page, so they cannot index or cite it.

## Evidence

**1. The CDN blocks the AI crawlers that feed answers (main cause).**
In the 22-line access log sample, every request from an AI search or answer crawler got 403 (512-byte response, consistent with a block page):

| User agent | Requests | Status |
|---|---|---|
| OAI-SearchBot/1.4 (ChatGPT search index) | 6 | 403 |
| ClaudeBot/1.0 | 4 | 403 |
| Claude-SearchBot/1.0 | 3 | 403 |
| PerplexityBot/1.0 | 1 | 403 |
| GPTBot/1.4 (training crawler) | 2 | 200 |
| Googlebot/2.1 | 6 | 200 |

The CDN export (2026-11-18) shows "Block AI bots (managed rule)" = **On**, enabled 2026-07-02. The site has been invisible to these crawlers since then, which matches "we never show up". robots.txt says Allow, so the two signals disagree; the CDN rule wins because it answers first.

**2. The block is not uniform, and the export does not explain why.**
GPTBot got 200 while OAI-SearchBot got 403 on the same site in the same window. So the managed rule is matching some AI user agents and not others, or matching by something other than UA (IP, ASN, or a bot score). The export does not show the rule's scope. Check the rule's match list in the dashboard before changing anything else.

**3. Bot Fight Mode is also on.**
Bot Fight Mode can challenge or block non-browser clients beyond the managed rule. The sample shows 403s, not challenge pages, so it is not the visible cause here. It should still be reviewed, because it can hit the same crawlers.

**4. The rate limit is not the cause.**
120 req/min per IP is far above what the sample shows (one request per hour per crawler IP). Under-attack mode is off.

**5. Even when allowed, the raw HTML gives crawlers nothing to read (second blocker).**
The guide's raw HTML (511 bytes) has an empty `<main id="root" data-guide="...">` and loads all content through two JavaScript bundles. Googlebot renders JavaScript, so it can see the page. Many AI crawlers fetch the raw HTML without rendering JavaScript, so once the edge block is lifted they would still see an empty shell. Server-render or prerender the guide text.

**6. nosnippet on every guide page (third blocker).**
`<meta name="robots" content="index, follow, nosnippet">` tells engines not to show text snippets from the page. That removes the quotable excerpts that answer engines use when they cite a source. This is a template-level setting. Remove it unless the team has a reason to keep it. Confirm how each AI engine treats nosnippet in its own docs; this review had no web access.

## Things that do not add up (verify before relying on them)

- The log reports 4180 bytes for the 200 responses, but the raw HTML file is 511 bytes. Either the logged response is different from the file exported, or the size field is wrong. The robots.txt is 102 bytes in the file and 96 bytes in the log. Confirm which response the log and the export refer to.
- The log sample is 22 lines. It shows the pattern but not volumes or trends. Pull a full-week count per user agent before drawing conclusions about scale.
- User agent strings can be spoofed. None of the IPs were verified against the vendors' published crawler IP ranges or reverse DNS (no web access here). Do this before allowlisting any IP, and do not allowlist by UA string alone.

## Recommended actions

1. **Decide the policy with ops (owner decision).** Ops enabled the block to cut scraper load. Get load numbers for the AI crawlers, then decide which bots to keep blocked. A sensible split is to block training crawlers (GPTBot, and any others the team chooses) and allow the search and answer crawlers (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, ClaudeBot, PerplexityBot) if the team wants citations.
2. **Change the CDN rule.** Either turn off the managed "Block AI bots" rule, or add a skip/allow rule for the search and answer agents, verified by IP or reverse DNS. Keep rate limits in place for load control.
3. **Remove `nosnippet`** from the guide template, or limit it to pages that truly should not be quoted.
4. **Server-render the guide body** (SSR or prerender) so the text is in the first HTML response.
5. **Verify after each change.** Re-run the log filter for these user agents and confirm 200s with real content. Then check whether the guides appear in ChatGPT and Claude answers. Expect a delay: crawling and indexing by the engines take time after a block is lifted.

## Scope and limits

- Based only on the four files exported to this folder. No live testing, no web access, no CDN rule detail beyond the export.
- No conclusions about traffic volume or the crawl schedule of any engine.
