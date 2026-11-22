"""Checks page titles and meta descriptions in one CSV file.

Input: a UTF-8 CSV whose header row contains the columns url, title and
description (other columns are ignored). The script only reads the input and
writes results to stdout; it never writes files.

Checks: empty tags, character-length bounds, a pixel-width proxy (an
approximation from a fixed character-width table, not a font renderer),
duplicate titles and duplicate descriptions across rows, and titles that
equal their description.

Usage: python -I title_meta_check.py <input-file> [--format json|table]
Exit codes: 0 no findings, 1 findings, 2 usage or input error.
"""
import argparse
import csv
import io
import json
import os
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
TITLE_MIN_CHARS = 25
TITLE_MAX_CHARS = 60
DESC_MIN_CHARS = 70
DESC_MAX_CHARS = 160
TITLE_MAX_PX = 580
DESC_MAX_PX = 920
REQUIRED_COLUMNS = ("url", "title", "description")

CODES = (
    "EMPTY_TITLE",
    "EMPTY_DESCRIPTION",
    "TITLE_TOO_SHORT",
    "TITLE_TOO_LONG",
    "DESCRIPTION_TOO_SHORT",
    "DESCRIPTION_TOO_LONG",
    "TITLE_PIXELS_OVER",
    "DESCRIPTION_PIXELS_OVER",
    "DUPLICATE_TITLE",
    "DUPLICATE_DESCRIPTION",
    "TITLE_EQUALS_DESCRIPTION",
)

DEFAULT_PX = 9
UPPER_PX = 11
CHAR_PX = {
    " ": 4, "I": 5, "i": 4, "j": 4, "l": 4, ".": 4, ",": 4, ":": 4,
    ";": 4, "'": 3, "!": 5, "|": 5, "-": 5, "(": 5, ")": 5, "f": 5,
    "r": 6, "t": 6, "m": 14, "w": 12, "M": 13, "W": 15,
}


class InputError(Exception):
    """Raised for unreadable, oversized, malformed or incomplete input."""


def char_px(ch):
    if ch in CHAR_PX:
        return CHAR_PX[ch]
    if ch.isupper():
        return UPPER_PX
    return DEFAULT_PX


def pixel_width(text):
    return sum(char_px(ch) for ch in text)


def normalize(text):
    return " ".join(text.split()).casefold()


def read_rows(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise InputError("cannot read input file: %s" % (exc.strerror or "unknown error"))
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input exceeds the 2 MB cap")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("input is not valid UTF-8")
    if not text.strip():
        raise InputError("input is empty")

    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
        cols = [h.strip().lower() for h in header]
        missing = [c for c in REQUIRED_COLUMNS if c not in cols]
        if missing:
            raise InputError("missing required column(s): " + ", ".join(missing))
        idx = {c: cols.index(c) for c in REQUIRED_COLUMNS}
        rows = []
        for rec in reader:
            if not rec:
                continue
            fields = [rec[idx[c]] if idx[c] < len(rec) else "" for c in REQUIRED_COLUMNS]
            rows.append((fields[0].strip(), fields[1], fields[2]))
    except csv.Error as exc:
        raise InputError("CSV parse error: %s" % exc)
    if not rows:
        raise InputError("no data rows after the header")
    return rows


def check_row(title, desc):
    out = []
    t = title.strip()
    d = desc.strip()
    if not t:
        out.append(("EMPTY_TITLE", "title is empty"))
    else:
        n = len(t)
        if n > TITLE_MAX_CHARS:
            out.append(("TITLE_TOO_LONG", "%d chars, limit %d" % (n, TITLE_MAX_CHARS)))
        elif n < TITLE_MIN_CHARS:
            out.append(("TITLE_TOO_SHORT", "%d chars, minimum %d" % (n, TITLE_MIN_CHARS)))
        px = pixel_width(t)
        if px > TITLE_MAX_PX:
            out.append(("TITLE_PIXELS_OVER", "about %d px, limit %d" % (px, TITLE_MAX_PX)))
    if not d:
        out.append(("EMPTY_DESCRIPTION", "description is empty"))
    else:
        n = len(d)
        if n > DESC_MAX_CHARS:
            out.append(("DESCRIPTION_TOO_LONG", "%d chars, limit %d" % (n, DESC_MAX_CHARS)))
        elif n < DESC_MIN_CHARS:
            out.append(("DESCRIPTION_TOO_SHORT", "%d chars, minimum %d" % (n, DESC_MIN_CHARS)))
        px = pixel_width(d)
        if px > DESC_MAX_PX:
            out.append(("DESCRIPTION_PIXELS_OVER", "about %d px, limit %d" % (px, DESC_MAX_PX)))
    if t and d and normalize(t) == normalize(d):
        out.append(("TITLE_EQUALS_DESCRIPTION", "title and description are the same text"))
    return out


def duplicate_findings(numbered, index, code, label):
    groups = {}
    for row_no, _url, title, desc in numbered:
        value = (title, desc)[index - 2]
        key = normalize(value)
        if key:
            groups.setdefault(key, []).append(row_no)
    found = {}
    for members in groups.values():
        if len(members) < 2:
            continue
        for r in members:
            others = ", ".join(str(o) for o in members if o != r)
            found.setdefault(r, []).append((code, "%s shared with rows %s" % (label, others)))
    return found


def run(path):
    rows = read_rows(path)
    numbered = [(i + 1, url, title, desc) for i, (url, title, desc) in enumerate(rows)]
    dup_title = duplicate_findings(numbered, 2, "DUPLICATE_TITLE", "title")
    dup_desc = duplicate_findings(numbered, 3, "DUPLICATE_DESCRIPTION", "description")
    findings = []
    for row_no, url, title, desc in numbered:
        items = check_row(title, desc)
        items += dup_title.get(row_no, [])
        items += dup_desc.get(row_no, [])
        for code, detail in items:
            findings.append({"row": row_no, "url": url, "code": code, "detail": detail})
    counts = {code: 0 for code in CODES}
    for item in findings:
        counts[item["code"]] += 1
    return numbered, findings, counts


def print_table(result):
    lines = ["%-5s %-24s %-44s %s" % ("row", "code", "url", "detail")]
    for f in result["findings"]:
        lines.append("%-5d %-24s %-44s %s" % (f["row"], f["code"], f["url"][:44], f["detail"]))
    lines.append("rows: %d  findings: %d  status: %s" % (
        result["rows"], len(result["findings"]), result["status"]))
    for line in lines:
        print(line.encode("ascii", "backslashreplace").decode("ascii"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check page titles and meta descriptions in a CSV file.")
    parser.add_argument("input_file", help="CSV with columns url, title, description")
    parser.add_argument("--format", choices=("json", "table"), default="json")
    args = parser.parse_args(argv)
    try:
        numbered, findings, counts = run(args.input_file)
    except InputError as exc:
        print(json.dumps({"status": "input_error", "error": str(exc)}))
        return 2
    result = {
        "file": os.path.basename(args.input_file),
        "rows": len(numbered),
        "status": "findings" if findings else "ok",
        "counts": counts,
        "findings": findings,
    }
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print_table(result)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
