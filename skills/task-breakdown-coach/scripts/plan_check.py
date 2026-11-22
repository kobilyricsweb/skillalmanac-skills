#!/usr/bin/env python3
"""Validate a task-breakdown plan file (JSON or Markdown) and print strict JSON.

    python plan_check.py <plan.json | plan.md>

Reads the one file it is given. Writes nothing. Prints one JSON object to stdout.
Errors go to stderr as a plain sentence.

Exit codes
    0  no error-level finding (warnings may exist)
    1  at least one error-level finding
    2  usage error, unreadable file, empty file, or a file that cannot be parsed

Plan formats
  JSON: {"goal": str, "first_action": str, "first_action_minutes": number,
         "limits": {"max_step_minutes": 45, "daily_capacity_minutes": 180},
         "next_action": "<step id>",
         "steps": [{"id": str, "title": str, "minutes": number,
                    "energy": "low"|"medium"|"high", "context": str,
                    "day": str, "done": bool}]}
  Markdown (any file whose name does not end in .json):
         Goal: text
         First action: text | 5m
         Capacity: 180            (minutes per day)
         Max step: 45             (minutes)
         Next action: s2
         - [ ] Title | 20m | energy:low | context:desk | day:mon | id:s2
         - [x] Title | 30m | energy:high | context:desk | day:mon
    Only the title and the minutes token are positional; the other tokens may
    come in any order. An absent id becomes s<position>.

JSON contract of the output (schema_version 1)
    {"schema_version": 1, "file": str, "format": "json"|"markdown",
     "limits_used": {"max_step_minutes": number, "daily_capacity_minutes": number|null},
     "steps": int, "ok": bool,
     "counts": {"error": int, "warning": int},
     "day_totals": {day: minutes},
     "findings": [{"severity": "error"|"warning", "code": str,
                   "step": str|null, "message": str}]}
    Findings are sorted by severity (errors first), then by position in the file.

Finding codes
    errors:   missing_first_action, first_action_not_concrete, first_action_too_long,
              no_steps, step_over_limit, step_not_concrete, missing_minutes,
              missing_energy, bad_energy, missing_context, day_overbooked,
              duplicate_id, bad_next_action
    warnings: first_action_minutes_missing, step_under_min, verb_not_recognized,
              day_tight, day_too_many_steps, two_high_energy_steps_in_day, capacity_missing, too_many_steps,
              no_next_action

The check is lexical. It cannot tell whether a step is really doable or whether
the minutes are realistic; a person or the agent decides that.
"""
import json
import os
import re
import sys

SCHEMA_VERSION = 1

# Step length bounds in minutes. Below 15 a step costs more in switching than it
# saves; above 45 it stops being a single sitting for most people. Working values.
MIN_STEP_MINUTES = 15
DEFAULT_MAX_STEP_MINUTES = 45
# The first action must be small enough to start without a decision.
MAX_FIRST_ACTION_MINUTES = 10
# A day is "tight" above this share of stated capacity; plans that fill 100% fail on day one.
TIGHT_SHARE = 0.8
# More than this many steps in one day is a juggling problem, not a plan.
MAX_STEPS_PER_DAY = 3
# A plan longer than this should be split into phases.
MAX_STEPS_TOTAL = 12
ENERGY_LEVELS = ("low", "medium", "high")

# Verbs that give no observable action. A title starting with one of these fails.
VAGUE_VERBS = {
    "work", "think", "deal", "handle", "look", "figure", "start", "begin",
    "finish", "plan", "organize", "organise", "prepare", "research", "consider",
    "focus", "improve", "address", "tackle", "explore", "review", "progress",
    "continue", "try", "manage", "sort", "get", "do", "make", "gather",
}
# Verbs with an observable result. A title starting with one of these passes the verb check.
CONCRETE_VERBS = {
    "open", "write", "draft", "email", "call", "text", "send", "list", "print",
    "download", "upload", "save", "copy", "paste", "move", "delete", "archive",
    "create", "add", "remove", "install", "run", "test", "read", "skim", "scan",
    "photograph", "measure", "weigh", "buy", "order", "book", "schedule", "pay",
    "sign", "fill", "submit", "post", "label", "sort", "pack", "unpack", "clear",
    "wipe", "wash", "fold", "pick", "collect", "place", "put", "set",
    "charge", "plug", "log", "ask", "tell", "message", "record", "outline",
    "type", "edit", "compare", "choose", "pick", "decide", "check", "fix",
    "rename", "tag", "bookmark", "clone", "commit", "push", "deploy", "ship",
    "name", "count", "tally", "cut", "trim", "sketch", "draw", "highlight",
    "underline", "summarize", "summarise", "walk", "stand", "sit", "take",
    "bring", "carry", "load", "unload", "water", "feed", "cook", "chop",
    "mix", "boil", "bake", "stretch", "knock", "reply", "forward", "request",
    "cancel", "renew", "register", "enter", "log", "update", "replace", "tape",
    "staple", "scribble", "dictate", "speak", "rehearse",
}
# Phrases that look like verb + object but are vague. Checked against the lowercase title.
VAGUE_PHRASES = (
    "get started", "work on", "think about", "deal with", "look into",
    "figure out", "get ready", "set up everything", "do the thing",
    "make progress", "take care of", "sort out",
)
# "sort" sits in both lists: with a concrete object it passes (CONCRETE_VERBS is
# checked first), and "sort out" is caught by VAGUE_PHRASES.

