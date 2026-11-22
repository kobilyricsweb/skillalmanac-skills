"""Estimate speaking time per slide from speaker notes and fit a talk to its slot.

Input: a UTF-8 text or Markdown file. Slides are separated by lines that are
exactly '---' after trimming spaces. Whitespace-only chunks are dropped.
A word is a whitespace-separated token that contains at least one letter or digit.

The script is read-only, writes only to stdout, uses only the standard library,
makes no network calls, and runs no subprocesses. It reads flat text, so no
nesting cap applies.

Exit codes: 0 talk fits the slot, 1 talk overruns the slot (finding),
2 usage or input error (one-line JSON error on stderr).
"""
import argparse
import json
import math
import os
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_SLIDES = 500
MAX_SLOT_MINUTES = 600.0
WPM_RANGE = (60, 220)
TRANSITION_RANGE = (0.0, 60.0)
FLAG_SHARE_PERCENT = 25.0
CUT_CAP_FRACTION = 0.5
SEPARATOR = "---"


def fail(message, code=2):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(code)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage: " + message)


def read_slides(path):
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        fail("cannot read input file: %s" % (exc.strerror or "unknown error"))
    if size > MAX_BYTES:
        fail("input file is larger than 2 MB")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        fail("cannot read input file: %s" % (exc.strerror or "unknown error"))
    if len(raw) > MAX_BYTES:
        fail("input file is larger than 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input file is not valid UTF-8")

    chunks = []
    current = []
    for line in text.splitlines():
        if line.strip() == SEPARATOR:
            chunks.append("\n".join(current))
            current = []
        else:
            current.append(line)
    chunks.append("\n".join(current))

    slides = [chunk for chunk in chunks if chunk.strip()]
    if not slides:
        fail("no slide text found")
    if len(slides) > MAX_SLIDES:
        fail("more than 500 slides")
    return slides


def count_words(chunk):
    return sum(1 for token in chunk.split() if any(ch.isalnum() for ch in token))


def analyse(slides, minutes, wpm, transition):
    rows = []
    for number, chunk in enumerate(slides, start=1):
        words = count_words(chunk)
        speak = words * 60.0 / wpm
        rows.append({"number": number, "words": words,
                     "speak": speak, "slide": speak + transition})

    total_words = sum(row["words"] for row in rows)
    if total_words == 0:
        fail("no words found in any slide")

    talk = sum(row["slide"] for row in rows)
    slot = minutes * 60.0
    over = talk - slot

    for row in rows:
        share = row["slide"] / talk * 100.0 if talk > 0 else 0.0
        row["share"] = share

    cuts = []
    unfixed = 0
    if over > 0:
        need = math.ceil(over * wpm / 60.0)
        for row in sorted(rows, key=lambda r: (-r["words"], r["number"])):
            if need <= 0:
                break
            cut = min(need, row["words"] // 2)
            if cut > 0:
                cuts.append({"slide": row["number"], "cut_words": cut,
                             "seconds_saved": round(cut * 60.0 / wpm, 1)})
                need -= cut
        unfixed = max(need, 0)

    return rows, talk, over, cuts, unfixed


def main(argv=None):
    parser = _Parser(prog="talk_timing.py",
                     description="Estimate speaking time per slide and fit a talk to its slot.")
    parser.add_argument("input", help="UTF-8 text or Markdown file; slides separated by '---' lines")
    parser.add_argument("--minutes", type=float, required=True,
                        help="talk slot in minutes, greater than 0 and at most 600")
    parser.add_argument("--wpm", type=int, default=130,
                        help="speaking pace in words per minute, 60 to 220 (default 130, a working value)")
    parser.add_argument("--transition-seconds", type=float, default=5.0,
                        help="seconds added per slide for the transition, 0 to 60 (default 5)")
    args = parser.parse_args(argv)

    if not (0.0 < args.minutes <= MAX_SLOT_MINUTES):
        fail("--minutes must be greater than 0 and at most 600")
    if not (WPM_RANGE[0] <= args.wpm <= WPM_RANGE[1]):
        fail("--wpm must be between 60 and 220")
    if not (TRANSITION_RANGE[0] <= args.transition_seconds <= TRANSITION_RANGE[1]):
        fail("--transition-seconds must be between 0 and 60")

    slides = read_slides(args.input)
    rows, talk, over, cuts, unfixed = analyse(
        slides, args.minutes, args.wpm, args.transition_seconds)

    result = {
        "source": args.input,
        "assumptions": {
            "wpm": args.wpm,
            "transition_seconds": args.transition_seconds,
            "flag_share_percent": FLAG_SHARE_PERCENT,
            "cut_cap_percent_of_slide": int(CUT_CAP_FRACTION * 100),
        },
        "slot_minutes": args.minutes,
        "talk_seconds": round(talk, 1),
        "talk_minutes": round(talk / 60.0, 2),
        "over_seconds": round(over, 1),
        "fits": over <= 0,
        "slides": [
            {"slide": row["number"],
             "words": row["words"],
             "speaking_seconds": round(row["speak"], 1),
             "slide_seconds": round(row["slide"], 1),
             "share_percent": round(row["share"], 1),
             "flagged": row["share"] > FLAG_SHARE_PERCENT}
            for row in rows
        ],
        "cuts": cuts,
        "unfixed_words": unfixed,
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0 if over <= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
