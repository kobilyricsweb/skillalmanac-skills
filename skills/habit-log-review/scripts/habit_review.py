#!/usr/bin/env python3
"""Review a habit, study, workout or focus log with plain arithmetic.

    python habit_review.py <log.csv|-> --as-of YYYY-MM-DD [--goal "Habit=daily"]
        [--goal "Habit=5/week>=20"] [--blank-means-no] [--date-order dmy|mdy]

Input: lines of "date,habit,value" (comma, tab or semicolon separated; a header
row named date/habit/value is optional; "#" lines and blank lines are ignored;
"-" reads standard input). A two-column "date,habit" log counts every row as done.
Value is a flag (yes/no/true/false/x/done/y/n, 1/0) or a number, optionally with
a unit (30, 30 min, 1.5h). Reads only the file it is given. Writes nothing.
Prints one JSON object to stdout. Errors go to stderr as one plain sentence.

Goals (never invented; one --goal per habit, name matched ignoring case):
    Name=daily          every day
    Name=N/week         N done days per Monday-to-Sunday week, N from 1 to 7
    either form can end in >=M: a day only counts when its value is at least M
    (minutes for time units). Without a goal the habit gets no verdict.

Exit codes: 0 = reviewed, no data-quality warnings; 1 = reviewed, at least one
warning (duplicates, mixed units, unknown days, skipped rows, future dates);
2 = bad input or usage (missing file, no usable rows, bad date or goal).

JSON contract (schema_version 1)
    top: schema_version, command "review", file, as_of, blank_means
         ("unknown" | "not_done"), date_order, rows_read, rows_used,
         habits[], warnings[] (strings "code: text"), summary {verdict: count}
    habit: name, goal {raw, kind, target, min_value} | null, value_type
         ("flag" | "number" | "mixed"), first_date, last_done_date, span_days,
         days_done, days_missed, days_unknown, streak_current, streak_longest,
         streak_unit ("days" | "weeks"), rate_7, rate_28, rate_all (percent of
         evaluable days, or null), adherence_28 (percent of goal, or null),
         weeks {closed, met, pct, open} | null, weekday_profile {Mon..Sun:
         {done, days, rate}}, best_weekday, worst_weekday, gap_min_days,
         gaps_total, gaps[{start, end, days, kind}], trend {recent_rate,
         prior_rate, delta_pts, direction}, days_since_last_done, verdict
         ("on_pace" | "slipping" | "stalled" | "too_early" | "no_goal"),
         pattern (see SKILL.md) | null, warnings[], notes[], readout
Day states: done, missed (explicit no, or below the minimum), unknown (no row;
only when blank is not read as "no"), pending (no row on the as-of day: the day
is not over, so it neither adds to nor breaks a streak). For weekly goals a
blank day is a rest day and counts as not done.
"""
import argparse
import csv
import datetime as dt
import io
import json
import re
import sys

SCHEMA_VERSION = 1
# A review needs two weeks of calendar span: fewer days cannot show a pattern.
MIN_SPAN_DAYS = 14
# Window used for every rate and for the pace verdict.
WINDOW_DAYS = 28
# At least a week of evaluable days inside the window, else a rate is noise.
MIN_EVAL_DAYS = 7
# Verdict ladder on adherence over the last 28 days, as percent of the goal.
ON_PACE_PCT = 80.0
SLIPPING_FLOOR_PCT = 40.0
# No done day for two weeks is stalled whatever the percentage says.
STALLED_DAYS = 14
# Trend compares the last 28 days with the 28 before; each needs two weeks of data.
TREND_MIN_EVAL = 14
TREND_FLAT_PTS = 10.0
# A weekday is compared only with at least four observed days.
MIN_WEEKDAY_DAYS = 4
WEEKDAY_SPREAD_PTS = 40.0
# A pause this long, followed by a done day, is a stop-and-restart pattern.
STOP_GAP_DAYS = 7
NEVER_TOOK_OFF_PCT = 30.0
# Guard against a date typo (year 2062) stretching the range.
MAX_SPAN_DAYS = 3660
MAX_GAPS_LISTED = 10
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
TRUE_WORDS = {"y", "yes", "true", "t", "x", "done", "✓", "✔"}
FALSE_WORDS = {"n", "no", "false", "f", "-", "skip", "skipped", "missed"}
MINUTE_UNITS = {"m", "min", "mins", "minute", "minutes"}
HOUR_UNITS = {"h", "hr", "hrs", "hour", "hours"}
HEADER_DATE = {"date", "day", "when"}
HEADER_HABIT = {"habit", "name", "activity", "task"}
HEADER_VALUE = {"value", "done", "minutes", "mins", "duration", "completed", "status"}
GOAL_RE = re.compile(r"^(.+?)\s*=\s*(?:(daily)|([1-7])\s*/\s*week)\s*(?:>=\s*(\d+(?:\.\d+)?))?$", re.I)


