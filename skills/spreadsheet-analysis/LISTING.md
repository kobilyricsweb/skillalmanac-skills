## תקציר

- תוכן עמוד ה-skill: עונה על שאלות על קובץ Excel או CSV אחרי בדיקת הנתונים, לא לפניה.
- מוצא שורות סיכום בתוך הנתונים, כפילויות, מספרים שנשמרו כטקסט, איות שונה של אותה קטגוריה וערכים חריגים.
- כל מספר מחושב ב-script, והתשובה מפרטת מה הוצא מהחישוב. בלי רשת, בלי שינוי הקובץ המקורי.
- במבחן, גם עוזר בלי ה-skill הגיע למספרים הנכונים; היתרון שנמדד הוא בפירוט ובהסבר.
- טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: spreadsheet-analysis

**One line:** Get totals from a spreadsheet that you can repeat in a meeting, with a list of what was wrong in the file.

## What it does

You share a CSV or Excel file and ask a question. Before any figure is given, a script audits the file for the things that quietly break totals: a Total row sitting inside the data, the same order entered twice, "North" and "north " counted as two regions, amounts typed as text, blanks, a value that looks like a typo. The figures are then computed by the script, not read by eye, and the answer states what was left out and shows the figure both ways where the choice matters.

## Capabilities

- An audit report of data problems with row numbers.
- Sums, averages and distinct counts, by category, with and without duplicates, or one row per key (for example per email).
- Reads .csv, .tsv and .xlsx with the Python standard library; never writes to your file.
- A reconciliation against the file's own total row.
- A fixed answer shape: the figure first, then how the data was treated and what to fix.

## When to use

Someone sends an export and asks for totals by region, spend by category, or how many unique customers; the totals in a sheet do not add up; you want to know whether a file is clean before sending it on.

## When not to use

Writing formulas, building charts or models, forecasting, database queries, converting PDFs.

## Before and after (from saved test runs)

**Without the skill.** A sales export has a Total row of 66,925. Summing the Amount column in a spreadsheet gives a different figure again, because eight amounts are text and two orders are entered twice.

**With the skill.** "North was the biggest region ... 24,700 ... Row 40 ('Total', 66,925) is a total row. It was left out ... SO-1009 (file rows 10 and 17) and SO-1023 (rows 25 and 33) ... 'North' was typed five ways ... The file's own total of 66,925 is wrong. It equals the sum that skips the 8 text amounts and still counts the two duplicates."

## Requirements

Python 3.9 or newer for the script (standard library only). No network access. English wording is assumed by the script.

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved test runs)

1. Prompt: "Here's our Q3 sales export. What were total sales per region, and which region was biggest?" Result: `evals/runs/s1-sales-by-region/with_skill/answer.md`. All figures equal the independent ground truth; blind score 9 against 8.
2. Prompt: "How many unique customers do we have, and what's our monthly revenue by plan?" Result: `evals/runs/s3-unique-customers/with_skill/answer.md`. 50 customers and 1,540 a month, both correct; tie with the plain assistant (9 and 9).

## Limits

- In testing, the plain assistant also reached every correct figure. The measured gain is detail and explanation, not correctness.
- Exact duplicates only; rows that differ by a typo are not detected.
- Excel dates appear as serial numbers; formulas are read as their last saved value; merged cells and hidden rows are not interpreted.
- Old .xls and password-protected files are not supported.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Blind grader: with skill preferred in 2 of 3, 1 tie. Static check: 0 fails. Token overhead about +9%. Not tested: other tools, real triggering, repeated runs, human review.

## Demo script (60 to 90 seconds)

1. Open the sales CSV; scroll to the Total row: 66,925.
2. Run the audit: five numbered problems appear, with row numbers.
3. Run `--sum Amount --by Region`: two blocks, duplicates kept and removed; North 24,700.
4. Show the answer: figure first, then why the file's own total is wrong.

## FAQ seeds

- Will it change my file? No. It only reads.
- Does it need Excel installed? No. Python 3.9 or newer.
- Does it work with Google Sheets? Export to .xlsx or .csv first.
- Does it need internet access? No.
- How is it different from asking an assistant to analyse a file? It forces an audit before any figure and a statement of what was excluded. In our test both got the numbers right; the skill's answers explained more.
- Can it handle large files? Not tested beyond about 60 rows.

## Changelog

- 0.1.0 (2026-11-20): first version, batch 01.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
