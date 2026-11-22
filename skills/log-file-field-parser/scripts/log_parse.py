"""Parse a text or JSON-lines log file into timestamp, level and message fields.

Reads one input file read-only, prints a JSON report to stdout, and optionally
writes a CSV of distinct masked messages to a new file. Python 3.9+ stdlib only.

Usage:
    python -I log_parse.py <input-file> [--csv <output-csv>]

Exit codes: 0 ok, 1 findings (ERROR or CRITICAL lines present), 2 usage or input error.
Errors are printed to stderr as one line of JSON: {"error": "...", "code": "..."}.
"""
import argparse
import csv
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
TOP_N = 10
TIMELINE_CAP = 50
UNPARSED_CAP = 50
UNPARSED_TEXT_CHARS = 200

ISO_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)
SYSLOG_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) {1,2}\d{1,2} \d{2}:\d{2}:\d{2}"
)
LEVEL_RE = re.compile(r"\b(DEBUG|INFO|WARNING|WARN|ERROR|ERR|CRITICAL|FATAL)\b")
LEVEL_MAP = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARNING",
    "WARN": "WARNING",
    "ERROR": "ERROR",
    "ERR": "ERROR",
    "CRITICAL": "CRITICAL",
    "FATAL": "CRITICAL",
}
LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
JSON_TIME_KEYS = ("timestamp", "@timestamp", "time", "ts", "date")
JSON_LEVEL_KEYS = ("level", "severity", "lvl")
JSON_MSG_KEYS = ("message", "msg")
DIGITS_RE = re.compile(r"\d+")
STRIP_CHARS = " \t[]():|-<>,;"
CSV_HEADER = ["message", "count", "first_line", "first_timestamp", "last_timestamp"]


def fail(code, message):
    sys.stderr.write(json.dumps({"error": message, "code": code}) + "\n")
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("USAGE", message)


def check_output(csv_path, input_path):
    out = os.path.abspath(csv_path)
    if os.path.exists(out):
        fail("OUTPUT_EXISTS", "output path already exists; choose a new file name")
    out_dir = os.path.dirname(out)
    if not os.path.isdir(out_dir):
        fail("OUTPUT_DIR_MISSING", "output folder does not exist")
    in_dir = os.path.dirname(os.path.abspath(input_path))
    if os.path.normcase(out_dir) == os.path.normcase(in_dir):
        fail("OUTPUT_IN_INPUT_DIR", "CSV must not be written into the input file's folder")


def read_input(path):
    if not os.path.exists(path):
        fail("FILE_NOT_FOUND", "input file not found")
    if not os.path.isfile(path):
        fail("NOT_A_FILE", "input path is not a regular file")
    try:
        size = os.path.getsize(path)
        if size > MAX_BYTES:
            fail("TOO_LARGE", "input is %d bytes; the limit is %d" % (size, MAX_BYTES))
        with open(path, "rb") as fh:
            data = fh.read(MAX_BYTES + 1)
    except OSError:
        fail("FILE_UNREADABLE", "input file could not be read")
    if len(data) > MAX_BYTES:
        fail("TOO_LARGE", "input grew past the %d byte limit while reading" % MAX_BYTES)
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("BAD_ENCODING", "input is not valid UTF-8")


def first_value(obj, keys):
    for key in keys:
        if key in obj and obj[key] is not None:
            return str(obj[key])
    return None


def parse_json_obj(obj):
    ts = None
    ts_raw = first_value(obj, JSON_TIME_KEYS)
    if ts_raw:
        found = ISO_RE.search(ts_raw) or SYSLOG_RE.search(ts_raw)
        ts = found.group(0) if found else None
    level_raw = first_value(obj, JSON_LEVEL_KEYS)
    level = LEVEL_MAP.get(level_raw.strip().upper()) if level_raw else None
    if ts is None:
        return None, None, None, "NO_TIMESTAMP"
    if level is None:
        return None, None, None, "NO_LEVEL"
    msg = (first_value(obj, JSON_MSG_KEYS) or "").strip()
    return ts, level, msg or "(empty)", None


