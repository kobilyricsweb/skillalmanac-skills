#!/usr/bin/env python3
"""Total and audit a volunteer hour log. Arithmetic and consistency only.

Usage:
    python volunteer_ledger.py LOG [--round-unit MIN] [--round-mode nearest|up|down]
        [--daily-cap HOURS] [--thresholds H1,H2,...] [--dup-minutes MIN]
        [--inactive-days N] [--as-of YYYY-MM-DD] [--allow-overnight]
        [--roster FILE] [--delimiter CHAR] [--output REPORT.json [--force]]

LOG is a CSV or text file. With a header row the recognised columns are
person, date, start, end, hours, activity, project and signed_off (common
aliases such as name, volunteer, task, approved by are accepted). Without a
header each line is person,date,start,end[,activity[,project]] or
person,date,hours. Dates are YYYY-MM-DD, times are 24-hour HH:MM or 1:30 PM.
Blank lines and lines starting with # are skipped.

Reads: LOG, and the roster file when given. Writes: only the --output file, and
only when asked. The output path is refused when it resolves to LOG or the
roster, even with --force; an existing output needs --force.
Prints one JSON object (schema_version "1") on stdout.

Exit codes: 0 no data-quality findings, 1 findings (rejected rows, quality flags
or near-name matches), 2 bad input or bad options. Threshold crossings and
inactive people are information and never change the exit code.

No network, no subprocess, standard library only.
"""
import argparse
import csv
import datetime
import difflib
import json
import os
import re
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict

SCHEMA_VERSION = "1"
# Two sign-ins for one person on one day whose start times are this close are
# treated as the same visit entered twice (a sheet signed at the door and again
# at a desk). The brief default; the coordinator can change it.
DEFAULT_DUP_MINUTES = 15
# A shift is an outlier when it is at least 3 times the median shift of the whole
# log and at least 4 hours long, and the log has at least 10 shifts. Both floors
# stop the rule firing on tiny logs or on a 2-hour shift in a log of 20-minute ones.
OUTLIER_FACTOR = 3
OUTLIER_MIN_MINUTES = 240
OUTLIER_MIN_ROWS = 10
# difflib ratio at or above which two different normalised names are listed as a
# possible match for a human to decide. 0.85 catches "Dan"/"Dana" and one-letter
# typos in names of 8 or more letters without listing every shared first name.
NEAR_NAME_RATIO = 0.85
# Years outside this range are almost always typing mistakes (0226, 2062).
YEAR_MIN, YEAR_MAX = 1990, 2100
MINUTES_PER_DAY = 1440
# A stated hours value beyond a day cannot be one shift.
MAX_HOURS_VALUE = 24
# Stated hours and computed duration may differ by this much before a flag.
HOURS_MISMATCH_TOLERANCE = 0.01

ALIASES = {
    "person": {"person", "name", "volunteer", "volunteer name", "full name"},
    "date": {"date", "day"},
    "start": {"start", "start time", "time in", "in", "from"},
    "end": {"end", "end time", "time out", "out", "to"},
    "hours": {"hours", "duration", "hrs"},
    "activity": {"activity", "task", "role"},
    "project": {"project", "program", "programme", "event"},
    "signoff": {"signed off", "signoff", "sign off", "approved", "approved by", "supervisor", "verified by"},
}
NEGATIVE_SIGNOFF = {"", "no", "n", "false", "0", "pending", "none", "-", "n/a", "na"}
QUALITY_KINDS = {"quality"}

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::\d{2})?\s*([AaPp][Mm])?$")


class InputError(Exception):
    """Raised for anything that should exit with code 2."""


def norm_space(text):
    return " ".join(unicodedata.normalize("NFKC", text or "").split())


def norm_name(text):
    """Key used to merge exact variants: case, spacing and . , only."""
    t = norm_space(text).casefold()
    t = t.replace(".", " ").replace(",", " ")
    return " ".join(t.split())


def parse_date(text):
    m = DATE_RE.match(text.strip())
    if not m:
        return None, "bad_date_format"
    try:
        d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None, "impossible_date"
    if not YEAR_MIN <= d.year <= YEAR_MAX:
        return None, "date_out_of_range"
    return d, None


def parse_time(text, is_end):
    """Minutes since midnight, or None. 24:00 is accepted only as an end."""
    m = TIME_RE.match(text.strip())
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), m.group(3)
    if minute > 59:
        return None
    if ampm:
        if not 1 <= hour <= 12:
            return None
        hour = hour % 12 + (12 if ampm.lower() == "pm" else 0)
    elif hour == 24 and minute == 0 and is_end:
        return MINUTES_PER_DAY
    elif hour > 23:
        return None
    return hour * 60 + minute


