---
name: data-analysis-eda
description: Runs a disciplined exploratory data analysis on a CSV, with a fixed seven-stage procedure (shape, types, missingness, distributions, outliers, relationships, leakage and time checks), a profiling script that prints strict JSON, and a findings contract where every claim carries evidence and a caveat. Use when the user says explore this CSV, EDA, profile this dataset, what is in this data, sanity-check before modelling, or find anything odd in this file. Do not use for building models, charts or dashboards, cleaning or rewriting the data, testing one stated hypothesis, or SQL and spreadsheet formula help.
license: Apache-2.0
compatibility: The profiling script needs Python 3.9 or newer, standard library only, no network. Without Python, follow the manual fallback in the Script section.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Data analysis EDA

Describe the data; prove nothing. The output of this skill is a profile, a short list of findings in a fixed contract, and a list of questions for the data owner. Causes, forecasts and decisions are out of scope.

## Ground rules

- Never edit the source file. Any derived file goes to a separate path.
- Every number you report comes from the script output or a command you ran in this session, never from memory or from reading a few rows.
- Report counts with their denominators ("41 of 1,203 rows", not "3%" alone). Do not compare groups smaller than 30 rows.
- EDA is hypothesis generation. Count how many comparisons you looked at and say so; at a 5% false-positive rate, 40 looks produce about 2 spurious patterns.
- If the user's question is a specific test or a model, stop and say this skill does not do that; offer the profile as step one.

## Workflow

Copy and tick:

```
- [ ] 0 Frame: what is one row, what is the outcome column (if any), where did the file come from
- [ ] 1 Profile with the script (keep the JSON)
- [ ] 2 Shape and integrity
- [ ] 3 Types and coding problems
- [ ] 4 Missingness
- [ ] 5 Distributions and outliers
- [ ] 6 Relationships (with a third-variable check)
- [ ] 7 Leakage and time checks
- [ ] 8 Write the report in the fixed format
```

0. **Frame.** Ask only what the file cannot tell you: the unit of a row, the outcome column, the collection period. If the user does not know, write the assumption down as an assumption and carry on.
1. **Profile.** `python scripts/eda_profile.py data.csv --target <outcome>` (leave out `--target` when there is no outcome). Save the JSON. If `rows_truncated` is true the statistics cover only the first rows of the file, which for a time-ordered file are the oldest ones: rerun with a larger `--max-rows` or say that conclusions apply to that slice only.
2. **Shape and integrity.** Read `rows_profiled`, `columns`, `bad_rows`, `duplicate_rows`, `warnings`. Bad rows above 1% of rows read, or any bad row whose line numbers cluster (a block of consecutive lines), mean the file is damaged or mis-delimited: report that first and ask before going on. Exact duplicate rows are a finding, not something to drop silently. A unique row id does not mean unique entities: check the entity key the user names for repeats.
3. **Types and coding.** For each column compare `type` with what the name implies (see [flag glossary](references/flag_glossary.md) for every flag and its usual cause). Check `mixed_type_columns`, `sentinel_suspect_columns`, `case_variant_columns`, `zero_padded_codes`, `formatted_numbers`, `binary_01`, `date_order_ambiguous`. Do not recode in place; list the recode you would apply and why.
4. **Missingness.** List columns with `missing_pct` of 5 or more; `missing_over_20_pct` is the pre-built list. Read `missing_tokens` to see which spellings were counted. Then, for each such column, compute the missing rate across the two most useful categorical columns and across time (first half against second half of the file). A gap of 10 points or more between groups of at least 30 rows each means the missingness is related to that column: report it as such and never write "missing at random". All-missing and constant columns go in the integrity list, not the findings.
5. **Distributions and outliers.** Per numeric column use `p05`, `median`, `p95`, `mean`, `std`, and the Tukey counts (`outliers_iqr_1_5` mild, `outliers_iqr_3` extreme). Working rules: mean and median differ by more than half a standard deviation, or `max` above 10 times `p95`, means a heavy tail, so report medians and quantiles instead of means. Report outliers as counts and example rows; never delete or cap them. An outlier at a `sentinel_suspects` value is a coding problem, not a value. Check units by eye on `min` and `max` (ages above 120, negative prices, a share above 100).
6. **Relationships.** Use `near_duplicate_numeric_pairs` (absolute Pearson r of 0.9 or more) to find redundant columns. For any pair, group or trend you plan to report, redo it split by the largest categorical column and by first half against second half; if the sign flips or the effect vanishes in the splits, report it as unstable (a reversal under splitting is the Simpson pattern). Prefer a plain table of group medians with counts to a single statistic. Pearson sees only straight-line association: if you need more, rank correlation from your own code is an acceptable second view.
7. **Leakage and time.** Read `target.leakage_candidates`: a numeric column with absolute r of 0.95 or more with the outcome, or a column whose values map to one outcome class at 99% or more (a missing cell counts as a value, so a field filled in only after the outcome shows up here). Also by name, look for columns that could only be known after the outcome (refund, cancel_reason, resolved_at, final_status, post-period totals) and say which you suspect. For time, read `date_columns`: `row_order` ascending means a time-based split is possible by position; `unsorted` means sort before splitting. Report the date range, gaps larger than 3 times the median interval (your own code), and any `date_order_ambiguous` column: the day/month reading changes the range and must be confirmed with the owner.
8. **Report** in the format below.

