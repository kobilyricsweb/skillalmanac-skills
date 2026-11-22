"""Convert a JSON array of objects to a CSV file.

Usage:
    python -I json_to_csv.py <input-file> <output-file> [--separator TEXT] [--one-row-per-item]

Reads a local JSON file whose top-level value is an array. Object items become
CSV rows. Nested objects are flattened into dot-joined column names. Arrays are
either joined into one cell with --separator (default "; ") or, with
--one-row-per-item, expanded into several rows. Columns are the union of all
keys in first-seen order. The output is UTF-8 CSV with CRLF line endings and
RFC 4180 quoting from the csv module.

The output file is created with exclusive-create mode: an existing file is
never overwritten, and the input path is never used as the output path.

Exit codes: 0 ok, 1 findings (CSV written, some array items skipped), 2 usage
or input error. Errors are one JSON line on stderr. The summary is one JSON
line on stdout.
"""

import argparse
import csv
import json
import os
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
DEFAULT_SEPARATOR = "; "
SKIPPED_INDEX_LIMIT = 20


class _Fail(Exception):
    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason
        self.message = message


def _emit_error(reason, message):
    line = {"status": "error", "reason": reason, "message": message}
    sys.stderr.write(json.dumps(line, ensure_ascii=True) + "\n")
    sys.exit(2)


class _ArgParser(argparse.ArgumentParser):
    def error(self, message):
        _emit_error("usage", message)


def _reject_constant(name):
    raise ValueError("non-standard JSON constant: " + name)


def _load(path):
    try:
        size = os.path.getsize(path)
    except FileNotFoundError:
        raise _Fail("file_missing", "input file does not exist")
    except OSError:
        raise _Fail("file_unreadable", "input file cannot be read")
    if size > MAX_INPUT_BYTES:
        raise _Fail("file_too_large", "input file is larger than 2 MB")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise _Fail("file_unreadable", "input file cannot be opened")
    if len(raw) > MAX_INPUT_BYTES:
        raise _Fail("file_too_large", "input file is larger than 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise _Fail("invalid_utf8", "input file is not valid UTF-8")
    try:
        data = json.loads(text, parse_constant=_reject_constant)
    except RecursionError:
        raise _Fail("too_deep", "JSON nesting is too deep")
    except ValueError:
        raise _Fail("invalid_json", "input is not valid JSON")
    if not isinstance(data, list):
        raise _Fail("not_array", "top-level JSON value is not an array")
    if len(data) == 0:
        raise _Fail("no_records", "array is empty")
    objects = []
    skipped = []
    for index, item in enumerate(data):
        if isinstance(item, dict):
            objects.append(item)
        else:
            skipped.append(index)
    if not objects:
        raise _Fail("no_records", "array contains no JSON objects")
    return objects, skipped


def _scalar_text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    return str(value)


def _compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _element_text(value):
    if isinstance(value, (dict, list)):
        return _compact(value)
    return _scalar_text(value)


def _flatten(obj, prefix, out):
    for key, value in obj.items():
        column = prefix + "." + key if prefix else key
        if isinstance(value, dict):
            if value:
                _flatten(value, column, out)
            else:
                out[column] = "{}"
        else:
            out[column] = value
    return out


def _put_element(row, column, element):
    if isinstance(element, dict):
        if not element:
            row[column] = "{}"
            return
        for sub_column, sub_value in _flatten(element, column, {}).items():
            if isinstance(sub_value, list):
                row[sub_column] = _compact(sub_value)
            else:
                row[sub_column] = _scalar_text(sub_value)
    else:
        row[column] = _element_text(element)


def _join_rows(record, separator):
    row = {}
    for column, value in _flatten(record, "", {}).items():
        if isinstance(value, list):
            row[column] = separator.join(_element_text(e) for e in value)
        else:
            row[column] = _scalar_text(value)
    return [row]


def _expanded_rows(record):
    flat = _flatten(record, "", {})
    longest = 1
    for value in flat.values():
        if isinstance(value, list) and len(value) > longest:
            longest = len(value)
    rows = []
    for i in range(longest):
        row = {}
        for column, value in flat.items():
            if isinstance(value, list):
                if i < len(value):
                    _put_element(row, column, value[i])
                else:
                    row[column] = ""
            else:
                row[column] = _scalar_text(value)
        rows.append(row)
    return rows


def _build_rows(objects, one_row_per_item, separator):
    all_rows = []
    for record in objects:
        if one_row_per_item:
            all_rows.extend(_expanded_rows(record))
        else:
            all_rows.extend(_join_rows(record, separator))
    return all_rows


def _write_csv(output_path, columns, rows):
    try:
        fh = open(output_path, "x", encoding="utf-8", newline="")
    except FileExistsError:
        raise _Fail("output_exists", "output file already exists; nothing written")
    except OSError:
        raise _Fail("output_unwritable", "output file cannot be created")
    try:
        with fh:
            writer = csv.writer(fh)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([row.get(c, "") for c in columns])
    except OSError:
        try:
            os.remove(output_path)
        except OSError:
            pass
        raise _Fail("output_unwritable", "output file could not be written")


def main(argv=None):
    parser = _ArgParser(
        prog="json_to_csv.py",
        description="Convert a JSON array of objects to a CSV file.",
    )
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    parser.add_argument("--separator", default=None,
                        help='text placed between array items (default "; ")')
    parser.add_argument("--one-row-per-item", action="store_true",
                        help="expand arrays into rows instead of joining them")
    args = parser.parse_args(argv)

    try:
        if args.one_row_per_item and args.separator is not None:
            raise _Fail("option_conflict", "--separator cannot be used with --one-row-per-item")
        separator = DEFAULT_SEPARATOR if args.separator is None else args.separator
        if "\n" in separator or "\r" in separator:
            raise _Fail("bad_option", "separator must not contain CR or LF")
        if os.path.realpath(args.input_file) == os.path.realpath(args.output_file):
            raise _Fail("same_path", "output path is the input path")

        objects, skipped = _load(args.input_file)
        try:
            all_rows = _build_rows(objects, args.one_row_per_item, separator)
        except RecursionError:
            raise _Fail("too_deep", "JSON nesting is too deep")

        columns = []
        seen = set()
        for row in all_rows:
            for column in row:
                if column not in seen:
                    seen.add(column)
                    columns.append(column)

        missing = 0
        for row in all_rows:
            for column in columns:
                if row.get(column, "") == "":
                    missing += 1

        _write_csv(args.output_file, columns, all_rows)
    except _Fail as failure:
        _emit_error(failure.reason, failure.message)

    summary = {
        "status": "findings" if skipped else "ok",
        "mode": "rows" if args.one_row_per_item else "join",
        "rows": len(all_rows),
        "columns": len(columns),
        "missing_values": missing,
        "skipped_records": len(skipped),
        "skipped_indices": skipped[:SKIPPED_INDEX_LIMIT],
        "column_names": columns,
        "output_file": os.path.basename(args.output_file),
    }
    sys.stdout.write(json.dumps(summary, ensure_ascii=True) + "\n")
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
