"""Convert a CSV, TSV or first HTML table in a text file into an aligned Markdown table.

Usage:
    python -I scripts/table_to_md.py <input-file> [--format auto|csv|tsv|html]
                                     [--output <new-file>] [--right-align-numeric]

The input is read only (UTF-8, at most 2 MB). The Markdown table goes to stdout,
or to a new file when --output is given; an existing output file is never
overwritten and the input is never written to. One JSON status line goes to stderr.

Exit codes: 0 ok, 1 findings (table written; review the findings), 2 usage or input error.
No network, no subprocess, no eval or exec.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from html.parser import HTMLParser

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_COLUMNS = 60  # working value
NUMERIC_RE = re.compile(r"^[+-]?\$?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?%?$")


class InputError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def emit_error(code, message):
    sys.stderr.write(json.dumps({"status": "error", "code": code, "message": message}) + "\n")


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        emit_error("USAGE", "invalid arguments; see the usage line in the skill")
        sys.exit(2)


def read_input(path):
    if not os.path.exists(path):
        raise InputError("FILE_NOT_FOUND", "input file does not exist")
    if not os.path.isfile(path):
        raise InputError("NOT_A_FILE", "input path is not a regular file")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError("FILE_NOT_FOUND", "input file cannot be read")
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("INPUT_TOO_LARGE", "input exceeds 2 MB")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("INVALID_UTF8", "input is not valid UTF-8")


def detect_format(text, requested):
    if requested != "auto":
        return requested
    if "<table" in text.lower():
        return "html"
    first = next((line for line in text.splitlines() if line.strip()), "")
    return "tsv" if first.count("\t") > first.count(",") else "csv"


def parse_delimited(text, delimiter):
    rows = []
    try:
        for row in csv.reader(io.StringIO(text), delimiter=delimiter):
            if any(cell.strip() for cell in row):
                rows.append(row)
    except csv.Error:
        raise InputError("PARSE_ERROR", "delimited text could not be parsed")
    return rows


class _FirstTableParser(HTMLParser):
    """Collects rows of the first top-level table. Nested tables are skipped."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.found = False
        self._depth = 0
        self._done = False
        self._row = None
        self._cell = None

    def _end_cell(self):
        if self._cell is not None:
            if self._row is None:
                self._row = []
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None

    def _end_row(self):
        self._end_cell()
        if self._row is not None:
            if any(cell for cell in self._row):
                self.rows.append(self._row)
            self._row = None

    def handle_starttag(self, tag, attrs):
        if self._done:
            return
        if tag == "table":
            if self._depth == 0:
                self.found = True
            self._depth += 1
            return
        if self._depth != 1:
            return
        if tag == "tr":
            self._end_row()
            self._row = []
        elif tag in ("td", "th"):
            self._end_cell()
            self._cell = []
            if self._row is None:
                self._row = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if self._done:
            return
        if tag == "table":
            self._depth -= 1
            if self._depth == 0:
                self._end_row()
                self._done = True
            return
        if self._depth != 1:
            return
        if tag in ("td", "th"):
            self._end_cell()
        elif tag == "tr":
            self._end_row()

    def handle_data(self, data):
        if self._cell is not None and self._depth == 1 and not self._done:
            self._cell.append(data)


def parse_html(text):
    parser = _FirstTableParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        raise InputError("PARSE_ERROR", "HTML could not be parsed")
    if not parser.found:
        raise InputError("NO_TABLE", "no table element found in the input")
    return parser.rows


def build_table(rows, right_numeric):
    rows = [[" ".join(cell.split()) for cell in row] for row in rows]
    ncols = max(len(row) for row in rows)
    if ncols > MAX_COLUMNS:
        raise InputError("TOO_MANY_COLUMNS", "table has more columns than the working limit of 60")

    findings = []
    for number, row in enumerate(rows, start=1):
        if len(row) != ncols:
            findings.append({"code": "RAGGED_ROW", "row": number,
                             "cells": len(row), "expected": ncols})
    for col, cell in enumerate(rows[0], start=1):
        if cell == "":
            findings.append({"code": "EMPTY_HEADER", "column": col})

    padded = [row + [""] * (ncols - len(row)) for row in rows]
    header, body = padded[0], padded[1:]

    numeric = []
    for col in range(ncols):
        values = [row[col] for row in body if row[col]]
        numeric.append(bool(values) and all(NUMERIC_RE.match(v) for v in values))

    def esc(value):
        return value.replace("|", "\\|")

    header_cells = [esc(c) for c in header]
    body_cells = [[esc(c) for c in row] for row in body]
    right = [right_numeric and numeric[col] for col in range(ncols)]

    widths = []
    for col in range(ncols):
        width = max([3, len(header_cells[col])] + [len(row[col]) for row in body_cells])
        widths.append(width)

    def fmt_row(cells):
        out = []
        for col, cell in enumerate(cells):
            out.append(cell.rjust(widths[col]) if right[col] else cell.ljust(widths[col]))
        return "| " + " | ".join(out) + " |"

    delim = []
    for col in range(ncols):
        dashes = widths[col] - 1
        if right[col]:
            delim.append("-" * dashes + ":")
        else:
            delim.append(":" + "-" * dashes)

    lines = [fmt_row(header_cells), "| " + " | ".join(delim) + " |"]
    lines.extend(fmt_row(row) for row in body_cells)
    return "\n".join(lines) + "\n", findings, len(body), ncols


def write_output(path, text, input_path):
    if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(input_path)):
        raise InputError("SAME_AS_INPUT", "output path is the input file")
    if os.path.lexists(path):
        raise InputError("OUTPUT_EXISTS", "output file already exists; choose a new name")
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except FileExistsError:
        raise InputError("OUTPUT_EXISTS", "output file already exists; choose a new name")
    except OSError:
        raise InputError("OUTPUT_WRITE_FAILED", "output file could not be created")


def main(argv=None):
    parser = _Parser(description="Convert a CSV, TSV or HTML table to an aligned Markdown table.")
    parser.add_argument("input")
    parser.add_argument("--format", choices=["auto", "csv", "tsv", "html"], default="auto")
    parser.add_argument("--output")
    parser.add_argument("--right-align-numeric", action="store_true")
    args = parser.parse_args(argv)

    try:
        text = read_input(args.input)
        fmt = detect_format(text, args.format)
        if fmt == "html":
            rows = parse_html(text)
        else:
            rows = parse_delimited(text, "\t" if fmt == "tsv" else ",")
        if not rows:
            raise InputError("EMPTY_TABLE", "no non-empty rows found")
        table_text, findings, nrows, ncols = build_table(rows, args.right_align_numeric)
        if args.output:
            write_output(args.output, table_text, args.input)
        else:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            sys.stdout.write(table_text)
    except InputError as exc:
        emit_error(exc.code, exc.message)
        return 2

    status = "findings" if findings else "ok"
    sys.stderr.write(json.dumps({"status": status, "rows": nrows, "columns": ncols,
                                 "findings": findings}) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
