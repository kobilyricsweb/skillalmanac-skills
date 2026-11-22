"""Screens username candidates for length, character set, edge separators,
digit runs, confusable characters, repeated characters and near-duplicate pairs.

Usage:
    python -I scripts/username_screen.py <input-file>

Input: UTF-8 text, one candidate per line. Blank lines and lines starting with
'#' are skipped. The input file is only read, never written. No network,
no subprocess, no eval or exec.

Exit codes: 0 = no candidate has findings, 1 = at least one finding,
2 = usage or input error (a one-line JSON error goes to stderr).
"""
import json
import os
import re
import sys

VERSION = "0.1.0"
MAX_BYTES = 2 * 1024 * 1024
MAX_CANDIDATES = 2000
MIN_LEN = 3
MAX_LEN = 20
SEPARATORS = "_.-"
ALLOWED = re.compile(r"[A-Za-z0-9_.\-]+")
DIGIT_RUN = re.compile(r"[0-9]{4,}")
REPEAT = re.compile(r"(.)\1\1")
ORDER = ["LEN_SHORT", "LEN_LONG", "CHARSET", "EDGE_SEP", "DIGIT_RUN",
         "CONFUSABLE", "REPEAT", "DUPLICATE", "NEAR_DUP"]


class InputError(Exception):
    pass


def read_candidates(path):
    try:
        size = os.path.getsize(path)
    except OSError:
        raise InputError("input file not found or not readable")
    if size > MAX_BYTES:
        raise InputError("input file is larger than 2 MB")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_BYTES + 1)
    except OSError:
        raise InputError("input file not readable")
    if len(raw) > MAX_BYTES:
        raise InputError("input file is larger than 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("input is not valid UTF-8")
    rows = []
    for line_no, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        rows.append((line_no, s))
    if not rows:
        raise InputError("no candidates in input")
    if len(rows) > MAX_CANDIDATES:
        raise InputError("more than 2000 candidates in one file")
    return rows


def own_findings(s):
    codes = set()
    low = s.lower()
    if len(s) < MIN_LEN:
        codes.add("LEN_SHORT")
    if len(s) > MAX_LEN:
        codes.add("LEN_LONG")
    if not ALLOWED.fullmatch(s):
        codes.add("CHARSET")
    if s[0] in SEPARATORS or s[-1] in SEPARATORS:
        codes.add("EDGE_SEP")
    if DIGIT_RUN.search(s):
        codes.add("DIGIT_RUN")
    if len(set(s) & {"1", "l", "I"}) >= 2 or len(set(low) & {"0", "o"}) >= 2 or "rn" in low:
        codes.add("CONFUSABLE")
    if REPEAT.search(low):
        codes.add("REPEAT")
    return codes


def edit_one(a, b):
    """True when a and b differ by exactly one edit (substitution, insertion or deletion)."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    if len(a) == len(b):
        return a[i + 1:] == b[i + 1:]
    return a[i:] == b[i + 1:]


def pair_findings(rows):
    extra = {}
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a = rows[i][1].lower()
            b = rows[j][1].lower()
            if a == b:
                code = "DUPLICATE"
            elif edit_one(a, b):
                code = "NEAR_DUP"
            else:
                continue
            extra.setdefault(i, set()).add(code)
            extra.setdefault(j, set()).add(code)
    return extra


def display(s):
    return "".join(ch if ch.isprintable() else "?" for ch in s)


def fail(message):
    sys.stderr.write(json.dumps({"error": message, "exit": 2}) + "\n")
    return 2


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: python -I scripts/username_screen.py <input-file>\n")
        return 2
    try:
        rows = read_candidates(argv[1])
    except InputError as exc:
        return fail(str(exc))
    extra = pair_findings(rows)
    results = []
    for idx, (line_no, s) in enumerate(rows):
        codes = own_findings(s) | extra.get(idx, set())
        ordered = [c for c in ORDER if c in codes]
        results.append((len(ordered), line_no, s, ordered))
    results.sort(key=lambda r: (r[0], r[1]))
    width = max([len(display(r[2])) for r in results] + [9])
    out = [f"username-candidate-screen {VERSION} (length {MIN_LEN}-{MAX_LEN})"]
    out.append(f"{'rank':<6}{'line':<7}{'candidate':<{width}}  {'length':<8}{'findings':<10}codes")
    for rank, (count, line_no, s, codes) in enumerate(results, 1):
        out.append(f"{rank:<6}{line_no:<7}{display(s):<{width}}  {len(s):<8}{count:<10}{','.join(codes) or 'none'}")
    flagged = sum(1 for r in results if r[0])
    out.append(f"candidates={len(results)} flagged={flagged} clean={len(results) - flagged}")
    print("\n".join(out))
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
