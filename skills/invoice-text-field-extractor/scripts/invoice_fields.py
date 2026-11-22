"""Extract invoice fields from extracted invoice text and check the arithmetic.

Reads one UTF-8 text file (at most 2 MB) and writes one JSON object to stdout.
Fields read: invoice number, issue date, due date, currency symbols, subtotal,
tax, total, and line items (description, quantity, optional unit price, amount).
Checks: line items sum to the subtotal, and subtotal plus tax equals the total,
each within 0.01.

Usage:
    python -I scripts/invoice_fields.py <input-file>

Exit codes: 0 no findings, 1 findings present, 2 usage or input error.
Errors are written to stderr as one line of JSON: {"error": ..., "message": ...}.
The script is read-only, makes no network calls, starts no subprocesses and
writes no files.
"""

import datetime
import json
import os
import re
import sys
from decimal import Decimal

MAX_BYTES = 2 * 1024 * 1024
TOLERANCE = Decimal("0.01")
FIELDS = ["invoice_number", "issue_date", "due_date", "currency", "subtotal", "tax", "total"]
MONEY_FIELDS = ["subtotal", "tax", "total"]

MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
]
MONTHS = {}
for _i, _name in enumerate(MONTH_NAMES, 1):
    MONTHS[_name] = _i
    MONTHS[_name[:3]] = _i
MONTHS["sept"] = 9

NUM = r"-?(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}"
MONEY_RE = re.compile(r"(?P<cur>[$€£¥])?\s?(?P<num>" + NUM + r")(?!\d)")
INVOICE_NO_RE = re.compile(
    r"^\s*(?:invoice\s*(?:no\.?|number|#)|inv\s*#)\s*[:#]?\s*(?P<v>[A-Za-z0-9][A-Za-z0-9\-/]{1,30})\s*$",
    re.IGNORECASE,
)
ISSUE_RE = re.compile(
    r"^\s*(?:invoice\s+date|issue\s+date|date\s+issued|date)\s*:\s*(?P<rest>.+?)\s*$",
    re.IGNORECASE,
)
DUE_RE = re.compile(
    r"^\s*(?:due\s+date|payment\s+due|due)\s*:\s*(?P<rest>.+?)\s*$",
    re.IGNORECASE,
)
SUBTOTAL_RE = re.compile(r"^\s*subtotal\s*:\s*(?P<rest>.*)$", re.IGNORECASE)
TAX_RE = re.compile(r"^\s*(?:sales\s+)?(?:tax|vat|gst)\b[^:]*:\s*(?P<rest>.*)$", re.IGNORECASE)
TOTAL_RE = re.compile(
    r"^\s*(?:total\s+amount|total\s+due|total|amount\s+due|balance\s+due)\s*:\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
ITEM_RE = re.compile(
    r"^\s*(?P<desc>[A-Za-z][^\d\n]*?)\s{2,}(?P<qty>\d+(?:\.\d+)?)\s{2,}"
    r"(?:[$€£¥]?\s?(?P<unit>" + NUM + r")\s{2,})?"
    r"[$€£¥]?\s?(?P<amount>" + NUM + r")\s*$"
)
DATE_PATTERNS = [
    (re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})\b"), "ymd"),
    (re.compile(r"\b(?P<m>\d{1,2})/(?P<d>\d{1,2})/(?P<y>\d{4})\b"), "mdy"),
    (re.compile(r"\b(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d>\d{1,2}),?\s+(?P<y>\d{4})\b"), "mony"),
    (re.compile(r"\b(?P<d>\d{1,2})\s+(?P<mon>[A-Za-z]{3,9})\.?,?\s+(?P<y>\d{4})\b"), "dmony"),
]


def fail(code, message):
    sys.stderr.write(json.dumps({"error": code, "message": message}) + "\n")
    sys.exit(2)


def fmt(value):
    return "{:.2f}".format(value)


def parse_date(text):
    """Return an ISO date string for the first valid date in text, else None."""
    for pattern, kind in DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        try:
            if kind == "ymd":
                day = datetime.date(int(m.group("y")), int(m.group("m")), int(m.group("d")))
            elif kind == "mdy":
                day = datetime.date(int(m.group("y")), int(m.group("m")), int(m.group("d")))
            else:
                month = MONTHS.get(m.group("mon").lower())
                if month is None:
                    continue
                day = datetime.date(int(m.group("y")), month, int(m.group("d")))
        except ValueError:
            continue
        return day.isoformat()
    return None


def last_money(rest):
    matches = list(MONEY_RE.finditer(rest))
    if not matches:
        return None
    return Decimal(matches[-1].group("num").replace(",", ""))


