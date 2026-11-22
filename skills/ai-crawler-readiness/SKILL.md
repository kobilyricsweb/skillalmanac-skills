---
name: ai-crawler-readiness
description: "Makes a website readable and citable for AI assistants and AI crawlers: an explicit robots.txt policy that separates training crawlers from answer-search crawlers and user-requested fetches, a spec-conformant llms.txt, Markdown versions of pages, and an offline script that shows what each AI crawler may fetch. Use when the user asks about AI search visibility, GEO or AEO, llms.txt, blocking or allowing AI bots in robots.txt, AI training opt-out, or why assistants do not cite their site. Do not use for a general SEO audit, keyword research or writing the content itself."
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only) and makes no network calls; it reads saved robots.txt and llms.txt files. Fetching the live files uses the agent's own tools. Without Python, trace each crawler's group by hand using the precedence rules in the reference.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# AI crawler readiness

Decide, on purpose, what AI systems may do with a site, then make that decision true in the files and make the content easy to quote. Most damage here is accidental: a rule meant for a training crawler that also removes the site from AI answers, or a new bot-specific group that silently drops every private path the general group protected.

## Ground rules

1. **Three kinds of access, three decisions.** Training crawlers collect text for model training. Answer-search crawlers build the index an assistant cites from. User-requested fetchers load one page because a person asked. Blocking one does not block the others. Ask the owner for a decision on each; never assume.
2. **Facts from the operators' own pages, with a date.** Crawler names and behaviour are read from [references/crawler-facts.md](references/crawler-facts.md), and re-read from the operators' documentation when network access is available. Do not write a crawler token from memory.
3. **robots.txt is a request.** Some user-requested fetchers state that they may not follow it. Real blocking needs server or firewall rules, and the published IP lists.
4. **No promises of citation.** No file makes an assistant cite a site. State what each change does and what is unproven. The main search engine states that it does not use llms.txt and needs no special files for its AI answers.
5. **Being indexed comes first.** AI answers in search engines draw on pages that are indexed and allowed to show a snippet. Check that before anything AI-specific.
6. **Never hide content for bots or show bots different content.** Markdown versions carry the same facts as the HTML page.

## Workflow

### 1. Get the decision

Ask, or read from the request, the owner's choice for each row. Write it down before touching a file.

| Access | Typical choice | Consequence of blocking |
|---|---|---|
| Model training | allow or block | content not used to train future models |
| Answer-search index | allow | site not shown in that assistant's search answers |
| User-requested fetch | allow | the assistant cannot open the page when a person asks about it |
| Classic search engines | allow | out of search results and the AI answers built on them |

### 2. Collect the current state

Save the live `robots.txt` (and `llms.txt` if one exists). Note anything that sits in front of the server: a CDN "block AI bots" switch, a managed robots.txt, a firewall rule, a login wall. These override the file without showing in it. If server logs are available, pull a sample of requests from the crawler names in the reference with their status codes.

### 3. Check access

```bash
python scripts/ai_access_check.py robots.txt --paths ROOT,blog/a-post,docs/ --private admin/,cart/ --expect "OAI-SearchBot=allow,GPTBot=block"
```

Use real paths from the site. `--paths` takes public content paths (write `ROOT` for the home page and leave the leading slash off the others, because some shells rewrite arguments that start with a slash). `--private` takes paths no crawler should fetch; any crawler allowed there is a FAIL. `--expect` holds the owner's decision for the public paths; a mismatch is a FAIL. Read every WARN: the common ones are a bot with its own group that no longer inherits the `*` disallows, a misspelled token that controls nothing, and an answer-search crawler blocked by mistake.

### 4. Write the policy

Edit robots.txt following the precedence rules and the patterns in [references/crawler-facts.md](references/crawler-facts.md):

- one group per decision, listing every token that shares it;
- every bot-specific group repeats the private-path disallows from the `*` group;
- comments state the intent of each group;
- keep the `Sitemap:` line.

Re-run the script on the edited file with the same `--private` and `--expect` until it prints no FAIL and every WARN is intended.

### 5. Make the content readable

Work through [references/readable-surfaces.md](references/readable-surfaces.md) for the parts in scope:

- **Raw HTML**: the main content and the key facts are in the first response, not behind scripts, tabs or logins.
- **Snippet eligibility**: no `noindex`, `nosnippet` or `max-snippet:0` on pages meant to be quoted.
- **Quotable pages**: a direct answer near the top, facts as text and tables, visible dates and authors, a stable URL per topic.
- **llms.txt**: write it to the format in the reference, then lint it with `python scripts/ai_access_check.py --llms llms.txt`.
- **Markdown versions**: where the site can serve them, with a canonical link back to the HTML page.

### 6. Report

```
Decision: training <allow/block>; answer search <allow/block>; user fetch <allow/block>
Before: <one line per crawler whose access did not match the decision>
Changed: <files and the lines changed>
After: <script result: FAIL/WARN counts; the access table>
Outside the files: <CDN, firewall, login walls: checked / not checked>
Unproven: <llms.txt effect; citation outcome>
Measure: <assistant referral visits; crawler hits by name and status in logs; a fixed set of prompts re-run monthly>
Facts read on: <date of the crawler reference, or today's re-read>
```

Deliver the full new robots.txt and llms.txt as files or code blocks, not as fragments.

## Limits

- The script reads files. It cannot see a CDN or firewall block, a login wall or what a crawler really does; logs are the only proof of access.
- Crawler names, purposes and compliance statements change. The bundled table carries the date it was read.
- The table covers the operators named in the reference. Others need their own documentation read before a rule is written for them.
- Whether any assistant reads llms.txt or prefers Markdown versions is not established by any operator's documentation read for this skill.
