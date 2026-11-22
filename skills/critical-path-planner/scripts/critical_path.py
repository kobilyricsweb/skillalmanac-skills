#!/usr/bin/env python3
"""Critical-path schedule from a task list with durations and predecessors.

Usage:
    python critical_path.py INPUT.json [--out REPORT.json] [--force]
    python critical_path.py -            (read the plan from standard input)

Reads one JSON plan (see the skill's SKILL.md for the keys). Prints one strict
JSON report on standard output. With --out it also writes the same JSON to
REPORT.json; it refuses an output path that is the input file (even with
--force), and refuses an existing output file unless --force is given.

What it computes (finish-to-start dependencies only):
  * dangling predecessors, duplicate predecessors, dependency cycles
  * earliest start/finish (es/ef), latest start/finish (ls/lf), total slack,
    free slack, the critical flag and every critical path
  * working-day dates when unit is "days" and a start_date is given
  * the gap to a deadline, and owners who have more tasks in progress on one
    day than their capacity (a plain per-day count; nothing is levelled)

Exit codes: 0 clean, 1 findings (any error or warning), 2 bad input or output
path. Python 3.9+, standard library only, no network, nothing is executed.
"""
import argparse
import datetime
import json
import os
import sys

SCHEMA_VERSION = 1

# A task is "at risk" when its slack is at most this share of the project
# length (minimum 1 unit): a delay of that size starts to eat the whole buffer.
AT_RISK_PERCENT = 10
# Sanity limits so a typo (a duration of 1e9) fails loudly instead of hanging.
MAX_TASKS = 5000
MAX_DURATION = 3650
# Enumerating every critical path can explode on wide plans; report this many.
MAX_PATHS = 50
# Upper bound on calendar days scanned when mapping working days to dates.
MAX_CALENDAR_SCAN = 200000
DEFAULT_WORKING_DAYS = (1, 2, 3, 4, 5)  # ISO weekday numbers, Monday is 1


class InputError(Exception):
    """The plan or an output path cannot be used; the message says what to fix."""


def parse_date(value, label):
    if not isinstance(value, str):
        raise InputError("%s must be a date string like 2026-03-02" % label)
    try:
        return datetime.date.fromisoformat(value.strip())
    except ValueError:
        raise InputError("%s is not a valid YYYY-MM-DD date: %r" % (label, value))


def load_plan(path):
    try:
        if path == "-":
            text = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8-sig") as handle:
                text = handle.read()
    except OSError as exc:
        raise InputError("cannot read input %s: %s" % (path, exc.strerror or exc))
    except UnicodeDecodeError:
        raise InputError("input is not valid UTF-8 text")
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise InputError("input is not valid JSON: %s" % exc)
    if not isinstance(data, dict):
        raise InputError("the plan must be a JSON object with a 'tasks' list")
    return data


