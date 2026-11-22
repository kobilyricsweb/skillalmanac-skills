"""Find exact and near-duplicate paragraphs across .txt and .md files in one folder.

Read-only: reads files under the input folder and writes nothing.
Stdlib only. No network, no subprocess, no eval or exec.

Usage:
    python -I scripts/dup_passages.py <input-folder>

Output: JSON report on stdout (see SKILL.md, "Script contract").
Errors: one-line JSON on stderr, {"error": <code>, "message": <text>}.

Exit codes:
    0  scan finished, no duplicate groups
    1  scan finished, one or more duplicate groups reported
    2  usage or input error
"""

import json
import os
import re
import sys
from collections import defaultdict

MAX_TOTAL_BYTES = 2 * 1024 * 1024  # total bytes read across all files
MIN_WORDS = 8  # paragraphs with fewer words are skipped (working value)
SHINGLE_SIZE = 8  # words per shingle (working value)
THRESHOLD_NUM = 3  # Jaccard threshold 0.6 as integer ratio 3/5 (working value)
THRESHOLD_DEN = 5
EXTENSIONS = (".txt", ".md")
WORD_RE = re.compile(r"\w+")


class InputError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def fail(code, message):
    sys.stderr.write(json.dumps({"error": code, "message": message}) + "\n")
    return 2


def collect_files(folder):
    """Return sorted (relative_path, full_path) pairs for .txt and .md files."""
    found = []
    for root, dirs, names in os.walk(folder, followlinks=False):
        dirs.sort()
        for name in sorted(names):
            if not name.lower().endswith(EXTENSIONS):
                continue
            full = os.path.join(root, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            found.append((rel, full))
    found.sort()
    return found


def read_files(pairs):
    """Read every file as UTF-8 (BOM allowed), enforcing the total byte cap."""
    budget = MAX_TOTAL_BYTES
    docs = []
    for rel, full in pairs:
        try:
            with open(full, "rb") as fh:
                raw = fh.read(budget + 1)
        except OSError:
            raise InputError("read_error", "cannot read file: " + rel)
        if len(raw) > budget:
            raise InputError("input_too_large", "inputs exceed 2 MB in total")
        budget -= len(raw)
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise InputError("invalid_utf8", "file is not valid UTF-8: " + rel)
        docs.append((rel, text))
    return docs


def paragraphs(text):
    """Return (first_line_number, joined_text) for each blank-line separated block."""
    out = []
    block = []
    start = 0
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped:
            if not block:
                start = number
            block.append(stripped)
        elif block:
            out.append((start, " ".join(block)))
            block = []
    if block:
        out.append((start, " ".join(block)))
    return out


def find_root(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def analyse(docs):
    occurrences = {}  # normalized key -> list of (file, line)
    words_of = {}  # normalized key -> word list
    compared = 0
    skipped = 0
    for rel, text in docs:
        for line, joined in paragraphs(text):
            key = " ".join(joined.split()).casefold()
            words = WORD_RE.findall(key)
            if len(words) < MIN_WORDS:
                skipped += 1
                continue
            compared += 1
            if key not in occurrences:
                occurrences[key] = []
                words_of[key] = words
            occurrences[key].append((rel, line))

    keys = list(occurrences)
    shingles = []
    for key in keys:
        w = words_of[key]
        shingles.append({" ".join(w[i:i + SHINGLE_SIZE]) for i in range(len(w) - SHINGLE_SIZE + 1)})

    index = defaultdict(list)
    for uid, sh in enumerate(shingles):
        for s in sh:
            index[s].append(uid)

    parent = list(range(len(keys)))
    for i, sh in enumerate(shingles):
        counts = defaultdict(int)
        for s in sh:
            for j in index[s]:
                if j > i:
                    counts[j] += 1
        for j, inter in counts.items():
            union = len(sh) + len(shingles[j]) - inter
            # Jaccard >= 0.6 without floating point: inter / union >= 3 / 5
            if inter * THRESHOLD_DEN >= union * THRESHOLD_NUM:
                ri = find_root(parent, i)
                rj = find_root(parent, j)
                if ri != rj:
                    parent[rj] = ri

    components = defaultdict(list)
    for uid in range(len(keys)):
        components[find_root(parent, uid)].append(uid)

    groups = []
    for members in components.values():
        occ = []
        for uid in members:
            occ.extend(occurrences[keys[uid]])
        if len(occ) < 2:
            continue
        occ.sort()
        group_type = "exact" if len(members) == 1 else "near"
        groups.append((occ[0], group_type, occ))
    groups.sort(key=lambda g: g[0])

    out_groups = []
    for n, (_, group_type, occ) in enumerate(groups, start=1):
        out_groups.append({
            "group_id": "G%d" % n,
            "type": group_type,
            "occurrences": [{"file": f, "line": ln} for f, ln in occ],
        })
    exact_n = sum(1 for g in out_groups if g["type"] == "exact")
    near_n = len(out_groups) - exact_n
    return {
        "settings": {
            "min_words": MIN_WORDS,
            "shingle_size": SHINGLE_SIZE,
            "jaccard_threshold": 0.6,
        },
        "files_scanned": len(docs),
        "paragraphs_compared": compared,
        "paragraphs_skipped_short": skipped,
        "groups": out_groups,
        "counts": {
            "groups": len(out_groups),
            "exact_groups": exact_n,
            "near_groups": near_n,
            "occurrences": sum(len(g["occurrences"]) for g in out_groups),
        },
    }


def main(argv):
    if len(argv) != 2:
        return fail("usage", "expected exactly one argument: <input-folder>")
    folder = argv[1]
    if not os.path.isdir(folder):
        return fail("not_directory", "argument is not a folder")
    try:
        pairs = collect_files(folder)
        if not pairs:
            return fail("no_files", "no .txt or .md files found in the folder")
        docs = read_files(pairs)
    except InputError as exc:
        return fail(exc.code, exc.message)
    result = analyse(docs)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 1 if result["groups"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
