#!/usr/bin/env python3
"""Find clashes in a booking list, roster or timetable and propose fixes.

Usage:
    python schedule_conflicts.py BOOKINGS [--rules RULES.json] [--format csv|ics]
           [--resource-from resources|attendee] [--step 15] [--search-days 7]
           [--min-free 30] [--no-suggest] [--delimiter ,]

BOOKINGS is a CSV file or an iCalendar (.ics) file. Nothing is written: the
report is strict JSON on stdout and the input files are only read.

CSV columns (header row required, names case-insensitive): id, resource
(aliases provider, staff, person, employee), room (alias location), client
(alias customer), start, end (or duration_min), buffer_min, units, fixed, title.
Times are ISO 8601 such as 2026-03-02 09:00 or 2026-03-02T09:00+02:00.

iCalendar subset: VEVENT with UID, DTSTART, DTEND or DURATION, SUMMARY,
LOCATION (room), RESOURCES or X-RESOURCE (resource), X-CLIENT, X-BUFFER-MIN,
X-UNITS, X-FIXED, STATUS. Cancelled events are skipped. RRULE and RDATE are not
expanded: only the first instance is checked and the event is listed as
recurring_not_expanded. TZID values are read as local wall-clock time.

Rules JSON keys (unknown keys are an error): default_buffer_min, min_rest_min,
max_booked_min_per_day, utc_offset, require_room, resources, rooms, capacity
({"resources": {}, "rooms": {}}), opening_hours, breaks, dst_change_dates.

Exit codes: 0 no hard or soft conflict, no unassigned and no rejected row;
1 findings; 2 unreadable or invalid input (message on stderr).
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone, time as dtime

SCHEMA_VERSION = 1
DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
# Suggestions are capped so a hopeless roster cannot make the search run for minutes.
MAX_MOVES = 50
# A candidate slot is only compared with bookings within this many days of it; it is
# wider than any realistic rest rule (11 to 12 hours).
NEAR_DAYS = 3
# Free-slot listing stops after this many days to keep the JSON readable.
MAX_FREE_DAYS = 62

SEV = {
    "resource_overlap": "hard", "resource_over_capacity": "hard",
    "room_overlap": "hard", "room_over_capacity": "hard",
    "client_double_booked": "hard", "outside_hours": "hard", "unknown_resource": "hard",
    "unknown_room": "hard",
    "buffer_breach": "soft", "rest_gap": "soft", "break_overlap": "soft",
    "max_daily_exceeded": "soft",
    "spans_midnight": "info", "dst_change_date": "info", "recurring_not_expanded": "info",
}
MOVABLE = {
    "resource_overlap", "resource_over_capacity", "room_overlap", "room_over_capacity",
    "client_double_booked", "outside_hours", "buffer_breach", "rest_gap", "break_overlap",
}
ALIASES = {
    "id": "id", "booking_id": "id", "uid": "id",
    "resource": "resource", "provider": "resource", "staff": "resource",
    "person": "resource", "employee": "resource",
    "room": "room", "location": "room",
    "client": "client", "customer": "client",
    "start": "start", "begin": "start", "dtstart": "start",
    "end": "end", "finish": "end", "dtend": "end",
    "duration_min": "duration_min", "duration": "duration_min",
    "buffer_min": "buffer_min", "buffer": "buffer_min", "turnover_min": "buffer_min",
    "units": "units", "headcount": "units",
    "fixed": "fixed", "locked": "fixed",
    "title": "title",
}
RULE_KEYS = {
    "default_buffer_min", "min_rest_min", "max_booked_min_per_day", "utc_offset",
    "require_room", "resources", "rooms", "capacity", "opening_hours", "breaks",
    "dst_change_dates",
}
TRUE_WORDS = {"1", "yes", "y", "true", "fixed", "locked", "x"}


class InputError(Exception):
    """Raised for anything the caller must fix before the check can run."""


# ---------------------------------------------------------------- helpers

def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M")


def mins(a, b):
    return int((b - a).total_seconds() // 60)


def hhmm(text, where):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(text).strip())
    if not m or int(m.group(2)) > 59:
        raise InputError(f"{where}: '{text}' is not a time like 09:00")
    total = int(m.group(1)) * 60 + int(m.group(2))
    if total > 1440:
        raise InputError(f"{where}: '{text}' is after 24:00")
    return total


def clock(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def parse_intervals(value, where):
    if not isinstance(value, list):
        raise InputError(f"{where}: expected [\"09:00\", \"17:00\"] or a list of such pairs")
    if value and isinstance(value[0], str):
        value = [value]
    out = []
    for pair in value:
        if not (isinstance(pair, list) and len(pair) == 2):
            raise InputError(f"{where}: each interval must be a pair like [\"09:00\", \"12:00\"]")
        s, e = hhmm(pair[0], where), hhmm(pair[1], where)
        if s >= e:
            raise InputError(f"{where}: interval {pair} ends before it starts")
        out.append((s, e))
    return sorted(out)


def parse_offset(text):
    m = re.fullmatch(r"([+-])(\d{2}):(\d{2})", str(text))
    if not m:
        raise InputError(f"rules.utc_offset: '{text}' must look like +02:00")
    delta = timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))
    return timezone(-delta if m.group(1) == "-" else delta)


def nonneg_int(value, where):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InputError(f"{where}: must be a whole number of minutes, 0 or more")
    return value


def load_rules(path):
    raw = {}
    if path:
        try:
            with open(path, encoding="utf-8-sig") as fh:
                raw = json.load(fh)
        except OSError as exc:
            raise InputError(f"cannot read rules file {path}: {exc}")
        except ValueError as exc:
            raise InputError(f"rules file {path} is not valid JSON: {exc}")
        if not isinstance(raw, dict):
            raise InputError("rules file must hold one JSON object")
        unknown = sorted(set(raw) - RULE_KEYS)
        if unknown:
            raise InputError(f"unknown rules key(s) {unknown}; allowed: {sorted(RULE_KEYS)}")
    rules = {
        "default_buffer_min": nonneg_int(raw.get("default_buffer_min", 0), "default_buffer_min"),
        "min_rest_min": nonneg_int(raw.get("min_rest_min", 0), "min_rest_min"),
        "max_booked_min_per_day": nonneg_int(raw.get("max_booked_min_per_day", 0), "max_booked_min_per_day"),
        "offset": parse_offset(raw.get("utc_offset", "+00:00")),
        "require_room": bool(raw.get("require_room", False)),
        "resources": None, "rooms": None,
        "cap_res": {}, "cap_room": {}, "hours": {}, "breaks": {}, "dst": set(),
    }
    for key in ("resources", "rooms"):
        if raw.get(key) is not None:
            if not (isinstance(raw[key], list) and all(isinstance(x, str) for x in raw[key])):
                raise InputError(f"{key}: expected a list of names")
            rules[key] = set(raw[key])
    cap = raw.get("capacity", {})
    if not isinstance(cap, dict) or set(cap) - {"resources", "rooms"}:
        raise InputError("capacity: expected {\"resources\": {...}, \"rooms\": {...}}")
    for key, target in (("resources", "cap_res"), ("rooms", "cap_room")):
        for name, n in (cap.get(key) or {}).items():
            if isinstance(n, bool) or not isinstance(n, int) or n < 1:
                raise InputError(f"capacity.{key}.{name}: must be a whole number of 1 or more")
            rules[target][name] = n
    hours = raw.get("opening_hours", {})
    if not isinstance(hours, dict):
        raise InputError("opening_hours: expected an object keyed by resource name or \"*\"")
    for name, spec in hours.items():
        if not isinstance(spec, dict) or set(spec) - set(DAY_KEYS):
            raise InputError(f"opening_hours.{name}: keys must be among {DAY_KEYS}")
        rules["hours"][name] = {DAY_KEYS.index(d): parse_intervals(v, f"opening_hours.{name}.{d}")
                                for d, v in spec.items()}
    brk = raw.get("breaks", {})
    if not isinstance(brk, dict):
        raise InputError("breaks: expected an object keyed by resource name or \"*\"")
    for name, spec in brk.items():
        rules["breaks"][name] = parse_intervals(spec, f"breaks.{name}")
    for d in raw.get("dst_change_dates", []):
        try:
            rules["dst"].add(datetime.strptime(str(d), "%Y-%m-%d").date())
        except ValueError:
            raise InputError(f"dst_change_dates: '{d}' is not YYYY-MM-DD")
    return rules


def parse_dt(text, offset):
    """Return (naive datetime, was_timezone_aware). Aware values go to the fixed offset."""
    s = str(text or "").strip()
    if not s:
        raise ValueError("empty")
    if s[-1] in "Zz":
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is not None:
        return dt.astimezone(offset).replace(tzinfo=None), True
    return dt, False


# ---------------------------------------------------------------- loading

def make_booking(raw, n, ctx, rules):
    ident = (raw.get("id") or "").strip() or f"row{n}"

    def reject(reason):
        ctx["rejected"].append({"row": n, "id": ident, "reason": reason})
        return None

    try:
        start, a1 = parse_dt(raw.get("start"), rules["offset"])
    except ValueError:
        return reject("bad_or_missing_start")
    if raw.get("end"):
        try:
            end, a2 = parse_dt(raw["end"], rules["offset"])
        except ValueError:
            return reject("bad_end")
        if a1 != a2:
            return reject("start_and_end_differ_in_timezone_info")
    else:
        try:
            dur = int(str(raw.get("duration_min", "")).strip())
        except ValueError:
            return reject("missing_end_and_duration")
        if dur <= 0:
            return reject("zero_or_negative_duration")
        end, a2 = start + timedelta(minutes=dur), a1
    if start.second or end.second or start.microsecond or end.microsecond:
        return reject("seconds_not_supported")
    if end < start:
        return reject("end_before_start")
    if end == start:
        return reject("zero_duration")
    if ident in ctx["ids"]:
        return reject("duplicate_id")
    try:
        buf = int(str(raw.get("buffer_min") or rules["default_buffer_min"]).strip())
        if buf < 0:
            raise ValueError
    except ValueError:
        return reject("bad_buffer_min")
    try:
        units = int(str(raw.get("units") or 1).strip())
        if units < 1:
            raise ValueError
    except ValueError:
        return reject("bad_units")
    ctx["ids"].add(ident)
    ctx["aware" if a1 else "naive"] += 1
    return {
        "id": ident, "resource": (raw.get("resource") or "").strip(),
        "room": (raw.get("room") or "").strip(), "client": (raw.get("client") or "").strip(),
        "start": start, "end": end, "dur": mins(start, end), "buffer": buf, "units": units,
        "fixed": str(raw.get("fixed") or "").strip().lower() in TRUE_WORDS,
        "title": (raw.get("title") or "").strip(), "row": n,
        "recurring": bool(raw.get("recurring")),
    }


def read_text(path):
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}")
    if not data.strip():
        raise InputError(f"{path} is empty")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError(f"{path} is not UTF-8 text; re-save it as UTF-8")


def load_csv(path, delimiter):
    text = read_text(path)
    head = text.splitlines()[0]
    if delimiter is None:
        delimiter = "\t" if "\t" in head and "," not in head else (";" if ";" in head and "," not in head else ",")
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    header = [re.sub(r"\s+", "_", h.strip().lower()) for h in rows[0]]
    cols = {i: ALIASES[h] for i, h in enumerate(header) if h in ALIASES}
    mapped = set(cols.values())
    if "start" not in mapped or not ({"end", "duration_min"} & mapped):
        raise InputError("CSV needs a header row with start and end (or duration_min) columns; "
                         f"found {header}")
    out = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        out.append({cols[i]: r[i] for i in cols if i < len(r)})
    ignored = [h for h in header if h and h not in ALIASES]
    return out, ignored


def split_ics_line(line):
    """Split NAME;PARAM=V:VALUE at the first colon that is not inside quotes."""
    quoted = False
    for i, ch in enumerate(line):
        if ch == '"':
            quoted = not quoted
        elif ch == ":" and not quoted:
            return line[:i], line[i + 1:]
    return line, ""


def ics_text(value):
    return (value.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",")
            .replace("\\;", ";").replace("\\\\", "\\"))


def ics_dt(value, params, ctx):
    v = value.strip()
    if params.get("VALUE", "").upper() == "DATE" or re.fullmatch(r"\d{8}", v):
        return f"{v[0:4]}-{v[4:6]}-{v[6:8]}" if len(v) == 8 else v
    m = re.fullmatch(r"(\d{8})T(\d{2})(\d{2})(\d{2})?(Z?)", v)
    if not m:
        return v
    d = m.group(1)
    if params.get("TZID") and not m.group(5):
        ctx["tzids"].add(params["TZID"])
    return f"{d[0:4]}-{d[4:6]}-{d[6:8]}T{m.group(2)}:{m.group(3)}:{m.group(4) or '00'}{'Z' if m.group(5) else ''}"


def load_ics(path, resource_from, ctx):
    text = read_text(path)
    lines = []
    for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if ln[:1] in (" ", "\t") and lines:
            lines[-1] += ln[1:]
        else:
            lines.append(ln)
    events, cur, nested = [], None, None
    for ln in lines:
        if not ln.strip():
            continue
        up = ln.strip().upper()
        if up == "BEGIN:VEVENT":
            cur = {}
        elif up == "END:VEVENT":
            if cur is not None:
                events.append(cur)
            cur = None
        elif cur is not None and up.startswith("BEGIN:"):
            nested = up[6:]
        elif cur is not None and nested and up == "END:" + nested:
            nested = None
        elif cur is not None and not nested:
            left, value = split_ics_line(ln)
            parts = left.split(";")
            params = {}
            for p in parts[1:]:
                k, _, v = p.partition("=")
                params[k.upper()] = v.strip('"')
            cur.setdefault(parts[0].upper(), []).append((params, value))
    if not events:
        raise InputError(f"{path} contains no VEVENT")
    out = []
    for n, ev in enumerate(events, 1):
        def first(name):
            return ev[name][0] if name in ev else ({}, "")
        uid = ics_text(first("UID")[1]).strip() or f"event{n}"
        if first("STATUS")[1].strip().upper() == "CANCELLED":
            ctx["skipped"].append({"row": n, "id": uid, "reason": "cancelled"})
            continue
        raw = {"id": uid, "title": ics_text(first("SUMMARY")[1]), "room": ics_text(first("LOCATION")[1]),
               "client": ics_text(first("X-CLIENT")[1]), "buffer_min": first("X-BUFFER-MIN")[1],
               "units": first("X-UNITS")[1], "fixed": first("X-FIXED")[1],
               "recurring": "RRULE" in ev or "RDATE" in ev}
        if resource_from == "attendee":
            params, value = first("ATTENDEE")
            raw["resource"] = ics_text(params.get("CN") or re.sub(r"(?i)^mailto:", "", value))
        else:
            raw["resource"] = ics_text((first("RESOURCES")[1] or first("X-RESOURCE")[1]).split(",")[0])
        p, v = first("DTSTART")
        raw["start"] = ics_dt(v, p, ctx)
        date_only = bool(v) and (p.get("VALUE", "").upper() == "DATE" or re.fullmatch(r"\d{8}", v.strip()))
        if "DTEND" in ev:
            p2, v2 = first("DTEND")
            raw["end"] = ics_dt(v2, p2, ctx)
        elif "DURATION" in ev:
            m = re.fullmatch(r"P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?",
                             first("DURATION")[1].strip().upper())
            if not m or m.group(5):
                raw["duration_min"] = "bad"
            else:
                w, d, h, mi = (int(x or 0) for x in m.groups()[:4])
                raw["duration_min"] = str(w * 10080 + d * 1440 + h * 60 + mi)
        elif date_only:
            raw["duration_min"] = "1440"
        out.append((n, raw))
    return out


# ---------------------------------------------------------------- checks

def conflict(kind, ids, **kw):
    c = {"type": kind, "severity": SEV[kind], "ids": sorted(ids), "resource": None, "room": None,
         "client": None, "start": None, "end": None, "overlap_min": None, "shortfall_min": None,
         "excess_min": None, "detail": ""}
    c.update(kw)
    return c


def sweep(group, cap, use_units):
    """Return [start, end, ids, minutes] spans where concurrent load exceeds cap."""
    events = []
    for b in group:
        w = b["units"] if use_units else 1
        events.append((b["start"], 1, b["id"], w))
        events.append((b["end"], 0, b["id"], w))
    events.sort(key=lambda e: (e[0], e[1], e[2]))
    active, total, prev, segs = {}, 0, None, []
    for t, kind, ident, w in events:
        if prev is not None and t > prev and total > cap:
            segs.append([prev, t, set(active), mins(prev, t)])
        if kind == 1:
            active[ident] = w
            total += w
        else:
            del active[ident]
            total -= w
        prev = t
    merged = []
    for s in segs:
        if merged and merged[-1][1] == s[0]:
            merged[-1] = [merged[-1][0], s[1], merged[-1][2] | s[2], merged[-1][3] + s[3]]
        else:
            merged.append(s)
    return merged


def group_by(bookings, key):
    out = {}
    for b in bookings:
        if b[key]:
            out.setdefault(b[key], []).append(b)
    for g in out.values():
        g.sort(key=lambda b: (b["start"], b["end"], b["id"]))
    return out


def lookup(table, name):
    return table.get(name, table.get("*"))


def find_conflicts(bookings, rules):
    found = []
    by_res, by_room, by_client = (group_by(bookings, k) for k in ("resource", "room", "client"))
    for scope, groups, caps in (("resource", by_res, rules["cap_res"]), ("room", by_room, rules["cap_room"])):
        for name, grp in groups.items():
            listed = name in caps
            for s, e, ids, m in sweep(grp, caps.get(name, 1), listed):
                kind = f"{scope}_over_capacity" if listed else f"{scope}_overlap"
                found.append(conflict(kind, ids, start=iso(s), end=iso(e), overlap_min=m,
                                      detail=f"{scope} {name}: {len(ids)} bookings exceed "
                                             f"{'capacity ' + str(caps[name]) if listed else 'one at a time'} for {m} min",
                                      **{scope: name}))
            # buffer breaches: a later booking starts after the earlier ends but inside its buffer
            for i, a in enumerate(grp):
                for b in grp[i + 1:]:
                    if b["start"] >= a["end"] + timedelta(minutes=a["buffer"]):
                        break
                    if b["start"] >= a["end"]:
                        short = a["buffer"] - mins(a["end"], b["start"])
                        found.append(conflict("buffer_breach", [a["id"], b["id"]], start=iso(a["end"]),
                                              end=iso(b["start"]), shortfall_min=short,
                                              detail=f"{scope} {name}: {a['id']} needs {a['buffer']} min after it, "
                                                     f"{b['id']} starts {mins(a['end'], b['start'])} min later",
                                              **{scope: name}))
    for name, grp in by_client.items():
        for s, e, ids, m in sweep(grp, 1, False):
            found.append(conflict("client_double_booked", ids, client=name, start=iso(s), end=iso(e),
                                  overlap_min=m, detail=f"client {name} is in {len(ids)} bookings at once"))
    for name, grp in by_res.items():
        last = None
        for b in grp:
            if (rules["min_rest_min"] and last and b["start"] >= last["end"]
                    and b["start"].date() != last["start"].date()):
                gap = mins(last["end"], b["start"])
                if gap < rules["min_rest_min"]:
                    found.append(conflict("rest_gap", [last["id"], b["id"]], resource=name, start=iso(last["end"]),
                                          end=iso(b["start"]), shortfall_min=rules["min_rest_min"] - gap,
                                          detail=f"{name}: {gap} min between {last['id']} and {b['id']}, "
                                                 f"rule is {rules['min_rest_min']}"))
            if last is None or b["end"] > last["end"]:
                last = b
        if rules["max_booked_min_per_day"]:
            days = {}
            for b in grp:
                days.setdefault(b["start"].date(), []).append(b)
            for d, items in days.items():
                total = sum(b["dur"] for b in items)
                if total > rules["max_booked_min_per_day"]:
                    found.append(conflict("max_daily_exceeded", [b["id"] for b in items], resource=name,
                                          start=iso(min(b["start"] for b in items)), end=iso(max(b["end"] for b in items)),
                                          excess_min=total - rules["max_booked_min_per_day"],
                                          detail=f"{name} on {d}: {total} min booked, limit {rules['max_booked_min_per_day']}"))
    for b in bookings:
        day0 = datetime.combine(b["start"].date(), dtime.min)
        s_min = mins(day0, b["start"])
        e_min = s_min + b["dur"]
        span = e_min > 1440
        base = dict(resource=b["resource"] or None, room=b["room"] or None, start=iso(b["start"]), end=iso(b["end"]))
        if span:
            found.append(conflict("spans_midnight", [b["id"]], detail=f"{b['id']} runs past midnight; "
                                  "it cannot fit a single-day opening interval, so leave opening_hours "
                                  "out for resources that work overnight", **base))
        if b["recurring"]:
            found.append(conflict("recurring_not_expanded", [b["id"]],
                                  detail=f"{b['id']} has a recurrence rule; only its first instance is checked", **base))
        if rules["dst"] & {b["start"].date(), b["end"].date()}:
            found.append(conflict("dst_change_date", [b["id"]],
                                  detail=f"{b['id']} falls on a listed clock-change date; confirm its real duration", **base))
        if rules["resources"] is not None and b["resource"] and b["resource"] not in rules["resources"]:
            found.append(conflict("unknown_resource", [b["id"]], detail=f"resource {b['resource']} is not in the rules list", **base))
        if rules["rooms"] is not None and b["room"] and b["room"] not in rules["rooms"]:
            found.append(conflict("unknown_room", [b["id"]], detail=f"room {b['room']} is not in the rules list", **base))
        hours = lookup(rules["hours"], b["resource"])
        if hours is not None:
            ivs = hours.get(b["start"].weekday(), [])
            if not any(s <= s_min and e_min <= e for s, e in ivs):
                shown = ", ".join(f"{clock(s)}-{clock(e)}" for s, e in ivs) or "closed"
                found.append(conflict("outside_hours", [b["id"]],
                                      detail=f"{b['id']} {clock(s_min)}-{clock(e_min)} vs open {shown} on {DAY_KEYS[b['start'].weekday()]}",
                                      **base))
        for bs, be in lookup(rules["breaks"], b["resource"]) or []:
            if s_min < be and bs < e_min:
                found.append(conflict("break_overlap", [b["id"]], overlap_min=min(e_min, be) - max(s_min, bs),
                                      detail=f"{b['id']} overlaps the {clock(bs)}-{clock(be)} break", **base))
    found.sort(key=lambda c: (c["start"] or "", c["type"], c["ids"]))
    return found


def free_slots(bookings, rules, min_free, notes):
    if not bookings:
        return {}
    first = min(b["start"] for b in bookings).date()
    last = max(b["end"] - timedelta(minutes=1) for b in bookings).date()
    if (last - first).days + 1 > MAX_FREE_DAYS:
        last = first + timedelta(days=MAX_FREE_DAYS - 1)
        notes.append(f"free_slots limited to the first {MAX_FREE_DAYS} days")
    names = {b["resource"] for b in bookings if b["resource"]} | (rules["resources"] or set())
    out = {}
    for name in sorted(names):
        hours = lookup(rules["hours"], name)
        if hours is None:
            continue
        mine = [b for b in bookings if b["resource"] == name]
        slots = []
        day = first
        while day <= last:
            base = datetime.combine(day, dtime.min)
            for s, e in hours.get(day.weekday(), []):
                blocked = [(b["start"], b["end"] + timedelta(minutes=b["buffer"])) for b in mine]
                blocked += [(base + timedelta(minutes=bs), base + timedelta(minutes=be))
                            for bs, be in lookup(rules["breaks"], name) or []]
                cur, stop = base + timedelta(minutes=s), base + timedelta(minutes=e)
                for bs, be in sorted(blocked):
                    if be <= cur or bs >= stop:
                        continue
                    if bs - cur >= timedelta(minutes=min_free):
                        slots.append({"start": iso(cur), "end": iso(bs), "minutes": mins(cur, bs)})
                    cur = max(cur, be)
                if stop - cur >= timedelta(minutes=min_free):
                    slots.append({"start": iso(cur), "end": iso(stop), "minutes": mins(cur, stop)})
            day += timedelta(days=1)
        out[name] = slots
    return out


def find_slot(b, others, rules, step, days):
    related = [o for o in others if o["id"] != b["id"] and (
        (b["resource"] and o["resource"] == b["resource"]) or (b["room"] and o["room"] == b["room"])
        or (b["client"] and o["client"] == b["client"]))]
    dur = timedelta(minutes=b["dur"])
    for k in range(0, days * 1440 // step + 1):
        for sign in ((1,) if k == 0 else (1, -1)):  # on a tie the later slot wins
            start = b["start"] + timedelta(minutes=sign * k * step)
            if (start.date() != (start + dur - timedelta(minutes=1)).date()
                    and b["start"].date() == (b["end"] - timedelta(minutes=1)).date()):
                continue  # never turn a same-day booking into an overnight one
            trial = dict(b, start=start, end=start + dur)
            near = [o for o in related if abs((o["start"] - start).days) <= NEAR_DAYS]
            bad = [c for c in find_conflicts([trial] + near, rules) if c["type"] in MOVABLE and b["id"] in c["ids"]]
            if not bad:
                return start
    return None


def suggest(bookings, rules, step, days, notes):
    sched = {b["id"]: dict(b) for b in bookings}
    moves, unmovable, stuck, failed = [], [], set(), set()
    for _ in range(MAX_MOVES * 4 + len(bookings) * 2):
        todo = [c for c in find_conflicts(list(sched.values()), rules)
                if c["type"] in MOVABLE and (c["type"], tuple(c["ids"])) not in stuck]
        if not todo:
            break
        if len(moves) >= MAX_MOVES:
            notes.append(f"suggestions stopped after {MAX_MOVES} moves")
            break
        c = todo[0]
        key = (c["type"], tuple(c["ids"]))
        cands = [sched[i] for i in c["ids"] if not sched[i]["fixed"] and i not in failed]
        if not cands:
            stuck.add(key)
            unmovable.append({"type": c["type"], "ids": c["ids"],
                              "reason": "every booking involved is fixed or has no free slot in the search window"})
            continue
        pick = max(cands, key=lambda b: (b["start"], b["id"]))
        new = find_slot(pick, list(sched.values()), rules, step, days)
        if new is None:
            failed.add(pick["id"])
            continue
        old = sched[pick["id"]]
        moves.append({"order": len(moves) + 1, "id": pick["id"], "resource": pick["resource"] or None,
                      "room": pick["room"] or None, "from_start": iso(old["start"]), "to_start": iso(new),
                      "to_end": iso(new + timedelta(minutes=pick["dur"])), "shift_min": mins(old["start"], new),
                      "resolves": c["type"]})
        old["start"], old["end"] = new, new + timedelta(minutes=pick["dur"])
    left = find_conflicts(list(sched.values()), rules)
    remaining = {"hard": sum(c["severity"] == "hard" for c in left), "soft": sum(c["severity"] == "soft" for c in left)}
    return moves, unmovable, remaining


# ---------------------------------------------------------------- main

def build_report(args):
    rules = load_rules(args.rules)
    ctx = {"rejected": [], "skipped": [], "ids": set(), "aware": 0, "naive": 0, "tzids": set()}
    fmt = args.format or ("ics" if args.bookings.lower().endswith(".ics") else "csv")
    notes = []
    if fmt == "ics":
        raw_rows = load_ics(args.bookings, args.resource_from, ctx)
    else:
        rows, ignored = load_csv(args.bookings, args.delimiter)
        raw_rows = list(enumerate(rows, 1))
        if ignored:
            notes.append(f"ignored CSV columns: {ignored}")
    bookings = []
    for n, raw in raw_rows:
        b = make_booking(raw, n, ctx, rules)
        if b:
            bookings.append(b)
    if ctx["aware"] and ctx["naive"]:
        raise InputError("some times carry a timezone or Z and some do not; make them all one kind")
    if len(ctx["tzids"]) > 1:
        raise InputError(f"events use several TZID values {sorted(ctx['tzids'])}; convert them to one zone first")
    if ctx["aware"]:
        notes.append("times with a timezone were converted with the fixed utc_offset from the rules (default +00:00); "
                     "daylight saving is not tracked")
    if ctx["tzids"]:
        notes.append(f"TZID {sorted(ctx['tzids'])[0]} read as local wall-clock time")
    if not bookings and not ctx["rejected"]:
        raise InputError("no bookings found")
    unassigned = [{"id": b["id"], "missing": "resource"} for b in bookings if not b["resource"]]
    if rules["require_room"]:
        unassigned += [{"id": b["id"], "missing": "room"} for b in bookings if not b["room"]]
    conflicts = find_conflicts(bookings, rules)
    moves, unmovable, remaining = ([], [], None)
    if not args.no_suggest and bookings:
        moves, unmovable, remaining = suggest(bookings, rules, args.step, args.search_days, notes)
    slots = free_slots(bookings, rules, args.min_free, notes)
    if not slots and bookings:
        notes.append("no opening_hours rules matched any resource, so free_slots is empty")
    sev = {k: sum(c["severity"] == k for c in conflicts) for k in ("hard", "soft", "info")}
    findings = sev["hard"] + sev["soft"] + len(unassigned) + len(ctx["rejected"])
    report = {
        "schema_version": SCHEMA_VERSION, "command": "check", "input_format": fmt,
        "bookings_used": len(bookings), "rejected_rows": ctx["rejected"], "skipped": ctx["skipped"],
        "conflicts": conflicts, "unassigned": unassigned,
        "suggested_moves": moves, "unmovable": unmovable,
        "remaining_after_moves": remaining, "free_slots": slots,
        "summary": {"hard": sev["hard"], "soft": sev["soft"], "info": sev["info"],
                    "unassigned": len(unassigned), "rejected": len(ctx["rejected"]),
                    "verdict": "conflicts" if findings else "clean"},
        "notes": notes,
    }
    return report, (1 if findings else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a booking list, roster or timetable for clashes.")
    ap.add_argument("bookings")
    ap.add_argument("--rules")
    ap.add_argument("--format", choices=["csv", "ics"])
    ap.add_argument("--resource-from", choices=["resources", "attendee"], default="resources")
    ap.add_argument("--step", type=int, default=15)
    ap.add_argument("--search-days", type=int, default=7)
    ap.add_argument("--min-free", type=int, default=30)
    ap.add_argument("--no-suggest", action="store_true")
    ap.add_argument("--delimiter")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if args.step < 1 or args.search_days < 0 or args.min_free < 1:
            raise InputError("--step and --min-free must be 1 or more, --search-days 0 or more")
        report, code = build_report(args)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
