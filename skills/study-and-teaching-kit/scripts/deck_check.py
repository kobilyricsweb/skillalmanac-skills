#!/usr/bin/env python3
"""Validate a flashcard deck and build a spaced-review schedule.

Usage:
    python deck_check.py validate <deck.json|deck.csv>
    python deck_check.py schedule --start YYYY-MM-DD [--exam YYYY-MM-DD]
                                  [--profile standard|dense]
                                  [--cards N --new-per-day M]

validate  Reads one deck file (read-only) and prints one JSON object listing
          problems per card: missing_field, bad_card, missing_tags,
          answer_leak, too_long, duplicate_front.
schedule  Reads nothing. Prints one JSON object with review dates computed
          from the start date (see the interval table in SKILL.md).

Deck formats
    JSON: a list of card objects, or {"cards": [...]}. Fields: front, back,
          tags (list of strings, or one string separated by ";"), optional id.
    CSV : UTF-8, header row with front,back,tags (optional id). Tags are
          separated by ";".

Output is strict JSON (no NaN) on stdout, UTF-8 on every platform.
Exit codes: 0 = no findings / schedule built, 1 = validate found problems,
2 = unusable input (missing file, bad date, bad option); the reason is
printed on stderr. Nothing is written anywhere. Standard library only.
"""
import argparse
import csv
import datetime
import io
import json
import math
import os
import re
import sys

# ---- thresholds: working values chosen for card quality, not measured optima ----
FRONT_MAX_WORDS = 30   # a prompt longer than this is usually several questions
BACK_MAX_WORDS = 40    # longer answers are usually several facts; split the card
BACK_MAX_LINES = 4     # a list answer of 5+ lines is a list to learn in parts
LEAK_RATIO = 0.6       # share of answer content words already present in the prompt
MAX_BYTES = 2_000_000  # refuse absurdly large deck files
MAX_REVIEWS_PER_DAY = 100  # above this a daily queue stops being realistic for most learners

