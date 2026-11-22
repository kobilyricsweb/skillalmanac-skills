"""Match a bank export against a ledger export and list the unmatched items.

Each input is a CSV with the columns date, description, amount (any order,
case-insensitive headers). Dates are YYYY-MM-DD or MM/DD/YYYY. Amounts are
decimal dollars with at most two decimal places; negatives may be written as
-12.00 or (12.00). A bank row and a ledger row match when the amounts are equal
exactly and the dates differ by no more than the tolerance in days. Matching is
one-to-one and greedy in bank-file order: each bank row takes the unused ledger
row with the smallest day difference (ties go to the earlier ledger line).

The script is read-only. It reads two files, writes JSON to standard output,
and writes nothing else. It makes no network calls and starts no subprocesses.

Exit codes: 0 every row matched, 1 at least one unmatched row on either side,
2 usage or input error (a one-line JSON error is written to standard error).
"""

import argparse
import csv
import io
import json
import os
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation

MAX_BYTES = 2 * 1024 * 1024
REQUIRED = ("date", "description", "amount")
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y")
DEFAULT_TOLERANCE = 3
MAX_TOLERANCE = 31


class JsonArgParser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage: " + message)


def fail(message):
    sys.stderr.write(json.dumps({"status": "error", "error": message}) + "\n")
    sys.exit(2)


def parse_date(raw):
    text = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError("date")


def parse_amount(raw):
    text = raw.strip().replace(",", "").replace("$", "")
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    if not text:
        raise ValueError("amount")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ValueError("amount")
    if not value.is_finite():
        raise ValueError("amount")
    if negative:
        if value < 0:
            raise ValueError("amount")
        value = -value
    if -value.as_tuple().exponent > 2:
        raise ValueError("amount")
    return value


def load_rows(path, label):
    if not os.path.isfile(path):
        fail(label + ": file not found")
    try:
        with open(path, "rb") as handle:
            data = handle.read(MAX_BYTES + 1)
    except OSError:
        fail(label + ": file cannot be read")
    if len(data) > MAX_BYTES:
        fail(label + ": file exceeds 2 MB")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail(label + ": file is not valid UTF-8")

    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        fail(label + ": file is empty")
    except csv.Error:
        fail(label + ": header cannot be parsed as CSV")
    names = [cell.strip().lower() for cell in header]
    for column in REQUIRED:
        if names.count(column) != 1:
            fail(label + ": header must contain exactly one column named " + column)
    index = {column: names.index(column) for column in REQUIRED}

    items = []
    try:
        for row in reader:
            line = reader.line_num
            if not any(cell.strip() for cell in row):
                continue
            if len(row) != len(names):
                fail(label + ": line %d has the wrong number of fields" % line)
            try:
                when = parse_date(row[index["date"]])
            except ValueError:
                fail(label + ": line %d has an unreadable date" % line)
            try:
                amount = parse_amount(row[index["amount"]])
            except ValueError:
                fail(label + ": line %d has an unreadable amount" % line)
            items.append({
                "line": line,
                "date": when,
                "amount": amount,
                "description": row[index["description"]].strip(),
            })
    except csv.Error:
        fail(label + ": CSV cannot be parsed")
    return items


def match_rows(bank, ledger, tolerance):
    used = set()
    pairs = []
    unmatched_bank = []
    for b in bank:
        best = None
        for j, l in enumerate(ledger):
            if j in used or l["amount"] != b["amount"]:
                continue
            gap = abs((b["date"] - l["date"]).days)
            if gap > tolerance:
                continue
            key = (gap, l["line"])
            if best is None or key < best[0]:
                best = (key, j)
        if best is None:
            unmatched_bank.append(b)
        else:
            j = best[1]
            used.add(j)
            pairs.append((b, ledger[j], best[0][0]))
    unmatched_ledger = [l for j, l in enumerate(ledger) if j not in used]
    return pairs, unmatched_bank, unmatched_ledger


def public(item):
    return {
        "line": item["line"],
        "date": item["date"].isoformat(),
        "amount": format(item["amount"], "f"),
        "description": item["description"][:120],
    }


def total(items):
    result = Decimal("0")
    for item in items:
        result += item["amount"]
    return result


def main(argv):
    parser = JsonArgParser(prog="reconcile.py", description="Match bank and ledger CSV exports.")
    parser.add_argument("--bank", required=True, help="bank export CSV")
    parser.add_argument("--ledger", required=True, help="ledger export CSV")
    parser.add_argument("--tolerance-days", type=int, default=DEFAULT_TOLERANCE,
                        help="maximum day difference, 0 to 31 (default 3)")
    args = parser.parse_args(argv)
    if not 0 <= args.tolerance_days <= MAX_TOLERANCE:
        fail("usage: --tolerance-days must be between 0 and 31")

    bank = load_rows(args.bank, "bank")
    ledger = load_rows(args.ledger, "ledger")
    pairs, unmatched_bank, unmatched_ledger = match_rows(bank, ledger, args.tolerance_days)

    bank_total = total(unmatched_bank)
    ledger_total = total(unmatched_ledger)
    findings = bool(unmatched_bank or unmatched_ledger)
    result = {
        "status": "findings" if findings else "match",
        "tolerance_days": args.tolerance_days,
        "bank_rows": len(bank),
        "ledger_rows": len(ledger),
        "matched_count": len(pairs),
        "matched_pairs": [
            {"bank_line": b["line"], "ledger_line": l["line"], "day_shift": shift}
            for b, l, shift in pairs
        ],
        "unmatched_bank": [public(item) for item in unmatched_bank],
        "unmatched_ledger": [public(item) for item in unmatched_ledger],
        "unmatched_bank_total": format(bank_total, "f"),
        "unmatched_ledger_total": format(ledger_total, "f"),
        "difference": format(bank_total - ledger_total, "f"),
    }
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
