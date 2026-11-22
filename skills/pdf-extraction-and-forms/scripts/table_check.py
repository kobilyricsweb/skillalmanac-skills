#!/usr/bin/env python3
"""Validate a table that was extracted from a PDF and saved as CSV. Standard library only.

    python table_check.py table.csv [--rows N] [--cols N] [--sum COL=VALUE ...]
                          [--total-row] [--tol 0.01] [--decimal dot|comma]

COL is a header name or a 1-based column number. --rows counts body rows only
(header and, with --total-row, the total row are excluded). --sum compares the
column sum of the body rows with a number taken from the PDF itself.
--total-row treats the last row as the table's printed total and compares it
with the sum of the rows above it, for every mostly-numeric column.

Reads the CSV, writes one strict JSON object to stdout, changes nothing.
Exit codes: 0 = all checks passed, 1 = at least one check failed, 2 = usage
error or unreadable file. Checks also always look for: ragged rows, blank
rows, header rows repeated inside the body (page breaks), exact duplicate rows
and cells that are not numbers in a numeric column.
"""
import csv
import json
import re
import sys

NUMERIC_SHARE = 0.8   # a column counts as numeric when this share of non-blank body cells parse
DEFAULT_TOL = 0.01    # absolute tolerance for sums: one cent covers rounding in printed totals
BLANKS = {"", "-", "--", "–", "—", "n/a", "N/A"}


def parse_number(cell, decimal):
    """Return float or None. Handles currency, (1,234.50), trailing minus, percent, both decimal styles."""
    s = cell.strip().replace("−", "-").replace(" ", "").replace(" ", "")
    s = re.sub(r"[$€£₪¥%]|USD|EUR|GBP|ILS|NIS", "", s)
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s.endswith("-") and s[:-1]:
        neg, s = True, s[:-1]
    if s.startswith("-"):
        neg, s = not neg, s[1:]
    if decimal == "comma":
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    if not re.fullmatch(r"\d+(\.\d+)?|\.\d+", s):
        return None
    v = float(s)
    return -v if neg else v


def main(argv):
    opts = {"rows": None, "cols": None, "sum": [], "total_row": False, "tol": DEFAULT_TOL, "decimal": "dot"}
    path, i = None, 0
    try:
        while i < len(argv):
            a = argv[i]
            if a == "--total-row":
                opts["total_row"] = True
            elif a in ("--rows", "--cols"):
                i += 1
                opts[a[2:]] = int(argv[i])
            elif a == "--sum":
                i += 1
                col, val = argv[i].rsplit("=", 1)
                opts["sum"].append((col, float(val)))
            elif a == "--tol":
                i += 1
                opts["tol"] = float(argv[i])
            elif a == "--decimal":
                i += 1
                if argv[i] not in ("dot", "comma"):
                    raise ValueError("decimal")
                opts["decimal"] = argv[i]
            elif a.startswith("-"):
                raise ValueError(a)
            elif path is None:
                path = a
            else:
                raise ValueError(a)
            i += 1
    except (IndexError, ValueError):
        path = None
    if path is None:
        print(json.dumps({"ok": False, "error": "usage: table_check.py table.csv [--rows N] [--cols N] [--sum COL=VALUE] [--total-row] [--tol X] [--decimal dot|comma]"}))
        return 2
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"ok": False, "error": "cannot read %s as UTF-8 CSV: %s" % (path, exc)}))
        return 2
    if not rows:
        print(json.dumps({"ok": False, "error": "empty file"}))
        return 2

    header, body = rows[0], rows[1:]
    width = len(header)
    checks, failed = [], False

    def add(name, ok, detail):
        nonlocal failed
        checks.append({"check": name, "ok": ok, "detail": detail})
        failed = failed or not ok

    blank = [n + 2 for n, r in enumerate(body) if not any(c.strip() for c in r)]
    body_idx = [(n + 2, r) for n, r in enumerate(body) if any(c.strip() for c in r)]
    add("blank_rows", not blank, {"csv_lines": blank})
    ragged = [{"csv_line": n, "cells": len(r)} for n, r in body_idx if len(r) != width]
    add("ragged_rows", not ragged, {"expected_cells": width, "rows": ragged})
    norm = [c.strip().lower() for c in header]
    repeated = [n for n, r in body_idx if [c.strip().lower() for c in r] == norm]
    add("repeated_header_rows", not repeated, {"csv_lines": repeated})
    body_idx = [(n, r) for n, r in body_idx if n not in repeated]
    seen, dups = {}, []
    for n, r in body_idx:
        k = tuple(c.strip() for c in r)
        if k in seen:
            dups.append({"csv_line": n, "same_as": seen[k]})
        else:
            seen[k] = n
    add("duplicate_rows", not dups, {"rows": dups, "note": "may be legitimate; confirm against the PDF"})

    total = None
    if opts["total_row"]:
        if not body_idx:
            add("total_row", False, {"error": "no body rows"})
        else:
            total = body_idx[-1]
            body_idx = body_idx[:-1]
    if opts["cols"] is not None:
        add("column_count", width == opts["cols"], {"found": width, "expected": opts["cols"]})
    if opts["rows"] is not None:
        add("row_count", len(body_idx) == opts["rows"], {"found": len(body_idx), "expected": opts["rows"]})

    numeric = {}
    bad_cells = []
    for c in range(width):
        vals, tot_non_blank, unparsed = [], 0, []
        for n, r in body_idx:
            if c >= len(r) or r[c].strip() in BLANKS:
                continue
            tot_non_blank += 1
            v = parse_number(r[c], opts["decimal"])
            if v is None:
                unparsed.append({"csv_line": n, "value": r[c]})
            else:
                vals.append(v)
        if tot_non_blank and len(vals) / tot_non_blank >= NUMERIC_SHARE:
            numeric[c] = vals
            bad_cells.extend({"column": header[c], **u} for u in unparsed)
    add("numeric_cells_parse", not bad_cells, {"cells": bad_cells, "numeric_columns": [header[c] for c in numeric]})

    def find_col(spec):
        if spec.isdigit() and 1 <= int(spec) <= width:
            return int(spec) - 1
        for c, h in enumerate(header):
            if h.strip().lower() == spec.strip().lower():
                return c
        return None

    for spec, want in opts["sum"]:
        c = find_col(spec)
        if c is None or c not in numeric:
            add("sum:" + spec, False, {"error": "column not found or not numeric"})
            continue
        got = round(sum(numeric[c]), 6)
        add("sum:" + header[c], abs(got - want) <= opts["tol"], {"sum_of_rows": got, "expected": want, "tolerance": opts["tol"]})
    if total is not None:
        for c in sorted(numeric):
            if c >= len(total[1]) or total[1][c].strip() in BLANKS:
                continue
            tv = parse_number(total[1][c], opts["decimal"])
            if tv is None:
                continue
            got = round(sum(numeric[c]), 6)
            add("total_row:" + header[c], abs(got - tv) <= opts["tol"], {"sum_of_rows": got, "printed_total": tv, "tolerance": opts["tol"]})

    rep = {"ok": not failed, "file": path, "columns": width, "body_rows": len(body_idx),
           "checks": checks,
           "limits": "Checks the CSV against numbers you supply or the table's own total. It cannot tell a wrong cell from a right one that still sums correctly."}
    print(json.dumps(rep, ensure_ascii=True, allow_nan=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
