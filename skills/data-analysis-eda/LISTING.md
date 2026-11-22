# Listing page content: data-analysis-eda

**One line:** A fixed exploratory-analysis procedure and CSV profiler that keeps findings descriptive, evidenced and caveated.

## What it does

The skill gives an agent an eight-step EDA procedure for a CSV: frame the file, profile it, check shape and integrity, types and coding, missingness, distributions and outliers, relationships (with a split check for reversals), and leakage and time. A standard-library script produces the profile as strict JSON. Findings must follow a five-field contract (id, claim, evidence, caveat, status) with a list of banned verbs, and the report ends with owner questions and a "Not checked" list. A table of things never to conclude from EDA (correlation as cause, "missing at random", outlier as error, and others) keeps the report descriptive.

## Capabilities

- `scripts/eda_profile.py`: per column the inferred type, missing count and percent (with the tokens counted as missing), distinct count, numeric summary (min, p05, p25, median, p75, p95, max, mean, std, Tukey outlier counts), top values, string length, date range and row order; flags for constant, near-constant, likely id, mixed types, suspected sentinel codes (999 and similar), zero-padded codes, case and whitespace variants, formatted numbers, ambiguous day/month dates
- File level: bad rows by line number (excluded from all statistics), exact duplicate rows, near-duplicate numeric column pairs, and with `--target` a leakage check (numeric correlation 0.95 or more; categories that map to one outcome class, counting a missing cell as a value)
- Handles quoted commas and embedded newlines, semicolon, tab and pipe delimiters, a BOM, a non-UTF-8 fallback, NUL characters, header problems, and files up to 500,000 good rows by default
- A flag glossary (rule, usual cause, check, wording) and a claim-wording guide

## When to use

You say explore this CSV, EDA, profile this dataset, what is in this data, sanity-check before modelling, or find anything odd in this file.

## When not to use

Building models, charts or dashboards; cleaning or rewriting the data; testing one stated hypothesis; SQL or spreadsheet formula help; non-CSV sources.

## How it differs from neighbouring skills

- `dataset-field-profiler` and `missingness-pattern-brief` (both in the Codex batch; their text was not read for this listing, so this uses their registry names and descriptions only): those are narrower deliverables, a field profile and a missingness brief by declared subgroup. This skill is the whole disciplined sequence around a profile: integrity, distributions, relationships with a third-variable check, leakage and time checks, the findings contract, and the list of conclusions to avoid. Use the narrower skill when only that one artefact is wanted.
- `spreadsheet-analysis` (a spreadsheet-focused skill in the catalogue, not read): this skill works on a CSV and does not compute business answers or build workbooks.

## Requirements

Python 3.9 or newer, standard library only. No network. Tested on Windows 11 with Python 3.11 only.

## Install

Copy the folder to `.claude/skills/data-analysis-eda/` or `.agents/skills/data-analysis-eda/` (pinned install commands are added at publication).

## Examples

**1. Profile a customer file before modelling.** Prompt: "Here is customers.csv. I want to build a churn model next week. Do an exploratory analysis first and save a report to report.md."

Real output of the profiling step, `python scripts/eda_profile.py evals/fixtures/messy.csv --target churned`, abridged to the fields the report is built from:

```json
{
  "rows_profiled": 36, "columns": 9, "duplicate_rows": 0,
  "likely_id_columns": ["customer_id"],
  "sentinel_suspect_columns": ["age"],
  "case_variant_columns": ["region"],
  "missing_over_20_pct": [{"name": "cancel_reason", "missing_pct": 66.67}],
  "near_duplicate_numeric_pairs": [{"a": "monthly_spend", "b": "annual_spend", "r": 1.0, "pairs": 36}],
  "age": {"type": "integer", "missing": 2, "sentinel_suspects": [{"value": 999, "count": 3}],
          "numeric": {"min": 25, "p05": 26.65, "median": 41.5, "p95": 999, "max": 999}},
  "zip": {"type": "string", "flags": ["zero_padded_codes"]},
  "target_leakage_candidates": [{"column": "cancel_reason", "check": "category_purity", "value": 1.0}]
}
```

A finding row written by hand from that output (illustrative; the full agent report has not been produced in a saved run):

```
F1 | cancel_reason holds a value only for churned customers (12 of 12) and is empty for the other 24 | columns_detail[cancel_reason], target.leakage_candidates[0] | It restates the outcome, so it must be excluded from any churn model; whether it is recorded at or after cancellation is not stated in the file | observed
```

**2. A raw export with damaged rows.** Prompt: "orders.csv is a raw export from our order system. Profile it and tell me what I need to know before I load it anywhere."

Real script output on `evals/files/t2-orders-export/orders.csv`: 18 rows profiled; 2 bad rows excluded at lines 12 and 15 (3 and 6 fields against 5 expected); `order_date` is `date_order_ambiguous`, ranging 2024-01-02 to 2024-04-01 read month-first, or 2024-01-02 to 2024-12-03 read day-first; `status` has the variants `shipped` and `Shipped`.

## Limits

- One CSV per run; no Excel, JSON or databases.
- Surface type rules: decimal commas read as text; "none" and "-" count as missing even when they are real categories.
- Pearson correlation on up to 20,000 rows and 30 columns; curved or group-driven relationships are missed. The leakage purity check cannot fire when the outcome's majority class exceeds about 96%.
- Thresholds (5%, 10 points, 20%, 0.9, 0.95, 30 rows) are working values, not optima.
- Exact-row duplicates only. An unbalanced quote can swallow the rest of a file into one bad row (the script warns above 100 lines).

## Evidence

| Check | Result | Date, environment |
|---|---|---|
| Static lint | 0 FAIL, 0 WARN | 2026-11-21 |
| Script fixtures (`python evals/run_fixtures.py`) | 11 of 11 cases | 2026-11-21, Windows 11, Python 3.11 |
| Trigger test, task evals with baseline, cross-tool, human review | Not run | |

## Demo script (60 to 90 seconds)

1. Prompt: "Explore customers.csv before I build a churn model." The agent runs the profile script on the file and keeps the JSON.
2. The agent reads the lists: one id column, `age` with three 999 values flagged as a sentinel, a `region` spelling variant, a zip column kept as text because of leading zeros.
3. With `--target churned` the leakage check flags `cancel_reason`, filled only when churned is 1.
4. The report lists findings as claim, evidence, caveat and status, then "Questions for the owner" and "Not checked". Before: "age averages 126". After: "median age is 41.5; 3 rows hold 999, probably a missing-value code".
(Storyboard from the fixture run above; a full agent run has not been recorded.)

## FAQ seeds

1. Does it need network access? No; the script is standard-library Python and reads only the file you name.
2. Will it change my CSV? No. The script only reads; the skill forbids editing the source file.
3. Does it fit Excel files? Not directly; export the sheet to CSV first.
4. Why does it refuse to say what "drives" something? EDA shows association in one file; the skill's contract bans causal wording and says what extra evidence would be needed.
5. What if the file is huge? The first 500,000 good rows are profiled by default and the report says so; raise `--max-rows` or sample.
6. How is it different from a profiling library? It is a procedure plus a findings contract with a stdlib script, not a report generator; it needs no installs.
7. Is any data sent anywhere? No; no network use at all.
8. How do I uninstall? Delete the folder.

## Changelog

- 0.1.0, 2026-11-21: first draft; lint and fixtures only.

## License and authorship

Apache-2.0. Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted with AI assistance (claude-sonnet-5-5); no human review has taken place yet. Accountable editor: Global Media Holdings.