MINUTES_TOKEN = re.compile(r"^(\d+(?:\.\d+)?)\s*(?:m|min|mins|minutes)$", re.I)
TAG_TOKEN = re.compile(r"^(energy|context|day|id)\s*[:=]\s*(.+)$", re.I)
STEP_LINE = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s*(.+)$")
HEADER_LINE = re.compile(r"^\s*(goal|first action|capacity|max step|next action)\s*:\s*(.*)$", re.I)


def fail(message):
    sys.stderr.write(message + "\n")
    return 2


def num(value):
    """Return a number for ints, floats and numeric strings; None for anything else (bool included)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return None
    return None


def parse_minutes_text(text):
    m = MINUTES_TOKEN.match(text.strip())
    if not m:
        return None
    value = float(m.group(1))
    return int(value) if value == int(value) else value


def parse_markdown(text):
    plan = {"steps": [], "limits": {}}
    for raw in text.splitlines():
        step = STEP_LINE.match(raw)
        if step:
            parts = [p.strip() for p in step.group(2).split("|")]
            item = {"title": parts[0], "done": step.group(1) != " "}
            for part in parts[1:]:
                minutes = parse_minutes_text(part)
                tag = TAG_TOKEN.match(part)
                if minutes is not None:
                    item["minutes"] = minutes
                elif tag:
                    item[tag.group(1).lower()] = tag.group(2).strip()
            plan["steps"].append(item)
            continue
        head = HEADER_LINE.match(raw)
        if not head:
            continue
        key, value = head.group(1).lower(), head.group(2).strip()
        if key == "goal":
            plan["goal"] = value
        elif key == "first action":
            parts = [p.strip() for p in value.split("|")]
            plan["first_action"] = parts[0]
            for part in parts[1:]:
                minutes = parse_minutes_text(part)
                if minutes is not None:
                    plan["first_action_minutes"] = minutes
        elif key == "capacity":
            plan["limits"]["daily_capacity_minutes"] = num(re.sub(r"[^0-9.]", "", value) or "x")
        elif key == "max step":
            plan["limits"]["max_step_minutes"] = num(re.sub(r"[^0-9.]", "", value) or "x")
        elif key == "next action":
            plan["next_action"] = value
    return plan


def verb_status(title):
    """Return 'ok', 'vague', 'no_object' or 'unknown' for a step title."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]*|\d+", title.lower())
    if len(words) < 2:
        return "no_object"
    lowered = " ".join(words)
    if any(lowered.startswith(p) for p in VAGUE_PHRASES):
        return "vague"
    verb = words[0]
    if verb in CONCRETE_VERBS:
        return "ok"
    if verb in VAGUE_VERBS:
        return "vague"
    return "unknown"


