"""Count keyword and phrase matches and density in plain page text.

Usage:
    python -I scripts/keyword_density.py <input-file> <keyword-file>

Arguments:
    input-file    UTF-8 plain text of one page (no HTML). Read only.
    keyword-file  UTF-8, one keyword or phrase per line. Blank lines are skipped.

Output: one JSON object on stdout (keys listed in SKILL.md).
Exit codes: 0 every keyword matched; 1 at least one keyword is ABSENT;
2 usage or input error, printed as one-line JSON on stderr.
No network, no subprocess, no files written. Density values are descriptive only.
"""

import json
import re
import sys
from collections import Counter

MAX_BYTES = 2 * 1024 * 1024
MAX_KEYWORDS = 100
MAX_PHRASE_WORDS = 10
TOP_N = 15
TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)*")
STOPWORDS = frozenset(
    "a about also an and are as at be been being but by can did do does for from "
    "had has have he her his i if in into is it its just more most no not of on or "
    "our she so than that the their them then there these they this to up us very "
    "was we were what when which who will with you your".split()
)
NOTE = "Density is descriptive only. No density value is a ranking target."


def fail(code, line=None):
    err = {"error": code}
    if line is not None:
        err["line"] = line
    sys.stderr.write(json.dumps(err) + "\n")
    sys.exit(2)


def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_BYTES + 1)
    except OSError:
        fail("file_unreadable")
    if len(raw) > MAX_BYTES:
        fail("file_too_large")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("not_utf8")


def load_keywords(path):
    keywords = []
    seen = set()
    for number, line in enumerate(read_text(path).splitlines(), start=1):
        label = line.strip()
        if not label:
            continue
        tokens = tuple(TOKEN_RE.findall(label.lower()))
        if not tokens:
            fail("keyword_without_words", number)
        if len(tokens) > MAX_PHRASE_WORDS:
            fail("phrase_too_long", number)
        if tokens in seen:
            fail("duplicate_keyword", number)
        seen.add(tokens)
        keywords.append((label, tokens))
        if len(keywords) > MAX_KEYWORDS:
            fail("too_many_keywords")
    if not keywords:
        fail("no_keywords")
    return keywords


def count_matches(tokens, keywords):
    """Overlapping, whole-word, case-insensitive counts for each keyword tuple."""
    wanted_by_size = {}
    for _, toks in keywords:
        wanted_by_size.setdefault(len(toks), set()).add(toks)
    counts = Counter()
    for size, wanted in wanted_by_size.items():
        for i in range(len(tokens) - size + 1):
            window = tuple(tokens[i:i + size])
            if window in wanted:
                counts[window] += 1
    return counts


def pct(matches, words, total):
    return round(matches * words * 100.0 / total, 2)


def ranked(counter, total, keep):
    items = sorted(counter.items(), key=lambda gc: (-gc[1], " ".join(gc[0])))
    out = []
    for gram, count in items:
        if not keep(gram):
            continue
        out.append({
            "term": " ".join(gram),
            "matches": count,
            "density_pct": pct(count, len(gram), total),
        })
        if len(out) == TOP_N:
            break
    return out


def main(argv):
    if len(argv) != 3:
        fail("usage")
    tokens = TOKEN_RE.findall(read_text(argv[1]).lower())
    total = len(tokens)
    if total == 0:
        fail("no_words")
    keywords = load_keywords(argv[2])
    counts = count_matches(tokens, keywords)

    rows = []
    absent = []
    for label, toks in keywords:
        matches = counts.get(toks, 0)
        status = "FOUND" if matches else "ABSENT"
        if not matches:
            absent.append(label)
        rows.append({
            "keyword": label,
            "words": len(toks),
            "matches": matches,
            "density_pct": pct(matches, len(toks), total),
            "status": status,
        })

    unigrams = Counter((t,) for t in tokens)
    bigrams = Counter(zip(tokens, tokens[1:]))
    result = {
        "total_words": total,
        "keywords": rows,
        "absent_keywords": absent,
        "top_terms": ranked(
            unigrams, total,
            lambda g: g[0] not in STOPWORDS and len(g[0]) >= 2),
        "top_bigrams": ranked(
            bigrams, total,
            lambda g: g[0] not in STOPWORDS and g[1] not in STOPWORDS),
        "note": NOTE,
    }
    print(json.dumps(result, indent=2))
    return 1 if absent else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
