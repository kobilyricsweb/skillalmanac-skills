# AI crawler facts and robots.txt patterns

Every row was read from the operator's own documentation on 2026-11-20 (URLs under Sources). Operators add and rename crawlers; re-read before relying on a row, and say in the report which date applies.

## Contents

1. Crawler table
2. robots.txt precedence rules
3. Policy patterns
4. What sits outside robots.txt
5. Sources

## 1. Crawler table

| robots.txt token | Operator | Kind | What the operator says |
|---|---|---|---|
| `GPTBot` | OpenAI | training | Crawls content that may be used in training generative models. Disallowing it signals the content should not be used for that |
| `OAI-SearchBot` | OpenAI | answer search | Surfaces sites in ChatGPT search. Sites that opt out are not shown in search answers, though they can still appear as navigational links. Changes take about 24 hours |
| `ChatGPT-User` | OpenAI | user-requested | Acts on a person's request in ChatGPT and custom GPTs; not automatic crawling; "robots.txt rules may not apply"; not used to decide what appears in search |
| `OAI-AdsBot` | OpenAI | ads | Visits only pages submitted as ads, to check them |
| `ClaudeBot` | Anthropic | training | Collects web content that could contribute to model training |
| `Claude-SearchBot` | Anthropic | answer search | Improves search result quality; blocking may reduce visibility and accuracy in search results |
| `Claude-User` | Anthropic | user-requested | Fetches when a person asks a question; blocking may reduce visibility for user-directed search |
| `PerplexityBot` | Perplexity | answer search | Surfaces and links sites in results; stated as not used to crawl for foundation-model training |
| `Perplexity-User` | Perplexity | user-requested | Fetches on a person's request; "generally ignores robots.txt rules" |
| `Google-Extended` | Google | control token | Controls use for training Gemini models and for grounding; no separate user-agent string; does not affect inclusion in Google Search |
| `Googlebot` | Google | search engine | Search crawling; AI answers in Search use indexed, snippet-eligible pages and need no extra files or markup |

Other statements read the same day:

- Anthropic's crawlers honour robots.txt and the non-standard `Crawl-delay`; blocking by IP address is not advised as an opt-out; ranges are published.
- OpenAI and Perplexity publish IP ranges as JSON files per crawler, for firewall allow or block rules.
- Perplexity says robots.txt changes can take up to 24 hours to be reflected.
- Google's documentation changelog (15 June 2026) says llms.txt files are not needed for Search and do not affect visibility or ranking; keeping them for other services is fine.
- A training-preference signal using a `__usage_ai-training` user-agent name is announced by Google for a later date; treat it as not yet in effect.

Not read for this version, so write no rule for them without reading their operator's page first: Microsoft's, Apple's, Meta's, Amazon's and Common Crawl's crawlers.

## 2. robots.txt precedence rules

1. A crawler uses **one group**: the group whose `User-agent` line names it. Only if no group names it does it use the `*` group.
2. A crawler with its own group **ignores the `*` group completely**. Disallows for `/admin/` or `/cart/` under `*` do not apply to it unless repeated.
3. Several `User-agent` lines in a row share the rules that follow.
4. Inside a group the **longest matching path wins**; `Allow` wins a tie. Order of lines does not matter.
5. `Disallow:` with an empty value allows everything. `Disallow: /` blocks everything.
6. Token matching is case-insensitive; the token must be the documented one. `User-agent: GPT-Bot` controls nothing.
7. A robots.txt that returns a server error can stop crawling; one that returns an HTML page is treated as garbage. It must be plain text with status 200.

## 3. Policy patterns

Cited in answers, not used for training (the private paths are repeated in every group):

```
# Everyone else
User-agent: *
Disallow: /admin/
Disallow: /cart/

# Model training: not allowed
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
Disallow: /

# Answer search and user-requested fetches: allowed, private paths still closed
User-agent: OAI-SearchBot
User-agent: Claude-SearchBot
User-agent: PerplexityBot
User-agent: ChatGPT-User
User-agent: Claude-User
User-agent: Perplexity-User
Disallow: /admin/
Disallow: /cart/

Sitemap: https://www.example.com/sitemap.xml
```

Open to everything: no AI-specific groups are needed; the `*` group applies. Add groups only to state the intent in comments.

Closed to AI entirely: one group listing all the tokens above with `Disallow: /`. Say plainly that user-requested fetchers may still load pages and that enforcement needs firewall rules on the published IP ranges. Blocking `Google-Extended` does not remove the site from Search or from AI answers inside Search; only `noindex`, `nosnippet` or blocking `Googlebot` does that, at the cost of search visibility.

## 4. What sits outside robots.txt

| Layer | What to check |
|---|---|
| CDN or host bot settings | A "block AI bots" switch or managed robots.txt overrides the origin's file |
| Firewall and rate limits | 403 or 429 responses to crawler user agents in the logs |
| Login, paywall, consent wall | The crawler receives the wall, not the content |
| Page-level directives | `noindex`, `nosnippet`, `max-snippet:0`, `data-nosnippet` on the passages meant to be quoted |
| Rendering | Content injected by scripts is missing for crawlers that do not run them |
| Impostors | A user-agent string proves nothing; verify with the operator's IP list or reverse DNS before trusting a log line |

## 5. Sources

Read on 2026-11-20:

- OpenAI crawler overview: `developers.openai.com/api/docs/bots` (redirect target of `platform.openai.com/docs/bots`).
- Anthropic help article "Does Anthropic crawl data from the web, and how can site owners block the crawler?": `support.claude.com/en/articles/8896518`.
- Perplexity crawler guide: `docs.perplexity.ai/guides/bots`.
- Google common crawlers: `developers.google.com/search/docs/crawling-indexing/google-common-crawlers`.
- Google AI features and your website: `developers.google.com/search/docs/appearance/ai-features`.
- Google Search documentation changelog: `developers.google.com/search/updates`.
- Group and matching rules: RFC 9309 (Robots Exclusion Protocol), from the author's knowledge of the standard, not re-opened.
