#!/usr/bin/env python3
"""Measure a terse reply: word count, filler, and what was lost against a full version.

    python terse_check.py <reply.md> [--budget N]
    python terse_check.py <reply.md> --compare <full_version.md>

Reads the given Markdown files. Writes nothing.

Exit codes: 0 = within budget and nothing technical missing, 1 = over budget,
filler found, a clipped warning, or technical items missing, 2 = usage error or
unreadable file.

Counts are words outside fenced code blocks. The comparison works on surface
forms (code blocks, inline code, numbers, URLs); it cannot judge meaning.
"""
import re
import sys

FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`([^`\n]+)`")
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'_./:-]*")
NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*(?:\s?(?:%|ms|s|sec|min|h|kb|mb|gb|tb|kib|mib|gib|px|x))?(?![\w])", re.I)
URL = re.compile(r"https?://[^\s)>\]]+")
# Phrases that carry no information in a technical reply.
FILLER = [
    r"\bgreat question\b", r"\bsure[,!]", r"\bof course\b", r"\bcertainly\b", r"\babsolutely\b",
    r"\bhappy to help\b", r"\bi hope (this|that) helps\b", r"\blet me know\b", r"\bfeel free\b",
    r"\bi('d| would) (recommend|suggest)\b", r"\bit('s| is) worth noting\b", r"\bplease note\b",
    r"\bas you can see\b", r"\bin order to\b", r"\bbasically\b", r"\bessentially\b",
    r"\byou('ll| will) (want|need) to\b", r"\blet's\b", r"\bhere('s| is) (how|what|the)\b",
    r"\bto (summari[sz]e|recap)\b", r"\bin summary\b", r"\bhope that helps\b", r"\bthanks for\b",
]
HAZARD = re.compile(r"\b(warning|danger|irreversible|cannot be undone|data loss|destructive)\b", re.I)
# A warning shorter than this cannot name both the hazard and the thing to do about it.
MIN_WARNING_WORDS = 8


def read(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        print(f"cannot read {path}: {e}", file=sys.stderr)
        sys.exit(2)
    if not text.strip():
        print(f"{path} is empty", file=sys.stderr)
        sys.exit(2)
    return text


def prose(text):
    return FENCE.sub(" ", text)


def count_words(text):
    return len(WORD.findall(prose(text)))


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


def technical_items(text):
    blocks = set()
    for b in FENCE.findall(text):
        for line in b.strip("`").split("\n")[1:]:
            if line.strip():
                blocks.add(norm(line))
    inline = {norm(x) for x in INLINE.findall(prose(text))}
    numbers = {norm(x).lower() for x in NUMBER.findall(prose(text))}
    urls = set(URL.findall(text))
    return blocks, inline, numbers, urls


def clipped_warnings(text):
    """Lines that flag a hazard but are too short to be a full sentence."""
    out = []
    for line in prose(text).split("\n"):
        if HAZARD.search(line) and len(WORD.findall(line)) < MIN_WARNING_WORDS:
            out.append(line.strip())
    return out


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args, budget, compare = [], None, None
    i = 0
    while i < len(argv):
        if argv[i] == "--budget" and i + 1 < len(argv) and argv[i + 1].isdigit():
            budget, i = int(argv[i + 1]), i + 2
        elif argv[i] == "--compare" and i + 1 < len(argv):
            compare, i = argv[i + 1], i + 2
        elif argv[i].startswith("--"):
            print(__doc__)
            return 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 1:
        print(__doc__)
        return 2
    text = read(args[0])
    words = count_words(text)
    problems = 0
    print(f"words outside code: {words}" + (f" (budget {budget})" if budget is not None else ""))
    if budget is not None and words > budget:
        print(f"  OVER by {words - budget}")
        problems += 1
    low = prose(text).lower()
    found = sorted({m.group(0) for rx in FILLER for m in re.finditer(rx, low)})
    if found:
        print("filler: " + "; ".join(found))
        problems += 1
    else:
        print("filler: none")
    clipped = clipped_warnings(text)
    for c in clipped:
        print(f"clipped warning (write it as one full sentence): {c}")
    problems += len(clipped)
    if compare:
        full = read(compare)
        fw = count_words(full)
        print(f"full version: {fw} words; reduction {100 * (fw - words) / fw:.0f}%" if fw else "full version has no prose")
        labels = ("code line", "inline code", "number", "url")
        for label, a, b in zip(labels, technical_items(full), technical_items(text)):
            hay = norm(text)
            missing = sorted(x for x in a - b if x not in hay)
            for x in missing:
                print(f"MISSING {label}: {x}")
            problems += len(missing)
        if problems == 0:
            print("nothing technical missing")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