def round_minutes(minutes, unit, mode):
    if unit <= 1:
        return minutes
    if mode == "up":
        return -(-minutes // unit) * unit
    if mode == "down":
        return minutes // unit * unit
    return (2 * minutes + unit) // (2 * unit) * unit  # half rounds up


def hours_of(minutes):
    return round(minutes / 60.0, 2)


def read_text(path, what):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise InputError("cannot read %s %r: %s" % (what, path, exc.strerror or exc))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("%s %r is not UTF-8; re-save it as UTF-8 CSV" % (what, path))
    if not text.strip():
        raise InputError("%s %r is empty" % (what, path))
    return text


def detect_columns(cells):
    """Map canonical column names to indexes when the row looks like a header."""
    found = {}
    for idx, cell in enumerate(cells):
        key = re.sub(r"[_\-]+", " ", cell.strip().casefold())
        for canon, names in ALIASES.items():
            if key in names and canon not in found:
                found[canon] = idx
    if "person" in found and "date" in found:
        return found
    return None


def split_lines(text, delimiter):
    rows = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            cells = next(csv.reader([line], delimiter=delimiter))
        except csv.Error:
            cells = [line]
        rows.append((lineno, [c.strip() for c in cells]))
    return rows


def parse_log(text, delimiter, allow_overnight, as_of):
    """Return (accepted, rejected, name_variants, signoff_checked)."""
    lines = split_lines(text, delimiter)
    if not lines:
        raise InputError("the log has no data lines")
    columns = detect_columns(lines[0][1])
    signoff_checked = False
    if columns is not None:
        lines = lines[1:]
        signoff_checked = "signoff" in columns
    accepted, rejected = [], []
    variants = defaultdict(Counter)
    first_seen = {}
    for row_no, (lineno, cells) in enumerate(lines, 1):
        def cell(name, pos=None):
            if columns is not None:
                idx = columns.get(name)
            else:
                idx = pos
            if idx is None or idx >= len(cells):
                return ""
            return cells[idx]

        raw = delimiter.join(cells)
        if columns is None:
            if len(cells) == 3:
                person, date_s, start_s, end_s, hours_s = cells[0], cells[1], "", "", cells[2]
                activity_s = project_s = ""
            else:
                person, date_s, start_s, end_s = cell("person", 0), cell("date", 1), cell("start", 2), cell("end", 3)
                hours_s = ""
                activity_s, project_s = cell("activity", 4), cell("project", 5)
            signoff_s = ""
        else:
            person, date_s, start_s, end_s = cell("person"), cell("date"), cell("start"), cell("end")
            hours_s, activity_s, project_s, signoff_s = cell("hours"), cell("activity"), cell("project"), cell("signoff")

        def reject(reason):
            rejected.append({"row": row_no, "line": lineno, "reason": reason, "raw": raw})

        display = norm_space(person)
        key = norm_name(person)
        if not key:
            reject("missing_name")
            continue
        variants[key][display] += 1
        first_seen.setdefault((key, display), len(first_seen))
        date, problem = parse_date(date_s)
        if problem:
            reject(problem)
            continue
        if as_of is not None and date > as_of:
            reject("future_date")
            continue
        flags = []
        start = end = None
        minutes = None
        overnight = False
        if start_s or end_s:
            if not (start_s and end_s):
                reject("incomplete_times")
                continue
            start = parse_time(start_s, False)
            end = parse_time(end_s, True)
            if start is None or end is None:
                reject("bad_time")
                continue
            if end == start:
                reject("zero_duration")
                continue
            if end < start:
                if not allow_overnight:
                    reject("end_before_start")
                    continue
                end += MINUTES_PER_DAY
                overnight = True
                flags.append(("overnight_shift", "info", "ends the next day"))
            minutes = end - start
            if hours_s:
                try:
                    stated = float(hours_s)
                except ValueError:
                    reject("bad_hours")
                    continue
                if abs(stated - minutes / 60.0) > HOURS_MISMATCH_TOLERANCE:
                    flags.append(("hours_mismatch", "quality",
                                  "hours column says %s, times give %s; times used" % (hours_s, hours_of(minutes))))
        else:
            if not hours_s:
                reject("no_duration")
                continue
            try:
                stated = float(hours_s)
            except ValueError:
                reject("bad_hours")
                continue
            if stated <= 0:
                reject("non_positive_duration")
                continue
            if stated > MAX_HOURS_VALUE:
                reject("over_24_hours")
                continue
            minutes = int(round(stated * 60))
        signed = None
        if signoff_checked:
            signed = signoff_s.strip().casefold() not in NEGATIVE_SIGNOFF
        accepted.append({
            "row": row_no, "line": lineno, "key": key, "display": display, "date": date,
            "start": start, "end": end, "minutes": minutes, "overnight": overnight,
            "activity": norm_space(activity_s) or "unspecified",
            "project": norm_space(project_s) or "unspecified",
            "signed": signed, "flags": flags, "has_times": start is not None,
            "hours_only": start is None, "stated_hours": hours_s,
        })
    return accepted, rejected, variants, first_seen, signoff_checked


def pick_display(variants, first_seen):
    names = {}
    for key, counter in variants.items():
        best = sorted(counter.items(), key=lambda kv: (-kv[1], first_seen[(key, kv[0])]))[0][0]
        names[key] = best
    return names


def drop_duplicates(accepted, dup_minutes, rejected):
    kept, seen = [], defaultdict(list)
    for r in accepted:
        if r["has_times"]:
            same = [o for o in seen[(r["key"], r["date"])] if abs(o["start"] - r["start"]) <= dup_minutes]
            if same:
                rejected.append({"row": r["row"], "line": r["line"], "reason": "duplicate_signin",
                                 "raw": "same person and date as row %d, start within %d minutes" % (same[0]["row"], dup_minutes)})
                continue
            seen[(r["key"], r["date"])].append(r)
        kept.append(r)
    return kept


def near_names(keys, display):
    pairs = []
    ordered = sorted(keys)
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            reason, ratio = None, None
            if sorted(a.split()) == sorted(b.split()):
                reason, ratio = "same_words_different_order", 1.0
            else:
                ratio = round(difflib.SequenceMatcher(None, a, b).ratio(), 3)
                if ratio >= NEAR_NAME_RATIO:
                    reason = "similar_spelling"
            if reason:
                pairs.append({"names": [display[a], display[b]], "reason": reason, "ratio": ratio})
    return pairs


def build_report(args, accepted, rejected, display, variants, signoff_checked, roster):
    unit, mode = args.round_unit, args.round_mode
    for r in accepted:
        r["rounded"] = round_minutes(r["minutes"], unit, mode)
    by_person = defaultdict(list)
    for r in accepted:
        by_person[r["key"]].append(r)
    person_flags = defaultdict(list)

    def flag(key, ftype, kind, rows, date, detail):
        person_flags[key].append({"type": ftype, "kind": kind, "rows": rows,
                                  "date": date.isoformat() if date else None, "detail": detail})

    for r in accepted:
        for ftype, kind, detail in r["flags"]:
            flag(r["key"], ftype, kind, [r["row"]], r["date"], detail)
        if r["signed"] is False:
            flag(r["key"], "missing_signoff", "quality", [r["row"]], r["date"], "no sign-off recorded")

    mins = [r["minutes"] for r in accepted]
    if len(mins) >= OUTLIER_MIN_ROWS:
        med = statistics.median(mins)
        for r in accepted:
            if r["minutes"] >= OUTLIER_MIN_MINUTES and r["minutes"] >= OUTLIER_FACTOR * med:
                flag(r["key"], "outlier_shift", "quality", [r["row"]], r["date"],
                     "%s h against a median shift of %s h" % (hours_of(r["minutes"]), hours_of(med)))

    for key, rows in by_person.items():
        timed = sorted((r for r in rows if r["has_times"]), key=lambda r: r["date"].toordinal() * MINUTES_PER_DAY + r["start"])
        spans = [(r["date"].toordinal() * MINUTES_PER_DAY + r["start"], r["date"].toordinal() * MINUTES_PER_DAY + r["end"], r) for r in timed]
        for i in range(len(spans)):
            for j in range(i + 1, len(spans)):
                if spans[j][0] >= spans[i][1]:
                    break
                overlap = min(spans[i][1], spans[j][1]) - spans[j][0]
                if overlap > 0:
                    flag(key, "overlapping_shifts", "quality", [spans[i][2]["row"], spans[j][2]["row"]],
                         spans[j][2]["date"], "rows %d and %d overlap by %d minutes" % (spans[i][2]["row"], spans[j][2]["row"], overlap))
        hs = defaultdict(list)
        for r in rows:
            if r["hours_only"]:
                hs[(r["date"], r["activity"], r["minutes"])].append(r["row"])
        for (d, _act, _m), rs in hs.items():
            if len(rs) > 1:
                flag(key, "possible_duplicate_hours", "quality", rs, d, "same date, activity and hours entered %d times" % len(rs))
        if args.daily_cap is not None:
            days = defaultdict(int)
            for r in rows:
                days[r["date"]] += r["rounded"]
            for d, m in days.items():
                if m > args.daily_cap * 60:
                    flag(key, "over_daily_cap", "quality", [r["row"] for r in rows if r["date"] == d], d,
                         "%s h on one day, cap %s h" % (hours_of(m), args.daily_cap))
        if args.thresholds:
            cum = 0
            for r in sorted(rows, key=lambda r: (r["date"], r["start"] if r["start"] is not None else -1, r["row"])):
                before = cum
                cum += r["rounded"]
                for t in args.thresholds:
                    if before < t * 60 <= cum:
                        flag(key, "threshold_crossed", "info", [r["row"]], r["date"],
                             "reached %s h on this date (running total %s h)" % (t, hours_of(cum)))
        if roster is not None and key not in roster:
            flag(key, "unmatched_name", "quality", [r["row"] for r in rows], None, "not on the roster file")

    people, by_activity, by_project, by_month = [], Counter(), Counter(), Counter()
    month_people = defaultdict(Counter)
    month_shifts, month_activity = Counter(), defaultdict(Counter)
    for key in sorted(by_person, key=lambda k: display[k].casefold()):
        rows = by_person[key]
        months, acts, projs = Counter(), Counter(), Counter()
        for r in rows:
            m = r["date"].strftime("%Y-%m")
            months[m] += r["rounded"]
            acts[r["activity"]] += r["rounded"]
            projs[r["project"]] += r["rounded"]
            by_activity[r["activity"]] += r["rounded"]
            by_project[r["project"]] += r["rounded"]
            by_month[m] += r["rounded"]
            month_people[m][display[key]] += r["rounded"]
            month_shifts[m] += 1
            month_activity[m][r["activity"]] += r["rounded"]
        dates = sorted(r["date"] for r in rows)
        people.append({
            "name": display[key], "hours": hours_of(sum(r["rounded"] for r in rows)), "shifts": len(rows),
            "first_date": dates[0].isoformat(), "last_date": dates[-1].isoformat(),
            "months": {m: hours_of(v) for m, v in sorted(months.items())},
            "activities": {a: hours_of(v) for a, v in sorted(acts.items())},
            "projects": {p: hours_of(v) for p, v in sorted(projs.items())},
            "name_variants": sorted(variants[key]) if len(variants[key]) > 1 else [],
            "flags": person_flags.get(key, []),
        })

    monthly = []
    for m in sorted(by_month):
        top = sorted(month_activity[m].items(), key=lambda kv: (-kv[1], kv[0]))[0]
        monthly.append({
            "month": m, "hours": hours_of(by_month[m]), "shifts": month_shifts[m],
            "volunteers": len(month_people[m]),
            "people": {n: hours_of(v) for n, v in sorted(month_people[m].items(), key=lambda kv: kv[0].casefold())},
            "top_activity": {"name": top[0], "hours": hours_of(top[1])},
        })

    all_dates = [r["date"] for r in accepted]
    as_of = args.as_of_date or (max(all_dates) if all_dates else None)
    inactive = []
    if args.inactive_days is not None and as_of is not None:
        for p in people:
            last = datetime.date.fromisoformat(p["last_date"])
            gap = (as_of - last).days
            if gap > args.inactive_days:
                inactive.append({"name": p["name"], "last_date": p["last_date"], "days_since": gap})

    flag_counts = Counter(f["type"] for fl in person_flags.values() for f in fl)
    near = near_names(set(by_person), display)
    quality = (any(f["kind"] in QUALITY_KINDS for fl in person_flags.values() for f in fl)
               or bool(rejected) or bool(near))
    rep = {
        "schema_version": SCHEMA_VERSION,
        "command": "ledger",
        "input": os.path.basename(args.log),
        "rows_read": len(accepted) + len(rejected),
        "rows_accepted": len(accepted),
        "rows_rejected": len(rejected),
        "settings": {
            "round_unit_minutes": unit, "round_mode": mode, "daily_cap_hours": args.daily_cap,
            "thresholds_hours": args.thresholds or [], "dup_minutes": args.dup_minutes,
            "inactive_days": args.inactive_days, "as_of": as_of.isoformat() if as_of else None,
            "allow_overnight": args.allow_overnight, "signoff_checked": signoff_checked,
            "roster_checked": roster is not None,
        },
        "people": people,
        "totals": {
            "hours": hours_of(sum(r["rounded"] for r in accepted)), "shifts": len(accepted), "volunteers": len(people),
            "by_activity": {k: hours_of(v) for k, v in sorted(by_activity.items())},
            "by_project": {k: hours_of(v) for k, v in sorted(by_project.items())},
            "by_month": {k: hours_of(v) for k, v in sorted(by_month.items())},
        },
        "monthly_report": monthly,
        "flag_counts": dict(sorted(flag_counts.items())),
        "near_name_matches": near,
        "inactive": inactive,
        "rejected_rows": sorted(rejected, key=lambda x: x["row"]),
        "verdict": "findings" if quality else "clean",
    }
    return rep, quality


def parse_args(argv):
    p = argparse.ArgumentParser(prog="volunteer_ledger.py", description="Total and audit a volunteer hour log.")
    p.add_argument("log", help="CSV or text log of shifts")
    p.add_argument("--round-unit", type=int, default=1, help="round each shift to this many minutes (default 1, no rounding)")
    p.add_argument("--round-mode", choices=["nearest", "up", "down"], default="nearest")
    p.add_argument("--daily-cap", type=float, default=None, help="flag a person-day above this many hours")
    p.add_argument("--thresholds", default="", help="comma-separated hour thresholds to report crossings for")
    p.add_argument("--dup-minutes", type=int, default=DEFAULT_DUP_MINUTES)
    p.add_argument("--inactive-days", type=int, default=None, help="list people with no shift in the last N days")
    p.add_argument("--as-of", default=None, help="reference date YYYY-MM-DD (default: latest date in the log); later dates are rejected")
    p.add_argument("--allow-overnight", action="store_true", help="treat end before start as a shift past midnight")
    p.add_argument("--roster", default=None, help="text file, one expected name per line")
    p.add_argument("--delimiter", default=",")
    p.add_argument("--output", default=None, help="also write the JSON report to this file")
    p.add_argument("--force", action="store_true", help="allow replacing an existing --output file (never an input)")
    args = p.parse_args(argv)
    if args.round_unit < 1:
        p.error("--round-unit must be 1 or more")
    if args.dup_minutes < 0:
        p.error("--dup-minutes must not be negative")
    if args.daily_cap is not None and args.daily_cap <= 0:
        p.error("--daily-cap must be above 0")
    if args.inactive_days is not None and args.inactive_days < 0:
        p.error("--inactive-days must not be negative")
    if len(args.delimiter) != 1:
        p.error("--delimiter must be one character")
    thresholds = []
    for part in [x for x in args.thresholds.split(",") if x.strip()]:
        try:
            value = float(part)
        except ValueError:
            p.error("--thresholds must be numbers, got %r" % part)
        if value <= 0:
            p.error("--thresholds must be above 0")
        thresholds.append(value)
    args.thresholds = sorted(set(thresholds))
    args.as_of_date = None
    if args.as_of is not None:
        d, problem = parse_date(args.as_of)
        if problem:
            p.error("--as-of must be a real YYYY-MM-DD date")
        args.as_of_date = d
    return args


def check_output_path(args):
    if not args.output:
        return
    out = os.path.realpath(args.output)
    for label, path in (("log", args.log), ("roster", args.roster)):
        if path and os.path.exists(path) and os.path.exists(out) and os.path.samefile(path, out):
            raise InputError("refusing to write the report over the %s file %r" % (label, path))
        if path and os.path.realpath(path) == out:
            raise InputError("refusing to write the report over the %s file %r" % (label, path))
    if os.path.exists(out) and not args.force:
        raise InputError("output %r exists; pass --force to replace it" % args.output)
    parent = os.path.dirname(out) or "."
    if not os.path.isdir(parent):
        raise InputError("output folder %r does not exist" % parent)


def main(argv=None):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except (OSError, ValueError):
        pass
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        check_output_path(args)
        text = read_text(args.log, "log")
        roster = None
        if args.roster:
            roster = {norm_name(x) for x in read_text(args.roster, "roster").splitlines() if norm_name(x)}
        accepted, rejected, variants, first_seen, signoff_checked = parse_log(
            text, args.delimiter, args.allow_overnight, args.as_of_date)
    except InputError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    display = pick_display(variants, first_seen)
    accepted = drop_duplicates(accepted, args.dup_minutes, rejected)
    report, findings = build_report(args, accepted, rejected, display, variants, signoff_checked, roster)
    out_text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out_text + "\n")
        except OSError as exc:
            sys.stderr.write("error: cannot write %r: %s\n" % (args.output, exc.strerror or exc))
            return 2
    sys.stdout.write(out_text + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
