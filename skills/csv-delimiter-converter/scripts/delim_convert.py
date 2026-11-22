"""Convert delimited text between comma, tab, semicolon and pipe.

Usage:
  python -I scripts/delim_convert.py <input-file> <output-file> --to {comma,tab,semicolon,pipe} [--from {auto,comma,tab,semicolon,pipe}]

The script reads <input-file> (UTF-8, at most 2 MB), detects the input delimiter
unless --from is given, parses it with the csv module, builds the converted text in
memory, parses that text back and compares every cell with the original. The output
file is created only when the comparison passes, using exclusive-create mode, so an
existing file is never overwritten and the input file is never written.

Exit codes: 0 status ok; 1 status findings (ragged records found, output written) or
status verify_failed (nothing written); 2 usage or input error.
A JSON result object is printed on stdout for exit 0 and 1. A one-line JSON error
object is printed on stderr for exit 2.
"""
import argparse
import collections
import csv
import io
import json
import os
import sys

MAX_BYTES = 2 * 1024 * 1024
DELIMS = {"comma": ",", "tab": "\t", "semicolon": ";", "pipe": "|"}
DETECT_ORDER = ["comma", "tab", "semicolon", "pipe"]
LIST_CAP = 20


def fail(code, message):
    sys.stderr.write(json.dumps({"error": message, "code": code}) + "\n")
    sys.exit(2)


def read_input(path):
    if not os.path.isfile(path):
        fail("input_missing", "input file not found or not a regular file")
    if os.path.getsize(path) > MAX_BYTES:
        fail("input_too_large", "input exceeds the 2 MB cap")
    with open(path, "rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        fail("input_too_large", "input exceeds the 2 MB cap")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8", "input is not valid UTF-8")


def parse(text, delim):
    try:
        reader = csv.reader(io.StringIO(text), delimiter=delim, quotechar='"', doublequote=True)
        return list(reader)
    except csv.Error as exc:
        fail("csv_parse_error", "csv parse failed: " + str(exc))


def detect(text):
    """Return the delimiter name whose parse gives the most uniform column count.

    Score per delimiter = (share of non-empty records at the modal column count,
    modal column count). A delimiter whose modal count is below 2 is not a candidate.
    Ties keep the earlier name in DETECT_ORDER.
    """
    best_name, best_score = None, None
    for name in DETECT_ORDER:
        rows = [r for r in parse(text, DELIMS[name]) if r]
        if not rows:
            continue
        counts = collections.Counter(len(r) for r in rows)
        mode_len, mode_count = counts.most_common(1)[0]
        if mode_len < 2:
            continue
        score = (mode_count / len(rows), mode_len)
        if best_score is None or score > best_score:
            best_name, best_score = name, score
    return best_name


def main():
    ap = argparse.ArgumentParser(description="Convert delimited text between comma, tab, semicolon and pipe.")
    ap.add_argument("input_file")
    ap.add_argument("output_file")
    ap.add_argument("--to", required=True, choices=sorted(DELIMS))
    ap.add_argument("--from", dest="src", default="auto", choices=["auto"] + sorted(DELIMS))
    args = ap.parse_args()

    in_path = os.path.abspath(args.input_file)
    out_path = os.path.abspath(args.output_file)
    if os.path.normcase(in_path) == os.path.normcase(out_path):
        fail("output_is_input", "output path is the input path")
    if os.path.exists(out_path):
        fail("output_exists", "output path already exists; choose a new file name")

    text = read_input(in_path)
    if not text.strip():
        fail("no_rows", "input has no content")

    if args.src == "auto":
        src_name = detect(text)
        if src_name is None:
            fail("delimiter_undetected", "no delimiter gives two or more columns; pass --from")
        source = "detected"
    else:
        src_name, source = args.src, "flag"

    rows = parse(text, DELIMS[src_name])
    nonempty = [r for r in rows if r]
    if not nonempty:
        fail("no_rows", "input has no non-empty records")
    modal = collections.Counter(len(r) for r in nonempty).most_common(1)[0][0]
    ragged = [i for i, r in enumerate(rows, 1) if r and len(r) != modal]
    newline_recs = [i for i, r in enumerate(rows, 1) if any("\n" in c or "\r" in c for c in r)]
    cells = sum(len(r) for r in rows)

    buf = io.StringIO(newline="")
    writer = csv.writer(buf, delimiter=DELIMS[args.to], quotechar='"',
                        quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writerows(rows)
    out_text = buf.getvalue()
    equal = parse(out_text, DELIMS[args.to]) == rows

    if not equal:
        status = "verify_failed"
    elif ragged:
        status = "findings"
    else:
        status = "ok"

    written = False
    if equal:
        try:
            with open(out_path, "x", encoding="utf-8", newline="") as fh:
                fh.write(out_text)
            written = True
        except FileExistsError:
            fail("output_exists", "output path already exists; choose a new file name")
        except OSError:
            fail("output_write_failed", "could not create the output file")

    result = {
        "status": status,
        "input_delimiter": src_name,
        "delimiter_source": source,
        "output_delimiter": args.to,
        "records": len(rows),
        "modal_columns": modal,
        "ragged_records": len(ragged),
        "ragged_record_numbers": ragged[:LIST_CAP],
        "embedded_newline_records": len(newline_recs),
        "embedded_newline_record_numbers": newline_recs[:LIST_CAP],
        "cells_compared": cells,
        "values_equal": equal,
        "output_written": written,
    }
    sys.stdout.write(json.dumps(result) + "\n")
    sys.exit(0 if status == "ok" else 1)


if __name__ == "__main__":
    main()
