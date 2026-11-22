"""Timeboxes one working day.

Places prioritised tasks (with minute estimates) into the free time left around
fixed events, adds a percentage buffer to each task, inserts short breaks, and
lists the tasks that do not fit. This is a planning aid only.

Usage:
    python -I scripts/timebox.py <input.json>

The input file is read only and no output file is written. The result is
printed to stdout as JSON. Exit codes: 0 = every task placed, 1 = at least one
task does not fit, 2 = usage or input error (a one-line JSON error goes to
stderr). Standard library only. No network, no subprocess, no eval.
"""

import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 6
TIME_RE = re.compile(r"^([01][0-9]|2[0-3]):([0-5][0-9])$")
TOP_KEYS = {"day_start", "day_end", "fixed", "tasks",
            "buffer_pct", "break_every", "break_minutes"}
FIXED_KEYS = {"title", "start", "end"}
TASK_KEYS = {"title", "minutes", "priority"}


class InputError(Exception):
    """Any usage or input problem. The message is shown to the user."""


def read_json(path):
    try:
        size = os.path.getsize(path)
    except OSError:
        raise InputError("input file cannot be read")
    if size > MAX_BYTES:
        raise InputError("input file is larger than 2 MB")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        raise InputError("input file cannot be read")
    if len(raw) > MAX_BYTES:
        raise InputError("input file is larger than 2 MB")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError("input file is not valid UTF-8")
    try:
        return json.loads(text)
    except (ValueError, RecursionError, MemoryError):
        raise InputError("input file is not valid JSON")


