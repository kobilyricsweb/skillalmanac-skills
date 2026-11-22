"""Convert a CSV file with a header row into a JSON array of records.

Usage:
    python -I csv_to_json.py <input-file> <output-file> [--delimiter CHAR] [--empty-null]

Reads the input CSV (UTF-8, optional BOM, 2 MB cap), keys each record by the
header row, infers a type per column (integer, float, boolean, or string), and
writes a new JSON file. The output path must not exist; it is opened in
exclusive-create mode and is never overwritten. A column type table is printed
to stdout.

Exit codes:
    0  success, no findings
    1  success, but at least one column is mixed (see the "note" column)
    2  usage or input error; a one-line JSON error is written to stderr

Standard library only. No network, no subprocess, no eval or exec.
"""

import argparse
import csv
import io
import json
import math
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024

INT_RE = re.compile(r"^[+-]?(0|[1-9][0-9]*)$")
FLOAT_RE = re.compile(r"^[+-]?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$")
BOOL_VALUES = {"true": True, "false": False}


class InputError(Exception):
    """Raised for any bad input; mapped to exit 2."""


class JsonArgumentParser(argparse.ArgumentParser):
    """Argument parser that reports usage errors as one-line JSON, exit 2."""

    def error(self, message):
        emit_error(message)
        sys.exit(2)


def emit_error(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")


def parse_delimiter(value):
    if value == "tab":
        return "\t"
    if len(value) != 1:
        raise InputError("delimiter must be one character or 'tab'")
    return value


def read_input(path):
    try:
        size = os.path.getsize(path)
    except OSError:
        raise InputError("input file is missing or unreadable")
    if size > MAX_BYTES:
        raise InputError("input file exceeds the 2 MB limit")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        raise InputError("input file is missing or unreadable")
    if len(raw) > MAX_BYTES:
        raise InputError("input file exceeds the 2 MB limit")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("input file is not valid UTF-8")


def parse_rows(text, delimiter):
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    try:
        rows = [row for row in reader if row]
    except csv.Error as exc:
        raise InputError("CSV parse error: %s" % exc)
    if not rows:
        raise InputError("input has no header row")
    header = [name.strip() for name in rows[0]]
    seen = set()
    for index, name in enumerate(header, start=1):
        if name == "":
            raise InputError("blank header at column %d" % index)
        if name in seen:
            raise InputError("duplicate header '%s'" % name)
        seen.add(name)
    data = rows[1:]
    for number, row in enumerate(data, start=1):
        if len(row) != len(header):
            raise InputError(
                "data row %d has %d fields, expected %d"
                % (number, len(row), len(header))
            )
    return header, data


def classify(value):
    """Return the narrowest type name a single non-empty value fits."""
    if INT_RE.match(value):
        return "integer"
    if value.lower() in BOOL_VALUES:
        return "boolean"
    if FLOAT_RE.match(value):
        try:
            if math.isfinite(float(value)):
                return "float"
        except (ValueError, OverflowError):
            pass
    return "string"


def column_type(values):
    """Decide the column type from its non-empty, stripped values."""
    if not values:
        return "string", ""
    kinds = [classify(v) for v in values]
    if all(k == "boolean" for k in kinds):
        return "boolean", ""
    if all(k == "integer" for k in kinds):
        return "integer", ""
    if all(k in ("integer", "float") for k in kinds):
        return "float", ""
    mixed = sum(1 for k in kinds if k != "string")
    if mixed:
        return "string", "mixed: %d cell(s) look numeric or boolean" % mixed
    return "string", ""


def convert(value, kind, empty_null):
    if value == "":
        return None if empty_null else ""
    if kind == "integer":
        return int(value)
    if kind == "float":
        return float(value)
    if kind == "boolean":
        return BOOL_VALUES[value.lower()]
    return value


def build_records(header, data, empty_null):
    stripped = [[cell.strip() for cell in row] for row in data]
    types = []
    table = []
    for col, name in enumerate(header):
        values = [row[col] for row in stripped if row[col] != ""]
        kind, note = column_type(values)
        types.append(kind)
        table.append((name, kind, len(values), len(stripped) - len(values), note))
    records = []
    for row in stripped:
        record = {}
        for col, name in enumerate(header):
            record[name] = convert(row[col], types[col], empty_null)
        records.append(record)
    return records, table


def format_table(table):
    headers = ("column", "type", "non_empty", "empty", "note")
    rows = [(str(c), t, str(n), str(e), note) for c, t, n, e, note in table]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    lines = []
    lines.append("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)).rstrip())
    lines.append("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())
    return "\n".join(lines)


def main(argv):
    parser = JsonArgumentParser(
        description="Convert a CSV file with a header row to a JSON array of records."
    )
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    parser.add_argument("--delimiter", default=",", help="one character, or 'tab' (default ',')")
    parser.add_argument("--empty-null", action="store_true", help="write empty cells as null instead of \"\"")
    args = parser.parse_args(argv)

    try:
        delimiter = parse_delimiter(args.delimiter)
        if os.path.abspath(args.input_file) == os.path.abspath(args.output_file):
            raise InputError("output path must differ from the input path")
        text = read_input(args.input_file)
        header, data = parse_rows(text, delimiter)
        records, table = build_records(header, data, args.empty_null)
        payload = json.dumps(records, ensure_ascii=False, indent=2) + "\n"
        try:
            with open(args.output_file, "x", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
        except FileExistsError:
            raise InputError("output file already exists; choose a new path")
        except OSError:
            raise InputError("output file cannot be created")
    except InputError as exc:
        emit_error(str(exc))
        return 2

    print("rows: %d" % len(records))
    print(format_table(table))
    has_mixed = any(note.startswith("mixed") for _, _, _, _, note in table)
    return 1 if has_mixed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
