#!/usr/bin/env python3
"""Check a meeting agenda against its time slot before the meeting happens.

Usage:
    python check_agenda.py AGENDA [--format auto|json|md] [--length MIN]
                           [--start HH:MM] [--attendees N] [--purpose P]
                           [--out REPORT.json] [--force]

AGENDA is a JSON file or a markdown agenda (see SKILL.md for both layouts).
Reads: the agenda file only. Writes: nothing, unless --out is given; then it
writes the JSON report to that path. It refuses an --out path that resolves to
the agenda file (even with --force) and refuses to replace an existing file
unless --force is given.

Stdout: one strict JSON report (schema_version 1).
Exit codes: 0 verdict pass, 1 verdict warn or fail, 2 bad input or bad usage.
No network, no subprocess, standard library only.
"""
import argparse
import json
import math
import os
import re
import sys

SCHEMA_VERSION = 1

# Working time rule per item type, in minutes (min, max). House values, not
# measured optima: an inform item beyond 10 minutes is usually a pre-read, a
# decide item beyond 15 usually hides an undecided discussion.
TYPE_LIMITS = {
    "inform": (5, 10),
    "discuss": (10, 20),
    "decide": (10, 15),
    "brainstorm": (15, 30),
}
ITEM_TYPES = ("inform", "discuss", "decide", "brainstorm", "break")
PURPOSES = ("decide", "inform", "brainstorm", "review")
BUFFER_FRACTION = 0.10          # slack kept free for overruns
OWNER_SHARE_MAX = 0.50          # one voice should not hold more than half
OWNER_SHARE_MIN_ITEMS = 3       # with fewer items the share is meaningless
LATE_DECISION_FRACTION = 0.90   # a decision starting in the last 10% gets squeezed
EARLY_DECISION_FRACTION = 0.50  # decision meetings: first decision in first half
BREAK_THRESHOLD_MIN = 90        # slots longer than this need a break item
MIN_BREAK_MIN = 5
INFO_TRIM_TO_MIN = 5            # first cut for an inform item

# Outcome wording. A usable outcome starts with a verb that names a result (or
# is a question). Weak verbs describe an activity, not a result.
OUTCOME_VERBS = {
    "decide", "approve", "choose", "agree", "confirm", "select", "pick", "assign",
    "prioritize", "prioritise", "rank", "sign", "commit", "resolve", "review",
    "share", "align", "understand", "learn", "hear", "update", "list", "generate",
    "produce", "draft", "identify", "plan", "set", "finalize", "finalise", "cut",
    "name", "agree", "estimate", "schedule", "accept", "reject", "ratify", "collect",
    "gather", "surface", "flag", "map", "define", "unblock", "clear", "retire",
    "announce", "present", "report", "walk", "demo", "score", "vote", "split",
}
WEAK_VERBS = {"discuss", "talk", "cover", "sync", "touch", "chat", "go", "look", "brief", "check"}