def check(plan):
    findings = []

    def add(severity, code, step, message):
        findings.append({"severity": severity, "code": code, "step": step, "message": message})

    limits = plan.get("limits") if isinstance(plan.get("limits"), dict) else {}
    max_step = num(limits.get("max_step_minutes"))
    max_step = max_step if max_step and max_step > 0 else DEFAULT_MAX_STEP_MINUTES
    capacity = num(limits.get("daily_capacity_minutes"))
    capacity = capacity if capacity and capacity > 0 else None

    # First action.
    first = plan.get("first_action")
    if not isinstance(first, str) or not first.strip():
        add("error", "missing_first_action", None,
            "No first_action. Write one physical action of 10 minutes or less that needs no decision.")
    else:
        status = verb_status(first)
        if status != "ok":
            add("error", "first_action_not_concrete", None,
                "First action must start with a physical verb and name an object (for example 'Open the tax folder on the desk'); status: " + status + ".")
        minutes = num(plan.get("first_action_minutes"))
        if minutes is None:
            add("warning", "first_action_minutes_missing", None,
                "State first_action_minutes so the 10-minute limit can be checked.")
        elif minutes > MAX_FIRST_ACTION_MINUTES:
            add("error", "first_action_too_long", None,
                "First action is %g minutes; the limit is %d. Shrink it." % (minutes, MAX_FIRST_ACTION_MINUTES))

    steps = plan.get("steps")
    steps = steps if isinstance(steps, list) else []
    if not steps:
        add("error", "no_steps", None, "The plan has no steps.")
    if len(steps) > MAX_STEPS_TOTAL:
        add("warning", "too_many_steps", None,
            "%d steps; more than %d should be split into phases." % (len(steps), MAX_STEPS_TOTAL))

    seen_ids = {}
    day_minutes = {}
    day_counts = {}
    day_high = {}
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            add("error", "step_not_concrete", "s%d" % index, "Step is not an object or a list item.")
            continue
        sid = str(step.get("id") or "s%d" % index)
        if sid in seen_ids:
            add("error", "duplicate_id", sid, "Step id '%s' is used more than once." % sid)
        seen_ids[sid] = step
        title = step.get("title")
        title = title.strip() if isinstance(title, str) else ""
        status = verb_status(title) if title else "no_object"
        if status in ("vague", "no_object"):
            add("error", "step_not_concrete", sid,
                "Title '%s' has no concrete verb plus object (%s). Rewrite it as an action someone could photograph being done." % (title, status))
        elif status == "unknown":
            add("warning", "verb_not_recognized", sid,
                "Verb in '%s' is not on the known concrete list; confirm it names an observable action." % title)
        minutes = num(step.get("minutes"))
        if minutes is None or minutes <= 0:
            add("error", "missing_minutes", sid, "Step has no positive minutes estimate.")
        else:
            if minutes > max_step:
                add("error", "step_over_limit", sid,
                    "%g minutes is over the %g-minute limit. Split it." % (minutes, max_step))
            elif minutes < MIN_STEP_MINUTES:
                add("warning", "step_under_min", sid,
                    "%g minutes is under %d; merge it with a neighbour unless it is the first action." % (minutes, MIN_STEP_MINUTES))
        energy = step.get("energy")
        if energy is None or str(energy).strip() == "":
            add("error", "missing_energy", sid, "Step has no energy tag (low, medium or high).")
        elif str(energy).strip().lower() not in ENERGY_LEVELS:
            add("error", "bad_energy", sid, "Energy '%s' is not low, medium or high." % energy)
        context = step.get("context")
        if not isinstance(context, str) or not context.strip():
            add("error", "missing_context", sid, "Step has no context tag (where or with what it can be done).")
        day = step.get("day")
        if day is not None and str(day).strip() != "" and minutes is not None and minutes > 0 and not step.get("done"):
            key = str(day).strip()
            day_minutes[key] = day_minutes.get(key, 0) + minutes
            day_counts[key] = day_counts.get(key, 0) + 1
            if str(energy or "").strip().lower() == "high":
                day_high[key] = day_high.get(key, 0) + 1

    # Day budgets.
    if day_minutes and capacity is None:
        add("warning", "capacity_missing", None,
            "Steps are assigned to days but no daily_capacity_minutes is stated, so overbooking cannot be checked.")
    for day in day_minutes:
        total = day_minutes[day]
        if capacity is not None and total > capacity:
            add("error", "day_overbooked", None,
                "Day '%s' holds %g minutes against a capacity of %g." % (day, total, capacity))
        elif capacity is not None and total > capacity * TIGHT_SHARE:
            add("warning", "day_tight", None,
                "Day '%s' is at %d%% of capacity; leave at least 20%% free." % (day, round(100 * total / capacity)))
        if day_counts[day] > MAX_STEPS_PER_DAY:
            add("warning", "day_too_many_steps", None,
                "Day '%s' has %d steps; the limit is %d." % (day, day_counts[day], MAX_STEPS_PER_DAY))

    for day, count in day_high.items():
        if count > 1:
            add("warning", "two_high_energy_steps_in_day", None,
                "Day '%s' has %d high-energy steps; the limit is 1 per day." % (day, count))

    # Next action.
    nxt = plan.get("next_action")
    if nxt in (None, ""):
        add("warning", "no_next_action", None, "No next_action id is set.")
    else:
        step = seen_ids.get(str(nxt))
        if step is None:
            add("error", "bad_next_action", str(nxt), "next_action '%s' matches no step id." % nxt)
        elif step.get("done"):
            add("error", "bad_next_action", str(nxt), "next_action '%s' is already done." % nxt)

    order = {"error": 0, "warning": 1}
    findings = [f for _, f in sorted(enumerate(findings), key=lambda p: (order[p[1]["severity"]], p[0]))]
    return findings, max_step, capacity, day_minutes, len(steps)


def main(argv):
    if len(argv) != 1:
        return fail("Usage: plan_check.py <plan.json | plan.md>")
    path = argv[0]
    try:
        with open(path, encoding="utf-8-sig") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        return fail("Cannot read %s: %s" % (path, exc))
    if not text.strip():
        return fail("File is empty: " + path)
    if path.lower().endswith(".json"):
        fmt = "json"
        try:
            plan = json.loads(text)
        except ValueError as exc:
            return fail("Invalid JSON in %s: %s" % (path, exc))
        if not isinstance(plan, dict):
            return fail("The JSON plan must be an object with a 'steps' list.")
    else:
        fmt = "markdown"
        plan = parse_markdown(text)
    findings, max_step, capacity, day_minutes, count = check(plan)
    errors = sum(1 for f in findings if f["severity"] == "error")
    report = {
        "schema_version": SCHEMA_VERSION,
        "file": os.path.basename(path),
        "format": fmt,
        "limits_used": {"max_step_minutes": max_step, "daily_capacity_minutes": capacity},
        "steps": count,
        "ok": errors == 0,
        "counts": {"error": errors, "warning": len(findings) - errors},
        "day_totals": {k: day_minutes[k] for k in sorted(day_minutes)},
        "findings": findings,
    }
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
