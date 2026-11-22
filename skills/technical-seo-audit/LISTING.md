## תקציר

- ה-skill בודק עמודים ואתרים קטנים מול רשימת בדיקות מדידה: כותרות, תיאורים, canonical, robots ו-noindex, sitemap, hreflang ותוכן ב-HTML הגולמי.
- כולל script לא מקוון שקורא קבצי HTML שמורים ומצליב אותם מול robots.txt וה-sitemap; כל ממצא מסומן כ'כלל מתועד' או 'מוסכמת כלים'.
- אין הבטחות דירוג, ותמיד יש רשימת 'לא נבדק'.
- טיוטה: לא לפרסום לפני סקירה אנושית ובדיקה בכלים נוספים.

---

# Listing page content: technical-seo-audit

**One line:** Audit pages and small sites for technical SEO against measurable thresholds, with documented rules kept apart from tool conventions.

## What it does

Six ground rules (measure then judge, label the basis, signals must agree, check the raw response, no ranking promises, say what was not checked) and a six-step workflow: scope, collect, run the page check, complete the site-level checks from a checklist, prioritise, report. The script parses saved HTML and reports rule-coded findings; with a `urls.csv`, robots.txt and sitemap.xml in the folder it also finds contradictions between files (in the sitemap but noindex, blocked but noindex, canonical elsewhere, non-reciprocal hreflang).

## Capabilities

- `seo_page_check.py`: about 30 rule ids, FAIL / WARN / NOTE, each with basis `search-engine-doc` or `convention`.
- A checklist reference with thresholds for page-level, site-level and performance gates, and a table of which signal wins in a conflict.
- A fixed report with verdict, prioritised table, conflicts explained, not checked, re-test.
- Sources with the date read.

## When to use

Pre-launch review; 'why is this page not indexed'; a crawl export to triage; checking whether a tool score of 100 means done.

## When not to use

Keyword research, content writing, link building, structured-data design, performance engineering.

## Requirements

Python 3.9+ (standard library). The script makes no network calls; pages are fetched first with the agent's own tools or supplied by the user. Tested in one tool only (see Evidence).

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved runs)

1. Prompt: "Our pricing page has not shown up in Google for three weeks. Lighthouse gives it SEO 100." Saved run: `evals/runs/t2-not-indexed/with_skill/reply.md`. It names the canonical pointing at the staging host, gives the corrected tag and flags `max-snippet:0`. The baseline found the same cause but added a recrawl time estimate, which the grader marked as a promise.
2. Prompt: "Here is our crawler export. The tool's health score is 96, so are we done?" Saved run: `evals/runs/t3-crawl-export/with_skill/reply.md` (blind score 10 against 7): every seeded problem with a numeric threshold.

## Limits

- Static HTML only: no redirects, status codes, rendered DOM, performance, link graph or index status.
- Zero findings does not mean the site will rank.
- On the full-site task the baseline model found every seeded blocker too (tie): the gain is thresholds, basis labels and no promises, not detection.
- Rules follow one search engine's documentation.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model (sonnet alias), one tool, 2026-11-20. Blind grading: 2 of 3 preferred with the skill, 1 tie, 0 preferred without. Static lint 0 FAIL. Token overhead about +8% per run. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Show the saved folder: eight HTML files, urls.csv, robots.txt, sitemap.xml.
2. Run the script: 7 FAIL, 13 WARN, 6 NOTE; highlight 'in the sitemap but noindex' and 'robots.txt blocks the URL, so the noindex cannot be read'.
3. Show the basis column: title length is `convention`.
4. End on the report's 'Not checked' list.

## FAQ seeds

- Does it crawl my site? No. It reads HTML you saved.
- Does it need network? The script, no.
- Will fixing these make me rank? No promise is made.
- Why is title length only a warning? Search engines document no character limit.
- Does it validate schema? Only that JSON-LD parses.
- What leaves my machine? Nothing.
- Can it read a crawl export? The skill's checklist covers it by hand; the script does not.

## Changelog

- 0.1.0 (2026-11-20): first batch version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
