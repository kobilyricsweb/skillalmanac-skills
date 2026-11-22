#!/usr/bin/env python3
"""Extract tables from one local HTML file into JSON or CSV output files.

Python 3.9+ standard library only. No network, no subprocess, no eval.
The input file is read-only. Output files are created with exclusive-create
mode, so an existing path is refused and never overwritten.

Usage:
  python -I html_tables.py <input-file> --format json --out <output-file>
  python -I html_tables.py <input-file> --format csv --out-dir <existing-dir>

Exit codes:
  0  tables extracted, no findings
  1  tables extracted, one or more findings (outputs were written)
  2  usage, input, or output error (one-line JSON error on stderr)
"""
import argparse
import csv
import json
import os
import sys
from html.parser import HTMLParser

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_SPAN = 1000


class UsageError(Exception):
    """Bad arguments, bad input, or an unusable output path."""


def _finding(code, row, col, detail):
    return {"code": code, "row": row, "col": col, "detail": detail}


class _Extractor(HTMLParser):
    """Collects top-level tables. Nested tables are flattened into the outer cell."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._depth = 0
        self._skip = 0
        self._cur = None
        self._section = None
        self._row = None
        self._cell = None
        self._in_caption = False
        self._caption_parts = []

    def _span(self, attrs, name):
        raw = dict(attrs).get(name)
        if raw is None:
            return 1
        row_no = len(self._cur["rows"]) + 1
        try:
            value = int(str(raw).strip())
        except ValueError:
            value = 0
        if value < 1:
            self._cur["findings"].append(
                _finding("SPAN_CLAMPED", row_no, None, name + " is not a positive integer; set to 1"))
            return 1
        if value > MAX_SPAN:
            self._cur["findings"].append(
                _finding("SPAN_CLAMPED", row_no, None, name + " above " + str(MAX_SPAN) + "; capped"))
            return MAX_SPAN
        return value

    def _close_cell(self):
        if self._cell is not None and self._row is not None:
            text = " ".join("".join(self._cell["parts"]).split())
            self._row.append({"text": text, "th": self._cell["th"],
                              "colspan": self._cell["colspan"], "rowspan": self._cell["rowspan"]})
        self._cell = None

    def _close_row(self):
        if self._row:
            self._cur["rows"].append({"section": self._section, "cells": self._row})
        self._row = None

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
            return
        if tag == "br" and self._cell is not None:
            self._cell["parts"].append(" ")
            return
        if tag == "table":
            self._depth += 1
            if self._depth == 1:
                self._cur = {"caption": None, "rows": [], "findings": [], "nested": False}
                self._section = None
            else:
                self._cur["nested"] = True
            return
        if self._depth != 1:
            return
        if tag == "caption":
            self._in_caption = True
            self._caption_parts = []
        elif tag in ("thead", "tbody", "tfoot"):
            self._close_cell()
            self._close_row()
            self._section = tag
        elif tag == "tr":
            self._close_cell()
            self._close_row()
            self._row = []
        elif tag in ("td", "th"):
            self._close_cell()
            if self._row is None:
                self._row = []
            self._cell = {"parts": [], "th": tag == "th",
                          "colspan": self._span(attrs, "colspan"),
                          "rowspan": self._span(attrs, "rowspan")}

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            if self._skip:
                self._skip -= 1
            return
        if tag == "table":
            if self._depth == 0:
                return
            self._depth -= 1
            if self._depth == 0:
                self._finish_table()
            return
        if self._depth != 1:
            return
        if tag == "caption":
            self._in_caption = False
            text = " ".join("".join(self._caption_parts).split())
            self._cur["caption"] = text or None
        elif tag in ("td", "th"):
            self._close_cell()
        elif tag == "tr":
            self._close_cell()
            self._close_row()
        elif tag in ("thead", "tbody", "tfoot"):
            self._close_cell()
            self._close_row()
            self._section = None

    def handle_data(self, data):
        if self._skip or self._depth == 0:
            return
        if self._in_caption:
            self._caption_parts.append(data)
        elif self._cell is not None:
            self._cell["parts"].append(data)

    def _finish_table(self):
        self._close_cell()
        self._close_row()
        self.tables.append(self._cur)
        self._cur = None
        self._depth = 0

    def finish(self):
        if self._cur is not None:
            self._finish_table()


def _expand(rows, findings):
    """Expand rowspan and colspan into a rectangular-by-row grid of strings."""
    grid = []
    spans = {}  # column -> [rows still to fill, text]
    for r_no, row in enumerate(rows, 1):
        line = {}
        new_spans = {}
        from_above = []
        col = 0
        for cell in row["cells"]:
            while col in spans:
                line[col] = spans[col][1]
                from_above.append(col)
                col += 1
            if cell["colspan"] > 1:
                findings.append(_finding("MERGED_COLSPAN", r_no, col + 1, "colspan=" + str(cell["colspan"])))
            if cell["rowspan"] > 1:
                findings.append(_finding("MERGED_ROWSPAN", r_no, col + 1, "rowspan=" + str(cell["rowspan"])))
            for k in range(cell["colspan"]):
                if (col + k) in spans:
                    findings.append(_finding("OVERLAP", r_no, col + k + 1,
                                             "cell overlaps a rowspan from an earlier row"))
                line[col + k] = cell["text"]
                if cell["rowspan"] > 1:
                    new_spans[col + k] = [cell["rowspan"] - 1, cell["text"]]
            col += cell["colspan"]
        while col in spans:
            line[col] = spans[col][1]
            from_above.append(col)
            col += 1
        for c in from_above:
            spans[c][0] -= 1
            if spans[c][0] == 0:
                del spans[c]
        spans.update(new_spans)
        grid.append([line.get(c, "") for c in range(max(line) + 1 if line else 0)])
    return grid


def _build_table(index, raw):
    findings = list(raw["findings"])
    if raw["nested"]:
        findings.append(_finding("NESTED_TABLE", None, None, "nested table flattened into outer cell text"))
    rows = raw["rows"]
    grid = _expand(rows, findings)
    width = max((len(r) for r in grid), default=0)
    for i, r in enumerate(grid, 1):
        if len(r) < width:
            findings.append(_finding("RAGGED_ROW", i, len(r) + 1,
                                     "row has " + str(len(r)) + " of " + str(width) + " columns; padded"))
            r.extend([""] * (width - len(r)))
    header = None
    if rows:
        first = rows[0]["cells"]
        if first and all(c["th"] for c in first):
            header = grid.pop(0)
        else:
            thead_idx = [i for i, row in enumerate(rows) if row["section"] == "thead"]
            if thead_idx:
                header = grid.pop(thead_idx[0])
    if header is None:
        findings.append(_finding("NO_HEADER", None, None, "no header row detected"))
    if not grid:
        findings.append(_finding("EMPTY_TABLE", None, None, "table has no data rows"))
    return {"index": index, "caption": raw["caption"], "header": header, "rows": grid,
            "row_count": len(grid), "column_count": width, "findings": findings}


def load_html(path):
    if not os.path.isfile(path):
        raise UsageError("input file not found")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise UsageError("input exceeds 2 MB limit")
    with open(path, "rb") as fh:
        data = fh.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise UsageError("input exceeds 2 MB limit")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise UsageError("input is not valid UTF-8")


def extract(text):
    parser = _Extractor()
    try:
        parser.feed(text)
        parser.close()
        parser.finish()
    except Exception:
        raise UsageError("HTML could not be parsed")
    return [_build_table(i, t) for i, t in enumerate(parser.tables, 1)]


def build_document(tables, source_name):
    file_findings = []
    if not tables:
        file_findings.append(_finding("NO_TABLES", None, None, "no table element found"))
    findings_count = sum(len(t["findings"]) for t in tables) + len(file_findings)
    return {"source_name": source_name, "table_count": len(tables),
            "row_count": sum(t["row_count"] for t in tables), "findings_count": findings_count,
            "file_findings": file_findings, "tables": tables}


def write_json(path, doc):
    with open(path, "x", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return [os.path.basename(path)]


def write_csv(out_dir, doc):
    if not os.path.isdir(out_dir):
        raise UsageError("output directory does not exist")
    plans = []
    index_tables = []
    for t in doc["tables"]:
        name = "table-%02d.csv" % t["index"]
        plans.append((os.path.join(out_dir, name), t))
        entry = {k: v for k, v in t.items() if k not in ("rows", "header")}
        entry["file"] = name
        index_tables.append(entry)
    index_path = os.path.join(out_dir, "index.json")
    for path, _ in plans + [(index_path, None)]:
        if os.path.exists(path):
            raise UsageError("output file already exists; refusing to overwrite")
    for path, t in plans:
        with open(path, "x", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            if t["header"] is not None:
                writer.writerow(t["header"])
            writer.writerows(t["rows"])
    index = dict(doc)
    index["tables"] = index_tables
    with open(index_path, "x", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return [os.path.basename(p) for p, _ in plans] + ["index.json"]


def _fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract HTML tables to JSON or CSV files.")
    parser.add_argument("input_file")
    parser.add_argument("--format", choices=["json", "csv"], required=True)
    parser.add_argument("--out", help="new JSON output file (--format json only)")
    parser.add_argument("--out-dir", help="existing directory for CSV output (--format csv only)")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        _fail("invalid arguments; see docstring for usage")
        return 2
    try:
        if args.format == "json" and (not args.out or args.out_dir):
            raise UsageError("--format json requires --out and must not use --out-dir")
        if args.format == "csv" and (not args.out_dir or args.out):
            raise UsageError("--format csv requires --out-dir and must not use --out")
        text = load_html(args.input_file)
        tables = extract(text)
        doc = build_document(tables, os.path.basename(args.input_file))
        if args.format == "json":
            outputs = write_json(args.out, doc)
        else:
            outputs = write_csv(args.out_dir, doc)
    except UsageError as exc:
        _fail(str(exc))
        return 2
    except FileExistsError:
        _fail("output file already exists; refusing to overwrite")
        return 2
    except OSError:
        _fail("file system error reading input or writing output")
        return 2
    status = "findings" if doc["findings_count"] else "ok"
    print(json.dumps({"status": status, "tables": doc["table_count"], "rows": doc["row_count"],
                      "findings": doc["findings_count"], "outputs": outputs}))
    return 1 if doc["findings_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
