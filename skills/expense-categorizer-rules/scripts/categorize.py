"""Categorize a bank transactions CSV with ordered keyword rules.

Usage:
  python -I categorize.py <transactions-csv> <rules-csv> <output-csv>

Inputs (read-only, UTF-8 with optional BOM, 2 MB cap each):
  transactions CSV: header row must contain date, description, amount
    (case-insensitive, any column order, extra columns ignored).
    date: YYYY-MM-DD. amount: decimal with optional leading minus, $ and commas.
  rules CSV: header row must contain keyword, category.
    Rules are tried in file order. First match wins. A rule matches when its
    keyword is a case-insensitive substring of the transaction description.

Output (new file only; opened with mode "x", never overwritten, never an input):
  CSV columns: date,description,amount,category,matched_rule_record
  Unmatched rows get category "Uncategorized" and an empty matched_rule_record.

Stdout: one line of JSON.
  Record numbers count CSV records from 1, where the header is record 1.

Exit codes:
  0  every transaction matched a rule
  1  one or more transactions are Uncategorized (output file still written)
  2  usage, input, or output error (one-line JSON error; no output file written)
"""
import csv
import datetime
import decimal
import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
UNCATEGORIZED = "Uncategorized"
AMOUNT_RE = re.compile(r"-?[0-9]+(\.[0-9]+)?")
OUT_COLUMNS = ["date", "description", "amount", "category", "matched_rule_record"]
TX_COLUMNS = ["date", "description", "amount"]
RULE_COLUMNS = ["keyword", "category"]


class InputError(Exception):
    """Raised for any bad input; the message never contains row contents."""


def emit(payload):
    sys.stdout.write(json.dumps(payload) + "\n")


def fail(message):
    emit({"status": "error", "message": message})
    return 2


def read_records(path, required):
    """Return (column_index, records) where records are (record_no, fields)."""
    try:
        if os.path.getsize(path) > MAX_INPUT_BYTES:
            raise InputError("input file exceeds 2 MB")
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            raw = list(csv.reader(handle))
    except InputError:
        raise
    except (OSError, UnicodeDecodeError, csv.Error):
        raise InputError("cannot read input file as UTF-8 CSV")
    if not raw:
        raise InputError("input file is empty")
    header = [name.strip().lower() for name in raw[0]]
    missing = [name for name in required if name not in header]
    if missing:
        raise InputError("missing required column(s): " + ",".join(missing))
    index = {name: header.index(name) for name in required}
    needed = max(index.values())
    records = []
    for record_no, fields in enumerate(raw[1:], start=2):
        if not fields or all(not field.strip() for field in fields):
            continue
        if len(fields) <= needed:
            raise InputError("too few fields on record %d" % record_no)
        records.append((record_no, fields))
    return index, records


def parse_date(text, record_no):
    try:
        parsed = datetime.datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise InputError("invalid date on record %d, expected YYYY-MM-DD" % record_no)
    return parsed.isoformat()


def parse_amount(text, record_no):
    cleaned = text.strip().replace("$", "").replace(",", "")
    if not AMOUNT_RE.fullmatch(cleaned):
        raise InputError("invalid amount on record %d" % record_no)
    return decimal.Decimal(cleaned)


def first_match(description, rules):
    folded = description.casefold()
    for rule in rules:
        if rule["folded"] in folded:
            return rule
    return None


def load_rules(path):
    index, records = read_records(path, RULE_COLUMNS)
    rules = []
    for record_no, fields in records:
        keyword = fields[index["keyword"]].strip()
        category = fields[index["category"]].strip()
        if not keyword or not category:
            raise InputError("empty keyword or category on record %d" % record_no)
        rules.append({
            "record": record_no,
            "category": category,
            "folded": keyword.casefold(),
            "hits": 0,
        })
    if not rules:
        raise InputError("rules file has no rule rows")
    return rules


def categorize_file(tx_path, rules):
    index, records = read_records(tx_path, TX_COLUMNS)
    if not records:
        raise InputError("transactions file has no transaction rows")
    out_rows = []
    totals = {}
    uncategorized_total = decimal.Decimal(0)
    uncategorized_records = []
    for record_no, fields in records:
        date = parse_date(fields[index["date"]], record_no)
        description = fields[index["description"]].strip()
        amount = parse_amount(fields[index["amount"]], record_no)
        rule = first_match(description, rules)
        if rule is None:
            category = UNCATEGORIZED
            matched = ""
            uncategorized_total += amount
            uncategorized_records.append(record_no)
        else:
            rule["hits"] += 1
            category = rule["category"]
            matched = str(rule["record"])
            totals[category] = totals.get(category, decimal.Decimal(0)) + amount
        out_rows.append([date, description, str(amount), category, matched])
    return out_rows, totals, uncategorized_total, uncategorized_records


def main(argv):
    if len(argv) != 4:
        return fail("usage: categorize.py <transactions-csv> <rules-csv> <output-csv>")
    tx_path, rules_path, out_path = argv[1], argv[2], argv[3]
    if os.path.exists(out_path):
        return fail("output file already exists; choose a new output path")
    try:
        rules = load_rules(rules_path)
        out_rows, totals, uncategorized_total, uncategorized_records = categorize_file(tx_path, rules)
    except InputError as exc:
        return fail(str(exc))
    try:
        with open(out_path, "x", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(OUT_COLUMNS)
            writer.writerows(out_rows)
    except FileExistsError:
        return fail("output file already exists; choose a new output path")
    except OSError:
        return fail("cannot write output file; check the output directory exists")
    count = len(out_rows)
    uncategorized = len(uncategorized_records)
    emit({
        "status": "findings" if uncategorized else "ok",
        "transactions": count,
        "categorized": count - uncategorized,
        "uncategorized": uncategorized,
        "totals": {name: str(value) for name, value in sorted(totals.items())},
        "uncategorized_total": str(uncategorized_total),
        "uncategorized_records": uncategorized_records,
        "rules": [
            {"record": rule["record"], "category": rule["category"], "hits": rule["hits"]}
            for rule in rules
        ],
    })
    return 1 if uncategorized else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