def collect(lines):
    """Return {field: [(line_no, value_string), ...]} for every label match."""
    cands = {f: [] for f in FIELDS}
    for n, line in enumerate(lines, 1):
        m = INVOICE_NO_RE.match(line)
        if m:
            cands["invoice_number"].append((n, m.group("v")))
        m = ISSUE_RE.match(line)
        if m:
            day = parse_date(m.group("rest"))
            if day:
                cands["issue_date"].append((n, day))
        m = DUE_RE.match(line)
        if m:
            day = parse_date(m.group("rest"))
            if day:
                cands["due_date"].append((n, day))
        for field, regex in (("subtotal", SUBTOTAL_RE), ("tax", TAX_RE), ("total", TOTAL_RE)):
            m = regex.match(line)
            if m:
                amount = last_money(m.group("rest"))
                if amount is not None:
                    cands[field].append((n, fmt(amount)))
        for mm in MONEY_RE.finditer(line):
            if mm.group("cur"):
                cands["currency"].append((n, mm.group("cur")))
    return cands


def resolve(pairs):
    if not pairs:
        return {"value": None, "confidence": "missing", "line": None, "candidates": []}
    distinct = []
    for _, value in pairs:
        if value not in distinct:
            distinct.append(value)
    if len(distinct) == 1:
        return {"value": distinct[0], "confidence": "found", "line": pairs[0][0], "candidates": []}
    return {
        "value": None,
        "confidence": "ambiguous",
        "line": None,
        "candidates": [{"line": n, "value": v} for n, v in pairs],
    }


def line_items(lines):
    items = []
    for n, line in enumerate(lines, 1):
        m = ITEM_RE.match(line)
        if not m:
            continue
        unit = m.group("unit")
        items.append({
            "line": n,
            "description": m.group("desc").strip(),
            "qty": m.group("qty"),
            "unit_price": fmt(Decimal(unit)) if unit else None,
            "amount": fmt(Decimal(m.group("amount"))),
        })
    return items


def extract(lines):
    cands = collect(lines)
    fields = {f: resolve(cands[f]) for f in FIELDS}
    items = line_items(lines)

    def known(name):
        field = fields[name]
        return Decimal(field["value"]) if field["confidence"] == "found" else None

    subtotal = known("subtotal")
    tax = known("tax")
    total = known("total")

    if items and subtotal is not None:
        items_sum = sum((Decimal(i["amount"]) for i in items), Decimal("0"))
        diff = items_sum - subtotal
        li_check = {
            "sum": fmt(items_sum),
            "subtotal": fmt(subtotal),
            "difference": fmt(diff),
            "status": "match" if abs(diff) <= TOLERANCE else "mismatch",
        }
    else:
        li_check = {
            "sum": fmt(sum((Decimal(i["amount"]) for i in items), Decimal("0"))) if items else None,
            "subtotal": fmt(subtotal) if subtotal is not None else None,
            "difference": None,
            "status": "not_checked",
        }

    if subtotal is not None and tax is not None and total is not None:
        expected = subtotal + tax
        diff = total - expected
        total_check = {
            "subtotal_plus_tax": fmt(expected),
            "total": fmt(total),
            "difference": fmt(diff),
            "status": "match" if abs(diff) <= TOLERANCE else "mismatch",
        }
    else:
        total_check = {
            "subtotal_plus_tax": None,
            "total": fmt(total) if total is not None else None,
            "difference": None,
            "status": "not_checked",
        }

    findings = []
    for name in FIELDS:
        confidence = fields[name]["confidence"]
        if confidence == "missing":
            findings.append({"code": "MISSING_FIELD", "subject": name})
        elif confidence == "ambiguous":
            findings.append({"code": "AMBIGUOUS_FIELD", "subject": name})
    if not items:
        findings.append({"code": "NO_LINE_ITEMS", "subject": "line_items"})
    if li_check["status"] == "mismatch":
        findings.append({"code": "LINE_ITEMS_MISMATCH", "subject": "line_items_vs_subtotal"})
    if total_check["status"] == "mismatch":
        findings.append({"code": "TOTAL_MISMATCH", "subject": "total_vs_subtotal_plus_tax"})

    return {
        "input_lines": len(lines),
        "fields": fields,
        "line_items": items,
        "checks": {
            "line_items_vs_subtotal": li_check,
            "total_vs_subtotal_plus_tax": total_check,
        },
        "findings": findings,
    }


def main(argv):
    if len(argv) != 2:
        fail("usage", "expected exactly one argument: <input-file>")
    path = argv[1]
    if not os.path.isfile(path):
        fail("missing_file", "input path is not a readable regular file")
    if os.path.getsize(path) > MAX_BYTES:
        fail("input_too_large", "input file is larger than 2 MB")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("read_error", "could not read the input file")
    if len(raw) > MAX_BYTES:
        fail("input_too_large", "input file is larger than 2 MB")
    if not raw.strip():
        fail("empty_input", "input file has no text")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8", "input file is not valid UTF-8 text")
    lines = text.splitlines()
    if not any(line.strip() for line in lines):
        fail("empty_input", "input file has no text")

    result = extract(lines)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
