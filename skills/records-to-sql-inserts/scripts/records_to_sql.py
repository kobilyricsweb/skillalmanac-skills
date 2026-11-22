"""Generate SQL CREATE TABLE and INSERT statements from CSV or JSON records.

Usage:
    python -I scripts/records_to_sql.py <input-file> <output-file.sql> [--table NAME]

The input is a .csv file with a header row, or a .json file holding a non-empty
array of flat objects. One SQL type is inferred per column (BOOLEAN, INTEGER,
REAL, DATE, TEXT). The output is a new .sql file with one CREATE TABLE and
INSERT statements of up to 100 rows each. The output path must not exist (it is
created in exclusive mode "x") and must differ from the input path. The input is
read only.

Exit codes: 0 written, no findings. 1 written, findings printed on stdout.
2 usage or input error, nothing written, one-line JSON error on stderr.
Standard library only. No network, no subprocess, no eval or exec.
"""
import argparse
import csv
import datetime
import io
import json
import math
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
BATCH_ROWS = 100
INT64_MIN = -(2 ** 63)
INT64_MAX = 2 ** 63 - 1
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,62}")
INT_RE = re.compile(r"-?(0|[1-9][0-9]*)")
LOOSE_NUM_RE = re.compile(r"-?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?")
LEADING_ZERO_RE = re.compile(r"-?0[0-9]")
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def fail(message):
    """Print a one-line JSON error on stderr and exit 2."""
    sys.stderr.write(json.dumps({"status": "error", "message": message}) + "\n")
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage: records_to_sql.py <input-file> <output-file.sql> [--table NAME]")


def validate_columns(names):
    if not names:
        fail("no columns found")
    lowered = set()
    for name in names:
        if not IDENT_RE.fullmatch(name):
            fail("column name is not a valid identifier: " + repr(name))
        if name.lower() in lowered:
            fail("duplicate column name (case-insensitive): " + name)
        lowered.add(name.lower())


