## תקציר

- ה-skill כותב ובודק JSON-LD: בוחר סוג לפי העמוד, אומר אם הסוג עדיין נותן תוצאה עשירה, ואוכף את כללי הדירוגים והביקורות.
- כולל script לא מקוון שבודק תחביר, שדות חובה, תאריכים, כתובות, דירוג בעמוד רשימה והתאמה לטקסט הגלוי.
- טבלת הסטטוס (FAQ ו-HowTo הופסקו) נקראה ממסמכי Google ב-2026-11-20 ונושאת תאריך.
- חולשה ידועה: במשימת תיקון השגיאות המדרג העדיף את התוצאה בלי ה-skill.

---

# Listing page content: structured-data-jsonld

**One line:** Write and check JSON-LD that matches the visible page, and say honestly which types still earn a rich result.

## What it does

Six ground rules (mark up only what is visible, one subject per page, be honest about the payoff, ratings are opinions about one item, valid is not shown, do not delete working markup) and a six-step workflow: read the page, choose types from a dated status table, write one linked graph, run the checker, confirm in the official tester, hand over. The script extracts every JSON-LD block, checks required properties for the main rich-result types, dates, URLs and rating ranges, flags retired types, rating markup on list pages and self-serving ratings, and compares marked-up ratings with the page's visible text.

## Capabilities

- `jsonld_check.py` for HTML or JSON input, with `--page-type list`.
- A status table: earns, restricted, retired, semantic only, with sources and the date read.
- Authoring patterns: graph skeleton, stable ids, required and recommended properties, two worked examples.
- A hand-over block that states the expected result and what was left out on purpose.

## When to use

Adding schema to a page or template; fixing structured-data errors; deciding whether FAQ, how-to, review or carousel markup is worth writing.

## When not to use

A full SEO audit, writing page content, Open Graph and meta tags, JSON Schema for APIs.

## Requirements

Python 3.9+ (standard library). No network. The final check in the search engine's own tester is done by the user. Tested in one tool only (see Evidence).

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved runs)

1. Prompt: "Make this 'best of' page eligible for review stars and a carousel." Saved run: `evals/runs/s3-list-page/with_skill/reply.md`. It removes all rating markup and says a carousel is not available; 5 of 6 assertions. The baseline kept per-item ratings on the list page and implied stars: 1 of 6.
2. Prompt: "Add schema so we get stars and FAQ dropdowns." Saved run (v0.1.1): `evals/runs/s1-review-article/with_skill/reply.md`: no FAQ promise, the marketplace rating left out, the editor's 8.7 out of 10 as one Review by the named author.

## Limits

- A fixed table of types; it ages. The status reference carries its date.
- The visible-text comparison is a text search.
- On the error-fixing task the with-skill output was judged worse than the baseline (it guessed a date and left a video node unresolved).
- Follows one search engine's documentation.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model (haiku alias), one tool, 2026-11-20. Blind grading: 2 of 3 preferred with the skill, 0 tie, 1 preferred without. Static lint 0 FAIL. Token overhead about +15% per run. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Show the list page with star markup on every item.
2. Run the script with `--page-type list`: three FAIL lines, 'ratings must be about one specific item'.
3. Show the status table row: carousel restricted, FAQ retired, with the date read.
4. Show the replacement markup and the hand-over line 'Expected result: none (semantic only)'.

## FAQ seeds

- Does FAQ schema still give dropdowns? Not since May 2026, per the documentation read on the date in the reference.
- Can I mark up ratings from another site? No.
- Can I mark up my own review score? As one Review by a named author on that product's review page; never as an aggregate.
- Does valid markup guarantee stars? No.
- Does it replace the official tester? No.
- Does it need network? No.
- What leaves my machine? Nothing.

## Changelog

- 0.1.1 (2026-11-20): one revision after the first eval runs; see VERIFICATION.md.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
