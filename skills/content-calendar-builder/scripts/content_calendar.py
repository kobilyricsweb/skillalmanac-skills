"""Build a dated content calendar CSV from a topics file.

Reads one topic per line. A line may be "channel|topic"; a line without "|"
goes to the channel "general". Assigns topics to posting dates on the given
weekdays, skipping holiday dates and capping posts per ISO week. Balances
channels so the same channel never fills two consecutive slots.

Writes a NEW CSV with the header date,weekday,channel,topic. It never
overwrites a file and never writes to the input path. Stdlib only, no
network, no subprocess.

Exit codes: 0 every topic scheduled; 1 some topics unscheduled (listed in
the stdout JSON); 2 usage or input error (one-line JSON on stderr).
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
from collections import deque

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_HORIZON_DAYS = 730
MAX_CHANNEL_LEN = 30
DEFAULT_CHANNEL = "general"
WEEKDAY_ABBR = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAY_LABEL = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class UsageError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, detail)
        self.code = code
        self.detail = detail


class JsonArgParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(json.dumps({"error": "bad_arguments", "detail": message}) + "\n")
        sys.exit(2)


def parse_args(argv):
    p = JsonArgParser(description="Build a dated content calendar CSV.")
    p.add_argument("topics", help="topics file, UTF-8, one topic per line")
    p.add_argument("--start", required=True, help="first possible post date, YYYY-MM-DD")
    p.add_argument("--weekdays", required=True, help="comma list, e.g. Mon,Wed,Fri")
    p.add_argument("--per-week", type=int, default=None,
                   help="max posts per ISO week (default: number of weekdays)")
    p.add_argument("--holidays", default="", help="comma list of YYYY-MM-DD dates to skip")
    p.add_argument("--out", required=True, help="new CSV path; must not already exist")
    return p.parse_args(argv)


def parse_date(value, what):
    try:
        return dt.datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        raise UsageError("bad_date", "%s must be YYYY-MM-DD" % what)


def parse_weekdays(value):
    days = set()
    for part in value.split(","):
        key = part.strip()[:3].lower()
        if not key or key not in WEEKDAY_ABBR or len(part.strip()) < 3:
            raise UsageError("bad_weekday", "weekday must be Mon, Tue, Wed, Thu, Fri, Sat or Sun")
        days.add(WEEKDAY_ABBR.index(key))
    if not days:
        raise UsageError("bad_weekday", "at least one weekday is required")
    return days


def read_topics(path):
    try:
        size = os.path.getsize(path)
    except OSError:
        raise UsageError("input_missing", "topics file cannot be read")
    if size > MAX_INPUT_BYTES:
        raise UsageError("input_too_large", "topics file is over 2 MB")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise UsageError("input_missing", "topics file cannot be read")
    if len(raw) > MAX_INPUT_BYTES:
        raise UsageError("input_too_large", "topics file is over 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise UsageError("input_not_utf8", "topics file is not valid UTF-8")
    topics = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if not s:
            continue
        if "|" in s:
            channel, _, topic = s.partition("|")
            channel = channel.strip()
            topic = topic.strip()
            if not channel or len(channel) > MAX_CHANNEL_LEN or not topic:
                raise UsageError("bad_line", "line %d: channel must be 1-%d characters and topic must not be empty"
                                 % (lineno, MAX_CHANNEL_LEN))
        else:
            channel, topic = DEFAULT_CHANNEL, s
        topics.append({"line": lineno, "channel": channel, "topic": topic})
    if not topics:
        raise UsageError("no_topics", "topics file has no non-empty lines")
    return topics


def build_slots(start, weekdays, per_week, holidays):
    slots = []
    end = start + dt.timedelta(days=MAX_HORIZON_DAYS)
    day = start
    week_key = None
    week_count = 0
    while day < end:
        iso = day.isocalendar()
        key = (iso[0], iso[1])
        if key != week_key:
            week_key = key
            week_count = 0
        if day.weekday() in weekdays and day not in holidays and week_count < per_week:
            slots.append(day)
            week_count += 1
        day += dt.timedelta(days=1)
    return slots


def assign(topics, slots):
    """Return (rows, unscheduled_items, reason_if_unscheduled_remain)."""
    queues = {}
    for t in topics:
        queues.setdefault(t["channel"], deque()).append(t)
    rows = []
    prev = None
    stopped_on_run_limit = False
    for slot in slots:
        best = None
        for ch, q in queues.items():
            if not q or ch == prev:
                continue
            if best is None or len(q) > len(queues[best]):
                best = ch
        if best is None:
            stopped_on_run_limit = any(queues[c] for c in queues)
            break
        rows.append((slot, queues[best].popleft()))
        prev = best
    reason = "channel_run_limit" if stopped_on_run_limit else "horizon_exhausted"
    unscheduled = []
    for ch, q in queues.items():
        for t in q:
            unscheduled.append({"line": t["line"], "channel": t["channel"], "reason": reason})
    unscheduled.sort(key=lambda u: u["line"])
    return rows, unscheduled


def write_calendar(out_path, topics_path, rows):
    if os.path.realpath(out_path) == os.path.realpath(topics_path):
        raise UsageError("output_is_input", "output path is the topics file")
    try:
        fh = open(out_path, "x", newline="", encoding="utf-8")
    except FileExistsError:
        raise UsageError("output_exists", "output file already exists; choose a new path")
    except OSError:
        raise UsageError("output_unwritable", "output path cannot be created")
    with fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "weekday", "channel", "topic"])
        for slot, t in rows:
            writer.writerow([slot.isoformat(), WEEKDAY_LABEL[slot.weekday()], t["channel"], t["topic"]])


def run(argv):
    args = parse_args(argv)
    weekdays = parse_weekdays(args.weekdays)
    start = parse_date(args.start, "--start")
    holidays = set()
    if args.holidays.strip():
        for part in args.holidays.split(","):
            holidays.add(parse_date(part, "--holidays entry"))
    per_week = args.per_week if args.per_week is not None else len(weekdays)
    if per_week < 1 or per_week > len(weekdays):
        raise UsageError("bad_arguments", "--per-week must be between 1 and the number of weekdays")
    topics = read_topics(args.topics)
    slots = build_slots(start, weekdays, per_week, holidays)
    rows, unscheduled = assign(topics, slots)
    write_calendar(args.out, args.topics, rows)
    summary = {
        "scheduled": len(rows),
        "unscheduled": len(unscheduled),
        "first_date": rows[0][0].isoformat() if rows else None,
        "last_date": rows[-1][0].isoformat() if rows else None,
        "unscheduled_items": unscheduled,
    }
    sys.stdout.write(json.dumps(summary) + "\n")
    return 1 if unscheduled else 0


def main():
    try:
        code = run(sys.argv[1:])
    except UsageError as exc:
        sys.stderr.write(json.dumps({"error": exc.code, "detail": exc.detail}) + "\n")
        return 2
    return code


if __name__ == "__main__":
    sys.exit(main())