SEVERITY_RANK = {"error": 0, "warning": 1, "info": 2}
BREAK_TITLE = re.compile(r"^(break|lunch|coffee|pause)\b", re.I)
MINUTES_RE = re.compile(r"^\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m(?:in(?:s|utes)?)?)?\s*$", re.I)
HHMM_RE = re.compile(r"^(\d{1,2}):(\d{2})$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
HEADER_RE = re.compile(r"^\s*([A-Za-z][A-Za-z ]*?)\s*:\s*(.*)$")
TAG_RE = re.compile(r"^\[([^\]]+)\]\s*(.*)$")


class AgendaError(Exception):
    """Bad input; message says what to fix."""


def parse_minutes(value, what):
    if isinstance(value, bool):
        raise AgendaError(f"{what}: expected minutes, got a boolean")
    if isinstance(value, (int, float)):
        if value != int(value) or value <= 0:
            raise AgendaError(f"{what}: minutes must be a positive whole number, got {value!r}")
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit() and int(text) > 0:
            return int(text)
        m = MINUTES_RE.match(text)
        if m and (m.group(1) or m.group(2)):
            total = int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
            if total > 0:
                return total
    raise AgendaError(f"{what}: cannot read {value!r} as minutes (use 10, 10m, 1h or 1h30m)")


def parse_hhmm(value, what):
    m = HHMM_RE.match(str(value).strip())
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        raise AgendaError(f"{what}: expected HH:MM on a 24-hour clock, got {value!r}")
    return int(m.group(1)) * 60 + int(m.group(2))


def fmt_clock(minutes):
    minutes %= 1440
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_count(value, what):
    if isinstance(value, bool) or isinstance(value, float) and value != int(value):
        raise AgendaError(f"{what}: expected a whole number, got {value!r}")
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise AgendaError(f"{what}: expected a whole number, got {value!r}")
    if n <= 0:
        raise AgendaError(f"{what}: must be positive, got {n}")
    return n


def parse_yes_no(value, what):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("yes", "y", "true"):
        return True
    if text in ("no", "n", "false"):
        return False
    raise AgendaError(f"{what}: expected yes or no, got {value!r}")


# ---------------------------------------------------------------- parsing

ITEM_KEYS_JSON = {"title", "owner", "type", "minutes", "outcome", "question", "needs_discussion", "start"}
MEETING_KEYS = {"title", "length_min", "start", "attendees", "purpose"}


def blank_item(title):
    return {"title": title, "owner": None, "type": None, "minutes": None, "outcome": None,
            "question": None, "needs_discussion": None, "start": None}


def parse_json(text):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise AgendaError(f"not valid JSON: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise AgendaError('JSON must be an object with an "items" list and optional "meeting" object')
    meeting = data.get("meeting") or {}
    if not isinstance(meeting, dict):
        raise AgendaError('"meeting" must be an object')
    extra = set(meeting) - MEETING_KEYS
    if extra:
        raise AgendaError(f"unknown meeting key(s): {', '.join(sorted(extra))}")
    items = []
    for n, raw in enumerate(data["items"], 1):
        if not isinstance(raw, dict):
            raise AgendaError(f"item {n}: must be an object")
        extra = set(raw) - ITEM_KEYS_JSON
        if extra:
            raise AgendaError(f"item {n}: unknown key(s): {', '.join(sorted(extra))}")
        item = blank_item(str(raw.get("title") or "").strip())
        for key in ("owner", "outcome", "question"):
            if raw.get(key) is not None:
                item[key] = str(raw[key]).strip() or None
        if raw.get("type") is not None:
            item["type"] = str(raw["type"]).strip().lower()
        if "minutes" not in raw:
            raise AgendaError(f"item {n}: missing minutes")
        item["minutes"] = parse_minutes(raw["minutes"], f"item {n} minutes")
        if raw.get("needs_discussion") is not None:
            item["needs_discussion"] = parse_yes_no(raw["needs_discussion"], f"item {n} needs_discussion")
        if raw.get("start") is not None:
            item["start"] = str(raw["start"]).strip()
        items.append(item)
    return {k: meeting.get(k) for k in MEETING_KEYS}, items


def parse_markdown(text):
    meeting = {k: None for k in MEETING_KEYS}
    items = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            if meeting["title"] is None:
                meeting["title"] = stripped.lstrip("#").strip() or None
            continue
        bullet = BULLET_RE.match(line)
        if bullet:
            items.append(parse_md_item(bullet.group(1), lineno, len(items) + 1))
            continue
        header = HEADER_RE.match(line)
        if header and not items:
            key = header.group(1).strip().lower().replace(" ", "_")
            key = {"length": "length_min", "meeting": "title"}.get(key, key)
            if key not in MEETING_KEYS:
                raise AgendaError(f"line {lineno}: unknown header '{header.group(1).strip()}'")
            meeting[key] = header.group(2).strip()
            continue
        raise AgendaError(f"line {lineno}: not a header, heading or agenda item: {stripped[:60]!r}")
    return meeting, items


def parse_md_item(body, lineno, n):
    tag = TAG_RE.match(body.strip())
    if not tag:
        raise AgendaError(f"line {lineno}: item {n} must start with a duration tag such as [10m]")
    minutes = parse_minutes(tag.group(1), f"line {lineno} duration tag")
    segments = [s.strip() for s in tag.group(2).split("|")]
    item = blank_item(segments[0])
    item["minutes"] = minutes
    for seg in segments[1:]:
        if not seg:
            continue
        if ":" not in seg:
            raise AgendaError(f"line {lineno}: segment {seg!r} needs a key, for example 'owner: Dana'")
        key, value = seg.split(":", 1)
        key, value = key.strip().lower(), value.strip()
        if key in ("decide", "inform", "discuss", "brainstorm"):
            item["type"], item["outcome"] = key, value or None
        elif key in ("owner", "outcome", "question", "start"):
            item[key] = value or None
        elif key == "type":
            item["type"] = value.lower()
        elif key == "discussion":
            item["needs_discussion"] = parse_yes_no(value, f"line {lineno} discussion")
        else:
            raise AgendaError(f"line {lineno}: unknown key {key!r}")
    return item


# --------------------------------------------------------------- analysis

def first_word(text):
    m = re.match(r"[A-Za-z']+", text.strip())
    return m.group(0).lower() if m else ""


def analyse(meeting, items):
    length = meeting["length_min"]
    start_clock = meeting["start"]
    attendees = meeting["attendees"]
    purpose = meeting["purpose"]
    required_buffer = math.ceil(length * BUFFER_FRACTION)

    findings = []
    flags = {i: set() for i in range(1, len(items) + 1)}

    def add(code, severity, idx, message):
        findings.append({"code": code, "severity": severity, "item": idx, "message": message})
        if idx is not None:
            flags[idx].add(code)

    # Resolve types first.
    for n, it in enumerate(items, 1):
        if it["type"] is None and BREAK_TITLE.match(it["title"] or ""):
            it["type"] = "break"
        if it["type"] is None:
            add("NO_GOAL_TYPE", "error", n, "item has no goal type: say decide, inform, discuss or brainstorm")
        elif it["type"] not in ITEM_TYPES:
            add("NO_GOAL_TYPE", "error", n, f"unknown goal type {it['type']!r}")
            it["type"] = None
        if not it["title"]:
            add("NO_TITLE", "error", n, "item has no title")

    # Chain the clock.
    cursor = 0
    ends_at = 0
    timeline = []
    meeting_start = parse_hhmm(start_clock, "start") if start_clock else None
    for n, it in enumerate(items, 1):
        start = cursor
        if it["start"]:
            if meeting_start is None:
                raise AgendaError(f"item {n}: has a start time but the meeting has no start; add start: HH:MM")
            start = parse_hhmm(it["start"], f"item {n} start") - meeting_start
            if start < 0:
                add("START_BEFORE_MEETING", "error", n, "item starts before the meeting starts")
            elif start < cursor:
                add("OVERLAP", "error", n, f"starts {cursor - start} min before the previous item ends")
            elif start > cursor:
                add("GAP_BEFORE", "info", n, f"{start - cursor} min unscheduled before this item")
        end = start + it["minutes"]
        timeline.append((start, end))
        cursor = end
        ends_at = max(ends_at, end)

    total = sum(it["minutes"] for it in items)
    buffer_min = length - ends_at
    if total > length:
        add("OVERBOOKED", "error", None, f"items add up to {total} min in a {length} min slot")
    elif buffer_min < required_buffer:
        add("BUFFER_TOO_SMALL", "warning", None,
            f"{buffer_min} min free, at least {required_buffer} min (10 percent) wanted")

    # Per-item checks.
    for n, it in enumerate(items, 1):
        t = it["type"]
        start, end = timeline[n - 1]
        if end > length:
            add("RUNS_PAST_SLOT", "error", n, f"ends at minute {end}, slot is {length} min")
        if t == "break":
            if it["minutes"] < MIN_BREAK_MIN:
                add("BREAK_TOO_SHORT", "warning", n, f"break is {it['minutes']} min, at least {MIN_BREAK_MIN} wanted")
            continue
        if t is None:
            continue
        if not it["owner"]:
            add("NO_OWNER", "error", n, "item has no owner")
        text = it["outcome"]
        if not text:
            add("NO_OUTCOME", "error", n, "item has no desired outcome")
        elif t != "decide" and "?" not in text:
            word = first_word(text)
            if word in WEAK_VERBS:
                add("OUTCOME_WEAK_VERB", "warning", n, f"'{word}' names an activity, not a result")
            elif word not in OUTCOME_VERBS:
                add("OUTCOME_NO_VERB", "warning", n, "outcome should start with a result verb or be a question")
        if t == "decide":
            question = it["question"] or text or ""
            if "?" not in question:
                add("NO_DECISION_QUESTION", "error", n, "a decide item needs the decision written as a question")
        lo, hi = TYPE_LIMITS[t]
        if it["minutes"] < lo:
            add("DURATION_BELOW_MIN", "warning", n, f"{it['minutes']} min is under the {lo} min floor for {t}")
        if it["minutes"] > hi:
            add("DURATION_ABOVE_MAX", "warning", n, f"{it['minutes']} min is over the {hi} min ceiling for {t}")
        if t in ("inform", "discuss") and it["needs_discussion"] is False:
            add("ASYNC_CANDIDATE", "warning", n, "no discussion needed: send it as a pre-read")
        if t == "decide" and start >= LATE_DECISION_FRACTION * length:
            add("DECISION_LATE", "warning", n, "decision starts in the last 10 percent of the slot")

    # Whole-meeting checks.
    work = [(n, it) for n, it in enumerate(items, 1) if it["type"] not in (None, "break")]
    if length > BREAK_THRESHOLD_MIN and not any(it["type"] == "break" for it in items):
        add("NO_BREAK", "warning", None, f"slot is over {BREAK_THRESHOLD_MIN} min and has no break")

    owner_minutes = {}
    display = {}
    for n, it in work:
        if it["owner"]:
            key = it["owner"].lower()
            display.setdefault(key, it["owner"])
            owner_minutes[key] = owner_minutes.get(key, 0) + it["minutes"]
    work_total = sum(it["minutes"] for _, it in work)
    if len(work) >= OWNER_SHARE_MIN_ITEMS and work_total:
        for key, mins in owner_minutes.items():
            if mins / work_total > OWNER_SHARE_MAX:
                add("OWNER_DOMINANT", "warning", None,
                    f"{display[key]} holds {mins} of {work_total} min ({round(100 * mins / work_total)} percent)")
                for n, it in work:
                    if it["owner"] and it["owner"].lower() == key:
                        flags[n].add("OWNER_DOMINANT")

    decide_items = [(n, timeline[n - 1][0]) for n, it in work if it["type"] == "decide"]
    if purpose == "decide":
        if not decide_items:
            add("NO_DECISION_ITEM", "error", None, "purpose is decide but no item is a decide item")
        elif decide_items[0][1] > EARLY_DECISION_FRACTION * length:
            add("DECISION_NOT_EARLY", "warning", decide_items[0][0],
                "first decision starts after the midpoint of the slot")
    if purpose == "brainstorm":
        brain = [n for n, it in work if it["type"] == "brainstorm"]
        if not brain:
            add("NO_BRAINSTORM_ITEM", "warning", None, "purpose is brainstorm but no item is a brainstorm item")
        elif not any(n > brain[-1] and it["type"] in ("decide", "discuss") for n, it in work):
            add("NO_CONVERGE_STEP", "warning", None, "no discuss or decide item after the last brainstorm item")
    if purpose == "inform" and work and all(it["type"] == "inform" for _, it in work):
        add("COULD_BE_ASYNC", "info", None, "every item is inform: a written update may replace the meeting")

    # Suggested cuts, never touching decide items.
    shortage = max(0, required_buffer - buffer_min)
    cuts = []
    saved = 0
    if shortage:
        tiers = [[], [], []]
        for n, it in work:
            t, mins = it["type"], it["minutes"]
            if t in ("inform", "discuss") and it["needs_discussion"] is False:
                tiers[0].append((mins, n, "move_to_preread", mins, 0))
            elif t == "inform" and mins > INFO_TRIM_TO_MIN:
                tiers[1].append((mins - INFO_TRIM_TO_MIN, n, "trim", mins, INFO_TRIM_TO_MIN))
            elif t in ("discuss", "brainstorm") and mins > TYPE_LIMITS[t][0]:
                tiers[2].append((mins - TYPE_LIMITS[t][0], n, "trim", mins, TYPE_LIMITS[t][0]))
        for tier in tiers:
            for save, n, action, frm, to in sorted(tier, key=lambda r: (-r[0], r[1])):
                if saved >= shortage:
                    break
                cuts.append({"item": n, "action": action, "from_min": frm, "to_min": to, "save_min": save})
                saved += save

    out_items = []
    for n, it in enumerate(items, 1):
        start, end = timeline[n - 1]
        out_items.append({
            "n": n, "title": it["title"], "type": it["type"], "minutes": it["minutes"], "owner": it["owner"],
            "outcome": it["outcome"], "start_min": start, "end_min": end,
            "start": fmt_clock(meeting_start + start) if meeting_start is not None else None,
            "end": fmt_clock(meeting_start + end) if meeting_start is not None else None,
            "flags": sorted(flags[n]),
        })
    findings.sort(key=lambda f: (f["item"] or 0, SEVERITY_RANK[f["severity"]], f["code"]))
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ("error", "warning", "info")}
    verdict = "fail" if counts["error"] else ("warn" if counts["warning"] else "pass")
    hours = None
    if attendees:
        hours = {"slot": round(attendees * length / 60, 2), "booked": round(attendees * total / 60, 2),
                 "cuts_save": round(attendees * saved / 60, 2)}
    return {
        "schema_version": SCHEMA_VERSION, "command": "check_agenda",
        "title": meeting["title"], "purpose": purpose, "length_min": length, "start": start_clock,
        "attendees": attendees, "total_min": total, "ends_at_min": ends_at, "buffer_min": buffer_min,
        "required_buffer_min": required_buffer, "items": out_items,
        "owner_minutes": {display[k]: v for k, v in owner_minutes.items()},
        "attendee_hours": hours, "findings": findings, "counts": counts,
        "shortage_min": shortage, "suggested_cuts": cuts, "cuts_save_min": saved,
        "cuts_cover_shortage": saved >= shortage, "verdict": verdict,
    }


# -------------------------------------------------------------------- CLI

def normalise_meeting(raw, args):
    meeting = dict(raw)
    for key, value in (("length_min", args.length), ("start", args.start),
                       ("attendees", args.attendees), ("purpose", args.purpose)):
        if value is not None:
            meeting[key] = value
    if meeting.get("length_min") is None:
        raise AgendaError("meeting length missing: add 'length: 60m' to the agenda or pass --length")
    meeting["length_min"] = parse_minutes(meeting["length_min"], "meeting length")
    if meeting.get("start") not in (None, ""):
        parse_hhmm(meeting["start"], "meeting start")
        meeting["start"] = str(meeting["start"]).strip()
    else:
        meeting["start"] = None
    if meeting.get("attendees") not in (None, ""):
        meeting["attendees"] = parse_count(meeting["attendees"], "attendees")
    else:
        meeting["attendees"] = None
    purpose = meeting.get("purpose")
    if purpose:
        purpose = str(purpose).strip().lower()
        if purpose not in PURPOSES:
            raise AgendaError(f"purpose must be one of {', '.join(PURPOSES)}, got {purpose!r}")
    meeting["purpose"] = purpose or None
    meeting["title"] = (str(meeting["title"]).strip() or None) if meeting.get("title") else None
    return meeting


def same_path(a, b):
    ra, rb = os.path.realpath(a), os.path.realpath(b)
    if os.path.normcase(ra) == os.path.normcase(rb):
        return True
    try:
        return os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)
    except OSError:
        return False