def as_pred_list(raw, task_id):
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = raw.split(",")
    if not isinstance(raw, list):
        raise InputError("task %s: predecessors must be a list of ids or a comma-separated string" % task_id)
    out = []
    for item in raw:
        if isinstance(item, bool) or not isinstance(item, (str, int)):
            raise InputError("task %s: each predecessor must be a task id" % task_id)
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def normalise(data):
    unit = str(data.get("unit", "days")).strip() or "days"
    raw_tasks = data.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise InputError("'tasks' must be a non-empty list")
    if len(raw_tasks) > MAX_TASKS:
        raise InputError("more than %d tasks; split the plan" % MAX_TASKS)

    tasks = []
    seen = set()
    for index, raw in enumerate(raw_tasks):
        if not isinstance(raw, dict):
            raise InputError("tasks[%d] must be an object" % index)
        tid = raw.get("id")
        if isinstance(tid, bool) or not isinstance(tid, (str, int)) or not str(tid).strip():
            raise InputError("tasks[%d] needs a non-empty 'id'" % index)
        tid = str(tid).strip()
        if tid in seen:
            raise InputError("duplicate task id %r; ids must be unique" % tid)
        seen.add(tid)
        dur = raw.get("duration")
        if isinstance(dur, bool) or not isinstance(dur, (int, float)):
            raise InputError("task %s: 'duration' must be a number in whole %s" % (tid, unit))
        if isinstance(dur, float) and not dur.is_integer():
            raise InputError("task %s: duration %s is not a whole number; pick a smaller unit" % (tid, dur))
        dur = int(dur)
        if dur < 0 or dur > MAX_DURATION:
            raise InputError("task %s: duration must be between 0 and %d" % (tid, MAX_DURATION))
        owner = raw.get("owner")
        owner = str(owner).strip() if owner not in (None, "") else None
        name = raw.get("name")
        name = str(name) if name not in (None, "") else tid
        tasks.append({
            "id": tid, "name": name, "duration": dur, "owner": owner,
            "predecessors": as_pred_list(raw.get("predecessors"), tid),
        })

    plan = {"unit": unit, "tasks": tasks, "info": []}

    days = data.get("working_days", list(DEFAULT_WORKING_DAYS))
    if (not isinstance(days, list) or not days
            or any(isinstance(d, bool) or not isinstance(d, int) or d < 1 or d > 7 for d in days)):
        raise InputError("'working_days' must be a non-empty list of ISO weekdays 1 (Mon) to 7 (Sun)")
    plan["working_days"] = set(days)
    holidays = data.get("holidays", [])
    if not isinstance(holidays, list):
        raise InputError("'holidays' must be a list of dates")
    plan["holidays"] = set(parse_date(h, "holiday") for h in holidays)

    start = data.get("start_date")
    plan["start"] = parse_date(start, "start_date") if start is not None else None
    if plan["start"] is not None and unit != "days":
        plan["info"].append("start_date ignored because unit is %r, not 'days'; only offsets are reported" % unit)
        plan["start"] = None

    deadline = data.get("deadline")
    deadline_days = data.get("deadline_days")
    if deadline is not None and deadline_days is not None:
        raise InputError("give 'deadline' (a date) or 'deadline_days' (a count), not both")
    plan["deadline"] = None
    plan["deadline_days"] = None
    if deadline is not None:
        if plan["start"] is None:
            raise InputError("'deadline' as a date needs unit 'days' and a 'start_date'; use 'deadline_days' instead")
        plan["deadline"] = parse_date(deadline, "deadline")
    if deadline_days is not None:
        if isinstance(deadline_days, bool) or not isinstance(deadline_days, int) or deadline_days < 0:
            raise InputError("'deadline_days' must be a whole number of %s, 0 or more" % unit)
        plan["deadline_days"] = deadline_days

    capacity = data.get("capacity", {})
    if not isinstance(capacity, dict):
        raise InputError("'capacity' must map owner names to whole numbers")
    plan["capacity"] = {}
    for owner, cap in capacity.items():
        if isinstance(cap, bool) or not isinstance(cap, int) or cap < 1:
            raise InputError("capacity for %s must be a whole number of 1 or more" % owner)
        plan["capacity"][str(owner).strip()] = cap
    default_cap = data.get("default_capacity", 1)
    if isinstance(default_cap, bool) or not isinstance(default_cap, int) or default_cap < 1:
        raise InputError("'default_capacity' must be a whole number of 1 or more")
    plan["default_capacity"] = default_cap
    return plan


