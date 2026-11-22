"""Render CSV or JSON rows as an accessible HTML table fragment.

Usage:
  python scripts/rows_to_html.py <input-file> --output <output-file> --caption "<caption>" [--format csv|json] [--align-numeric]

Input: a CSV file (first row is the header) or a JSON file holding an array of objects.
Nested JSON values are flattened with dot-separated keys (lists use numeric indexes).
Output: one new UTF-8 HTML fragment with a caption, thead (th scope="col"), tbody,
and HTML-escaped cell text. An existing output path is refused, never overwritten.

Exit codes: 0 table written and every row matches the column set;
1 table written but some rows were ragged (listed in ragged_rows);
2 usage or input error, reported as one-line JSON on stderr.
Stdlib only. No network, no subprocess, no eval or exec.
"""
import argparse
import csv
import html
import io
import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024  # working value: input cap
NUMERIC_RE = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")


class InputError(Exception):
    pass


def fail(message):
    sys.stderr.write(json.dumps({"error": message, "exit": 2}) + "\n")
    return 2


def resolve_format(path, requested):
    if requested is not None:
        return requested
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return "csv"
    if ext == ".json":
        return "json"
    raise InputError("cannot infer format from extension; pass --format csv or --format json")


def read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input exceeds 2 MB cap")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("input is not valid UTF-8")


def parse_csv(text):
    try:
        rows = [r for r in csv.reader(io.StringIO(text, newline="")) if r]
    except csv.Error:
        raise InputError("CSV could not be parsed")
    if not rows:
        raise InputError("CSV has no header row")
    names = list(rows[0])
    if any(not n.strip() for n in names):
        raise InputError("empty column name in header")
    if len(set(names)) != len(names):
        raise InputError("duplicate column name in header")
    records = []
    for cells in rows[1:]:
        rec = dict(zip(names, cells))
        records.append((rec, len(cells) != len(names)))
    return names, records


def to_text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    return str(value)


def flatten(value, prefix, out):
    if isinstance(value, dict):
        if not value and prefix:
            out[prefix] = ""
            return
        for key, child in value.items():
            flatten(child, f"{prefix}.{key}" if prefix else str(key), out)
    elif isinstance(value, list):
        if not value:
            out[prefix] = ""
            return
        for index, child in enumerate(value):
            flatten(child, f"{prefix}.{index}", out)
    else:
        out[prefix] = to_text(value)


def parse_json(text):
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        raise InputError("JSON could not be parsed")
    if not isinstance(data, list):
        raise InputError("JSON root must be an array of objects")
    flat = []
    for item in data:
        if not isinstance(item, dict):
            raise InputError("every JSON array item must be an object")
        out = {}
        try:
            flatten(item, "", out)
        except RecursionError:
            raise InputError("JSON nesting is too deep")
        flat.append(out)
    columns = []
    seen = set()
    for rec in flat:
        for key in rec:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    colset = set(columns)
    records = [(rec, set(rec) != colset) for rec in flat]
    return columns, records


def numeric_columns(columns, records):
    found = []
    for col in columns:
        vals = [rec.get(col, "") for rec, _ in records if rec.get(col, "") != ""]
        if vals and all(NUMERIC_RE.fullmatch(v) for v in vals):
            found.append(col)
    return found


def esc(text):
    return html.escape(text, quote=True)


def build_table(columns, records, caption, align_numeric):
    numeric = set(numeric_columns(columns, records)) if align_numeric else set()
    lines = ["<table>", f"  <caption>{esc(caption)}</caption>", "  <thead>", "    <tr>"]
    for col in columns:
        lines.append(f'      <th scope="col">{esc(col)}</th>')
    lines += ["    </tr>", "  </thead>", "  <tbody>"]
    for rec, _ in records:
        lines.append("    <tr>")
        for col in columns:
            cell = esc(rec.get(col, ""))
            if col in numeric:
                lines.append(f'      <td class="num">{cell}</td>')
            else:
                lines.append(f"      <td>{cell}</td>")
        lines.append("    </tr>")
    lines += ["  </tbody>", "</table>", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render CSV or JSON rows as an accessible HTML table fragment.")
    parser.add_argument("input", help="CSV file with a header row, or JSON file holding an array of objects")
    parser.add_argument("--output", required=True, help="new HTML file to create; existing paths are refused")
    parser.add_argument("--caption", required=True, help="non-empty table caption")
    parser.add_argument("--format", choices=["csv", "json"], help="input format; default is taken from the extension")
    parser.add_argument("--align-numeric", action="store_true", help="add class=\"num\" to all-numeric columns")
    args = parser.parse_args(argv)

    caption = args.caption.strip()
    if not caption:
        return fail("caption must not be empty")
    if os.path.abspath(args.output) == os.path.abspath(args.input):
        return fail("output path must differ from input path")
    try:
        fmt = resolve_format(args.input, args.format)
        text = read_text(args.input)
        if fmt == "csv":
            columns, records = parse_csv(text)
        else:
            columns, records = parse_json(text)
    except InputError as exc:
        return fail(str(exc))
    except OSError:
        return fail("input file is missing or unreadable")

    if not records:
        return fail("no data rows")
    if not columns:
        return fail("no columns")

    table = build_table(columns, records, caption, args.align_numeric)
    try:
        with open(args.output, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(table)
    except FileExistsError:
        return fail("output path already exists; refusing to overwrite")
    except OSError:
        return fail("output file could not be created")

    ragged = [n for n, (_, flag) in enumerate(records, 1) if flag]
    summary = {
        "rows": len(records),
        "columns": len(columns),
        "numeric_columns": numeric_columns(columns, records) if args.align_numeric else [],
        "ragged_rows": ragged,
        "output_bytes": len(table.encode("utf-8")),
    }
    sys.stdout.write(json.dumps(summary) + "\n")
    return 1 if ragged else 0


if __name__ == "__main__":
    sys.exit(main())
