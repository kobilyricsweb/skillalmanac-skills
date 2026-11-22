"""Validate a CSV file against optional per-column rules.

Usage:
    python -I scripts/csv_validate.py <input-file> [--rules <rules-json>] [--delimiter <char>]

Reads the CSV and, if given, the rules JSON, then writes one JSON object to
stdout. Never writes files, never modifies inputs, makes no network calls.

Row numbers count every CSV record, header included: row 1 is the header and
row 2 is the first data row. Blank lines are skipped but still occupy a row
number.

Exit codes: 0 no findings, 1 one or more findings, 2 usage or input error.
"""

import csv
import datetime
import io
import json
import math
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
FINDING_CAP = 200
REGEX_MAX_LEN = 200
RULE_KEYS = {"type", "required", "unique", "enum", "regex", "min", "max"}
RULE_TYPES = {"int", "float", "date", "email"}
INT_RE = re.compile(r"[+-]?[0-9]+")
FLOAT_RE = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
DATE_RE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class InputError(Exception):
    """A usage or input problem. The script prints a one-line JSON error and exits 2."""


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=True) + "\n")


def read_text(path, label):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            raise InputError("%s is larger than 2 MB" % label)
        with open(path, "rb") as fh:
            raw = fh.read(MAX_BYTES + 1)
    except OSError:
        raise InputError("%s not found or not readable" % label)
    if len(raw) > MAX_BYTES:
        raise InputError("%s is larger than 2 MB" % label)
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("%s is not valid UTF-8" % label)


def parse_records(text, delimiter):
    records = []
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        for record in reader:
            records.append(record)
    except csv.Error:
        raise InputError("malformed CSV at record %d" % (len(records) + 1))
    return records


