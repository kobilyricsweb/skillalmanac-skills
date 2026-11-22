"""Convert a plain-text table with aligned columns or repeated spaces into CSV.

Usage:
    python -I scripts/text_table_csv.py <input-file> <output-csv> [--split]

Fixed mode (default): the first non-space character of each token on the
header line starts a column. Each data line is sliced at those positions.
Split mode (--split): fields are separated by one or more tabs or by two or
more spaces.

Blank lines and rule or separator lines (for example a row of dashes under
the header) are skipped and counted. The first remaining line is the header.

Reads the input only. Writes one new CSV, opened with exclusive-create mode.
Refuses to run when the output exists or equals the input.

Exit codes: 0 no findings, 1 findings (the CSV is still written),
2 usage or input error. Standard library only. No network, no subprocess.
"""

import argparse
import csv
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
RULE_RE = re.compile(r"[\s\-=_+|:*~]+")
TOKEN_RE = re.compile(r"\S+")
SPLIT_RE = re.compile(r"\t+| {2,}")


def fail(message):
    sys.stdout.write(json.dumps({"status": "error", "error": message}) + "\n")
    sys.exit(2)


def is_rule_line(text):
    return bool(RULE_RE.fullmatch(text)) and len(re.findall(r"[-=_]", text)) >= 3


def read_lines(path):
    if not os.path.isfile(path):
        fail("input file not found")
    with open(path, "rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        fail("input exceeds 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # the empty piece after a trailing newline is not a line
    return lines


def classify(lines):
    blank = 0
    rules = 0
    content = []
    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip("\r")
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif is_rule_line(stripped):
            rules += 1
        else:
            content.append((number, line))
    return content, blank, rules


def fixed_layout(header):
    starts = [m.start() for m in TOKEN_RE.finditer(header)]
    gaps = set(range(0, starts[0]))
    for k in range(len(starts) - 1):
        seg_end = starts[k + 1]
        text_end = starts[k] + len(header[starts[k]:seg_end].rstrip())
        gaps.update(range(text_end, seg_end))
    return starts, gaps


def slice_fixed(line, starts):
    cells = []
    for k, st in enumerate(starts):
        begin = 0 if k == 0 else st
        end = starts[k + 1] if k + 1 < len(starts) else len(line)
        cells.append(line[begin:end].strip())
    return cells


def check_fixed(line, starts, gaps):
    problems = []
    if len(line.rstrip()) <= starts[-1]:
        problems.append(("short_row", "row has no text at or after the last column start"))
    for match in TOKEN_RE.finditer(line):
        s, e = match.span()
        if s in gaps or any(s < st < e for st in starts):
            problems.append(
                ("misaligned_row",
                 "token at character %d is in a gap or crosses a column start" % (s + 1)))
            break
    return problems


def split_cells(line):
    return [cell.strip() for cell in SPLIT_RE.split(line.strip())]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert an aligned plain-text table to CSV.")
    parser.add_argument("input_file")
    parser.add_argument("output_csv")
    parser.add_argument("--split", action="store_true",
                        help="split on tabs or 2+ spaces instead of header columns")
    args = parser.parse_args(argv)

    in_abs = os.path.normcase(os.path.abspath(args.input_file))
    out_abs = os.path.normcase(os.path.abspath(args.output_csv))
    if in_abs == out_abs:
        fail("output path equals input path")
    if os.path.exists(args.output_csv):
        fail("output path already exists")

    content, blank, rules = classify(read_lines(args.input_file))
    if not content:
        fail("no header line found")

    header_number, header_line = content[0]
    findings = []
    if args.split:
        header_cells = split_cells(header_line)
        starts = gaps = None
    else:
        starts, gaps = fixed_layout(header_line)
        header_cells = slice_fixed(header_line, starts)

    rows = []
    for number, line in content[1:]:
        if args.split:
            cells = split_cells(line)
            if len(cells) != len(header_cells):
                findings.append({
                    "line": number,
                    "code": "column_count_mismatch",
                    "detail": "%d fields, header has %d" % (len(cells), len(header_cells)),
                })
        else:
            cells = slice_fixed(line, starts)
            for code, detail in check_fixed(line, starts, gaps):
                findings.append({"line": number, "code": code, "detail": detail})
        rows.append(cells)

    try:
        with open(args.output_csv, "x", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header_cells)
            writer.writerows(rows)
    except FileExistsError:
        fail("output path already exists")
    except OSError:
        fail("output file could not be written")

    summary = {
        "status": "findings" if findings else "ok",
        "input": os.path.basename(args.input_file),
        "output": os.path.basename(args.output_csv),
        "mode": "split" if args.split else "fixed",
        "header_line": header_number,
        "columns": len(header_cells),
        "data_rows": len(rows),
        "blank_lines": blank,
        "rule_lines": rules,
        "findings": findings,
    }
    sys.stdout.write(json.dumps(summary) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
