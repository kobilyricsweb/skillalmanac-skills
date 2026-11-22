"""Build a deduplicated flashcard CSV from 'term :: definition' lines and flag weak cards.

Usage:
    python -I scripts/flashcards.py <input-file> <output-csv>

The input file is read only (UTF-8, optional BOM, at most 2 MB, at most 5000 cards).
The output CSV is created new with header front,back; an existing path is refused.
Duplicates are dropped; flagged cards are kept in the CSV and listed on stdout.

Exit codes: 0 no findings, 1 findings printed (CSV still written), 2 usage or input error.
Errors are one line of JSON on stderr.
"""
import csv
import json
import os
import re
import sys
import unicodedata

MAX_BYTES = 2 * 1024 * 1024
MAX_CARDS = 5000
NEAR_JACCARD = 0.8
FRONT_MAX_WORDS = 12
BACK_MAX_WORDS = 30
DELIM = "::"


def fail(message, **extra):
    payload = {"error": message}
    payload.update(extra)
    sys.stderr.write(json.dumps(payload, sort_keys=True) + "\n")
    sys.exit(2)


def tokens(text):
    """Casefold, NFKC-normalize and split on non-word characters."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    return re.findall(r"\w+", folded)


def jaccard(a, b):
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def parse(text):
    cards = []
    blank = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            blank += 1
            continue
        if line.count(DELIM) != 1:
            fail("malformed_line", line=line_no, reason="expected exactly one '::'")
        front, back = (part.strip() for part in line.split(DELIM))
        if not front or not back:
            fail("malformed_line", line=line_no, reason="empty front or back")
        if not tokens(front) or not tokens(back):
            fail("malformed_line", line=line_no, reason="no letters or digits")
        cards.append((line_no, front, back))
        if len(cards) > MAX_CARDS:
            fail("too_many_cards", max_cards=MAX_CARDS)
    if not cards:
        fail("no_cards")
    return cards, blank


def main(argv):
    if len(argv) != 3:
        fail("usage", expected="flashcards.py <input-file> <output-csv>")
    in_path, out_path = argv[1], argv[2]
    if not os.path.isfile(in_path):
        fail("input_missing")
    if os.path.realpath(in_path) == os.path.realpath(out_path):
        fail("output_equals_input")
    if os.path.lexists(out_path):
        fail("output_exists")
    out_dir = os.path.dirname(os.path.abspath(out_path))
    if not os.path.isdir(out_dir):
        fail("output_dir_missing")
    try:
        with open(in_path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("input_unreadable")
    if len(raw) > MAX_BYTES:
        fail("input_too_large", max_bytes=MAX_BYTES)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8")

    cards, blank = parse(text)

    kept = []      # (line_no, front, back, front_key, front_set, back_key)
    drops = []     # (line_no, code, duplicate_of_line)
    flags = []     # (line_no, code)
    for line_no, front, back in cards:
        f_tokens = tokens(front)
        b_tokens = tokens(back)
        f_key = " ".join(f_tokens)
        b_key = " ".join(b_tokens)
        f_set = set(f_tokens)

        exact = next((k for k in kept if k[3] == f_key and k[5] == b_key), None)
        if exact is not None:
            drops.append((line_no, "DUP_EXACT", exact[0]))
            continue
        near = next((k for k in kept if jaccard(f_set, k[4]) > NEAR_JACCARD), None)
        if near is not None:
            drops.append((line_no, "DUP_NEAR", near[0]))
            continue

        kept.append((line_no, front, back, f_key, f_set, b_key))
        if len(front.split()) > FRONT_MAX_WORDS:
            flags.append((line_no, "FRONT_LONG"))
        if len(back.split()) > BACK_MAX_WORDS:
            flags.append((line_no, "BACK_LONG"))
        if f_key and f" {f_key} " in f" {b_key} ":
            flags.append((line_no, "DEF_CONTAINS_TERM"))

    try:
        with open(out_path, "x", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["front", "back"])
            for _, front, back, _, _, _ in kept:
                writer.writerow([front, back])
    except FileExistsError:
        fail("output_exists")
    except OSError:
        fail("output_unwritable")

    sys.stdout.write(
        "lines=%d blank=%d cards=%d\n" % (len(cards) + blank, blank, len(cards))
    )
    sys.stdout.write(
        "kept=%d dropped=%d flags=%d\n" % (len(kept), len(drops), len(flags))
    )
    for line_no, code, dup_line in drops:
        sys.stdout.write("DROP line=%d code=%s duplicate_of_line=%d\n" % (line_no, code, dup_line))
    for line_no, code in flags:
        sys.stdout.write("FLAG line=%d code=%s\n" % (line_no, code))
    sys.stdout.write("written=%s\n" % out_path)
    findings = len(drops) + len(flags)
    sys.stdout.write("result=%s\n" % ("findings" if findings else "clean"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