## Findings contract

Every finding is one row with all five fields:

| Field | Rule |
|---|---|
| `id` | F1, F2, ... in order of importance to the reader |
| `claim` | One descriptive sentence using only: is, has, contains, differs, is associated with, is missing. Banned: causes, drives, because, leads to, proves, predicts, significant (unless you ran and stated a test), "no relationship" |
| `evidence` | Column names, the numbers with denominators, and where they came from (JSON path such as `columns_detail[age].numeric.median`, or the command) |
| `caveat` | At least one concrete limit: sample slice, missing share, group size, one-off split, ambiguity. "More data would help" does not count |
| `status` | `observed` (computed directly), `suggestive` (pattern seen but unstable or untested in splits), `question` (the data cannot settle it; owner must answer) |

Rank by what would change the reader's next action, not by size of effect. Five to ten findings; move the rest to an appendix list.

## Report format

```
Dataset: <file>, <rows> rows, <columns> columns, <bad rows>, <duplicate rows>, slice or full
Integrity and coding issues: <table: column, issue, evidence, proposed handling>
Findings: <contract rows>
Leakage and time risks: <candidates with reason, date range, order, split advice>
Questions for the owner: <numbered, each answerable in one line>
Not checked: <e.g. other files, joins, entity-level duplicates, free text, causal questions>
```

## What never to conclude from EDA

| You saw | Do not say | Say instead |
|---|---|---|
| Two columns move together | One causes the other | They are associated in this file (n, r, split result) |
| Missing values in a column | They are random, or can be filled with the mean | The missing rate differs by X (or does not) across the groups checked |
| A far-out value | It is an error, so remove it | It is N standard deviations out; owner should confirm |
| Group A averages higher than B | A has an effect | A differs from B in this sample; confounders not checked |
| A strong single predictor | It will make a good feature | It is associated; check it is known before the outcome |
| A trend across dates | The real world changed | The recorded values changed; collection or coding may have changed |
| No pattern found | There is none | None was found with these looks and this sample size |
| A column is constant | It is irrelevant | It does not vary in this file |
| A row id is unique | There are no duplicate customers or events | Rows are unique; entity repeats were or were not checked |

Longer rewrites from bad to acceptable wording are in [claim wording](references/claim_wording.md); read it when you are unsure whether a sentence is a claim or a description.

## Script

`scripts/eda_profile.py` is run, not read or edited; do not change it to make a check pass.

```
python scripts/eda_profile.py data.csv [--target COL] [--delimiter ";"] [--max-rows 500000] [--top 5] [--no-corr] [--strict]
```

It prints strict JSON (ASCII, no NaN) and reads only the named file. Top-level keys: `rows_profiled`, `rows_truncated`, `columns`, `delimiter`, `encoding`, `blank_lines_skipped`, `duplicate_rows`, `bad_rows` (`count`, `pct_of_rows_read`, `first_examples` with line numbers), `warnings`, the lists `constant_columns`, `near_constant_columns`, `all_missing_columns`, `likely_id_columns`, `repeating_key_columns`, `mixed_type_columns`, `sentinel_suspect_columns`, `case_variant_columns`, `date_columns`, `missing_over_20_pct`, `near_duplicate_numeric_pairs`, `target` (null without `--target`), `type_counts`, `not_computed`, and `columns_detail` with one entry per column (`type`, `missing`, `missing_pct`, `distinct`, `numeric`, `string_length`, `date`, `top_values`, `flags`). Bad rows (wrong field count, parse error) are excluded from every statistic and listed by line number; blank lines are skipped. Exit 0 on success, 1 only with `--strict` and bad rows, 2 for an unreadable file, no header, no data rows or a bad `--target`.

Without Python, do the same stages by hand in whatever tool is available: row and column counts, count of blanks and of the tokens NA, N/A, null, none, -, ? per column, distinct counts, min, median, max per numeric column, a sorted view of the date column, and the group-wise missing rates from stage 4. State in the report that the script was not run.

## Limits

- The script reads one CSV (comma, semicolon, tab or pipe separated), up to 500,000 good rows by default; it does not read Excel, JSON or databases.
- Type rules are surface rules: decimal commas ("1,5") read as text, "none" and "-" count as missing even when they are real categories (the matched tokens are listed so you can check), and a column with leading-zero digits is read as a code, not a number.
- Correlation is Pearson on up to 20,000 evenly spaced rows and 30 numeric columns; it misses curved and category-driven relationships. The purity leak check needs 30 or more rows and a column with at most half as many distinct values as rows; a rare outcome (majority share above about 96%) cannot trigger it.
- The 5%, 10-point, 20%, 0.9, 0.95 and 30-row thresholds are working values, not optimal ones.
- Duplicate detection is exact-row only. Unbalanced quotes can swallow the rest of a file into one bad row; the script warns when one record spans over 100 lines.
- This skill reads data you hand it: it does not remove personal data, so keep reports free of row-level personal values unless the user asks for them.
