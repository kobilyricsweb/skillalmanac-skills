#!/usr/bin/env python3
"""overlap_windows.py: meeting windows across time zones, DST-aware, ranked for fairness.

Usage:
    python overlap_windows.py plan INPUT.json [--out REPORT.json] [--force] [--max-windows N]
    python overlap_windows.py check-zones NAME [NAME ...] [--date YYYY-MM-DD]

Reads: the INPUT.json you name (see SKILL.md for the fields). Uses only the Python
standard library; zone data comes from `zoneinfo`. No network is used.
Writes: nothing, unless --out is given. --out writes one JSON report to that path;
it refuses an existing file without --force and ALWAYS refuses the input file itself,
even with --force. stdout always carries the same JSON report.

Exit codes:
    0  plan produced and clean (every working date has a full-overlap slot, no DST drift)
    1  plan produced with findings (a DST change shifts a pair of people relative to
       each other, or a date has no slot where everyone is inside working hours),
       or check-zones found a zone that cannot be used
    2  bad input (unknown or ambiguous zone, bad time, bad date, no tz database, ...)

Windows needs the PyPI package `tzdata` for IANA names. Without it this script says so
and exits 2, unless every participant supplies a fixed `utc_offset` (then DST is NOT tracked).
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime, time, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python older than 3.9
    ZoneInfo = None

SCHEMA_VERSION = 1

# A slot is "all_inside" only when every person keeps at least this many minutes between
# the meeting and the edge of their working day. 60 matches the common "not first or
# last hour" rule of thumb for a planned call.
EDGE_MINUTES = 60
# Inside hours but closer than EDGE_MINUTES to an edge costs a quarter of a minute per
# missing minute, so being on the edge is a small cost and being outside is a large one.
EDGE_WEIGHT = 0.25
# Cost of a meeting on someone's day off or holiday: a full day of minutes.
DAY_OFF_COST = 1440
DEFAULT_MEETING = 60
DEFAULT_STEP = 30  # use 15 when a participant is in a :45 zone such as Asia/Kathmandu
DEFAULT_MAX_WINDOWS = 3
# For the rotation, a date may use any slot of its best quality whose worst single cost
# is within this many minutes of that date's best, so that the burden can move around.
ROTATION_SLACK = 120
MAX_RANGE_DAYS = 366
MAX_PARTICIPANTS = 20
DEFAULT_START, DEFAULT_END = "09:00", "17:00"
DEFAULT_DAYS_OFF = ("sat", "sun")
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
QUALITY_RANK = {"all_inside": 0, "edge": 1, "one_outside": 2, "several_outside": 3, "day_off": 4}

# Abbreviations are refused: they name no rule set. Candidates are shown to help the user pick.
AMBIGUOUS = {
    "IST": ["Asia/Kolkata (India)", "Asia/Jerusalem (Israel)", "Europe/Dublin (Irish Summer Time)"],
    "CST": ["America/Chicago (US Central)", "Asia/Shanghai (China)", "America/Havana (Cuba)"],
    "BST": ["Europe/London (British Summer Time)", "Asia/Dhaka (Bangladesh)"],
    "EST": ["America/New_York (US Eastern, DST-aware)", "America/Panama (fixed -05:00)", "Australia/Sydney (Eastern Standard Time)"],
    "PST": ["America/Los_Angeles (US Pacific)", "Asia/Manila (Philippines)"],
    "MST": ["America/Denver (US Mountain, DST)", "America/Phoenix (US Arizona, no DST)"],
    "AST": ["America/Halifax (Atlantic)", "Asia/Riyadh (Arabia)"],
    "GST": ["Asia/Dubai (Gulf)", "Atlantic/South_Georgia"],
    "SST": ["Pacific/Pago_Pago (Samoa)", "Asia/Singapore (Singapore Standard Time)"],
    "CET": ["Europe/Berlin", "Europe/Paris", "Europe/Madrid (all observe EU DST)"],
    "EET": ["Europe/Helsinki", "Europe/Athens", "Africa/Cairo (rules differ)"],
}

RE_ZONE = re.compile(r"^[A-Za-z0-9_+\-]+(/[A-Za-z0-9_+\-]+){0,2}$")


class InputError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


# ----------------------------------------------------------------------------- parsing

def parse_hm(text, field, allow_24=False):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(text).strip())
    if not m:
        raise InputError("bad_time", "%s must look like HH:MM, got %r" % (field, text))
    h, mi = int(m.group(1)), int(m.group(2))
    if mi > 59 or h > 24 or (h == 24 and (mi != 0 or not allow_24)):
        raise InputError("bad_time", "%s is not a valid time of day: %r" % (field, text))
    return h * 60 + mi


def parse_offset(text, who):
    m = re.fullmatch(r"([+-])(\d{1,2}):(\d{2})", str(text).strip())
    if not m or int(m.group(2)) > 14 or int(m.group(3)) > 59:
        raise InputError("bad_offset", "%s: utc_offset must look like +05:30 or -08:00, got %r" % (who, text))
    delta = timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))
    return timezone(delta if m.group(1) == "+" else -delta)


def parse_date(text, field):
    try:
        return date.fromisoformat(str(text))
    except ValueError:
        raise InputError("bad_date", "%s must be YYYY-MM-DD, got %r" % (field, text))


def tzdb_ok(simulate_missing=False):
    if simulate_missing or ZoneInfo is None:
        return False
    try:
        ZoneInfo("UTC")
        return True
    except Exception:
        return False


def zone_problem(zone):
    """Return None when the name looks like an IANA key, else (code, message)."""
    if zone != "UTC" and "/" not in zone:
        key = zone.upper()
        hint = AMBIGUOUS.get(key)
        if hint:
            msg = "%r is an abbreviation that names several rule sets (%s). Ask the user for an IANA zone such as Area/City." % (zone, "; ".join(hint))
        else:
            msg = "%r is an abbreviation, not an IANA zone. Ask the user for the city-based name (Area/City)." % zone
        return ("ambiguous_zone", msg)
    if not RE_ZONE.match(zone):
        return ("unknown_zone", "%r is not a valid zone key" % zone)
    return None


def build_participant(raw, db_ok, global_holidays, warnings):
    if not isinstance(raw, dict):
        raise InputError("bad_input", "each participant must be an object")
    name = str(raw.get("name", "")).strip()
    if not name:
        raise InputError("bad_input", "every participant needs a non-empty name")
    zone = raw.get("zone")
    offset = raw.get("utc_offset")
    tz, source, label = None, None, None
    if zone:
        zone = str(zone).strip()
        prob = zone_problem(zone)
        if prob:
            raise InputError(prob[0], "%s: %s" % (name, prob[1]))
        if zone.startswith("Etc/GMT") and re.search(r"[+-]\d", zone):
            warnings.append({"code": "etc_gmt_sign_inverted", "participant": name,
                             "message": "%s: Etc/GMT+5 means UTC-5 (the sign is inverted) and never has DST; confirm this is intended." % zone})
        if db_ok:
            try:
                tz = ZoneInfo(zone)
            except Exception:
                raise InputError("unknown_zone", "%s: zone %r is not in the tz database (typo, or a retired name)" % (name, zone))
            source, label = "iana", zone
        elif offset:
            tz = parse_offset(offset, name)
            source, label = "fixed_offset", str(offset)
            warnings.append({"code": "fixed_offset_no_dst_tracking", "participant": name,
                             "message": "No tz database available; %s uses the fixed offset %s for every date, so DST changes are NOT tracked." % (name, offset)})
        else:
            raise InputError("no_tz_database", "No tz database available on this system (on Windows install the PyPI package tzdata), "
                             "or give %s a fixed utc_offset such as +05:30 (DST will then not be tracked)." % name)
    elif offset:
        tz = parse_offset(offset, name)
        source, label = "fixed_offset", str(offset)
        warnings.append({"code": "fixed_offset_no_dst_tracking", "participant": name,
                         "message": "%s has only a fixed offset; DST changes are NOT tracked." % name})
    else:
        raise InputError("bad_input", "%s needs a zone (IANA name) or a utc_offset" % name)

    if "work_start" in raw or "work_end" in raw:
        ws = parse_hm(raw.get("work_start", DEFAULT_START), name + " work_start")
        we = parse_hm(raw.get("work_end", DEFAULT_END), name + " work_end", allow_24=True)
    else:
        ws, we = parse_hm(DEFAULT_START, "work_start"), parse_hm(DEFAULT_END, "work_end")
        warnings.append({"code": "default_hours_used", "participant": name,
                         "message": "%s gave no working hours; %s-%s assumed." % (name, DEFAULT_START, DEFAULT_END)})
    if ws == we:
        raise InputError("bad_time", "%s: work_start equals work_end; use 24-hour shifts only by listing the real hours" % name)
    days_off = raw.get("days_off", list(DEFAULT_DAYS_OFF))
    offs = set()
    for d in days_off:
        key = str(d).strip().lower()[:3]
        if key not in DAYS:
            raise InputError("bad_day", "%s: days_off entry %r is not a weekday name" % (name, d))
        offs.add(key)
    holidays = set(global_holidays)
    for h in raw.get("holidays", []):
        holidays.add(parse_date(h, name + " holidays").isoformat())
    return {"name": name, "tz": tz, "source": source, "zone": label, "ws": ws, "we": we,
            "days_off": offs, "holidays": holidays}


# ----------------------------------------------------------------------------- core maths

def is_off(p, d):
    return DAYS[d.weekday()] in p["days_off"] or d.isoformat() in p["holidays"]


def minutes(delta):
    return delta.total_seconds() / 60.0


def assess(p, ls, le):
    """Judge one meeting [ls, le) in p's local wall-clock time. Shifts belong to the date they start on."""
    ld = ls.date()
    best_short = None
    in_off_nominal = False
    for k in (-1, 0, 1):
        d = ld + timedelta(days=k)
        base = datetime.combine(d, time())
        s = base + timedelta(minutes=p["ws"])
        e = base + timedelta(minutes=p["we"] if p["we"] > p["ws"] else p["we"] + 1440)
        if is_off(p, d):
            if s <= ls < e:
                in_off_nominal = True
            continue
        if ls >= s and le <= e:
            margin = min(minutes(ls - s), minutes(e - le))
            inside_ok = margin >= EDGE_MINUTES
            return {"status": "inside" if inside_ok else "edge", "margin": margin, "shortfall": None, "day_off": False,
                    "pain": 0.0 if inside_ok else (EDGE_MINUTES - margin) * EDGE_WEIGHT}
        short = max(0.0, minutes(s - ls)) + max(0.0, minutes(le - e))
        if best_short is None or short < best_short:
            best_short = short
    day_off = in_off_nominal or is_off(p, ld)
    if best_short is None:
        best_short = float(DAY_OFF_COST)
    pain = max(best_short, float(DAY_OFF_COST)) if day_off else best_short
    return {"status": "day_off" if day_off else "outside", "margin": None, "shortfall": best_short,
            "day_off": day_off, "pain": pain}


