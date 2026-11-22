"""Extract URLs, hashtags, @mentions and dates from one UTF-8 text file.

Usage:
    python -I extract_entities.py <input-file>

Reads the file (at most 2 MB), writes one JSON object to stdout, writes no
files and makes no network calls. Names and organizations are not extracted.

Exit codes:
    0  scan finished, no ambiguous numeric dates
    1  scan finished, at least one ambiguous numeric date (needs review)
    2  usage or input error; a one-line JSON error is written to stderr
"""

import datetime
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024

URL_RE = re.compile(r"(?i)(?:\bhttps?://|\bwww\.)[^\s<>\"']+")
HASHTAG_RE = re.compile(r"(?<![\w&#])#([A-Za-z][A-Za-z0-9_]{1,49})")
MENTION_RE = re.compile(r"(?<![\w@.+\-])@([A-Za-z0-9_]{1,30})")
ISO_RE = re.compile(r"(?<![\d/.\-])(\d{4})-(\d{2})-(\d{2})(?![\d/\-])")
SLASH_RE = re.compile(r"(?<![\d/.\-])(\d{1,2})/(\d{1,2})/(\d{4})(?![\d/\-])")

CLOSERS = {")": "(", "]": "[", "}": "{"}


class InputError(Exception):
    """Raised for an input that cannot be scanned."""


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def read_lines(path):
    if not os.path.isfile(path):
        raise InputError("input is not a readable file")
    with open(path, "rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise InputError("input exceeds the 2 MB cap")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("input is not valid UTF-8")
    lines = [line.rstrip("\r") for line in text.split("\n")]
    if len(lines) > 1 and lines[-1] == "":
        lines.pop()
    return lines


def trim_url(url):
    """Drop trailing sentence punctuation and unbalanced closing brackets."""
    while url:
        last = url[-1]
        if last in ".,;:!?'\"":
            url = url[:-1]
        elif last in CLOSERS and url.count(last) > url.count(CLOSERS[last]):
            url = url[:-1]
        else:
            break
    return url


def valid_host(url):
    """The host must contain a dot and must not start or end with one."""
    rest = re.sub(r"(?i)^(?:https?://|www\.)", "", url)
    host = re.split(r"[/?#]", rest, maxsplit=1)[0]
    return "." in host and not host.startswith(".") and not host.endswith(".")


def mask(line, spans):
    chars = list(line)
    for start, end in spans:
        for index in range(start, end):
            chars[index] = " "
    return "".join(chars)


def make_date(year, month, day):
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def interpret_date(kind, groups):
    """Return (iso, alt_iso, ambiguous), or None when the date is impossible.

    ISO dates are YYYY-MM-DD. Slash dates are read as US month/day/year
    (working value); when both parts are 12 or less and differ, the date is
    ambiguous and the day/month reading is returned as alt_iso.
    """
    if kind == "iso":
        date = make_date(groups[0], groups[1], groups[2])
        return (date.isoformat(), None, False) if date else None
    first, second, year = groups
    if first > 12 and second > 12:
        return None
    if first > 12:
        date = make_date(year, second, first)
        return (date.isoformat(), None, False) if date else None
    if second > 12 or first == second:
        date = make_date(year, first, second)
        return (date.isoformat(), None, False) if date else None
    as_mdy = make_date(year, first, second)
    as_dmy = make_date(year, second, first)
    if as_mdy is None or as_dmy is None:
        return None
    return (as_mdy.isoformat(), as_dmy.isoformat(), True)


def bump(entry, number):
    entry["count"] += 1
    if not entry["lines"] or entry["lines"][-1] != number:
        entry["lines"].append(number)


def add_hit(store, key, value, number):
    if key not in store:
        store[key] = {"value": value, "count": 0, "first_line": number, "lines": []}
    bump(store[key], number)


def scan(path):
    lines = read_lines(path)
    urls, tags, mentions, dates, rejected = {}, {}, {}, {}, []
    for number, raw in enumerate(lines, start=1):
        spans = []
        for match in URL_RE.finditer(raw):
            spans.append(match.span())
            url = trim_url(match.group(0))
            if valid_host(url):
                add_hit(urls, url, url, number)
        masked = mask(raw, spans)
        for match in HASHTAG_RE.finditer(masked):
            add_hit(tags, match.group(1).casefold(), "#" + match.group(1), number)
        for match in MENTION_RE.finditer(masked):
            add_hit(mentions, match.group(1).casefold(), "@" + match.group(1), number)
        for kind, pattern in (("iso", ISO_RE), ("slash", SLASH_RE)):
            for match in pattern.finditer(masked):
                result = interpret_date(kind, [int(g) for g in match.groups()])
                if result is None:
                    rejected.append({"as_written": match.group(0), "line": number})
                    continue
                iso, alt, ambiguous = result
                key = iso + "|" + (alt or "")
                if key not in dates:
                    dates[key] = {
                        "iso": iso,
                        "alt_iso": alt,
                        "ambiguous": ambiguous,
                        "as_written": [],
                        "count": 0,
                        "first_line": number,
                        "lines": [],
                    }
                entry = dates[key]
                if match.group(0) not in entry["as_written"]:
                    entry["as_written"].append(match.group(0))
                bump(entry, number)

    def ordered(store):
        return sorted(store.values(), key=lambda e: (e["first_line"], e["value"]))

    date_list = sorted(dates.values(), key=lambda e: (e["first_line"], e["iso"]))
    ambiguous_count = sum(1 for e in date_list if e["ambiguous"])
    return {
        "input": os.path.basename(path),
        "summary": {
            "lines_scanned": len(lines),
            "url_unique": len(urls),
            "hashtag_unique": len(tags),
            "mention_unique": len(mentions),
            "date_unique": len(date_list),
            "ambiguous_date_unique": ambiguous_count,
            "rejected_date_candidates": len(rejected),
        },
        "urls": ordered(urls),
        "hashtags": ordered(tags),
        "mentions": ordered(mentions),
        "dates": date_list,
        "rejected_dates": rejected,
    }


def main(argv):
    if len(argv) != 2:
        fail("usage: python -I extract_entities.py <input-file>")
    try:
        result = scan(argv[1])
    except InputError as exc:
        fail(str(exc))
    except OSError:
        fail("input could not be read")
    sys.stdout.write(json.dumps(result, ensure_ascii=True, indent=2) + "\n")
    return 1 if result["summary"]["ambiguous_date_unique"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
