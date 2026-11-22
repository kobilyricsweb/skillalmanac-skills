#!/usr/bin/env python3
"""Quote Estimate Builder: total an itemized quote from a CSV file.

Reads a CSV with the columns item, qty, unit_price and an optional
discount_percent. Each row is checked, then line and quote totals are
computed with Decimal arithmetic and ROUND_HALF_UP to 2 decimal places.
Tax is applied once, to the net subtotal, at the rate the user supplies.

Usage:
    python -I quote.py <input-file> --tax-rate <percent>

Output: a plain-text table on stdout, then one JSON object on the last line.

Exit codes:
    0  every data row is valid and the totals cover all rows
    1  one or more rows are flagged; totals cover valid rows only
    2  usage or input error (one-line JSON error on stderr)

Read-only: the input file is never modified and no file is written.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

MAX_INPUT_BYTES = 2 * 1024 * 1024
CENT = Decimal("0.01")
HUNDRED = Decimal("100")
TWELVE_DIGITS = Decimal(10) ** 12
NUMBER_RE = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")
REQUIRED_COLUMNS = ("item", "qty", "unit_price")
OPTIONAL_COLUMNS = ("discount_percent",)


def fail(code, message):
    """Write a one-line JSON error to stderr and exit 2."""
    sys.stderr.write(json.dumps({"error": message, "code": code}) + "\n")
    sys.exit(2)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("USAGE", message)


def parse_amount(text):
    """Return (value, None) for a valid non-negative number, else (None, reason)."""
    if not NUMBER_RE.match(text):
        return None, "NOT_NUMBER"
    if text.startswith("-"):
        return None, "NEGATIVE"
    value = Decimal(text)
    if value >= TWELVE_DIGITS:
        return None, "TOO_LARGE"
    return value, None


def parse_tax_rate(text):
    if not NUMBER_RE.match(text) or text.startswith("-"):
        fail("TAX_RATE_INVALID", "tax rate must be a plain percent such as 8.25")
    rate = Decimal(text)
    if rate > HUNDRED:
        fail("TAX_RATE_OUT_OF_RANGE", "tax rate must be between 0 and 100 percent")
    return rate


def read_text(path):
    if not os.path.isfile(path):
        fail("FILE_NOT_FOUND", "input file does not exist")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        fail("INPUT_TOO_LARGE", "input file is over 2 MB")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("FILE_UNREADABLE", "input file could not be read")
    if len(raw) > MAX_INPUT_BYTES:
        fail("INPUT_TOO_LARGE", "input file is over 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("INVALID_UTF8", "input file is not valid UTF-8")
    if "\x00" in text:
        fail("INPUT_NOT_CSV", "input file contains NUL bytes")
    return text


def read_columns_and_rows(text):
    """Return (column index map, width, data rows) with blank rows removed."""
    try:
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error:
        fail("INPUT_NOT_CSV", "input file could not be parsed as CSV")
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        fail("EMPTY_INPUT", "input file has no header row")
    header = [cell.strip().lower() for cell in rows[0]]
    if len(set(header)) != len(header):
        fail("HEADER_DUPLICATE", "header has a repeated column name")
    missing = [name for name in REQUIRED_COLUMNS if name not in header]
    if missing:
        fail("HEADER_MISSING", "missing required columns: " + ", ".join(missing))
    if len(rows) < 2:
        fail("NO_DATA_ROWS", "input file has a header but no data rows")
    columns = {name: header.index(name) for name in REQUIRED_COLUMNS + OPTIONAL_COLUMNS if name in header}
    return columns, len(header), rows[1:]


def money(value):
    return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


def build_record(row_number, cells, columns, width):
    record = {
        "row": row_number,
        "item": None,
        "qty": None,
        "unit_price": None,
        "discount_percent": None,
        "line_gross": None,
        "line_discount": None,
        "line_net": None,
        "flags": [],
    }
    if len(cells) != width:
        record["flags"].append("ROW_MALFORMED")
        return record

    item = cells[columns["item"]].strip()
    qty_text = cells[columns["qty"]].strip()
    price_text = cells[columns["unit_price"]].strip()
    disc_text = cells[columns["discount_percent"]].strip() if "discount_percent" in columns else ""
    record.update(item=item, qty=qty_text, unit_price=price_text, discount_percent=disc_text)

    flags = []
    if not item:
        flags.append("ITEM_EMPTY")
    qty, reason = parse_amount(qty_text)
    if reason:
        flags.append("QTY_" + reason)
    price, reason = parse_amount(price_text)
    if reason:
        flags.append("PRICE_" + reason)
    disc = Decimal(0)
    if disc_text:
        value, reason = parse_amount(disc_text)
        if reason == "NOT_NUMBER":
            flags.append("DISCOUNT_NOT_NUMBER")
        elif reason is not None or value > HUNDRED:
            flags.append("DISCOUNT_OUT_OF_RANGE")
        else:
            disc = value
    record["flags"] = flags
    if flags:
        return record

    gross = (qty * price).quantize(CENT, rounding=ROUND_HALF_UP)
    discount = (gross * disc / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)
    record["line_gross"] = money(gross)
    record["line_discount"] = money(discount)
    record["line_net"] = money(gross - discount)
    return record


def compute_totals(records, rate):
    valid = [r for r in records if not r["flags"]]
    gross = sum((Decimal(r["line_gross"]) for r in valid), Decimal(0))
    discount = sum((Decimal(r["line_discount"]) for r in valid), Decimal(0))
    subtotal = gross - discount
    tax = (subtotal * rate / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)
    grand = subtotal + tax
    return {
        "gross_subtotal": money(gross),
        "discount_total": money(discount),
        "subtotal": money(subtotal),
        "tax": money(tax),
        "grand_total": money(grand),
    }


def print_table(records, totals, rate):
    headers = ["Row", "Item", "Qty", "Unit price", "Disc %", "Gross", "Discount", "Net", "Flags"]
    body = []
    for r in records:
        flags = ",".join(r["flags"]) if r["flags"] else "-"
        body.append([
            str(r["row"]), r["item"] or "", r["qty"] or "", r["unit_price"] or "",
            r["discount_percent"] or "", r["line_gross"] or "-", r["line_discount"] or "-",
            r["line_net"] or "-", flags,
        ])
    widths = [max(len(headers[i]), *(len(row[i]) for row in body)) for i in range(len(headers))]
    line = "  ".join(headers[i].ljust(widths[i]) for i in range(len(headers)))
    print(line)
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in body:
        print("  ".join(row[i].ljust(widths[i]) for i in range(len(headers))))
    print()
    print("Tax rate (percent): " + format(rate.normalize(), "f"))
    for label, key in (("Gross subtotal", "gross_subtotal"), ("Discount total", "discount_total"),
                       ("Subtotal", "subtotal"), ("Tax", "tax"), ("Grand total", "grand_total")):
        print(label.ljust(16) + totals[key])


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = Parser(prog="quote.py", description="Total an itemized quote from a CSV file.")
    parser.add_argument("input_file", help="CSV with item, qty, unit_price and optional discount_percent")
    parser.add_argument("--tax-rate", required=True, help="tax rate in percent, 0 to 100, for example 8.25")
    args = parser.parse_args(argv)

    rate = parse_tax_rate(args.tax_rate)
    text = read_text(args.input_file)
    columns, width, data_rows = read_columns_and_rows(text)

    with localcontext() as ctx:
        ctx.prec = 60
        records = [build_record(i, cells, columns, width) for i, cells in enumerate(data_rows, start=1)]
        totals = compute_totals(records, rate)

    flagged = [r for r in records if r["flags"]]
    status = "flagged" if flagged else "ok"
    print_table(records, totals, rate)
    payload = {
        "status": status,
        "tax_rate_percent": format(rate.normalize(), "f"),
        "line_count": len(records),
        "valid_line_count": len(records) - len(flagged),
        "flagged_line_count": len(flagged),
        "lines": records,
        "totals": totals,
    }
    print(json.dumps(payload, ensure_ascii=True))
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