def fmt_local(dt_utc, tz):
    loc = dt_utc.astimezone(tz)
    off = loc.utcoffset()
    total = int(minutes(off))
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return "%s%s%02d:%02d" % (loc.strftime("%Y-%m-%dT%H:%M"), sign, total // 60, total % 60)


def fmt_utc(dt_utc):
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_slot(start_utc, length, people):
    end_utc = start_utc + timedelta(minutes=length)
    results = []
    for p in people:
        ls = start_utc.astimezone(p["tz"]).replace(tzinfo=None)
        le = end_utc.astimezone(p["tz"]).replace(tzinfo=None)
        results.append(assess(p, ls, le))
    if any(r["day_off"] for r in results):
        quality = "day_off"
    else:
        n_out = sum(1 for r in results if r["status"] == "outside")
        if n_out == 0:
            quality = "edge" if any(r["status"] == "edge" for r in results) else "all_inside"
        elif n_out == 1:
            quality = "one_outside"
        else:
            quality = "several_outside"
    pains = [r["pain"] for r in results]
    margins = [r["margin"] for r in results if r["margin"] is not None]
    return {"start": start_utc, "end": end_utc, "results": results, "quality": quality,
            "sig": tuple(i for i, r in enumerate(results) if r["status"] in ("outside", "day_off")),
            "max_pain": max(pains), "sum_pain": sum(pains), "min_margin": min(margins) if margins else -1.0}


def slot_json(slot, people):
    local = {}
    for p, r in zip(people, slot["results"]):
        local[p["name"]] = {
            "start": fmt_local(slot["start"], p["tz"]), "end": fmt_local(slot["end"], p["tz"]),
            "status": r["status"],
            "margin_minutes": None if r["margin"] is None else round(r["margin"], 1),
            "shortfall_minutes": None if r["shortfall"] is None else round(r["shortfall"], 1),
            "pain": round(r["pain"], 2)}
    return local


def candidate_slots(day, anchor_tz, step, length, people):
    slots = []
    for m in range(0, 1440, step):
        naive = datetime.combine(day, time()) + timedelta(minutes=m)
        aware = naive.replace(tzinfo=anchor_tz)
        utc = aware.astimezone(timezone.utc)
        if utc.astimezone(anchor_tz).replace(tzinfo=None) != naive:
            continue  # wall time that does not exist (spring-forward gap)
        slots.append(make_slot(utc, length, people))
    return slots


def build_windows(slots):
    runs = []
    for s in slots:
        if runs and runs[-1][-1]["quality"] == s["quality"] and runs[-1][-1]["sig"] == s["sig"]:
            runs[-1].append(s)
        else:
            runs.append([s])
    windows = []
    for run in runs:
        best = min(run, key=lambda s: (s["max_pain"], s["sum_pain"], -s["min_margin"], s["start"]))
        windows.append({"run": run, "best": best})
    windows.sort(key=lambda w: (QUALITY_RANK[w["best"]["quality"]], w["best"]["max_pain"], w["best"]["sum_pain"], w["best"]["start"]))
    return windows


def noon_offset(p, d):
    return datetime.combine(d, time(12)).replace(tzinfo=p["tz"]).utcoffset()


def dst_scan(people, first, last):
    changes, shifts = [], []
    d = first
    prev = {p["name"]: noon_offset(p, first - timedelta(days=1)) for p in people}
    while d <= last:
        cur = {p["name"]: noon_offset(p, d) for p in people}
        for p in people:
            if cur[p["name"]] != prev[p["name"]]:
                changes.append({"date": d.isoformat(), "participant": p["name"], "zone": p["zone"],
                                "from_utc_offset": off_str(prev[p["name"]]), "to_utc_offset": off_str(cur[p["name"]]),
                                "shift_minutes": int(minutes(cur[p["name"]] - prev[p["name"]]))})
        for i in range(len(people)):
            for j in range(i + 1, len(people)):
                a, b = people[i]["name"], people[j]["name"]
                before = int(minutes(prev[a] - prev[b]))
                after = int(minutes(cur[a] - cur[b]))
                if before != after:
                    shifts.append({"date": d.isoformat(), "pair": [a, b], "offset_difference_before_minutes": before,
                                   "offset_difference_after_minutes": after,
                                   "meaning": "A fixed UTC time moves by %d minutes for one of them relative to the other; recheck any recurring slot from this date." % abs(after - before)})
        prev = cur
        d += timedelta(days=1)
    return changes, shifts


def off_str(delta):
    total = int(minutes(delta))
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return "%s%02d:%02d" % (sign, total // 60, total % 60)


def plan_rotation(day_records, people, slack, meeting_dates):
    cum = [0.0] * len(people)
    entries, skipped = [], []
    for rec in day_records:
        if rec["status"] == "everyone_off":
            skipped.append({"date": rec["date"], "reason": "everyone_off"})
            continue
        if meeting_dates is not None:
            if rec["date"] not in meeting_dates:
                continue
        elif rec["best_quality"] == "day_off":
            skipped.append({"date": rec["date"], "reason": "best_slot_is_on_a_day_off"})
            continue
        best = rec["windows"][0]["best"]
        rank = QUALITY_RANK[best["quality"]]
        cands = [s for s in rec["slots"] if QUALITY_RANK[s["quality"]] == rank and s["max_pain"] <= best["max_pain"] + slack]

        def key(s):
            new = [c + r["pain"] for c, r in zip(cum, s["results"])]
            return (max(new), max(new) - min(new), sum(new), -s["min_margin"], s["start"])

        pick = min(cands, key=key)
        for i, r in enumerate(pick["results"]):
            cum[i] += r["pain"]
        entries.append({"date": rec["date"], "start_utc": fmt_utc(pick["start"]), "end_utc": fmt_utc(pick["end"]),
                        "quality": pick["quality"], "local_times_by_person": slot_json(pick, people),
                        "cumulative_pain_by_person": {p["name"]: round(c, 2) for p, c in zip(people, cum)}})
    payers = [c for c in cum if c > 0]
    # Fairness compares only people who bear some cost; someone who is never inconvenienced
    # (the person in the middle zone) is luck, not unfairness. One payer alone scores 0.
    spread = (max(payers) - min(payers)) if payers else 0.0
    top = max(payers) if payers else 0.0
    if not payers:
        score = 1.0
    elif len(payers) == 1:
        score = 0.0
    else:
        score = round(1.0 - spread / top, 3)
    return {"method": "greedy: for each date pick the slot that keeps the largest running total lowest, then the smallest gap between people",
            "rotation_slack_minutes": slack,
            "slots": entries, "skipped_dates": skipped,
            "total_pain_by_person": {p["name"]: round(c, 2) for p, c in zip(people, cum)},
            "spread_among_cost_bearers_minutes": round(spread, 2),
            "fairness_score": score, "people_bearing_cost": len(payers),
            "no_rotation_needed": not payers}


# ----------------------------------------------------------------------------- commands

def run_plan(cfg, max_windows, simulate_no_tzdb):
    if not isinstance(cfg, dict):
        raise InputError("bad_input", "input must be a JSON object")
    warnings = []
    db_ok = tzdb_ok(simulate_no_tzdb)
    first = parse_date(cfg.get("start_date"), "start_date")
    last = parse_date(cfg.get("end_date", cfg.get("start_date")), "end_date")
    if last < first:
        raise InputError("bad_date", "end_date is before start_date")
    if (last - first).days + 1 > MAX_RANGE_DAYS:
        raise InputError("bad_date", "date range is longer than %d days" % MAX_RANGE_DAYS)
    length = cfg.get("meeting_minutes", DEFAULT_MEETING)
    step = cfg.get("step_minutes", DEFAULT_STEP)
    if not isinstance(length, int) or not 15 <= length <= 480:
        raise InputError("bad_input", "meeting_minutes must be an integer from 15 to 480")
    if not isinstance(step, int) or not 5 <= step <= 120:
        raise InputError("bad_input", "step_minutes must be an integer from 5 to 120")
    slack = cfg.get("rotation_slack_minutes", ROTATION_SLACK)
    if not isinstance(slack, (int, float)) or slack < 0:
        raise InputError("bad_input", "rotation_slack_minutes must be a number >= 0")
    raw_people = cfg.get("participants")
    if not isinstance(raw_people, list) or not 2 <= len(raw_people) <= MAX_PARTICIPANTS:
        raise InputError("bad_input", "participants must be a list of 2 to %d people" % MAX_PARTICIPANTS)
    gh = [parse_date(h, "holidays").isoformat() for h in cfg.get("holidays", [])]
    people = [build_participant(r, db_ok, gh, warnings) for r in raw_people]
    names = [p["name"] for p in people]
    if len(set(names)) != len(names):
        raise InputError("bad_input", "participant names must be unique")
    anchor = people[0]
    if cfg.get("anchor_zone"):
        az = str(cfg["anchor_zone"]).strip()
        match = [p for p in people if p["zone"] == az]
        if not match:
            raise InputError("bad_input", "anchor_zone must equal one participant's zone")
        anchor = match[0]
    meeting_dates = None
    if cfg.get("meeting_dates") is not None:
        meeting_dates = set(parse_date(d, "meeting_dates").isoformat() for d in cfg["meeting_dates"])
        for d in meeting_dates:
            if not first.isoformat() <= d <= last.isoformat():
                raise InputError("bad_date", "meeting_dates entry %s is outside the date range" % d)

    changes, shifts = dst_scan(people, first, last)
    records, dates_out = [], []
    d = first
    while d <= last:
        noon_offs = [p["name"] for p in people if is_off(p, datetime.combine(d, time(12)).replace(tzinfo=anchor["tz"]).astimezone(p["tz"]).date())]
        row = {"date": d.isoformat(), "anchor_weekday": DAYS[d.weekday()],
               "dst_changes_today": [c for c in changes if c["date"] == d.isoformat()] + [s for s in shifts if s["date"] == d.isoformat()]}
        if len(noon_offs) == len(people):
            row.update({"status": "everyone_off", "off_at_anchor_noon": noon_offs, "best_quality": None, "windows": []})
            records.append({"date": d.isoformat(), "status": "everyone_off", "best_quality": None, "windows": [], "slots": []})
        else:
            slots = candidate_slots(d, anchor["tz"], step, length, people)
            wins = build_windows(slots)
            best_q = wins[0]["best"]["quality"]
            out_wins = []
            for w in wins[:max_windows]:
                run, best = w["run"], w["best"]
                out_wins.append({
                    "quality": best["quality"], "least_bad": best["quality"] in ("one_outside", "several_outside", "day_off"),
                    "earliest_start_utc": fmt_utc(run[0]["start"]), "latest_start_utc": fmt_utc(run[-1]["start"]),
                    "best_start_utc": fmt_utc(best["start"]), "best_end_utc": fmt_utc(best["end"]),
                    "people_inside": sum(1 for r in best["results"] if r["status"] in ("inside", "edge")),
                    "local_times_by_person": slot_json(best, people),
                    "pain_by_person": {p["name"]: round(r["pain"], 2) for p, r in zip(people, best["results"])}})
            row.update({"status": "some_off" if noon_offs else "all_working", "off_at_anchor_noon": noon_offs,
                        "best_quality": best_q, "windows": out_wins})
            records.append({"date": d.isoformat(), "status": row["status"], "best_quality": best_q, "windows": wins, "slots": slots})
        dates_out.append(row)
        d += timedelta(days=1)

    rotation = plan_rotation(records, people, slack, meeting_dates)
    counts = {}
    for r in dates_out:
        key = r["best_quality"] or "everyone_off"
        counts[key] = counts.get(key, 0) + 1
    bad = [r["date"] for r in dates_out if r["best_quality"] in ("one_outside", "several_outside", "day_off")]
    findings = []
    if shifts:
        findings.append("%d DST change(s) move at least one pair relative to each other" % len(shifts))
    if bad:
        findings.append("%d date(s) have no slot where everyone is inside working hours" % len(bad))
    report = {
        "schema_version": SCHEMA_VERSION, "command": "plan", "ok": True,
        "inputs": {"anchor_zone": anchor["zone"], "start_date": first.isoformat(), "end_date": last.isoformat(),
                   "meeting_minutes": length, "step_minutes": step, "edge_minutes": EDGE_MINUTES,
                   "tz_database": "available" if db_ok else "missing",
                   "participants": [{"name": p["name"], "zone": p["zone"], "tz_source": p["source"],
                                     "work_start": "%02d:%02d" % divmod(p["ws"], 60), "work_end": "%02d:%02d" % divmod(p["we"], 60),
                                     "days_off": sorted(p["days_off"], key=DAYS.index), "holidays": sorted(p["holidays"])} for p in people]},
        "warnings": warnings, "dates": dates_out, "dst_changes": changes, "relative_offset_shifts": shifts,
        "rotation_plan": rotation, "summary": {"dates_by_best_quality": counts, "findings": findings,
                                               "date_label_note": "Dates are calendar dates in the anchor zone; DST change dates are in each participant's own zone."}}
    return report, (1 if findings else 0)


def run_check_zones(names, on_date, simulate_no_tzdb):
    db_ok = tzdb_ok(simulate_no_tzdb)
    out, bad = [], False
    when = None
    if on_date:
        when = datetime.combine(parse_date(on_date, "--date"), time(12), tzinfo=timezone.utc)
    for name in names:
        prob = zone_problem(name)
        entry = {"input": name}
        if prob:
            entry.update({"status": prob[0], "message": prob[1]})
        elif not db_ok:
            entry.update({"status": "no_tz_database", "message": "No tz database on this system; install the PyPI package tzdata or supply fixed offsets."})
        else:
            try:
                tz = ZoneInfo(name)
                entry["status"] = "ok"
                if when is not None:
                    entry["utc_offset_at_noon_utc"] = off_str(when.astimezone(tz).utcoffset())
            except Exception:
                entry.update({"status": "unknown_zone", "message": "Not in the tz database (typo, or a retired name)."})
        bad = bad or entry["status"] != "ok"
        out.append(entry)
    return {"schema_version": SCHEMA_VERSION, "command": "check-zones", "ok": not bad, "zones": out}, (1 if bad else 0)


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="DST-aware meeting windows across time zones")
    ap.add_argument("--simulate-no-tzdb", action="store_true", help="testing hook: behave as if no tz database were installed")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("plan")
    pp.add_argument("input")
    pp.add_argument("--out")
    pp.add_argument("--force", action="store_true")
    pp.add_argument("--max-windows", type=int, default=DEFAULT_MAX_WINDOWS)
    pz = sub.add_parser("check-zones")
    pz.add_argument("names", nargs="+")
    pz.add_argument("--date")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        if args.cmd == "check-zones":
            report, code = run_check_zones(args.names, args.date, args.simulate_no_tzdb)
            emit(report)
            return code
        if not 1 <= args.max_windows <= 20:
            raise InputError("bad_input", "--max-windows must be from 1 to 20")
        if not os.path.isfile(args.input):
            raise InputError("no_input", "input file not found: %s" % args.input)
        if args.out:
            same = os.path.realpath(args.out) == os.path.realpath(args.input)
            if not same and os.path.exists(args.out):
                same = os.path.samefile(args.out, args.input)
            if same:
                raise InputError("output_is_input", "refusing to write the report over the input file; choose another --out path")
            if os.path.exists(args.out) and not args.force:
                raise InputError("output_exists", "output file exists; use --force to replace it (never allowed for the input file)")
            if not os.path.isdir(os.path.dirname(os.path.abspath(args.out))):
                raise InputError("bad_output", "the folder for --out does not exist")
        try:
            with open(args.input, encoding="utf-8-sig") as fh:
                cfg = json.load(fh)
        except (OSError, ValueError) as exc:
            raise InputError("bad_json", "cannot read input as JSON: %s" % exc)
        report, code = run_plan(cfg, args.max_windows, args.simulate_no_tzdb)
        emit(report)
        if args.out:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
        return code
    except InputError as exc:
        emit({"schema_version": SCHEMA_VERSION, "ok": False, "error": exc.code, "message": exc.message})
        sys.stderr.write("error: %s\n" % exc.message)
        return 2


if __name__ == "__main__":
    sys.exit(main())
