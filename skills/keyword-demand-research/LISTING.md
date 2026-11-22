## תקציר

- ה-skill מודד ביקוש חיפוש לנושא: מאחד וריאנטים קרובים כדי לא לספור פעמיים, מסווג כוונה, קורא מגמה בחלונות קבועים ומדווח מה לא נמדד.
- כולל script לא מקוון (Python, ספריה סטנדרטית) שמקבץ, מסכם ומסמן קפיצה חד-פעמית, התאוששות של חודש אחד ומונח חדש.
- אין מפתחות API בתוך ה-skill: הנתונים באים מייצוא של המשתמש או מחשבון ה-API שלו, עם תקרת הוצאה.
- טיוטה: לא לפרסום לפני סקירה אנושית ובדיקה בכלים נוספים.

---

# Listing page content: keyword-demand-research

**One line:** Turn a keyword export into a de-duplicated demand figure with intent labels and an honest trend reading.

## What it does

The skill sets six ground rules (every number from a file, count each search need once, say what each number is, classify before totalling, name the trend window, the user's account and budget) and a six-step workflow: fix the question, collect in rounds, cluster and measure, read the top by eye, read the trend, report. A script merges close variants (same words after plural and punctuation, or identical monthly series), labels intent from editable word rules, separates brand-navigational and excluded meanings, and prints raw, de-duplicated and counted totals with trend readings and flags.

## Capabilities

- `keyword_cluster.py`: clusters, raw vs de-duplicated totals, intent table, trend label per cluster, flags (`one-off-spike`, `one-month-rebound-after-decline`, `new-in-last-12-months`), optional per-keyword CSV.
- A collection method for paid keyword APIs: balance check, spend cap, raw-response cache, ledger, rounds, stop rule.
- Trend-reading rules with the wording to use and the traps (near-zero base, one-month rebound, season with one cycle).
- A fixed report layout with a 'limits and not obtained' line.

## When to use

Sizing demand for a topic before a content plan; checking a claim such as 'up 300%'; deciding which topics to write first from an export; planning a keyword study on your own API account.

## When not to use

Auditing a page, writing the article, paid-ads bid planning, app-store keyword metadata.

## Requirements

Python 3.9+ (standard library). No network. Keyword data from the user's own export or API account. Tested in one tool only (see Evidence).

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved runs)

1. Prompt: "How big is the search demand we can actually target with articles, and which 5 topics should we write first?" with a 36-keyword export. Saved run: `evals/runs/k1-demand-size/with_skill/reply.md`. It reports raw 334,477 against de-duplicated 175,710, removes three competitor brands and two other meanings, and flags the Black Friday spike. The same model without the skill passed 6 of 7 assertions (trend statements without periods).
2. Prompt: "My cofounder says habit-tracker searches rebounded 20%+ last month and the AI angle is up thousands of percent. Is the topic growing?" Saved run: `evals/runs/k2-trend-check/with_skill/reply.md`. It names both windows, the January peak and the near-zero base; the baseline double counted plural variants.

## Limits

- Clusters on spelling and identical series, not on meaning.
- Intent rules are English word lists; many keywords come out `unclassified` until rules are added.
- Keyword tools do not see searches inside AI assistants or marketplaces.
- The script was the calculator for the with-skill runs; the fixture's ground truth was built by hand in the eval builder, not by the script.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model (sonnet alias), one tool, 2026-11-20. Blind grading: 3 of 3 preferred with the skill, 0 tie, 0 preferred without. Static lint 0 FAIL. Token overhead about +8% per run. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Show the 36-row export and a bare sum: 334,477 searches a month.
2. Run the script: 24 clusters, 175,710 de-duplicated, 130,410 counted after brands and other meanings.
3. Zoom on three flags: the Black Friday spike, the one-month rebound, the new term.
4. End on the report block with 'limits and not obtained'.

## FAQ seeds

- Does it call a keyword API? No. It reads your export; the reference explains how to pull data with your own account and cap.
- Does it embed or ask for API keys? No.
- Which tools' exports work? Any CSV with a `keyword` column and monthly columns ending in YYYY-MM.
- Why is my total smaller than the tool's? Close variants share one number; the raw sum counts them twice.
- Does it forecast traffic? No. Searches are not visits.
- Other languages? Clustering works; intent needs your own rules file.
- What leaves my machine? Nothing.

## Changelog

- 0.1.0 (2026-11-20): first batch version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
