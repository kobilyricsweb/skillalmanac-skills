---
name: spreadsheet-analysis
description: Answers questions about a spreadsheet (.csv, .tsv, .xlsx) by auditing the data before calculating. A bundled script finds total rows inside the data, duplicate rows, numbers stored as text, spelling variants, mixed dates, blanks and extreme values, then computes sums, averages and distinct counts, stating what was excluded. Use when the user shares an Excel or CSV file and asks for totals, averages, counts, a breakdown by category, a summary, or whether the data looks right. Do not use for writing formulas or charts, financial modelling, forecasting, or database queries.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer (standard library only) and reads .csv, .tsv and .xlsx. No network access is used. Without Python, follow the manual checks in the reference file.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Spreadsheet analysis

Give the user a number they can repeat in a meeting. Most wrong answers from spreadsheets come from the data, not the arithmetic: a total row summed with its own parts, an order entered twice, "North" and "north " counted as two regions, amounts typed as text. Audit first, compute second, and say what was done.

## Ground rules

1. **Audit before any figure.** No total, average or count is reported until the audit has run on that file.
2. **Compute, never eyeball.** Every figure comes from the script or from code, not from reading rows.
3. **Never change the user's file.** Work on what is read; describe fixes instead of applying them to the original.
4. **No silent choices.** Every row left out and every value reinterpreted is listed in the answer. When a choice changes the answer, show the figure both ways.
5. **Keep suspicious values, flag them.** An extreme value stays in the main figure unless it is impossible; the answer also gives the figure without it and asks.
6. **Stay inside the data.** Do not explain why a number moved, forecast, or advise on what to do unless the user asks, and then label it as interpretation.

## Workflow

### 1. Audit

```bash
python scripts/sheet_profile.py data.xlsx
```

For a workbook with several sheets add `--sheet N`. Read the `DATA PROBLEMS` list in full. For what each problem does to a result and the default treatment, see [references/data-problems.md](references/data-problems.md); read the entries for the problems the audit reported.

### 2. Decide the treatment

Defaults, unless the user says otherwise:

| Problem | Treatment | Say it? |
|---|---|---|
| Total or subtotal rows in the data | Left out of every calculation | Yes |
| Exact duplicate rows | If the table has an ID column that should be unique (order number, invoice number), remove the repeats. If not, keep them and give the figure both ways | Yes, with row numbers |
| Same category spelt with different case or spaces | Merged | Yes, list the variants |
| Numbers stored as text ("$1,200", "(300)", "12%") | Read as numbers; brackets mean negative | Yes |
| Blank numeric cells | Left out of sums and averages; never treated as zero | Yes, with the count |
| Extreme value | Kept; figure also given without it | Yes, with the row |
| Mixed or ambiguous dates | Do not group by month until the day/month order is confirmed or provable from the data (a day above 12) | Yes |
| Repeated values in a column that should be unique (emails, IDs) after ignoring case and spaces | Count each once for "how many unique"; list the rows | Yes |

If the user can answer and a choice moves the result materially, ask one question before finalising. Otherwise apply the default and show both figures.

### 3. Compute

```bash
python scripts/sheet_profile.py data.xlsx --sum Amount --by Region
python scripts/sheet_profile.py data.xlsx --mean Amount --by Category
python scripts/sheet_profile.py data.xlsx --count-distinct Email
python scripts/sheet_profile.py data.xlsx --sum Fee --by Plan --unique-by Email
```

Each run prints the result with duplicates kept and with exact duplicates removed, and what was left out. `--unique-by` adds a result that keeps one row per distinct value of a key column, for tables where the same customer or order was entered more than once with small differences. For anything the script cannot compute (date filters, several conditions, joins), write code that applies the same treatments, and check one figure a second way.

### 4. Reconcile

- If the file has its own total row, compare it with the computed total. A difference is a finding: name the rows that explain it.
- Check that group figures add up to the overall figure.
- Check the row count used against the audit's row count minus what was excluded.

### 5. Report

Use this shape and save it as `answer.md` when a file is requested:

```
Answer: <the figure or the table, first>
How the data was treated: <rows left out, variants merged, text read as numbers; with counts and row numbers>
Problems to fix in the file: <each problem, the rows, and the effect on the answer>
Figure both ways: <only where a choice changes the answer>
Not checked: <what the audit cannot see>
```

Do not edit the script to change a result. If the script cannot run, apply the manual checks in the reference file and state that the audit was manual.

## Limits

- Exact duplicates only. Two rows that differ by a typo are not detected.
- Dates in .xlsx files are stored as serial numbers and appear as numbers; the script does not convert them.
- Formulas are read as their last saved value. Merged cells, hidden rows and colour coding are not interpreted.
- The audit finds structural problems. It cannot tell whether a value is true.
- Old .xls files and password-protected workbooks are not supported.