def json_cell(value, index, key):
    """Turn one JSON scalar into None (NULL) or a string for inference."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            fail("record %d field %s is not a finite number" % (index, key))
        return repr(value)
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    fail("record %d field %s is nested or unsupported" % (index, key))


def read_csv(text):
    try:
        rows = [row for row in csv.reader(io.StringIO(text, newline="")) if row]
    except csv.Error:
        fail("csv parse error")
    if not rows:
        fail("csv has no header row")
    header = [cell.strip() for cell in rows[0]]
    validate_columns(header)
    data = rows[1:]
    if not data:
        fail("csv has no data rows")
    records = []
    for number, row in enumerate(data, start=1):
        if len(row) != len(header):
            fail("data row %d has %d fields, header has %d" % (number, len(row), len(header)))
        record = {}
        for name, cell in zip(header, row):
            stripped = cell.strip()
            record[name] = stripped if stripped else None
        records.append(record)
    return header, records


def read_json(text):
    def reject_constant(name):
        raise ValueError(name)

    try:
        payload = json.loads(text, parse_constant=reject_constant)
    except (ValueError, RecursionError):
        fail("json parse error, or a non-finite number was found")
    if not isinstance(payload, list) or not payload:
        fail("json must be a non-empty array of objects")
    columns = []
    seen = set()
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            fail("record %d is not an object" % index)
        for key in item:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    validate_columns(columns)
    records = []
    for index, item in enumerate(payload, start=1):
        records.append({key: json_cell(item.get(key), index, key) for key in columns})
    return columns, records


def read_input(path):
    try:
        size = os.path.getsize(path)
    except OSError:
        fail("input file not found or unreadable")
    if size > MAX_INPUT_BYTES:
        fail("input exceeds the 2 MB limit")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("input file not found or unreadable")
    if len(raw) > MAX_INPUT_BYTES:
        fail("input exceeds the 2 MB limit")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")
    if "\x00" in text:
        fail("input contains a NUL character")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return read_csv(text)
    if ext == ".json":
        return read_json(text)
    fail("input must be a .csv or .json file")


def valid_date(value):
    try:
        datetime.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
        return True
    except ValueError:
        return False


def infer_type(values):
    """Return (SQL type, finding code or None) for the non-NULL values of one column."""
    if not values:
        return "TEXT", "EMPTY_COLUMN"
    if all(v.lower() in ("true", "false") for v in values):
        return "BOOLEAN", None
    if all(LOOSE_NUM_RE.fullmatch(v) for v in values):
        if any(LEADING_ZERO_RE.match(v) for v in values):
            return "TEXT", "LEADING_ZEROS"
        if all(INT_RE.fullmatch(v) for v in values):
            if all(INT64_MIN <= int(v) <= INT64_MAX for v in values):
                return "INTEGER", None
            return "TEXT", "OUT_OF_RANGE_INTEGER"
        return "REAL", None
    if all(DATE_RE.fullmatch(v) and valid_date(v) for v in values):
        return "DATE", None
    return "TEXT", None


FINDING_DETAIL = {
    "EMPTY_COLUMN": "no non-NULL values, typed TEXT",
    "LEADING_ZEROS": "numeric-looking values with leading zeros, typed TEXT to keep them",
    "OUT_OF_RANGE_INTEGER": "integer outside the signed 64-bit range, typed TEXT",
}


def render(value, sql_type):
    if value is None:
        return "NULL"
    if sql_type in ("INTEGER", "REAL"):
        return value
    if sql_type == "BOOLEAN":
        return "TRUE" if value.lower() == "true" else "FALSE"
    return "'" + value.replace("'", "''") + "'"


def build_sql(table, columns, types, records):
    header = [
        "-- Generated by records_to_sql.py. Rows: %d." % len(records),
        "-- Identifiers are double-quoted (ANSI SQL). MySQL needs ANSI_QUOTES or backticks.",
        "-- BOOLEAN is written as TRUE/FALSE. Older SQLite needs 1/0; MySQL stores BOOLEAN as TINYINT(1).",
        "-- Backslashes are not escaped. MySQL needs NO_BACKSLASH_ESCAPES or edited string literals.",
        "-- No primary key or NOT NULL constraints are emitted. Add them by hand if needed.",
        "",
    ]
    column_defs = ",\n".join('  "%s" %s' % (c, types[c]) for c in columns)
    lines = header + ['CREATE TABLE "%s" (\n%s\n);' % (table, column_defs), ""]
    column_list = ", ".join('"%s"' % c for c in columns)
    statements = 0
    for start in range(0, len(records), BATCH_ROWS):
        chunk = records[start:start + BATCH_ROWS]
        tuples = [
            "  (" + ", ".join(render(r[c], types[c]) for c in columns) + ")"
            for r in chunk
        ]
        lines.append('INSERT INTO "%s" (%s) VALUES\n%s;' % (table, column_list, ",\n".join(tuples)))
        lines.append("")
        statements += 1
    return "\n".join(lines) + "\n", statements


def main(argv=None):
    parser = _Parser(prog="records_to_sql.py", description="CSV or JSON records to SQL DDL and INSERTs.")
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    parser.add_argument("--table", default=None, help="table name (default: input file name)")
    args = parser.parse_args(argv)

    input_path = args.input_file
    output_path = args.output_file
    if not output_path.lower().endswith(".sql"):
        fail("output file must end in .sql")
    if os.path.realpath(output_path) == os.path.realpath(input_path):
        fail("output path must differ from the input path")
    if not os.path.isdir(os.path.dirname(os.path.abspath(output_path))):
        fail("output folder does not exist")

    table = args.table or os.path.splitext(os.path.basename(input_path))[0]
    if not IDENT_RE.fullmatch(table):
        fail("table name is not a valid identifier; pass --table NAME")

    columns, records = read_input(input_path)
    if not records:
        fail("no records found")

    types = {}
    nulls = {}
    findings = []
    for column in columns:
        values = [r[column] for r in records if r[column] is not None]
        sql_type, code = infer_type(values)
        types[column] = sql_type
        nulls[column] = len(records) - len(values)
        if code:
            findings.append((code, column, FINDING_DETAIL[code]))

    sql, statements = build_sql(table, columns, types, records)
    try:
        encoded = sql.encode("utf-8")
    except UnicodeEncodeError:
        fail("text contains characters that cannot be encoded as UTF-8")

    try:
        with open(output_path, "xb") as handle:
            handle.write(encoded)
    except FileExistsError:
        fail("output file already exists; refusing to overwrite")
    except OSError:
        fail("cannot create output file")

    print("records_to_sql: written " + os.path.basename(output_path))
    print("rows: %d" % len(records))
    print("statements: %d (batch size %d)" % (statements, BATCH_ROWS))
    print("column,type,nulls")
    for column in columns:
        print("%s,%s,%d" % (column, types[column], nulls[column]))
    for code, column, detail in findings:
        print("FINDING %s %s: %s" % (code, column, detail))
    print("findings: %d" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
