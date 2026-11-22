"""Scan a plain-text draft for stock filler phrases, hedges and repeated sentence openers.

Usage:
    python -I phrase_scan.py <input-file>

Reads one UTF-8 text file (max 2 MB), never writes files, never opens the
network, and never labels the text as written by any person or tool. Output is
a JSON object on stdout. Errors are a one-line JSON object on stderr.

Exit codes:
    0  no findings
    1  one or more findings (phrase hits or repeated openers)
    2  usage or input error (see the error codes in SKILL.md)
"""

import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
OPENER_WORDS = 2
OPENER_MIN_COUNT = 3

# Working list (not a published spec). Each entry: (phrase, category).
PHRASES = [
    ("in today's fast-paced world", "filler"),
    ("in today's digital age", "filler"),
    ("delve into", "filler"),
    ("dive deep into", "filler"),
    ("let's dive in", "filler"),
    ("without further ado", "filler"),
    ("it's important to note", "filler"),
    ("it is important to note", "filler"),
    ("it's worth noting", "filler"),
    ("it is worth noting", "filler"),
    ("it should be noted", "filler"),
    ("it goes without saying", "filler"),
    ("needless to say", "filler"),
    ("in conclusion", "filler"),
    ("at the end of the day", "filler"),
    ("last but not least", "filler"),
    ("first and foremost", "filler"),
    ("in order to", "filler"),
    ("due to the fact that", "filler"),
    ("at this point in time", "filler"),
    ("when it comes to", "filler"),
    ("a testament to", "filler"),
    ("plays a crucial role", "filler"),
    ("plays a vital role", "filler"),
    ("a myriad of", "filler"),
    ("a plethora of", "filler"),
    ("navigate the landscape", "filler"),
    ("in the realm of", "filler"),
    ("unlock the power of", "filler"),
    ("game-changer", "filler"),
    ("seamless", "filler"),
    ("robust", "filler"),
    ("leverage", "filler"),
    ("tapestry", "filler"),
    ("moving forward", "filler"),
    ("that being said", "filler"),
    ("with that said", "filler"),
    ("in a nutshell", "filler"),
    ("the bottom line is", "filler"),
    ("more often than not", "filler"),
    ("the fact of the matter is", "filler"),
    ("it could be argued", "hedge"),
    ("arguably", "hedge"),
    ("it seems like", "hedge"),
    ("may potentially", "hedge"),
    ("could potentially", "hedge"),
    ("might possibly", "hedge"),
    ("generally speaking", "hedge"),
    ("to some extent", "hedge"),
    ("in many ways", "hedge"),
]

WORD_RE = re.compile(r"[A-Za-z0-9']+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def fail(code, message, exit_code=2):
    sys.stderr.write(json.dumps({"error": message, "code": code}) + "\n")
    sys.exit(exit_code)


def read_input(path):
    if not os.path.exists(path):
        fail("file_missing", "input file does not exist")
    if not os.path.isfile(path):
        fail("not_a_file", "input path is not a regular file")
    if os.path.getsize(path) > MAX_BYTES:
        fail("too_large", "input file is larger than 2 MB")
    with open(path, "rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        fail("too_large", "input file is larger than 2 MB")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8", "input file is not valid UTF-8")


def phrase_pattern(phrase):
    parts = [re.escape(part) for part in phrase.split(" ")]
    body = r"\s+".join(parts)
    return re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])", re.IGNORECASE)


def scan(text):
    text = text.replace("’", "'").replace("‘", "'")
    lines = text.splitlines()
    total_words = len(WORD_RE.findall(text))
    if total_words == 0:
        fail("empty_input", "input file contains no words")

    phrase_hits = []
    for index, (phrase, category) in enumerate(PHRASES):
        pattern = phrase_pattern(phrase)
        line_numbers = []
        count = 0
        for line_no, line in enumerate(lines, start=1):
            found = len(pattern.findall(line))
            if found:
                count += found
                line_numbers.append(line_no)
        if count:
            phrase_hits.append({
                "phrase": phrase,
                "category": category,
                "count": count,
                "lines": line_numbers,
                "_order": index,
            })
    phrase_hits.sort(key=lambda h: (-h["count"], h["_order"]))
    for hit in phrase_hits:
        del hit["_order"]

    openers = {}
    for line_no, line in enumerate(lines, start=1):
        for sentence in SENTENCE_SPLIT_RE.split(line.strip()):
            words = [w.lower() for w in WORD_RE.findall(sentence)]
            if len(words) < OPENER_WORDS:
                continue
            key = " ".join(words[:OPENER_WORDS])
            entry = openers.setdefault(key, {"count": 0, "lines": []})
            entry["count"] += 1
            entry["lines"].append(line_no)

    opener_repeats = []
    for key in sorted(openers):
        entry = openers[key]
        if entry["count"] >= OPENER_MIN_COUNT:
            opener_repeats.append({
                "opener": key,
                "count": entry["count"],
                "lines": entry["lines"],
            })
    opener_repeats.sort(key=lambda o: (-o["count"], o["opener"]))

    phrase_total = sum(h["count"] for h in phrase_hits)
    density = round(phrase_total * 1000.0 / total_words, 2)
    return {
        "words": total_words,
        "lines": len(lines),
        "phrase_hit_total": phrase_total,
        "hits_per_1000_words": density,
        "phrase_hits": phrase_hits,
        "opener_repeats": opener_repeats,
        "finding_count": len(phrase_hits) + len(opener_repeats),
    }


def main(argv):
    if len(argv) != 2:
        fail("usage", "usage: phrase_scan.py <input-file>")
    path = argv[1]
    text = read_input(path)
    result = scan(text)
    result = {"file": os.path.basename(path), **result}
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + "\n")
    return 1 if result["finding_count"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
