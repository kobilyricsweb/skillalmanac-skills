# Expense Categorizer Rules

## One line

Sorts a bank transactions CSV into categories with ordered keyword rules and reports per-category totals and the rows no rule matched.

## What it does

The skill runs a standard-library Python script on two CSV files. The first holds dated bank transactions with date, description and amount columns. The second holds keyword rules with keyword and category columns. Each description is checked against the rules in file order, and the first rule whose keyword appears in the description, ignoring case, sets the category. Totals are summed per category with decimal arithmetic, so no float rounding enters the report.

The script writes a new CSV that adds the category and the number of the rule that matched. Rows no rule matched are labeled Uncategorized and listed by CSV record number, so the user can see which merchants still need a rule. The script refuses to write to a path that already exists, which keeps earlier runs intact when the rules are revised and the file is run again.

## When to use

Use it when a bookkeeping spreadsheet of bank transactions is still unsorted and the user wants a first pass at categories by merchant keyword. It fits a monthly export that has been converted to ISO dates. It also fits a rules file that grows over time, because each rerun produces a fresh output and a report of what is still uncategorized.

## When not to use

Do not use it for tax classification, deduction decisions, or accounting advice. Do not use it when the export uses parenthesized negatives or non-ISO dates unless someone converts them first. Do not use it for categorization by machine learning or a merchant database, and do not use it on files larger than 2 MB without splitting them by month.

## Requirements

Python 3.9 or later, standard library only. No network access, no subprocess calls, and no third-party packages. The skill folder needs read access to the inputs and write access to the output directory.

## Example

Command, run on the shipped fixtures with a new output path:

```
python -I "<skill-folder>/scripts/categorize.py" "fixtures/transactions.csv" "fixtures/rules.csv" "<output-file>"
```

Stdout (one line, exit code 1):

```
{"status": "findings", "transactions": 8, "categorized": 6, "uncategorized": 2, "totals": {"Dining": "0.00", "Groceries": "-115.30", "Transport": "-78.75"}, "uncategorized_total": "-35.99", "uncategorized_records": [7, 8], "rules": [{"record": 2, "category": "Groceries", "hits": 2}, {"record": 3, "category": "Transport", "hits": 2}, {"record": 4, "category": "Dining", "hits": 2}]}
```

Output CSV written to `<output-file>`:

```
date,description,amount,category,matched_rule_record
2026-03-01,GREEN GROCER #12,-54.20,Groceries,2
2026-03-02,SHELL FUEL 0045,-38.75,Transport,3
2026-03-03,COFFEE HOUSE,-4.50,Dining,4
2026-03-04,COFFEE HOUSE REFUND,4.50,Dining,4
2026-03-05,CITY GROCER MARKET,-61.10,Groceries,2
2026-03-06,BOOKSHOP ONLINE,-23.99,Uncategorized,
2026-03-07,UNKNOWN MERCHANT 8831,-12.00,Uncategorized,
2026-03-08,SHELL FUEL 0098,-40.00,Transport,3
```

2 of 8 rows are uncategorized, a 25% share, which is above the 20% working threshold in the skill, so the agent asks for more rules before the totals are used.

## Limits

Matching is substring-based, so a short keyword can match more rows than intended; the skill's threshold flags keywords under 4 characters (a working value) for the user to review. Only the first matching rule applies, so rule order matters and must be reviewed by the user. Dates must be YYYY-MM-DD and amounts must be plain decimals with an optional minus sign, dollar sign or commas. Inputs are capped at 2 MB each. Extra columns in the transactions file are dropped from the output. The script does not detect duplicate transactions or transfers between accounts.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
