"""Solve a word search grid from two text files.

Reads a grid file (one row per line, ASCII letters only, all rows the same
length; blank lines are skipped) and a word file (one word per line, ASCII
letters only, no duplicates; blank lines are skipped). For each word, searches
all 8 directions and reports the 1-based start row and column and the
direction of the first match in scan order: rows top to bottom, columns left
to right, directions in the order E, W, S, N, SE, SW, NE, NW. Words with no
match are listed under not_found.

Usage:
    python -I scripts/wordsearch.py <grid-file> <word-file>

Exit codes:
    0  every word found
    1  one or more words not found
    2  usage or input error; a one-line JSON object with key "error" goes to stderr

Read-only: the input files are never modified and no output file is written.
No network, no subprocess, no eval or exec. Input files are capped at 2 MB.
"""

import json
import os
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024

DIRECTIONS = [
    ("E", 0, 1),
    ("W", 0, -1),
    ("S", 1, 0),
    ("N", -1, 0),
    ("SE", 1, 1),
    ("SW", 1, -1),
    ("NE", -1, 1),
    ("NW", -1, -1),
]


class InputError(Exception):
    """Raised for any file or content problem that must exit with code 2."""


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def read_text(path, label):
    """Return the file text decoded as UTF-8 (a leading BOM is tolerated)."""
    try:
        size = os.path.getsize(path)
    except OSError:
        raise InputError("cannot read " + label)
    if size > MAX_INPUT_BYTES:
        raise InputError(label + " exceeds 2 MB")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError("cannot read " + label)
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError(label + " exceeds 2 MB")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError(label + " is not valid UTF-8")


def is_ascii_letters(text):
    return all("A" <= ch <= "Z" for ch in text)


def load_grid(text):
    rows = []
    for line in text.splitlines():
        row = line.strip().upper()
        if row:
            rows.append(row)
    if not rows:
        raise InputError("grid is empty")
    width = len(rows[0])
    for row in rows:
        if len(row) != width:
            raise InputError("ragged grid: every row must have the same length")
        if not is_ascii_letters(row):
            raise InputError("grid contains characters other than A-Z")
    return rows


def load_words(text):
    words = []
    seen = set()
    for line in text.splitlines():
        word = line.strip().upper()
        if not word:
            continue
        if not is_ascii_letters(word):
            raise InputError("word list contains characters other than A-Z")
        if word in seen:
            raise InputError("duplicate word in word list")
        seen.add(word)
        words.append(word)
    if not words:
        raise InputError("word list is empty")
    return words


def find_word(grid, word):
    """Return (row, col, direction) of the first match, 1-based, or None."""
    rows = len(grid)
    cols = len(grid[0])
    length = len(word)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != word[0]:
                continue
            for name, dr, dc in DIRECTIONS:
                end_r = r + dr * (length - 1)
                end_c = c + dc * (length - 1)
                if not (0 <= end_r < rows and 0 <= end_c < cols):
                    continue
                matched = True
                for i in range(1, length):
                    if grid[r + dr * i][c + dc * i] != word[i]:
                        matched = False
                        break
                if matched:
                    return (r + 1, c + 1, name)
    return None


def main(argv):
    if len(argv) != 3:
        fail("usage: wordsearch.py <grid-file> <word-file>")
    try:
        grid = load_grid(read_text(argv[1], "grid file"))
        words = load_words(read_text(argv[2], "word file"))
    except InputError as exc:
        fail(str(exc))

    found = []
    not_found = []
    for word in words:
        hit = find_word(grid, word)
        if hit is None:
            not_found.append(word)
        else:
            found.append({"word": word, "row": hit[0], "col": hit[1], "direction": hit[2]})

    result = {
        "status": "all_found" if not not_found else "some_not_found",
        "rows": len(grid),
        "cols": len(grid[0]),
        "found": found,
        "not_found": not_found,
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0 if not not_found else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