def parse_text(line):
    found = ISO_RE.search(line) or SYSLOG_RE.search(line)
    if not found:
        return None, None, None, "NO_TIMESTAMP"
    ts = found.group(0)
    rest = line[: found.start()] + " " + line[found.end():]
    level_found = LEVEL_RE.search(rest)
    if not level_found:
        return None, None, None, "NO_LEVEL"
    level = LEVEL_MAP[level_found.group(1)]
    msg = rest[: level_found.start()] + " " + rest[level_found.end():]
    msg = " ".join(msg.split()).strip(STRIP_CHARS)
    return ts, level, msg or "(empty)", None


def parse_line(raw):
    """Return (timestamp, level, message, reason). reason is None when parsed."""
    stripped = raw.strip()
    if stripped.startswith("{"):
        try:
            obj = json.loads(stripped)
        except (ValueError, RecursionError):
            return None, None, None, "BAD_JSON"
        if isinstance(obj, dict):
            return parse_json_obj(obj)
    return parse_text(stripped)


def analyze(text):
    counts = {level: 0 for level in LEVELS}
    distinct = {}
    unparsed = []
    unparsed_count = 0
    total = 0
    parsed = 0
    for lineno, raw in enumerate(text.split("\n"), start=1):
        raw = raw.rstrip("\r")
        if not raw.strip():
            continue
        total += 1
        ts, level, msg, reason = parse_line(raw)
        if reason:
            unparsed_count += 1
            if len(unparsed) < UNPARSED_CAP:
                unparsed.append({
                    "line": lineno,
                    "reason": reason,
                    "text": raw.strip()[:UNPARSED_TEXT_CHARS],
                })
            continue
        parsed += 1
        counts[level] += 1
        key = DIGITS_RE.sub("#", msg)
        rec = distinct.get(key)
        if rec is None:
            rec = {
                "message": key,
                "count": 0,
                "first_line": lineno,
                "first_timestamp": ts,
                "last_timestamp": ts,
            }
            distinct[key] = rec
        rec["count"] += 1
        rec["last_timestamp"] = ts
    rows = list(distinct.values())  # insertion order is first-occurrence order
    top = sorted(rows, key=lambda r: (-r["count"], r["first_line"]))[:TOP_N]
    report = {
        "input_lines": total,
        "parsed_lines": parsed,
        "unparsed_lines": unparsed_count,
        "levels": counts,
        "unparsed": unparsed,
        "distinct_messages": len(rows),
        "top_messages": [
            {"rank": i, "count": r["count"], "message": r["message"]}
            for i, r in enumerate(top, start=1)
        ],
        "timeline_total": len(rows),
        "timeline": [
            {
                "first_line": r["first_line"],
                "first_timestamp": r["first_timestamp"],
                "last_timestamp": r["last_timestamp"],
                "count": r["count"],
                "message": r["message"],
            }
            for r in rows[:TIMELINE_CAP]
        ],
        "csv_path": None,
        "csv_rows": 0,
    }
    return report, rows


def write_csv(path, rows):
    try:
        with open(path, "x", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(CSV_HEADER)
            for r in rows:
                writer.writerow([
                    r["message"],
                    r["count"],
                    r["first_line"],
                    r["first_timestamp"],
                    r["last_timestamp"],
                ])
    except FileExistsError:
        fail("OUTPUT_EXISTS", "output path already exists; choose a new file name")
    except OSError:
        fail("OUTPUT_WRITE_FAILED", "output file could not be written")
    return len(rows)


def main(argv=None):
    parser = _Parser(
        prog="log_parse.py",
        description="Parse a text or JSON-lines log into timestamp, level and message.",
    )
    parser.add_argument("input_file")
    parser.add_argument("--csv", dest="csv_path", default=None)
    args = parser.parse_args(argv)

    if args.csv_path:
        check_output(args.csv_path, args.input_file)
    text = read_input(args.input_file)
    report, rows = analyze(text)
    if report["input_lines"] == 0:
        fail("EMPTY_INPUT", "input has no non-blank lines")
    if args.csv_path:
        report["csv_rows"] = write_csv(args.csv_path, rows)
        report["csv_path"] = os.path.abspath(args.csv_path)
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    findings = report["levels"]["ERROR"] + report["levels"]["CRITICAL"]
    return 1 if findings > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