def check_depth(value):
    stack = [(value, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > MAX_DEPTH:
            raise InputError("JSON is nested deeper than %d levels" % MAX_DEPTH)
        if isinstance(node, dict):
            stack.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            stack.extend((child, depth + 1) for child in node)


def check_keys(item, allowed, field):
    if not isinstance(item, dict):
        raise InputError("%s must be a JSON object" % field)
    extra = sorted(set(item) - allowed)
    if extra:
        raise InputError("%s has unknown key: %s" % (field, extra[0]))


def to_minutes(value, field):
    if not isinstance(value, str) or not TIME_RE.match(value):
        raise InputError("%s must be a 24-hour HH:MM string" % field)
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def to_int(value, field, low, high, default=None):
    if value is None and default is not None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputError("%s must be an integer" % field)
    if value < low or value > high:
        raise InputError("%s must be between %d and %d" % (field, low, high))
    return value


def to_title(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise InputError("%s must be a non-empty string of at most 200 characters" % field)
    return value.strip()


def clock(minutes):
    return "%02d:%02d" % (minutes // 60, minutes % 60)


def parse(data):
    check_keys(data, TOP_KEYS, "input")
    day_start = to_minutes(data.get("day_start"), "day_start")
    day_end = to_minutes(data.get("day_end"), "day_end")
    if day_end <= day_start:
        raise InputError("day_end must be later than day_start (overnight days are not supported)")
    settings = {
        "buffer_pct": to_int(data.get("buffer_pct"), "buffer_pct", 0, 100, 25),
        "break_every": to_int(data.get("break_every"), "break_every", 15, 240, 90),
        "break_minutes": to_int(data.get("break_minutes"), "break_minutes", 1, 60, 10),
    }
    fixed_raw = data.get("fixed", [])
    if not isinstance(fixed_raw, list) or len(fixed_raw) > 50:
        raise InputError("fixed must be a list of at most 50 objects")
    fixed = []
    for index, item in enumerate(fixed_raw):
        field = "fixed[%d]" % index
        check_keys(item, FIXED_KEYS, field)
        start = to_minutes(item.get("start"), field + ".start")
        end = to_minutes(item.get("end"), field + ".end")
        if end <= start or start < day_start or end > day_end:
            raise InputError("%s must end after it starts and lie inside the day" % field)
        fixed.append({"title": to_title(item.get("title"), field + ".title"),
                      "start": start, "end": end})
    fixed.sort(key=lambda event: event["start"])
    for before, after in zip(fixed, fixed[1:]):
        if after["start"] < before["end"]:
            raise InputError("fixed events overlap")
    tasks_raw = data.get("tasks")
    if not isinstance(tasks_raw, list) or not 1 <= len(tasks_raw) <= 200:
        raise InputError("tasks must be a list of 1 to 200 objects")
    tasks = []
    for index, item in enumerate(tasks_raw):
        field = "tasks[%d]" % index
        check_keys(item, TASK_KEYS, field)
        tasks.append({
            "title": to_title(item.get("title"), field + ".title"),
            "minutes": to_int(item.get("minutes"), field + ".minutes", 1, 480),
            "priority": to_int(item.get("priority"), field + ".priority", 1, 5, 3),
            "order": index,
        })
    return day_start, day_end, settings, fixed, tasks


def build(day_start, day_end, settings, fixed, tasks):
    buffer_pct = settings["buffer_pct"]
    break_every = settings["break_every"]
    break_minutes = settings["break_minutes"]

    windows = []
    cursor = day_start
    for event in fixed:
        if event["start"] > cursor:
            windows.append({"start": cursor, "end": event["start"],
                            "cursor": cursor, "since_break": 0})
        cursor = max(cursor, event["end"])
    if day_end > cursor:
        windows.append({"start": cursor, "end": day_end,
                        "cursor": cursor, "since_break": 0})
    free_minutes = sum(win["end"] - win["start"] for win in windows)

    items = [{"type": "fixed", "title": e["title"], "start": e["start"], "end": e["end"]}
             for e in fixed]
    not_fitting = []
    scheduled_minutes = 0
    block_total = 0
    break_total = 0

    for task in sorted(tasks, key=lambda t: (t["priority"], t["order"])):
        block = (task["minutes"] * (100 + buffer_pct) + 99) // 100
        placed = False
        for win in windows:
            due = win["since_break"] >= break_every
            needed = block + (break_minutes if due else 0)
            if win["cursor"] + needed > win["end"]:
                continue
            if due:
                items.append({"type": "break", "title": "Break",
                              "start": win["cursor"], "end": win["cursor"] + break_minutes})
                win["cursor"] += break_minutes
                win["since_break"] = 0
                break_total += break_minutes
            items.append({"type": "task", "title": task["title"],
                          "priority": task["priority"], "minutes": task["minutes"],
                          "block_minutes": block,
                          "start": win["cursor"], "end": win["cursor"] + block})
            win["cursor"] += block
            win["since_break"] += block
            scheduled_minutes += task["minutes"]
            block_total += block
            placed = True
            break
        if not placed:
            not_fitting.append({"title": task["title"], "priority": task["priority"],
                                "minutes": task["minutes"], "block_minutes": block})

    schedule = []
    for item in sorted(items, key=lambda i: (i["start"], i["end"])):
        row = dict(item)
        row["start"] = clock(item["start"])
        row["end"] = clock(item["end"])
        schedule.append(row)

    totals = {
        "free_minutes": free_minutes,
        "task_minutes_scheduled": scheduled_minutes,
        "block_minutes_scheduled": block_total,
        "break_minutes": break_total,
        "unused_free_minutes": free_minutes - block_total - break_total,
        "task_minutes_not_fitting": sum(row["minutes"] for row in not_fitting),
    }
    return {
        "day": {"start": clock(day_start), "end": clock(day_end),
                "minutes": day_end - day_start},
        "settings": settings,
        "schedule": schedule,
        "not_fitting": not_fitting,
        "totals": totals,
    }


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(json.dumps(
            {"error": "usage: python -I scripts/timebox.py <input.json>"}) + "\n")
        return 2
    try:
        data = read_json(argv[1])
        check_depth(data)
        result = build(*parse(data))
    except InputError as exc:
        sys.stderr.write(json.dumps({"error": str(exc)}) + "\n")
        return 2
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + "\n")
    return 1 if result["not_fitting"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