def find_cycles(ids, preds):
    """Strongly connected components with a cycle, each as one concrete loop."""
    succ = dict((i, []) for i in ids)
    for v in ids:
        for u in preds[v]:
            succ[u].append(v)
    position = dict((tid, n) for n, tid in enumerate(ids))
    index, low, on_stack, stack, comps = {}, {}, set(), [], []
    counter = 0
    for root in ids:
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        work = [(root, 0)]
        while work:
            node, i = work[-1]
            if i < len(succ[node]):
                work[-1] = (node, i + 1)
                nxt = succ[node][i]
                if nxt not in index:
                    index[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, 0))
                elif nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
            else:
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    comp = []
                    while True:
                        w = stack.pop()
                        on_stack.discard(w)
                        comp.append(w)
                        if w == node:
                            break
                    comps.append(comp)
    cycles = []
    for comp in comps:
        if len(comp) == 1 and comp[0] not in succ[comp[0]]:
            continue
        members = set(comp)
        start = min(comp, key=lambda t: position[t])
        walk = [start]
        cur = start
        while True:
            nxt = next(s for s in succ[cur] if s in members)
            if nxt in walk:
                cycles.append(walk[walk.index(nxt):] + [nxt])
                break
            walk.append(nxt)
            cur = nxt
    cycles.sort(key=lambda c: position[c[0]])
    return cycles


def working_dates(start, plan, count):
    """The first `count` working dates on or after start."""
    out = []
    day = start
    scanned = 0
    while len(out) < count:
        if day.isoweekday() in plan["working_days"] and day not in plan["holidays"]:
            out.append(day)
        day += datetime.timedelta(days=1)
        scanned += 1
        if scanned > MAX_CALENDAR_SCAN:
            raise InputError("the working calendar has too few working days; check working_days and holidays")
    return out


def count_working_days(start, end, plan):
    if end < start:
        raise InputError("deadline %s is before start_date %s" % (end, start))
    if (end - start).days > MAX_CALENDAR_SCAN:
        raise InputError("deadline is too far from start_date")
    total = 0
    day = start
    while day <= end:
        if day.isoweekday() in plan["working_days"] and day not in plan["holidays"]:
            total += 1
        day += datetime.timedelta(days=1)
    return total


def critical_paths(ids, preds, es, ef, slack):
    tight = dict((v, []) for v in ids)
    has_tight_pred = set()
    for v in ids:
        for u in preds[v]:
            if slack[u] == 0 and slack[v] == 0 and ef[u] == es[v]:
                tight[u].append(v)
                has_tight_pred.add(v)
    starts = [t for t in ids if slack[t] == 0 and t not in has_tight_pred]
    paths = []
    truncated = False
    work = [[s] for s in reversed(starts)]
    while work:
        if len(paths) >= MAX_PATHS:
            truncated = True
            break
        path = work.pop()
        kids = tight[path[-1]]
        if not kids:
            paths.append(path)
        else:
            for kid in reversed(kids):
                work.append(path + [kid])
    return paths, truncated


def overloads(plan, tasks_out, es, ef, dates):
    """Per-day count of in-progress tasks per owner against capacity."""
    by_owner = {}
    for task in plan["tasks"]:
        if task["owner"] and task["duration"] > 0:
            by_owner.setdefault(task["owner"], []).append(task["id"])
    found = []
    for owner in sorted(by_owner):
        cap = plan["capacity"].get(owner, plan["default_capacity"])
        active = {}
        for tid in by_owner[owner]:
            for day in range(es[tid], ef[tid]):
                active.setdefault(day, []).append(tid)
        run = None
        for day in sorted(active):
            if len(active[day]) > cap:
                if run and run["to_day"] == day - 1 and run["tasks"] == active[day]:
                    run["to_day"] = day
                else:
                    run = {"owner": owner, "from_day": day, "to_day": day, "tasks": list(active[day]),
                           "count": len(active[day]), "capacity": cap}
                    found.append(run)
            else:
                run = None
    for item in found:
        item["from_date"] = dates[item["from_day"]].isoformat() if dates else None
        item["to_date"] = dates[item["to_day"]].isoformat() if dates else None
        item["slack"] = dict((t, tasks_out[t]["slack"]) for t in item["tasks"])
    return found


