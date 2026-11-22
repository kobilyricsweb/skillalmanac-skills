"""Split a CSV file into numbered part files by data-row count.

Every part repeats the header row. Records are parsed with the csv module, so
quoted multiline fields stay inside one record. Part files are created with
exclusive mode ("x"): if any part path already exists, the script exits 2 before
writing anything. The input file is only read and is never written to.

Usage:
    python -I csv_split.py <input-file> --rows <N> --out-dir <dir> [--prefix <name>]

Arguments:
    input-file      CSV file, 1 byte to 2 MB, UTF-8 (a leading BOM is accepted).
    --rows N        Data rows per part, integer 1 to 1000000.
    --out-dir DIR   Existing directory that receives the part files.
    --prefix NAME   Part file prefix, 1 to 64 characters from [A-Za-z0-9_-].
                    Default: part. Files are named <prefix>_001.csv, _002.csv, ...

Output: one JSON object on stdout for exit codes 0 and 1. Errors are one JSON
object on stderr with exit code 2.

Exit codes:
    0  parts written and verified; no ragged rows
    1  parts written and verified, but ragged rows were found, or verification failed
    2  usage or input error; nothing was written
"""

import argparse
import csv
import io
import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ROWS_PER_PART = 1000000
MAX_REPORTED_RAGGED = 50
PREFIX_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage: " + message)


def fail(message):
    sys.stderr.write(json.dumps({"status": "error", "message": message}) + "\n")
    sys.exit(2)


def parse_args(argv):
    parser = _Parser(prog="csv_split.py", add_help=True)
    parser.add_argument("input_file")
    parser.add_argument("--rows", required=True, type=int)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--prefix", default="part")
    args = parser.parse_args(argv)
    if not (1 <= args.rows <= MAX_ROWS_PER_PART):
        fail("--rows must be an integer from 1 to %d" % MAX_ROWS_PER_PART)
    if not PREFIX_PATTERN.match(args.prefix):
        fail("--prefix must be 1 to 64 characters from A-Z, a-z, 0-9, underscore, hyphen")
    return args


def read_records(path):
    """Return every CSV record in the file, header included."""
    if not os.path.isfile(path):
        fail("input file not found or not a regular file")
    size = os.path.getsize(path)
    if size == 0:
        fail("input file is empty")
    if size > MAX_INPUT_BYTES:
        fail("input file exceeds the 2 MB cap")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("input file could not be read")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input file is not valid UTF-8")
    try:
        return list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as exc:
        fail("malformed CSV: " + str(exc))


def read_back(path):
    """Parse a written part file the same way the input was parsed."""
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.reader(fh))


def same_file(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def main(argv):
    args = parse_args(argv)
    records = read_records(args.input_file)
    if not records:
        fail("input file has no records")
    header = records[0]
    data = records[1:]
    if not header:
        fail("header row is empty")
    if not data:
        fail("no data rows to split (header only)")

    if not os.path.isdir(args.out_dir):
        fail("--out-dir does not exist or is not a directory")

    chunks = [data[i:i + args.rows] for i in range(0, len(data), args.rows)]
    width = max(3, len(str(len(chunks))))
    names = [args.prefix + "_" + str(i + 1).zfill(width) + ".csv" for i in range(len(chunks))]
    paths = [os.path.join(args.out_dir, name) for name in names]

    for name, path in zip(names, paths):
        if same_file(path, args.input_file):
            fail("a part path would overwrite the input file")
        if os.path.lexists(path):
            fail("part file already exists, nothing written: " + name)

    created = []
    try:
        for path, chunk in zip(paths, chunks):
            with open(path, "x", encoding="utf-8", newline="") as fh:
                created.append(path)
                writer = csv.writer(fh, lineterminator="\n")
                writer.writerow(header)
                writer.writerows(chunk)
    except (OSError, csv.Error):
        for path in created:
            try:
                os.remove(path)
            except OSError:
                pass
        fail("writing a part file failed; files created by this run were removed")

    verified = True
    parts = []
    total = 0
    for name, path, chunk in zip(names, paths, chunks):
        try:
            back = read_back(path)
        except (OSError, csv.Error, UnicodeDecodeError):
            back = None
        if back != [header] + chunk:
            verified = False
        parts.append({"file": name, "data_rows": len(chunk)})
        total += len(chunk)
    if total != len(data):
        verified = False

    ragged = [i for i, rec in enumerate(data, start=1) if len(rec) != len(header)]

    if not verified:
        status, code = "verification_failed", 1
    elif ragged:
        status, code = "ragged_rows", 1
    else:
        status, code = "ok", 0

    report = {
        "status": status,
        "input_data_rows": len(data),
        "rows_per_part": args.rows,
        "header_columns": len(header),
        "parts": parts,
        "parts_data_rows_total": total,
        "verified": verified,
        "ragged_row_count": len(ragged),
        "ragged_rows": ragged[:MAX_REPORTED_RAGGED],
    }
    sys.stdout.write(json.dumps(report) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
