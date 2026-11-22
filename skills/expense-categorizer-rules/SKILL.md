---
name: expense-categorizer-rules
description: Categorizes a bank transactions CSV with ordered keyword rules, first match wins, and reports totals per category plus the uncategorized rows. Use when a spreadsheet of dated bank transactions needs sorting by merchant keyword, or when per-category totals are needed from a bank export that has date, description and amount columns. Do not use for tax classification, accounting advice, downloading statements, or categorizing with machine learning or a merchant database.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Expense Categorizer Rules

This skill runs `scripts/categorize.py` on one bank transactions CSV and one rules CSV. It writes a new categorized CSV and reports totals per category. It never edits the inputs and never overwrites an existing file.

Shipped files:

- `scripts/categorize.py`: the categorizer (stdlib only).
- `fixtures/transactions.csv` and `fixtures/rules.csv`: the 8-transaction, 3-rule smoke input. Do not run the user's workflow on these.
- `LICENSE.txt`: Apache-2.0 license text.

## 1. Workflow

1. **Intake check.** Open the transactions file and read its header row. Confirm it contains `date`, `description` and `amount` (case-insensitive). Output: the header names found, or a stop message (see the refuse list).
2. **Date format.** Confirm every date is `YYYY-MM-DD`. Bank exports often use `MM/DD/YYYY`; convert those dates before the run. Output: count of dates converted.
3. **Rules check.** Open the rules file. Confirm the header is `keyword,category`. Check each keyword against the threshold table below. Output: rule count and any keyword that fails.
4. **Size and paths.** Confirm each input is 2,097,152 bytes or less. Choose an output path that does not exist yet. Output: the three paths to use.
5. **Run the script.** Use the exact command in section 3. Output: stdout JSON and the exit code.
6. **Read the exit code** with the table in section 3. Output: one status line.
7. **Write the summary** using the contract in section 4. Output: the summary in chat.
8. **Close the loop.** If `uncategorized` is above the threshold, ask the user for rules covering those records, add them to a copy of the rules file, and rerun to a new output path. Output: the rule suggestions, not applied automatically.

## 2. Decision and threshold table

| Check | Value | Action when it fails |
|---|---|---|
| Required transaction columns | `date`, `description`, `amount` | Stop. Ask for a column mapping. |
| Date format | `YYYY-MM-DD` | Script exits 2. Convert and rerun. |
| Amount format | optional leading `-`, optional `$`, commas allowed, e.g. `-54.20`, `1,250.00` | Parenthesized or trailing-sign amounts exit 2. Ask for a corrected file. |
| Keyword length | 4 characters or more (working value) | Warn the user that short keywords match more rows than intended. |
| Input file size | 2,097,152 bytes or less (fixed by script) | Split the export by month and run each part to its own output. |
| Output path | must not exist (fixed by script) | Pick a new file name. Never overwrite. |
| Uncategorized share | 20% of transactions or less (working value) | Above 20%: list the uncategorized records and ask for more rules before the totals are used. |

## 3. Script contract

Command (replace the placeholders; quote every path):

```
python -I "<skill-folder>/scripts/categorize.py" "<input-file>" "<rules-file>" "<output-file>"
```

Arguments, in order: transactions CSV, rules CSV, output CSV. Exactly three arguments are required.

Matching rule: a keyword matches when it is a case-insensitive substring of the description. Rules are tried in file order and the first match wins. Record numbers count CSV records from 1, so the header is record 1 and the first rule is record 2.

Output CSV columns: `date,description,amount,category,matched_rule_record`. Amounts are written with the same decimal digits as parsed. Unmatched rows get category `Uncategorized` and an empty `matched_rule_record`. Extra input columns are dropped.

Stdout is one line of JSON with these keys: `status` (`ok` or `findings`), `transactions`, `categorized`, `uncategorized`, `totals` (object: category name to decimal string, sorted by name), `uncategorized_total`, `uncategorized_records` (list of record numbers), `rules` (list of objects with `record`, `category`, `hits`).

Error stdout is one line: `{"status": "error", "message": "..."}`. Messages never include row contents.

Exit codes:

| Exit | Meaning | Output file |
|---|---|---|
| 0 | every transaction matched a rule (`status` = `ok`) | written |
| 1 | one or more rows are `Uncategorized` (`status` = `findings`) | written |
| 2 | usage, input, or output error (`status` = `error`) | not written |

## 4. Output contract for the chat reply

Use these headings, in this order:

- `## Status`: the `status` value, transaction count, categorized count, uncategorized count.
- `## Totals by category`: table with columns `Category` and `Total`, one row per key in `totals`, then a row `Uncategorized` with `uncategorized_total`.
- `## Rules used`: table with columns `Record`, `Category`, `Hits`, in record order. Include rules with 0 hits.
- `## Uncategorized records`: the record numbers, comma-separated. Write `none` when the list is empty.
- `## Output file`: the output path only. Do not paste the CSV into chat unless the user asks.

Totals are signed. Negative values are spending; positive values are credits or deposits.

## 5. Refuse / stop when

- The user asks whether a category is a tax deduction, what tax treatment applies, or for accounting advice. Say that this skill sorts rows by keyword and gives no tax or accounting advice.
- The transactions header lacks `date`, `description` or `amount`. Stop and ask for a column mapping.
- Dates or amounts do not match the formats in section 2 and the user will not correct the file. Stop with the exit 2 message.
- The output path already exists, or the user asks to write over the input or rules file. Stop and choose a new path.
- An input is over 2,097,152 bytes. Split it first.
- The user asks you to fetch bank data, log in to a bank, or send the file anywhere. This skill has no network access and does not do that.
- The transactions or rules path was not given. Ask for both as a numbered list: 1. transactions CSV path, 2. rules CSV path, 3. output path.
- The user asks for machine-learned or merchant-database categories. Only keyword rules are supported.