def build_report(plan):
    tasks = plan["tasks"]
    ids = [t["id"] for t in tasks]
    known = set(ids)
    warnings = []

    preds = {}
    for t in tasks:
        seen, clean = set(), []
        for p in t["predecessors"]:
            if p in seen:
                warnings.append({"rule": "duplicate_predecessor", "severity": "warning", "task": t["id"],
                                 "message": "task %s lists predecessor %s more than once; counted once" % (t["id"], p)})
            else:
                seen.add(p)
                clean.append(p)
        t["predecessors"] = clean
    dangling = []
    for t in tasks:
        for p in t["predecessors"]:
            if p not in known:
                dangling.append({"task": t["id"], "predecessor": p})
                warnings.append({"rule": "dangling_predecessor", "severity": "error", "task": t["id"],
                                 "message": "task %s depends on %s, which is not in the plan; the link is ignored" % (t["id"], p)})
    for t in tasks:
        preds[t["id"]] = [p for p in t["predecessors"] if p in known]

    cycles = find_cycles(ids, preds)
    for cyc in cycles:
        warnings.append({"rule": "cycle", "severity": "error", "tasks": cyc[:-1],
                         "message": "dependency cycle %s; no schedule can be computed until one link is cut" % " -> ".join(cyc)})

    has_succ = set(p for t in ids for p in preds[t])
    if len(tasks) > 1:
        for t in ids:
            if not t_has_any_pred(tasks, t) and t not in has_succ:
                warnings.append({"rule": "isolated_task", "severity": "warning", "task": t,
                                 "message": "task %s has no predecessors and no successors; a dependency may be missing" % t})

    report = {
        "schema_version": SCHEMA_VERSION, "command": "schedule", "ok": False, "unit": plan["unit"],
        "scheduled": False, "project_duration": None, "start_date": None, "finish_date": None,
        "deadline": plan["deadline"].isoformat() if plan["deadline"] else None,
        "deadline_days": None, "deadline_gap": None, "critical_count": None,
        "at_risk_percent": AT_RISK_PERCENT, "tasks": [], "paths": [], "cycles": cycles,
        "dangling": dangling, "overloads": [], "warnings": warnings,
    }
    for text in plan["info"]:
        warnings.append({"rule": "note", "severity": "info", "message": text})

    if cycles:
        for t in tasks:
            report["tasks"].append({"id": t["id"], "name": t["name"], "owner": t["owner"],
                                    "duration": t["duration"], "predecessors": t["predecessors"]})
        return report

    # Topological order (Kahn). Input order breaks ties so output is stable.
    remaining = dict((t, len(preds[t])) for t in ids)
    succ = dict((t, []) for t in ids)
    for t in ids:
        for p in preds[t]:
            succ[p].append(t)
    ready = [t for t in ids if remaining[t] == 0]
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for s in succ[node]:
            remaining[s] -= 1
            if remaining[s] == 0:
                ready.append(s)

    dur = dict((t["id"], t["duration"]) for t in tasks)
    es, ef, ls, lf = {}, {}, {}, {}
    for t in order:
        es[t] = max([ef[p] for p in preds[t]] or [0])
        ef[t] = es[t] + dur[t]
    total = max(ef.values())
    for t in reversed(order):
        lf[t] = min([ls[s] for s in succ[t]] or [total])
        ls[t] = lf[t] - dur[t]
    slack = dict((t, ls[t] - es[t]) for t in ids)
    free = dict((t, min([es[s] for s in succ[t]] or [total]) - ef[t]) for t in ids)
    at_risk_limit = max(1, -(-total * AT_RISK_PERCENT // 100))

    dates = None
    if plan["start"] is not None:
        dates = working_dates(plan["start"], plan, total + 1)
        if dates[0] != plan["start"]:
            warnings.append({"rule": "note", "severity": "info",
                             "message": "start_date %s is not a working day; the plan starts on %s" % (plan["start"], dates[0])})
        report["start_date"] = dates[0].isoformat()
        report["finish_date"] = dates[max(total - 1, 0)].isoformat()

    deadline_days = plan["deadline_days"]
    if plan["deadline"] is not None:
        deadline_days = count_working_days(plan["start"], plan["deadline"], plan)
    gap = None
    if deadline_days is not None:
        gap = deadline_days - total
        report["deadline_days"] = deadline_days
        report["deadline_gap"] = gap
        if gap < 0:
            warnings.append({"rule": "deadline_missed", "severity": "error",
                             "message": "the plan needs %d %s but the deadline allows %d: %d late" % (total, plan["unit"], deadline_days, -gap)})

    by_id = {}
    for t in tasks:
        tid = t["id"]
        row = {"id": tid, "name": t["name"], "owner": t["owner"], "duration": dur[tid],
               "predecessors": t["predecessors"], "es": es[tid], "ef": ef[tid], "ls": ls[tid], "lf": lf[tid],
               "slack": slack[tid], "free_slack": free[tid],
               "deadline_slack": slack[tid] + gap if gap is not None else None,
               "critical": slack[tid] == 0, "at_risk": 0 < slack[tid] <= at_risk_limit,
               "start_date": None, "finish_date": None}
        if dates:
            row["start_date"] = dates[es[tid]].isoformat()
            row["finish_date"] = dates[ef[tid] - 1].isoformat() if dur[tid] > 0 else row["start_date"]
        by_id[tid] = row
        report["tasks"].append(row)

    paths, truncated = critical_paths(ids, preds, es, ef, slack)
    if truncated:
        warnings.append({"rule": "paths_truncated", "severity": "warning",
                         "message": "more than %d critical paths; the list is cut" % MAX_PATHS})
    report["scheduled"] = True
    report["project_duration"] = total
    report["critical_count"] = sum(1 for t in ids if slack[t] == 0)
    report["paths"] = paths
    report["overloads"] = overloads(plan, by_id, es, ef, dates)
    for item in report["overloads"]:
        warnings.append({"rule": "overload", "severity": "warning", "owner": item["owner"],
                         "message": "%s has %d tasks in progress on days %d-%d (capacity %d)" % (
                             item["owner"], item["count"], item["from_day"], item["to_day"], item["capacity"])})
    return report


def t_has_any_pred(tasks, tid):
    for t in tasks:
        if t["id"] == tid:
            return bool(t["predecessors"])
    return False


def emit(report):
    return json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)


def check_output_path(out, source):
    if out is None:
        return
    if source != "-" and os.path.exists(source) and os.path.exists(out) and os.path.samefile(source, out):
        raise InputError("refusing to write the report over the input file %s" % source)
    if source != "-" and os.path.realpath(source) == os.path.realpath(out):
        raise InputError("refusing to write the report over the input file %s" % source)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Critical path, slack, cycles and owner overload from a task list.")
    parser.add_argument("input", help="plan JSON file, or - for standard input")
    parser.add_argument("--out", help="also write the JSON report to this new file")
    parser.add_argument("--force", action="store_true", help="allow replacing an existing --out file (never the input)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        check_output_path(args.out, args.input)
        if args.out and os.path.exists(args.out) and not args.force:
            raise InputError("output %s already exists; pass --force to replace it" % args.out)
        report = build_report(normalise(load_plan(args.input)))
        report["ok"] = not any(w["severity"] in ("error", "warning") for w in report["warnings"])
        text = emit(report)
        if args.out:
            try:
                with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(text + "\n")
            except OSError as exc:
                raise InputError("cannot write %s: %s" % (args.out, exc.strerror or exc))
    except InputError as exc:
        sys.stderr.write("critical_path: %s\n" % exc)
        sys.stdout.write(json.dumps({"schema_version": SCHEMA_VERSION, "command": "schedule", "error": str(exc)}) + "\n")
        return 2
    sys.stdout.write(text + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