# ---- spacing profiles: days after first study. See references/evidence.md ----
PROFILES = {
    "standard": [1, 3, 7, 14, 30, 60, 120],
    "dense": [1, 2, 4, 8, 16, 32, 64],
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

STOPWORDS = frozenset(
    "the and for are was were has have had that this these those with from into onto "
    "what which who whom whose when where why how does did can could would should will "
    "its their there then than but not you your our out all any one two per via also "
    "about over under between while both each such been being more most other some".split()
)

CHECK_ORDER = ["bad_card", "missing_field", "missing_tags", "answer_leak", "too_long", "duplicate_front"]


class UsageError(Exception):
    """Raised for input the user must fix; mapped to exit code 2."""


# --------------------------------------------------------------------------- text helpers
def tokens(text):
    return re.findall(r"[^\W_]+", text.lower())


def stem(tok):
    # crude plural fold so "mitochondria" style pairs and "cells"/"cell" match
    return tok[:-1] if len(tok) > 4 and tok.endswith("s") else tok


def content_tokens(text):
    out = []
    for t in tokens(text):
        keep = (t.isdigit() and len(t) >= 2) or (len(t) >= 3 and t not in STOPWORDS)
        if keep:
            s = stem(t)
            if s not in out:
                out.append(s)
    return out


def as_text(value):
    if value is None:
        return ""
    return value.strip() if isinstance(value, str) else str(value).strip()


def parse_tags(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [t.strip() for t in value.split(";") if t.strip()]
    if isinstance(value, list) and all(isinstance(t, str) for t in value):
        return [t.strip() for t in value if t.strip()]
    raise ValueError("tags must be a list of strings or one string separated by ';'")


# --------------------------------------------------------------------------- loading
def read_deck(path):
    if not os.path.isfile(path):
        raise UsageError(f"file not found: {path}")
    if os.path.getsize(path) == 0:
        raise UsageError(f"file is empty: {path}")
    if os.path.getsize(path) > MAX_BYTES:
        raise UsageError(f"file is larger than {MAX_BYTES} bytes; split the deck")
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        raw = fh.read()
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise UsageError(f"not valid JSON: {exc}")
        if isinstance(data, dict) and isinstance(data.get("cards"), list):
            data = data["cards"]
        if not isinstance(data, list):
            raise UsageError('JSON deck must be a list of cards or {"cards": [...]}')
        return "json", data
    if ext == ".csv":
        reader = csv.DictReader(io.StringIO(raw))
        if not reader.fieldnames:
            raise UsageError("CSV has no header row")
        names = [n.strip().lower() for n in reader.fieldnames]
        for need in ("front", "back", "tags"):
            if need not in names:
                raise UsageError(f"CSV header must contain front, back, tags; missing: {need}")
        rows = []
        for row in reader:
            rows.append({(k or "").strip().lower(): v for k, v in row.items()})
        return "csv", rows
    raise UsageError("deck file must end in .json or .csv")


# --------------------------------------------------------------------------- validate
def validate(path):
    fmt, cards = read_deck(path)
    findings = []

    def add(index, card, check, detail):
        item = {"card": index, "check": check, "detail": detail}
        if isinstance(card, dict) and card.get("id") not in (None, ""):
            item["id"] = card["id"]
        findings.append(item)

    seen_fronts = {}
    for i, card in enumerate(cards, start=1):
        if not isinstance(card, dict):
            add(i, None, "bad_card", "card is not an object")
            continue
        front, back = as_text(card.get("front")), as_text(card.get("back"))
        for name, val in (("front", front), ("back", back)):
            if not val:
                add(i, card, "missing_field", f"{name} is empty or missing")
        try:
            tags = parse_tags(card.get("tags"))
        except ValueError as exc:
            tags = []
            add(i, card, "missing_tags", str(exc))
        else:
            if not tags:
                add(i, card, "missing_tags", "card has no tags")
        if not front or not back:
            continue

        f_tok, b_tok = tokens(front), tokens(back)
        ct = content_tokens(back)
        overlap = [t for t in ct if t in {stem(x) for x in f_tok}]
        joined_back = " ".join(b_tok)
        contained = len(joined_back) >= 3 and f" {joined_back} " in f" {' '.join(f_tok)} "
        if contained or (ct and len(overlap) / len(ct) >= LEAK_RATIO):
            shown = overlap if overlap else b_tok
            add(i, card, "answer_leak", "prompt already contains answer words: " + ", ".join(shown))

        if len(front.split()) > FRONT_MAX_WORDS:
            add(i, card, "too_long", f"front has {len(front.split())} words (max {FRONT_MAX_WORDS})")
        if len(back.split()) > BACK_MAX_WORDS:
            add(i, card, "too_long", f"back has {len(back.split())} words (max {BACK_MAX_WORDS})")
        lines = [ln for ln in back.splitlines() if ln.strip()]
        if len(lines) > BACK_MAX_LINES:
            add(i, card, "too_long", f"back has {len(lines)} lines (max {BACK_MAX_LINES})")

        key = " ".join(f_tok)
        if key in seen_fronts:
            first = seen_fronts[key]
            same_back = " ".join(tokens(as_text(cards[first - 1].get("back")))) == " ".join(b_tok)
            add(i, card, "duplicate_front",
                f"same front as card {first}" + (" and the same back" if same_back else " with a different back"))
        else:
            seen_fronts[key] = i

    findings.sort(key=lambda f: (f["card"], CHECK_ORDER.index(f["check"])))
    counts = {}
    for f in findings:
        counts[f["check"]] = counts.get(f["check"], 0) + 1
    report = {
        "command": "validate",
        "file": os.path.basename(path),
        "format": fmt,
        "cards": len(cards),
        "ok": not findings,
        "counts_by_check": counts,
        "findings": findings,
    }
    return report, (0 if not findings else 1)


# --------------------------------------------------------------------------- schedule
def parse_date(text, label):
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):  # same strictness on Python 3.9 and 3.11+
            raise ValueError(text)
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise UsageError(f"{label} must be a real date written YYYY-MM-DD, got {text!r}")


def offsets_for(profile, available):
    """Review offsets in days after first study. available=None means no exam."""
    base = PROFILES[profile]
    if available is None:
        return list(base), False
    kept = [o for o in base if o <= available]
    added = False
    # a last review the day before the exam, unless it would sit right after another review
    if available >= 1 and available not in kept and (not kept or available - kept[-1] >= 2):
        kept.append(available)
        added = True
    return kept, added


def describe(day, intro):
    return {"date": day.isoformat(), "weekday": WEEKDAYS[day.weekday()], "day_offset": (day - intro).days}


def schedule(args):
    start = parse_date(args.start, "--start")
    exam = parse_date(args.exam, "--exam") if args.exam else None
    if (args.cards is None) != (args.new_per_day is None):
        raise UsageError("--cards and --new-per-day must be given together")
    if args.cards is not None and (args.cards < 1 or args.new_per_day < 1):
        raise UsageError("--cards and --new-per-day must be positive whole numbers")
    horizon = None
    if exam:
        horizon = (exam - start).days
        if horizon < 2:
            raise UsageError("--exam must be at least 2 days after --start")

    def plan_for(intro_offset):
        avail = None if horizon is None else horizon - 1 - intro_offset
        return offsets_for(args.profile, avail)

    offs, added = plan_for(0)
    sessions = [{"session": 0, "kind": "study", "gap_days": None, **describe(start, start)}]
    prev = 0
    for n, o in enumerate(offs, start=1):
        day = start + datetime.timedelta(days=o)
        kind = "final_review" if (added and o == offs[-1]) else "review"
        sessions.append({"session": n, "kind": kind, "gap_days": o - prev, **describe(day, start)})
        prev = o
    report = {
        "command": "schedule",
        "profile": args.profile,
        "start": start.isoformat(),
        "exam": exam.isoformat() if exam else None,
        "offsets": offs,
        "final_review_added": added,
        "sessions": sessions,
    }
    notes = []
    if args.cards is not None:
        n_batches = math.ceil(args.cards / args.new_per_day)
        if horizon is not None and n_batches - 1 > horizon - 2:
            raise UsageError(
                f"{args.cards} cards at {args.new_per_day} per day need {n_batches} introduction days; "
                f"only {max(horizon - 1, 0)} days remain before the exam eve. Raise --new-per-day or cut cards."
            )
        batches, load = [], {}
        for k in range(n_batches):
            size = min(args.new_per_day, args.cards - k * args.new_per_day)
            intro = start + datetime.timedelta(days=k)
            b_offs, _ = plan_for(k)
            dates = [(intro + datetime.timedelta(days=o)) for o in b_offs]
            batches.append({"batch": k + 1, "cards": size, "introduced": intro.isoformat(),
                            "review_dates": [d.isoformat() for d in dates]})
            load.setdefault(intro, {"new": 0, "reviews": 0})["new"] += size
            for d in dates:
                load.setdefault(d, {"new": 0, "reviews": 0})["reviews"] += size
        ordered = sorted(load)
        peak_day = max(ordered, key=lambda d: (load[d]["reviews"], -d.toordinal()))
        report["batches"] = batches
        report["daily_load"] = [{"date": d.isoformat(), **load[d]} for d in ordered]
        report["peak_reviews"] = load[peak_day]["reviews"]
        report["peak_date"] = peak_day.isoformat()
        if load[peak_day]["reviews"] > MAX_REVIEWS_PER_DAY:
            notes.append(f"peak of {load[peak_day]['reviews']} reviews on {peak_day.isoformat()} exceeds "
                         f"{MAX_REVIEWS_PER_DAY}; lower --new-per-day or cut cards")
    if exam and horizon < 7:
        notes.append("fewer than 7 days to the exam: only the early intervals fit")
    report["notes"] = notes
    return report, 0


# --------------------------------------------------------------------------- main
def emit(report):
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass
    ap = argparse.ArgumentParser(prog="deck_check.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    pv = sub.add_parser("validate")
    pv.add_argument("deck")
    ps = sub.add_parser("schedule")
    ps.add_argument("--start", required=True)
    ps.add_argument("--exam")
    ps.add_argument("--profile", choices=sorted(PROFILES), default="standard")
    ps.add_argument("--cards", type=int)
    ps.add_argument("--new-per-day", dest="new_per_day", type=int)
    args = ap.parse_args(argv)
    try:
        report, code = validate(args.deck) if args.command == "validate" else schedule(args)
    except UsageError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    emit(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