def check_rule(name, rule):
    if not isinstance(rule, dict):
        raise InputError("rule for column %s must be an object" % name)
    unknown = sorted(set(rule) - RULE_KEYS)
    if unknown:
        raise InputError("unknown rule key for column %s: %s" % (name, unknown[0]))
    if "type" in rule:
        kind = rule["type"]
        if not isinstance(kind, str) or kind not in RULE_TYPES:
            raise InputError("type for column %s must be one of int, float, date, email" % name)
    for key in ("required", "unique"):
        if key in rule and not isinstance(rule[key], bool):
            raise InputError("%s for column %s must be true or false" % (key, name))
    if "enum" in rule:
        values = rule["enum"]
        if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
            raise InputError("enum for column %s must be a non-empty list of strings" % name)
    if "regex" in rule:
        pattern = rule["regex"]
        if not isinstance(pattern, str) or len(pattern) > REGEX_MAX_LEN:
            raise InputError("regex for column %s must be a string of at most 200 characters" % name)
        try:
            re.compile(pattern)
        except (re.error, OverflowError, RecursionError):
            raise InputError("regex for column %s does not compile" % name)
    for key in ("min", "max"):
        if key in rule:
            value = rule[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise InputError("%s for column %s must be a finite number" % (key, name))
    if "min" in rule and "max" in rule and rule["min"] > rule["max"]:
        raise InputError("min is greater than max for column %s" % name)


def load_rules(path, column_index):
    text = read_text(path, "rules file")
    try:
        doc = json.loads(text)
    except (ValueError, RecursionError):
        raise InputError("rules file is not valid JSON")
    if not isinstance(doc, dict) or set(doc) != {"columns"} or not isinstance(doc["columns"], dict):
        raise InputError('rules file must be a JSON object whose only key is "columns"')
    rules = []
    for name, rule in doc["columns"].items():
        if name not in column_index:
            raise InputError("rules name a column that is not in the header: %s" % name)
        check_rule(name, rule)
        rules.append((column_index[name], name, rule))
    rules.sort(key=lambda item: item[0])
    return rules


def valid_iso_date(value):
    match = DATE_RE.fullmatch(value)
    if not match:
        return False
    try:
        datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return False
    return True


def check_cell(rule, value):
    """Return (code, message) for the first failing value check, or None."""
    kind = rule.get("type")
    if kind == "int" and not INT_RE.fullmatch(value):
        return "TYPE_INT", "expected a whole number"
    if kind == "float" and not FLOAT_RE.fullmatch(value):
        return "TYPE_FLOAT", "expected a number"
    if kind == "date" and not valid_iso_date(value):
        return "TYPE_DATE", "expected an ISO date YYYY-MM-DD"
    if kind == "email" and not EMAIL_RE.fullmatch(value):
        return "TYPE_EMAIL", "expected an email address"
    if "enum" in rule and value not in rule["enum"]:
        return "ENUM", "value is not in the allowed list"
    if "regex" in rule and not re.fullmatch(rule["regex"], value):
        return "REGEX", "value does not match the pattern"
    if "min" in rule or "max" in rule:
        if not FLOAT_RE.fullmatch(value):
            return "NOT_NUMERIC", "min or max is set but the value is not a number"
        number = float(value)
        if "min" in rule and number < rule["min"]:
            return "MIN", "value is below min"
        if "max" in rule and number > rule["max"]:
            return "MAX", "value is above max"
    return None


def run(argv):
    args = argv[1:]
    rules_path = None
    delimiter = ","
    positional = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--rules", "--delimiter"):
            if i + 1 >= len(args):
                raise InputError("%s needs a value" % arg)
            if arg == "--rules":
                rules_path = args[i + 1]
            else:
                delimiter = args[i + 1]
            i += 2
            continue
        if arg.startswith("--"):
            raise InputError("unknown option: %s" % arg)
        positional.append(arg)
        i += 1
    if len(positional) != 1:
        raise InputError("usage: csv_validate.py <input-file> [--rules <rules-json>] [--delimiter <char>]")
    if len(delimiter) != 1 or delimiter in '"\r\n':
        raise InputError("delimiter must be one character other than a quote or a line break")

    records = parse_records(read_text(positional[0], "input file"), delimiter)
    if not records:
        raise InputError("input file has no header row")
    header = records[0]
    width = len(header)
    findings = []

    def add(row, col0, code, message):
        name = None if col0 is None else (header[col0].strip() or None)
        findings.append({
            "row": row,
            "column_index": None if col0 is None else col0 + 1,
            "column": name,
            "code": code,
            "message": message,
        })

    column_index = {}
    for col0, raw in enumerate(header):
        name = raw.strip()
        if not name:
            add(1, col0, "BLANK_HEADER", "header cell is blank")
        elif name in column_index:
            add(1, col0, "DUPLICATE_HEADER", "header name repeats an earlier column")
        else:
            column_index[name] = col0

    rules = load_rules(rules_path, column_index) if rules_path is not None else []

    blank_rows = 0
    checked = 0
    unique_seen = {}
    for row_no, record in enumerate(records[1:], start=2):
        if not record:
            blank_rows += 1
            continue
        checked += 1
        if len(record) != width:
            add(row_no, None, "RAGGED_ROW", "expected %d fields, found %d" % (width, len(record)))
            continue
        for col0, name, rule in rules:
            value = record[col0].strip()
            if value == "":
                if rule.get("required"):
                    add(row_no, col0, "REQUIRED", "required value is empty")
                continue
            if rule.get("unique"):
                seen = unique_seen.setdefault(name, {})
                if value in seen:
                    add(row_no, col0, "UNIQUE", "duplicate of row %d" % seen[value])
                else:
                    seen[value] = row_no
            failure = check_cell(rule, value)
            if failure:
                add(row_no, col0, failure[0], failure[1])

    findings.sort(key=lambda f: (f["row"], f["column_index"] or 0, f["code"]))
    counts = {}
    for finding in findings:
        counts[finding["code"]] = counts.get(finding["code"], 0) + 1
    total = len(findings)
    emit({
        "status": "clean" if total == 0 else "findings",
        "rows_checked": checked,
        "blank_rows_skipped": blank_rows,
        "columns": width,
        "findings_total": total,
        "truncated": total > FINDING_CAP,
        "counts_by_code": {code: counts[code] for code in sorted(counts)},
        "findings": findings[:FINDING_CAP],
    })
    return 0 if total == 0 else 1


def main(argv):
    try:
        return run(argv)
    except InputError as exc:
        emit({"status": "error", "error": str(exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
