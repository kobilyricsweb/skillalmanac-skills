"""Merge several CSV files by stacking them or by joining them on one key column.

Stack mode writes every data row of every input under one header: the union of
all input headers in first-seen order. A cell whose column a file does not have
is written empty. An optional source column records the input file name.

Join mode joins the inputs in order on one key column. The first input is the
base. Inner join keeps only rows whose key matches in every input. Left join
keeps every base row. Duplicate keys multiply output rows, as in SQL, and are
reported per file.

The script is read-only on its inputs, refuses to overwrite or to write over an
input, and uses the Python standard library only. It makes no network calls.

Usage:
  python -I scripts/csv_merge.py stack [--source-column NAME] --output OUT IN1 IN2 [IN3 ...]
  python -I scripts/csv_merge.py join --key COL [--how inner|left] --output OUT IN1 IN2 [IN3 ...]

Report: one line of JSON on stdout.
Errors: one line of JSON on stderr, as {"error": "..."}.
Exit codes: 0 ok with no findings; 1 ok with findings (rows dropped or duplicate
keys found; the output file is still written); 2 usage or input error.
"""

import argparse
import csv
import io
import json
import os
import sys
from collections import Counter

MAX_INPUT_BYTES = 2 * 1024 * 1024
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


class Fail(Exception):
    """Raised for any usage or input problem that must end with exit 2."""


def fail(message):
    raise Fail(message)


class JsonArgParser(argparse.ArgumentParser):
    """Argument parser that reports usage errors as one JSON line and exits 2."""

    def error(self, message):
        print(json.dumps({"error": "usage: " + message}), file=sys.stderr)
        sys.exit(EXIT_ERROR)


def build_parser():
    parser = JsonArgParser(description="Stack or join CSV files.")
    sub = parser.add_subparsers(dest="mode", required=True, parser_class=JsonArgParser)

    stack = sub.add_parser("stack", help="stack files under a unified header")
    stack.add_argument("--source-column", default=None, help="add a column with the input file name")
    stack.add_argument("--output", required=True, help="new CSV file to create (must not exist)")
    stack.add_argument("inputs", nargs="+", help="two or more input CSV files")

    join = sub.add_parser("join", help="join files on a key column")
    join.add_argument("--key", required=True, help="key column present in every input header")
    join.add_argument("--how", choices=["inner", "left"], default="inner")
    join.add_argument("--output", required=True, help="new CSV file to create (must not exist)")
    join.add_argument("inputs", nargs="+", help="two or more input CSV files; first is the base")
    return parser


def read_table(path):
    """Return (header, body_rows) for one input CSV, or fail with exit 2."""
    name = os.path.basename(path)
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("cannot read input file: " + name)
    if size > MAX_INPUT_BYTES or len(raw) > MAX_INPUT_BYTES:
        fail("input file is over 2 MB: " + name)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8: " + name)
    try:
        rows = [row for row in csv.reader(io.StringIO(text, newline="")) if row]
    except csv.Error:
        fail("malformed CSV in input file: " + name)
    if not rows:
        fail("input file has no header row: " + name)
    header = [cell.strip() for cell in rows[0]]
    if any(not cell for cell in header):
        fail("empty header name in input file: " + name)
    if len(set(header)) != len(header):
        fail("duplicate header name in input file: " + name)
    body = rows[1:]
    for number, row in enumerate(body, start=1):
        if len(row) != len(header):
            fail("data row %d has %d cells but header has %d in input file: %s"
                 % (number, len(row), len(header), name))
    return header, body


def stack_tables(paths, tables, source_column):
    columns = []
    for header, _ in tables:
        for name in header:
            if name not in columns:
                columns.append(name)
    if source_column is not None:
        if source_column in columns:
            fail("source column name already exists in the inputs: " + source_column)
        columns.append(source_column)

    records = []
    files = []
    for path, (header, body) in zip(paths, tables):
        position = {name: index for index, name in enumerate(header)}
        for row in body:
            record = [row[position[col]] if col in position else "" for col in columns]
            if source_column is not None:
                record[-1] = os.path.basename(path)
            records.append(record)
        files.append({"file": os.path.basename(path), "rows": len(body)})
    report = {
        "mode": "stack",
        "columns": len(columns),
        "files": files,
        "rows_written": len(records),
        "rows_dropped": 0,
    }
    return columns, records, report