class InputError(Exception):
    """Bad input or usage; reported on stderr, exit code 2."""


def parse_date(text, order):
    """Return (date, None) or (None, reason)."""
    s = text.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}[T ]", s):
        s = s[:10]
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s)
    parts = None
    if m:
        parts = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\.?,?\s+(\d{4})$", s)
    if m and m.group(2).lower() in MONTHS:
        parts = (int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    m = re.match(r"^([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$", s)
    if m and m.group(1).lower() in MONTHS:
        parts = (int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)
    if m:
        if order is None:
            return None, "ambiguous day/month order (pass --date-order dmy or mdy)"
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        parts = (y, b, a) if order == "dmy" else (y, a, b)
    if parts is None:
        return None, "unrecognised date"
    try:
        return dt.date(*parts), None
    except ValueError:
        return None, "impossible date"


def parse_value(text):
    """Return ("flag", 0|1, None), ("num", float, unit) or None."""
    s = text.strip().lower()
    if s in TRUE_WORDS:
        return ("flag", 1, None)
    if s in FALSE_WORDS:
        return ("flag", 0, None)
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([a-z%]*)$", s)
    if not m:
        return None
    number, unit = float(m.group(1)), m.group(2)
    if unit in MINUTE_UNITS:
        return ("num", number, "min")
    if unit in HOUR_UNITS:
        return ("num", number * 60.0, "min")
    return ("num", number, unit)


def read_rows(text, order):
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        raise InputError("The log is empty. Give lines of date,habit,value.")
    first = lines[0]
    delim = "\t" if "\t" in first else ("," if "," in first else (";" if ";" in first else ","))
    rows = list(csv.reader(lines, delimiter=delim))
    cols = (0, 1, 2)
    value_col_present = True
    if rows[0][0].strip().lower() in HEADER_DATE:
        head = [c.strip().lower() for c in rows[0]]
        rows = rows[1:]
        date_i = next(i for i, c in enumerate(head) if c in HEADER_DATE)
        habit_i = next((i for i, c in enumerate(head) if c in HEADER_HABIT), None)
        value_i = next((i for i, c in enumerate(head) if c in HEADER_VALUE), None)
        if habit_i is None:
            raise InputError("The header has no habit column (habit, name, activity or task).")
        cols = (date_i, habit_i, value_i)
        value_col_present = value_i is not None
    elif len(rows[0]) < 3:
        value_col_present = False
    return rows, cols, value_col_present


def parse_goal(raw):
    m = GOAL_RE.match(raw.strip())
    if not m:
        raise InputError("Bad --goal %r. Use Name=daily or Name=N/week (N 1 to 7), optionally ending in >=M." % raw)
    kind = "daily" if m.group(2) else "weekly"
    target = 1 if kind == "daily" else int(m.group(3))
    minv = float(m.group(4)) if m.group(4) else None
    return m.group(1).strip(), {"raw": raw.strip(), "kind": kind, "target": target, "min_value": minv}


def pct(done, total):
    return round(100.0 * done / total, 1) if total else None


def day_done(vals, minv):
    """Merge one day's rows. Returns (done, conflict)."""
    flag_yes = any(k == "flag" and n for k, n, _ in vals)
    flag_no = any(k == "flag" and not n for k, n, _ in vals)
    nums = [n for k, n, _ in vals if k == "num"]
    num_ok = bool(nums) and (sum(nums) >= minv if minv is not None else sum(nums) > 0)
    return (flag_yes or num_ok), (flag_yes and flag_no)


def runs_of(statuses, dates, bad):
    """Runs of consecutive dates whose status is in `bad`: (start, end, kinds)."""
    out, cur = [], None
    for d in dates:
        s = statuses[d]
        if s in bad:
            if cur is None:
                cur = [d, d, {s}]
            else:
                cur[1] = d
                cur[2].add(s)
        else:
            if cur is not None:
                out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return out


def analyse(h, goal, as_of, blank_no):
    name, days = h["name"], h["days"]
    minv = goal["min_value"] if goal else None
    weekly = bool(goal) and goal["kind"] == "weekly"
    first = min(days)
    state, conflicts, dup_extra = {}, 0, 0
    labels = set()
    for d, vals in days.items():
        dup_extra += len(vals) - 1
        done, conflict = day_done(vals, minv)
        state[d] = done
        conflicts += 1 if conflict else 0
        for kind, n, unit in vals:
            if kind == "flag":
                labels.add("flag")
            elif unit:
                labels.add(unit)
            elif n not in (0.0, 1.0):
                labels.add("count")
    value_type = "mixed" if len(labels) > 1 else ("number" if labels and labels != {"flag"} else "flag")

    dates = [first + dt.timedelta(days=i) for i in range((as_of - first).days + 1)]
    status = {}
    for d in dates:
        if d in state:
            status[d] = "done" if state[d] else "missed"
        elif d == as_of:
            status[d] = "pending"
        elif weekly or blank_no:
            status[d] = "missed"
        else:
            status[d] = "unknown"

    def window(lo_back, hi_back):
        lo, hi = as_of - dt.timedelta(days=lo_back), as_of - dt.timedelta(days=hi_back)
        return [d for d in dates if lo <= d <= hi]

    def stats(ds):
        ev = [d for d in ds if status[d] in ("done", "missed")]
        return sum(1 for d in ev if status[d] == "done"), len(ev)

    done_all, ev_all = stats(dates)
    done_7, ev_7 = stats(window(6, 0))
    done_28, ev_28 = stats(window(WINDOW_DAYS - 1, 0))
    adherence = None
    if goal and ev_28:
        if weekly:
            expected = goal["target"] * ev_28 / 7.0
            adherence = round(min(100.0, 100.0 * done_28 / expected), 1)
        else:
            adherence = pct(done_28, ev_28)

    # streaks
    weeks = None
    streak_unit = "days"
    cur = longest = 0
    if weekly:
        streak_unit = "weeks"
        closed = met = 0
        open_week = None
        ws = first - dt.timedelta(days=first.weekday())
        while ws <= as_of:
            if ws >= first:
                week_days = [ws + dt.timedelta(days=i) for i in range(7)]
                n_done = sum(1 for d in week_days if status.get(d) == "done")
                if ws + dt.timedelta(days=6) < as_of:
                    closed += 1
                    if n_done >= goal["target"]:
                        met += 1
                        cur += 1
                    else:
                        cur = 0
                else:
                    ok = n_done >= goal["target"]
                    open_week = {"week_start": ws.isoformat(), "done": n_done,
                                 "target": goal["target"], "status": "open_met" if ok else "open_pending"}
                    cur += 1 if ok else 0
                longest = max(longest, cur)
            ws += dt.timedelta(days=7)
        weeks = {"closed": closed, "met": met, "pct": pct(met, closed), "open": open_week}
    else:
        for d in dates:
            s = status[d]
            if s == "done":
                cur += 1
            elif s in ("missed", "unknown"):
                cur = 0
            longest = max(longest, cur)

    # gaps
    gap_min = 7 if weekly else 2
    all_runs = runs_of(status, dates, ("missed", "unknown"))
    done_dates = [d for d in dates if status[d] == "done"]
    last_done = max(done_dates) if done_dates else None
    gap_rows = [r for r in all_runs if (r[1] - r[0]).days + 1 >= gap_min]
    stop_start = any((r[1] - r[0]).days + 1 >= STOP_GAP_DAYS and last_done and r[1] < last_done for r in all_runs)
    listed = sorted(gap_rows, key=lambda r: (-((r[1] - r[0]).days + 1), r[0]))[:MAX_GAPS_LISTED]
    gaps = [{"start": r[0].isoformat(), "end": r[1].isoformat(), "days": (r[1] - r[0]).days + 1,
             "kind": next(iter(r[2])) if len(r[2]) == 1 else "mixed"}
            for r in sorted(listed, key=lambda r: r[0])]

    # weekday profile
    prof = {w: [0, 0] for w in WEEKDAYS}
    for d in dates:
        if status[d] in ("done", "missed"):
            prof[WEEKDAYS[d.weekday()]][1] += 1
            prof[WEEKDAYS[d.weekday()]][0] += 1 if status[d] == "done" else 0
    weekday_profile = {w: {"done": v[0], "days": v[1], "rate": pct(v[0], v[1])} for w, v in prof.items()}
    q = [(prof[w][0] / prof[w][1], i) for i, w in enumerate(WEEKDAYS) if prof[w][1] >= MIN_WEEKDAY_DAYS]
    best = worst = None
    spread = 0.0
    if len(q) >= 2:
        hi, lo = max(r for r, _ in q), min(r for r, _ in q)
        if hi != lo:
            best = WEEKDAYS[min(i for r, i in q if r == hi)]
            worst = WEEKDAYS[min(i for r, i in q if r == lo)]
            spread = (hi - lo) * 100.0

    # trend
    d_rec, e_rec = stats(window(WINDOW_DAYS - 1, 0))
    d_pri, e_pri = stats(window(2 * WINDOW_DAYS - 1, WINDOW_DAYS))
    trend = {"recent_rate": None, "prior_rate": None, "delta_pts": None, "direction": "insufficient"}
    if e_rec >= TREND_MIN_EVAL and e_pri >= TREND_MIN_EVAL:
        delta = 100.0 * d_rec / e_rec - 100.0 * d_pri / e_pri
        trend = {"recent_rate": pct(d_rec, e_rec), "prior_rate": pct(d_pri, e_pri), "delta_pts": round(delta, 1),
                 "direction": "up" if delta >= TREND_FLAT_PTS else ("down" if delta <= -TREND_FLAT_PTS else "flat")}

    span = (as_of - first).days + 1
    since = (as_of - last_done).days if last_done else None
    rate_all = pct(done_all, ev_all)
    if span < MIN_SPAN_DAYS or ev_28 < MIN_EVAL_DAYS:
        verdict = "too_early"
    elif goal is None:
        verdict = "no_goal"
    elif since is None or since >= STALLED_DAYS or adherence < SLIPPING_FLOOR_PCT:
        verdict = "stalled"
    elif adherence < ON_PACE_PCT:
        verdict = "slipping"
    else:
        verdict = "on_pace"

    pattern = None
    if verdict not in ("too_early", "no_goal"):
        if rate_all is not None and rate_all < NEVER_TOOK_OFF_PCT and verdict != "on_pace":
            pattern = "never_took_off"
        elif trend["direction"] == "down" and verdict != "on_pace":
            pattern = "fading"
        elif best is not None and spread >= WEEKDAY_SPREAD_PTS:
            pattern = "weekday_gap"
        elif stop_start:
            pattern = "stop_start"
        elif verdict == "on_pace":
            pattern = "steady"
        else:
            pattern = "uneven"

    unknown = sum(1 for d in dates if status[d] == "unknown")
    warnings, notes = [], []
    if dup_extra:
        warnings.append("duplicate_rows: %d extra row(s) for the same day merged (numbers added, any yes wins)" % dup_extra)
    if conflicts:
        warnings.append("day_conflict: %d day(s) have both a yes and a no; counted as done" % conflicts)
    if value_type == "mixed":
        warnings.append("mixed_units: values mix %s; check the minimum before trusting the done count" % ", ".join(sorted(labels)))
    if unknown:
        warnings.append("unknown_days: %d day(s) have no row and are not counted as missed (use --blank-means-no if blank means no)" % unknown)
    if goal is None:
        notes.append("No goal given for this habit: ask the user for one before judging pace.")
    if weekly:
        notes.append("Weekly goal: blank days are rest days and count as not done.")
    if best is None:
        notes.append("Weekday comparison needs at least %d observed days on two or more weekdays." % MIN_WEEKDAY_DAYS)

    head = "%s: %s." % (name, verdict.replace("_", " "))
    if verdict == "too_early":
        readout = "%s %d day(s) of data; at least %d days with %d evaluable are needed." % (head, span, MIN_SPAN_DAYS, MIN_EVAL_DAYS)
    else:
        readout = "%s Streak %d %s (longest %d). Last 28 days: %s%% of days done%s. Trend: %s." % (
            head, cur, streak_unit, longest, pct(done_28, ev_28),
            "" if adherence is None else ", %s%% of goal" % adherence, trend["direction"])

    return {
        "name": name, "goal": goal, "value_type": value_type, "first_date": first.isoformat(),
        "last_done_date": last_done.isoformat() if last_done else None, "span_days": span,
        "days_done": done_all, "days_missed": ev_all - done_all, "days_unknown": unknown,
        "streak_current": cur, "streak_longest": longest, "streak_unit": streak_unit,
        "rate_7": pct(done_7, ev_7), "rate_28": pct(done_28, ev_28), "rate_all": rate_all,
        "adherence_28": adherence, "weeks": weeks, "weekday_profile": weekday_profile,
        "best_weekday": best, "worst_weekday": worst, "gap_min_days": gap_min,
        "gaps_total": len(gap_rows), "gaps": gaps, "trend": trend, "days_since_last_done": since,
        "verdict": verdict, "pattern": pattern, "warnings": sorted(warnings), "notes": notes, "readout": readout,
    }


def build_report(args):
    if args.file == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(args.file, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            raise InputError("Cannot read %s: %s." % (args.file, exc.strerror or exc))
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise InputError("%s is not UTF-8 text; re-save it as UTF-8 CSV." % args.file)
    goals = {}
    for raw_goal in args.goal:
        gname, goal = parse_goal(raw_goal)
        if gname.casefold() in goals:
            raise InputError("Two --goal options for %r; give one goal per habit." % gname)
        goals[gname.casefold()] = goal
    as_of_arg = None
    if args.as_of:
        as_of_arg, why = parse_date(args.as_of, None)
        if as_of_arg is None:
            raise InputError("--as-of must be a real date like 2026-11-21.")

    rows, (date_i, habit_i, value_i), value_col = read_rows(text, args.date_order)
    habits, order = {}, []
    skipped, reasons = 0, {}
    parsed = []
    for row in rows:
        if len(row) <= max(date_i, habit_i):
            skipped += 1
            reasons.setdefault("too few columns", []).append(",".join(row))
            continue
        d, why = parse_date(row[date_i], args.date_order)
        habit = re.sub(r"\s+", " ", row[habit_i].strip()) if habit_i < len(row) else ""
        if d is None or not habit:
            skipped += 1
            reasons.setdefault(why or "empty habit name", []).append(",".join(row))
            continue
        if value_col:
            val = parse_value(row[value_i]) if value_i < len(row) else None
            if val is None:
                skipped += 1
                reasons.setdefault("unreadable value", []).append(",".join(row))
                continue
        else:
            val = ("flag", 1, None)
        parsed.append((d, habit, val))
    if not parsed:
        detail = "; ".join("%s (e.g. %s)" % (k, v[0]) for k, v in sorted(reasons.items()))
        raise InputError("No usable rows. %s" % (detail or "Check the column order date,habit,value."))

    as_of = as_of_arg or max(p[0] for p in parsed)
    future = 0
    used = 0
    for d, habit, val in parsed:
        if d > as_of:
            future += 1
            continue
        key = habit.casefold()
        if key not in habits:
            habits[key] = {"name": habit, "days": {}}
            order.append(key)
        habits[key]["days"].setdefault(d, []).append(val)
        used += 1
    if not habits:
        raise InputError("Every row is after the as-of date %s." % as_of.isoformat())
    if (as_of - min(min(h["days"]) for h in habits.values())).days + 1 > MAX_SPAN_DAYS:
        raise InputError("The log spans more than %d days; check the dates for a typo." % MAX_SPAN_DAYS)

    out = [analyse(habits[k], goals.get(k), as_of, args.blank_means_no) for k in order]
    warnings = []
    if skipped:
        shown = "; ".join("%s: %d (e.g. %s)" % (k, len(v), v[0]) for k, v in sorted(reasons.items()))
        warnings.append("skipped_rows: %d row(s) skipped; %s" % (skipped, shown))
    if future:
        warnings.append("future_dates: %d row(s) dated after %s were ignored" % (future, as_of.isoformat()))
    if not value_col:
        warnings.append("no_value_column: the log has no value column, so every row was counted as done")
    for k, g in sorted(goals.items()):
        if k not in habits:
            warnings.append("goal_unmatched: goal %r matches no habit in the log" % g["raw"])
    summary = {}
    for h in out:
        summary[h["verdict"]] = summary.get(h["verdict"], 0) + 1
    return {
        "schema_version": SCHEMA_VERSION, "command": "review", "file": args.file,
        "as_of": as_of.isoformat(), "blank_means": "not_done" if args.blank_means_no else "unknown",
        "date_order": args.date_order, "rows_read": len(rows), "rows_used": used,
        "habits": out, "warnings": sorted(warnings), "summary": summary,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review a habit log with plain arithmetic.")
    parser.add_argument("file", help="CSV log, or - for standard input")
    parser.add_argument("--as-of", help="review date, YYYY-MM-DD (default: the latest date in the log; pass today's date)")
    parser.add_argument("--goal", action="append", default=[], help='e.g. "Reading=daily>=20" or "Run=3/week"')
    parser.add_argument("--blank-means-no", action="store_true", help="a day with no row counts as not done")
    parser.add_argument("--date-order", choices=["dmy", "mdy"], help="needed for dates like 03/04/2026")
    args = parser.parse_args(argv)
    try:
        report = build_report(args)
    except InputError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, indent=2))
    flagged = bool(report["warnings"]) or any(h["warnings"] for h in report["habits"])
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
