## תקציר

- ה-skill מגדיר מדיניות מפורשת לסורקי AI ב-robots.txt (אימון, חיפוש-תשובות, שליפה לבקשת משתמש), כותב llms.txt לפי המפרט ומתכנן גרסאות Markdown.
- כולל script לא מקוון שמראה מה כל סורק רשאי לשלוף ומכשיל כשסורק עם קבוצה משלו מאבד את חסימות ה-`*`.
- עובדות הסורקים נקראו ממסמכי OpenAI, Anthropic, Perplexity ו-Google ב-2026-11-20; אין הבטחת ציטוט, ו-Google מצהירה שאינה משתמשת ב-llms.txt.
- במשימת robots.txt המודל הבסיסי השיג תיקו.

---

# Listing page content: ai-crawler-readiness

**One line:** Set an explicit AI-crawler policy, write a conformant llms.txt and make pages quotable, with facts read from the operators' own documentation.

## What it does

Six ground rules (three kinds of access and three decisions, facts from the operators' pages with a date, robots.txt is a request, no promises of citation, being indexed comes first, never show bots different content) and a six-step workflow: get the owner's decision, collect the current state, check access, write the policy, make the content readable, report. The script applies standard group precedence to a saved robots.txt for each documented AI crawler token, checks an expected policy and a list of private paths, warns about misspelled tokens, and lints llms.txt structure.

## Capabilities

- `ai_access_check.py`: access table per crawler and path, `--expect`, `--private`, `--llms`.
- A dated crawler table: token, operator, kind, what the operator says.
- robots.txt precedence rules and three policy patterns.
- llms.txt format, Markdown-version rules, a quotable-page pattern and a measuring table.
- A report that separates established facts from unproven ones.

## When to use

Deciding whether to block or allow AI bots; opting out of training without leaving AI answers; writing llms.txt; diagnosing why assistants never cite a site.

## When not to use

General SEO audits, keyword research, building scrapers, writing agent instruction files for a repository.

## Requirements

Python 3.9+ (standard library). No network for the script; live files are fetched with the agent's own tools. Tested in one tool only (see Evidence).

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved runs)

1. Prompt: "Write an llms.txt from this page list. Will this get us into Google AI Overviews and ChatGPT?" Saved run: `evals/runs/a2-llms-txt/with_skill/`: 33 curated links with an Optional section, lint clean, and a plain 'no promise' answer. The baseline listed all 40 pages including login and legal.
2. Prompt: "robots.txt allows everything but we never show up in ChatGPT or Claude answers. Why?" Saved run: `evals/runs/a3-not-cited/with_skill/reply.md`: the CDN bot-block rule from the 403 lines in the log, the nosnippet tag and the script-rendered page.

## Limits

- Reads files only; a CDN or firewall block is visible only in logs.
- Crawler facts change; the table carries its date and covers four operators.
- No evidence that any assistant reads llms.txt.
- On the robots.txt task the baseline produced an equally correct file (tie).

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model (haiku alias), one tool, 2026-11-20. Blind grading: 2 of 3 preferred with the skill, 1 tie, 0 preferred without. Static lint 0 FAIL. Token overhead about +12% per run. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Show a robots.txt with `User-agent: GPT-Bot` and a new `OAI-SearchBot` group that says `Allow: /`.
2. Run the script with `--private admin/`: FAIL, the search bot may now fetch /admin/; WARN, GPT-Bot is not a documented token.
3. Show the corrected file and the access table: training blocked, answer search allowed, private paths closed for all.
4. End on the report line 'Unproven: llms.txt effect; citation outcome'.

## FAQ seeds

- Will llms.txt get me cited? No operator documentation says so; Google says it does not use it.
- Does blocking the training bot remove me from AI answers? No, they are separate crawlers.
- Does blocking Google-Extended remove me from AI Overviews? No.
- Is robots.txt enforcement? No; some user-requested fetchers say they may not follow it.
- Which bots are covered? The ones in the dated table; others need their documentation read first.
- Does it need network? The script, no.
- What leaves my machine? Nothing.

## Changelog

- 0.1.0 (2026-11-20): first batch version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