def read_text(path):
    if not os.path.isfile(path):
        raise AgendaError(f"cannot read {path}: no such file")
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise AgendaError(f"cannot read {path} as UTF-8 text: {exc}")
    if not text.strip():
        raise AgendaError(f"{path} is empty")
    return text


def build_parser():
    p = argparse.ArgumentParser(prog="check_agenda.py", description="Check a meeting agenda against its slot.")
    p.add_argument("agenda")
    p.add_argument("--format", choices=("auto", "json", "md"), default="auto")
    p.add_argument("--length", help="meeting length, for example 60, 60m or 1h30m (overrides the file)")
    p.add_argument("--start", help="meeting start, HH:MM 24-hour (overrides the file)")
    p.add_argument("--attendees", help="attendee count, only if the user gave one (overrides the file)")
    p.add_argument("--purpose", help="decide, inform, brainstorm or review (overrides the file)")
    p.add_argument("--out", help="also write the JSON report to this path")
    p.add_argument("--force", action="store_true", help="allow --out to replace an existing file other than the agenda")
    return p


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        if args.out and same_path(args.out, args.agenda):
            raise AgendaError("--out resolves to the agenda file: refusing to overwrite an input")
        if args.out and os.path.exists(args.out) and not args.force:
            raise AgendaError(f"{args.out} exists: pass --force to replace it")
        text = read_text(args.agenda)
        fmt = args.format
        if fmt == "auto":
            fmt = "json" if text.lstrip().startswith("{") else "md"
        raw_meeting, items = parse_json(text) if fmt == "json" else parse_markdown(text)
        if not items:
            raise AgendaError("the agenda has no items")
        report = analyse(normalise_meeting(raw_meeting, args), items)
    except AgendaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    print(payload)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(payload + "\n")
        except OSError as exc:
            print(f"error: cannot write {args.out}: {exc}", file=sys.stderr)
            return 2
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
