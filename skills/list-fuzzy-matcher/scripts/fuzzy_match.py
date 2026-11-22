"""Match items in a left CSV list to the closest items in a right CSV list.

Each CSV must have a header row. The item column is chosen by header name or
0-based index (default: first column). Items are normalized (casefolded,
punctuation turned into spaces, whitespace collapsed), then every left item is
scored against each distinct right item with difflib.SequenceMatcher.ratio().

Status per left item (thresholds are working values, see the constants):
  unmatched  best score below --no-match-below
  tie        two distinct right items share the best score (4 decimal places)
  weak       best score below --flag-below
  ok         anything else

Writes one row per left item to a NEW CSV file and prints one JSON summary line
to stdout. Exit 0 when every item is ok, 1 when any item is flagged, 2 on usage
or input error. Inputs are only read. The output path must not exist; it is
created with mode "x" and is never overwritten.
"""

import argparse
import csv
import difflib
import io
import json
import os
import sys

MAX_BYTES = 2 * 1024 * 1024  # input cap per file
MAX_ROWS = 1000  # data rows per side (working value)
FLAG_BELOW = 0.85  # working value
NO_MATCH_BELOW = 0.60  # working value
SCORE_PLACES = 4

OUTPUT_HEADER = [
    "left_item",
    "status",
    "best_match",
    "best_score",
    "runner_up_match",
    "runner_up_score",
]


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage: " + message)


def fail(message):
    sys.stderr.write(json.dumps({"ok": False, "error": message}) + "\n")
    sys.exit(2)


def normalize(text):
    mapped = "".join(ch if ch.isalnum() else " " for ch in text.casefold())
    return " ".join(mapped.split())


def read_items(path, column, label):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            fail(label + " input is larger than 2 MB")
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        fail("cannot read " + label + " input: " + (exc.strerror or "unknown error"))
    if len(raw) > MAX_BYTES:
        fail(label + " input is larger than 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail(label + " input is not valid UTF-8")
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        fail("malformed " + label + " CSV: " + str(exc))
    if not rows:
        fail(label + " input has no header row")
    header = [cell.strip() for cell in rows[0]]
    if column is None:
        index = 0
    elif column.isdigit():
        index = int(column)
    elif column in header:
        index = header.index(column)
    else:
        fail(label + " column not found in header: " + column)
    if index >= len(header):
        fail(label + " column index is outside the header")
    data = rows[1:]
    if len(data) > MAX_ROWS:
        fail(label + " input has more than " + str(MAX_ROWS) + " data rows")
    items = []
    skipped = 0
    for row in data:
        original = row[index].strip() if index < len(row) else ""
        key = normalize(original)
        if not key:
            skipped += 1
            continue
        items.append((original, key))
    if not items:
        fail(label + " input has no non-blank items")
    return items, skipped


def build_candidates(right_items):
    distinct = {}
    for original, key in right_items:
        if key not in distinct:
            distinct[key] = original
    candidates = []
    for key, original in distinct.items():
        matcher = difflib.SequenceMatcher(None, autojunk=False)
        matcher.set_seq2(key)
        candidates.append((key, original, matcher))
    return candidates


def match_rows(left_items, right_items, flag_below, no_match_below):
    candidates = build_candidates(right_items)
    rows = []
    counts = {"ok": 0, "weak": 0, "tie": 0, "unmatched": 0}
    for original, key in left_items:
        scored = []
        for rkey, roriginal, matcher in candidates:
            matcher.set_seq1(key)
            scored.append((round(matcher.ratio(), SCORE_PLACES), rkey, roriginal))
        scored.sort(key=lambda t: (-t[0], t[1]))
        best_score, _, best_text = scored[0]
        runner = scored[1] if len(scored) > 1 else None
        if best_score < no_match_below:
            status = "unmatched"
        elif runner is not None and runner[0] == best_score:
            status = "tie"
        elif best_score < flag_below:
            status = "weak"
        else:
            status = "ok"
        counts[status] += 1
        rows.append([
            original,
            status,
            best_text,
            "%.4f" % best_score,
            runner[2] if runner else "",
            ("%.4f" % runner[0]) if runner else "",
        ])
    return rows, counts


def main(argv=None):
    parser = _Parser(
        prog="fuzzy_match.py",
        description="Match left CSV items to the closest right CSV items.",
    )
    parser.add_argument("--left", required=True, help="left CSV file with a header row")
    parser.add_argument("--right", required=True, help="right CSV file with a header row")
    parser.add_argument("--output", required=True, help="NEW output CSV path; must not exist")
    parser.add_argument("--left-column", default=None, help="header name or 0-based index; default 0")
    parser.add_argument("--right-column", default=None, help="header name or 0-based index; default 0")
    parser.add_argument("--flag-below", type=float, default=FLAG_BELOW)
    parser.add_argument("--no-match-below", type=float, default=NO_MATCH_BELOW)
    args = parser.parse_args(argv)

    if not (0 < args.no_match_below < args.flag_below <= 1):
        fail("need 0 < no-match-below < flag-below <= 1")

    out_real = os.path.realpath(args.output)
    for path in (args.left, args.right):
        if os.path.realpath(path) == out_real:
            fail("output path must not be an input path")
    if os.path.lexists(args.output):
        fail("output already exists; refusing to overwrite")

    left_items, left_skipped = read_items(args.left, args.left_column, "left")
    right_items, right_skipped = read_items(args.right, args.right_column, "right")
    rows, counts = match_rows(left_items, right_items, args.flag_below, args.no_match_below)

    try:
        with open(args.output, "x", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(OUTPUT_HEADER)
            writer.writerows(rows)
    except FileExistsError:
        fail("output already exists; refusing to overwrite")
    except OSError as exc:
        fail("cannot write output: " + (exc.strerror or "unknown error"))

    flagged = counts["weak"] + counts["tie"] + counts["unmatched"] > 0
    code = 1 if flagged else 0
    summary = {
        "exit": code,
        "left_items": len(left_items),
        "right_items": len(right_items),
        "skipped_blank": {"left": left_skipped, "right": right_skipped},
        "status_counts": counts,
    }
    print(json.dumps(summary))
    sys.exit(code)


if __name__ == "__main__":
    main()
