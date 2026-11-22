"""Explain 5-field cron expressions and list their next run times in UTC.

Input: one JSON file (--input PATH) holding either one request object or a
list of 1 to 50 request objects. A request object has these keys:
  expression  five fields: minute hour day-of-month month day-of-week
  start       "YYYY-MM-DDTHH:MM", optionally with ":SS" and a trailing "Z"
              or "+00:00". Any other offset is refused. Times are UTC.
  count       optional integer from 1 to 50 (default 5)

Output: one JSON document on stdout. The script reads only the named input
file. It writes no files and does not connect anywhere.

Exit codes: 0 every request returned its requested number of runs;
1 at least one request returned fewer runs (a finding); 2 usage or input
error, reported as a one-line JSON object with an "error" key on stdout.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_NESTING = 8
MAX_ITEMS = 50
MAX_EXPR_LEN = 200
MAX_COUNT = 50
DEFAULT_COUNT = 5
HORIZON_DAYS = 2928  # 8 * 366 days scanned after the start time

MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday"]
MONTH_ABBR = {name[:3].upper(): i for i, name in enumerate(MONTH_NAMES) if i}
DAY_ABBR = {name[:3].upper(): i for i, name in enumerate(DAY_NAMES)}

# field name, lowest value, highest value, name map
FIELD_SPECS = [
    ("minute", 0, 59, {}),
    ("hour", 0, 23, {}),
    ("day_of_month", 1, 31, {}),
    ("month", 1, 12, MONTH_ABBR),
    ("day_of_week", 0, 7, DAY_ABBR),
]
FIELD_TITLES = {
    "minute": "Minute",
    "hour": "Hour",
    "day_of_month": "Day of month",
    "month": "Month",
    "day_of_week": "Day of week",
}
FULL_TEXT = {
    "minute": "every minute",
    "hour": "every hour",
    "day_of_month": "every day of the month",
    "month": "every month",
    "day_of_week": "every day of the week",
}
ALLOWED_KEYS = {"expression", "start", "count"}

START_RE = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2})(?::([0-9]{2}))?"
    r"(?:Z|\+00:00)?")
NUMBER_RE = re.compile(r"[0-9]{1,3}")


class InputError(Exception):
    """Raised for any request that cannot be read or parsed."""


def parse_value(token, fname, low, high, names):
    up = token.upper()
    if up in names:
        value = names[up]
    elif NUMBER_RE.fullmatch(token):
        value = int(token)
    else:
        raise InputError("%s: '%s' is not a number or a name" % (fname, token))
    if value < low or value > high:
        raise InputError("%s: %d is outside %d-%d" % (fname, value, low, high))
    return value


def parse_field(raw, fname, low, high, names):
    if raw == "":
        raise InputError("%s: empty field" % fname)
    values = set()
    for item in raw.split(","):
        if item == "":
            raise InputError("%s: empty list item" % fname)
        base, slash, step_txt = item.partition("/")
        step = 1
        if slash:
            if not NUMBER_RE.fullmatch(step_txt) or int(step_txt) < 1:
                raise InputError("%s: step '%s' must be a whole number of at least 1"
                                 % (fname, step_txt))
            step = int(step_txt)
        if base == "*":
            first, last = low, high
        elif "-" in base:
            lo_txt, _, hi_txt = base.partition("-")
            first = parse_value(lo_txt, fname, low, high, names)
            last = parse_value(hi_txt, fname, low, high, names)
            if first > last:
                raise InputError("%s: range '%s' runs backwards" % (fname, base))
        else:
            first = parse_value(base, fname, low, high, names)
            last = high if slash else first
        values.update(range(first, last + 1, step))
    if fname == "day_of_week":
        values = set(0 if v == 7 else v for v in values)
    return values


def parse_expression(expr):
    if len(expr) > MAX_EXPR_LEN:
        raise InputError("expression is longer than %d characters" % MAX_EXPR_LEN)
    parts = expr.split()
    if len(parts) != 5:
        raise InputError("expected 5 fields, found %d (macros such as @daily are refused)"
                         % len(parts))
    sets = {}
    for (fname, low, high, names), raw in zip(FIELD_SPECS, parts):
        sets[fname] = sorted(parse_field(raw, fname, low, high, names))
    return {
        "sets": sets,
        # Vixie rule: a day field whose text starts with an asterisk is unrestricted.
        "dom_restricted": not parts[2].startswith("*"),
        "dow_restricted": not parts[4].startswith("*"),
    }


def parse_start(txt):
    match = START_RE.fullmatch(txt)
    if not match:
        raise InputError("start must look like YYYY-MM-DDTHH:MM with optional :SS "
                         "and optional Z or +00:00")
    parts = [int(x) if x is not None else 0 for x in match.groups()]
    try:
        return dt.datetime(*parts)
    except ValueError:
        raise InputError("start is not a real UTC date and time")


def day_matches(spec, day):
    dom_ok = day.day in spec["sets"]["day_of_month"]
    dow_ok = (day.weekday() + 1) % 7 in spec["sets"]["day_of_week"]
    if spec["dom_restricted"] and spec["dow_restricted"]:
        return dom_ok or dow_ok
    return dom_ok and dow_ok


def find_runs(spec, start, count):
    # Strictly after the start: the first candidate is the next whole minute.
    t0 = start.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)
    runs = []
    for offset in range(HORIZON_DAYS):
        day = t0.date() + dt.timedelta(days=offset)
        if day.month not in spec["sets"]["month"] or not day_matches(spec, day):
            continue
        for hour in spec["sets"]["hour"]:
            for minute in spec["sets"]["minute"]:
                cand = dt.datetime(day.year, day.month, day.day, hour, minute)
                if cand < t0:
                    continue
                runs.append(cand)
                if len(runs) == count:
                    return runs
    return runs


def label(fname, value):
    if fname == "month":
        return MONTH_NAMES[value]
    if fname == "day_of_week":
        return DAY_NAMES[value]
    return str(value)


def listing(fname, values):
    runs = []
    first = prev = values[0]
    for v in values[1:]:
        if v == prev + 1:
            prev = v
            continue
        runs.append((first, prev))
        first = prev = v
    runs.append((first, prev))
    pieces = []
    for a, b in runs:
        if a == b:
            pieces.append(label(fname, a))
        elif b - a == 1:
            pieces.append("%s and %s" % (label(fname, a), label(fname, b)))
        else:
            pieces.append("%s through %s" % (label(fname, a), label(fname, b)))
    if len(pieces) == 1:
        return pieces[0]
    return ", ".join(pieces[:-1]) + " and " + pieces[-1]


def describe_field(fname, values):
    full = list(range(0, 7)) if fname == "day_of_week" else None
    if full is None:
        low, high = next((lo, hi) for name, lo, hi, _ in FIELD_SPECS if name == fname)
        full = list(range(low, high + 1))
    if values == full:
        return FULL_TEXT[fname]
    return listing(fname, values)


def explain(spec):
    lines = []
    for fname, _, _, _ in FIELD_SPECS:
        lines.append("%s: %s" % (FIELD_TITLES[fname], describe_field(fname, spec["sets"][fname])))
    if spec["dom_restricted"] and spec["dow_restricted"]:
        lines.append("Both day fields are restricted, so a day matches when either "
                     "one matches (OR, the classic Vixie rule).")
    else:
        lines.append("At least one day field starts with an asterisk, so a day must "
                     "match both day fields (AND).")
    return lines


def fmt(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_result(index, obj):
    if not isinstance(obj, dict):
        raise InputError("request must be a JSON object")
    unknown = sorted(str(k) for k in set(obj) - ALLOWED_KEYS)
    if unknown:
        raise InputError("unknown key(s): " + ", ".join(unknown))
    if "expression" not in obj or "start" not in obj:
        raise InputError("expression and start are required")
    expr = obj["expression"]
    if not isinstance(expr, str):
        raise InputError("expression must be a string")
    start_txt = obj["start"]
    if not isinstance(start_txt, str):
        raise InputError("start must be a string")
    count = obj.get("count", DEFAULT_COUNT)
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_COUNT:
        raise InputError("count must be an integer from 1 to %d" % MAX_COUNT)
    start = parse_start(start_txt)
    spec = parse_expression(expr)
    runs = find_runs(spec, start, count)
    findings = []
    if len(runs) < count:
        findings.append("found %d of %d requested runs within %d days after start"
                        % (len(runs), count, HORIZON_DAYS))
    names = [name for name, _, _, _ in FIELD_SPECS]
    return {
        "index": index,
        "expression": expr,
        "start_utc": fmt(start),
        "count_requested": count,
        "fields": {name: ",".join(str(v) for v in spec["sets"][name]) for name in names},
        "day_rule": "or" if spec["dom_restricted"] and spec["dow_restricted"] else "and",
        "explanation": explain(spec),
        "runs_utc": [fmt(r) for r in runs],
        "findings": findings,
    }


def run_request(index, obj):
    try:
        return build_result(index, obj)
    except InputError as exc:
        raise InputError("item %d: %s" % (index, exc))


def json_depth(obj):
    best = 0
    stack = [(obj, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > best:
            best = depth
        if isinstance(node, dict):
            children = list(node.values())
        elif isinstance(node, list):
            children = node
        else:
            continue
        for child in children:
            stack.append((child, depth + 1))
    return best


def load_requests(path):
    if not os.path.isfile(path):
        raise InputError("input file is missing or is not a file")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise InputError("input file is larger than 2 MB")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError("input file cannot be read")
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input file is larger than 2 MB")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError("input file is not valid UTF-8")
    try:
        data = json.loads(text)
    except (ValueError, RecursionError, MemoryError):
        raise InputError("input file is not valid JSON")
    if json_depth(data) > MAX_NESTING:
        raise InputError("input nesting is deeper than %d levels" % MAX_NESTING)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        if not 1 <= len(data) <= MAX_ITEMS:
            raise InputError("a list input must hold 1 to %d requests" % MAX_ITEMS)
        return data
    raise InputError("input must be a JSON object or a list of objects")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Explain cron expressions and list next UTC run times.")
    parser.add_argument("--input", required=True, metavar="PATH",
                        help="JSON file with one request object or a list of up to 50")
    args = parser.parse_args(argv)
    try:
        requests = load_requests(args.input)
        results = [run_request(i, obj) for i, obj in enumerate(requests)]
    except InputError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    findings = sum(len(r["findings"]) for r in results)
    print(json.dumps({"items": len(results), "results": results}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