def join_tables(paths, tables, key, how):
    for path, (header, _) in zip(paths, tables):
        if key not in header:
            fail("key column %r is missing from input file: %s" % (key, os.path.basename(path)))

    columns = list(tables[0][0])
    for header, _ in tables[1:]:
        for name in header:
            if name == key:
                continue
            if name in columns:
                fail("column %r appears in more than one input besides the key; rename it first" % name)
            columns.append(name)

    key_positions = [header.index(key) for header, _ in tables]

    # Duplicate keys per file: distinct non-empty keys that occur more than once.
    duplicates = []
    for (header, body), position in zip(tables, key_positions):
        counts = Counter(row[position].strip() for row in body if row[position].strip())
        duplicates.append(sum(1 for count in counts.values() if count > 1))

    base_header, base_body = tables[0]
    current = []
    for index, row in enumerate(base_body):
        values = dict(zip(base_header, row))
        current.append((values, [(0, index)], row[key_positions[0]].strip()))

    for file_index in range(1, len(tables)):
        header, body = tables[file_index]
        position = key_positions[file_index]
        lookup = {}
        for index, row in enumerate(body):
            value = row[position].strip()
            if value:
                lookup.setdefault(value, []).append(index)
        next_rows = []
        for values, sources, value in current:
            matches = lookup.get(value, []) if value else []
            if matches:
                for index in matches:
                    merged = dict(values)
                    for name, cell in zip(header, body[index]):
                        if name != key:
                            merged[name] = cell
                    next_rows.append((merged, sources + [(file_index, index)], value))
            elif how == "left":
                next_rows.append((values, sources, value))
        current = next_rows

    used = [set() for _ in tables]
    records = []
    for values, sources, _ in current:
        for file_index, index in sources:
            used[file_index].add(index)
        records.append([values.get(col, "") for col in columns])

    files = []
    total_dropped = 0
    for file_index, (path, (_, body)) in enumerate(zip(paths, tables)):
        dropped = len(body) - len(used[file_index])
        total_dropped += dropped
        files.append({
            "file": os.path.basename(path),
            "rows": len(body),
            "duplicate_keys": duplicates[file_index],
            "rows_dropped": dropped,
        })
    report = {
        "mode": "join",
        "key": key,
        "how": how,
        "columns": len(columns),
        "files": files,
        "rows_written": len(records),
        "rows_dropped": total_dropped,
    }
    return columns, records, report


def write_output(output, inputs, columns, records):
    out_abs = os.path.normcase(os.path.abspath(output))
    for path in inputs:
        if os.path.normcase(os.path.abspath(path)) == out_abs:
            fail("output path is the same as an input file")
    try:
        with open(output, "x", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(columns)
            writer.writerows(records)
    except FileExistsError:
        fail("output file already exists; choose a new path: " + os.path.basename(output))
    except OSError:
        fail("cannot create output file: " + os.path.basename(output))


def run(args):
    if len(args.inputs) < 2:
        fail("at least two input files are required")
    if args.mode == "join" and not args.key.strip():
        fail("--key must not be empty")
    tables = [read_table(path) for path in args.inputs]
    if args.mode == "stack":
        columns, records, report = stack_tables(args.inputs, tables, args.source_column)
    else:
        columns, records, report = join_tables(args.inputs, tables, args.key.strip(), args.how)
    write_output(args.output, args.inputs, columns, records)
    findings = report["rows_dropped"] > 0 or any(
        entry.get("duplicate_keys", 0) > 0 for entry in report["files"])
    return report, EXIT_FINDINGS if findings else EXIT_OK


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report, code = run(args)
    except Fail as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return EXIT_ERROR
    print(json.dumps(report))
    return code


if __name__ == "__main__":
    sys.exit(main())
