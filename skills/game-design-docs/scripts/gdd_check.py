#!/usr/bin/env python3
"""Validate a game design document (Markdown) and an economy table (CSV).

    python gdd_check.py --gdd design.md
    python gdd_check.py --economy economy.csv [--max-hours 20] [--exempt-resource xp]
    python gdd_check.py --gdd design.md --economy economy.csv

Reads the files it is given and writes nothing. Prints ONE JSON object to stdout
(schema_version 1). Messages for humans go to stderr only on usage errors.

Exit codes: 0 = no error findings (warnings allowed), 1 = at least one error
finding, 2 = usage problem or unreadable/empty file (JSON with "error" is still
printed).

JSON contract
    {"schema_version": 1, "tool": "gdd_check", "ok": bool,
     "inputs": {"gdd": str|null, "economy": str|null},
     "summary": {"errors": int, "warnings": int},
     "findings": [{"severity": "error"|"warning", "code": str, "where": str,
                   "message": str}],
     "gdd": null | {"sections_found": [str], "pillars": int, "mechanics": int,
                    "progression_tiers": int},
     "economy": null | {"resources": {name: {"sources": float, "sinks": float}},
                        "tiers": [{"tier": int, "resource": str, "cost": float,
                                   "net_per_hour": float, "hours": float|null,
                                   "limit_hours": float}],
                        "exempt_resources": [str]}}
    Findings are sorted by severity (errors first), then where, then code.

The GDD must use the headings defined in references/gdd-format.md. The economy
CSV needs the columns id,type,resource,amount and optionally tier. For a source
or sink, amount is units per hour of average play and tier is the first tier at
which the flow is active (default 1). For a tier row, amount is the one-time
cost to reach that tier and tier is the tier being bought (2, 3, ...).
Heuristic checks (feedback channel words, inflation ratio) are warnings, never
errors, because they can be wrong in context.
"""
import argparse
import csv
import io
import json
import re
import sys

SCHEMA_VERSION = 1

REQUIRED_SECTIONS = ["core loop", "pillars", "mechanics", "progression", "economy",
                     "scope budget", "playtest plan"]
MAX_PILLARS = 3  # more than three pillars stop settling disputes; rule from the skill
MIN_LOOP_STEPS, MAX_LOOP_STEPS = 3, 6  # fewer is not a loop, more is two loops glued together
PLACEHOLDERS = {"", "tbd", "todo", "n/a", "na", "none", "-", "?", "...", "tba", "later"}
FEEDBACK_WORDS = ("visual", "audio", "sound", "sfx", "haptic", "vibrat", "ui", "hud", "animation",
                  "particle", "shake", "flash", "popup", "pop-up", "text", "number", "music",
                  "color", "colour", "bar", "icon", "voice", "screen")
MUST_SHARE_LIMIT = 0.8  # must-have work above 80% of capacity leaves no buffer for the unknown
MIN_PLAYTEST_QUESTIONS = 3  # one question is an opinion poll, three can steer a build
INFLATION_RATIO = 2.0  # sources above 2x sinks at full unlock: currency piles up (working value)
DEFAULT_MAX_HOURS = 20.0  # hours of average play to afford one tier when the GDD gives no target
TARGET_TOLERANCE = 1.5  # a tier may take 1.5x its GDD target hours before it is an error
ECON_TYPES = {"source", "sink", "tier"}

FIELDS = (("inputs", "inputs?"), ("outputs", "outputs?"), ("feedback", "feedback"))


class Usage(Exception):
    pass


class Findings:
    def __init__(self):
        self.items = []

    def add(self, severity, code, where, message):
        self.items.append({"severity": severity, "code": code, "where": where, "message": message})

    def error(self, code, where, message):
        self.add("error", code, where, message)

    def warn(self, code, where, message):
        self.add("warning", code, where, message)


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except FileNotFoundError:
        raise Usage("file not found: " + path)
    except (OSError, UnicodeDecodeError) as exc:
        raise Usage("cannot read %s as UTF-8: %s" % (path, exc))
    if not text.strip():
        raise Usage("file is empty: " + path)
    return text


def is_placeholder(value):
    v = value.strip().strip("*_`").strip().lower()
    return v in PLACEHOLDERS or bool(re.match(r"^<[^>]*>$", v))  # <angle-bracket> prompts from the template


def to_number(value):
    try:
        return float(value.strip().replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------- Markdown parsing

def split_sections(text):
    """Return (title, ordered list of (name_lower, raw_name, body_lines)). Fences are skipped."""
    title, sections, current, in_fence = None, [], None, False
    for line in text.splitlines():
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            if current is not None:
                current[2].append(line)
            continue
        if not in_fence:
            m2 = re.match(r"^##\s+(.+?)\s*#*\s*$", line)
            if m2 and not line.startswith("###"):
                current = (m2.group(1).strip().lower(), m2.group(1).strip(), [])
                sections.append(current)
                continue
            m1 = re.match(r"^#\s+(.+?)\s*#*\s*$", line)
            if m1 and title is None:
                title = m1.group(1)
                continue
        if current is not None:
            current[2].append(line)
    return title, sections


def content_lines(body):
    return [ln for ln in body if ln.strip() and not re.match(r"^#{1,6}\s", ln)]


def parse_tables(body):
    """Return list of (header_cells_lower, rows) for each pipe table in body."""
    tables, block = [], []
    for ln in body + [""]:
        if ln.strip().startswith("|"):
            block.append(ln.strip())
        else:
            if len(block) >= 2:
                rows = [[c.strip() for c in r.strip("|").split("|")] for r in block]
                if all(re.match(r"^:?-{2,}:?$", c.replace(" ", "")) for c in rows[1] if c):
                    tables.append(([c.lower() for c in rows[0]], rows[2:]))
            block = []
    return tables


def find_col(header, *needles):
    for i, h in enumerate(header):
        if any(n in h for n in needles):
            return i
    return None


def field_value(lines, name_pattern):
    pat = re.compile(r"^\s*(?:[-*+]\s+)?\**_?(?:%s)_?\**\s*:\**\s*(.*)$" % name_pattern, re.I)
    for ln in lines:
        m = pat.match(ln)
        if m:
            return m.group(1).strip()
    return None


# ---------------------------------------------------------------- GDD checks

def check_gdd(text, f, summary):
    title, sections = split_sections(text)
    by_name = {}
    for low, raw, body in sections:
        if low in by_name:
            f.warn("section-duplicate", "gdd:" + raw, "heading '## %s' appears more than once; only the first is checked" % raw)
        else:
            by_name[low] = body
    if title is None:
        f.warn("title-missing", "gdd", "no '# Title' line at the top")
    for name in REQUIRED_SECTIONS:
        if name not in by_name:
            f.error("section-missing", "gdd:" + name, "required heading '## %s' is missing" % name.title())
        elif not content_lines(by_name[name]):
            f.error("section-empty", "gdd:" + name, "section '## %s' has no content" % name.title())
    summary["sections_found"] = [n for n in REQUIRED_SECTIONS if n in by_name]

    if "core loop" in by_name:
        check_core_loop(by_name["core loop"], f)
    summary["pillars"] = check_pillars(by_name.get("pillars"), f)
    summary["mechanics"] = check_mechanics(by_name.get("mechanics"), f)
    tiers = check_progression(by_name.get("progression"), f)
    summary["progression_tiers"] = len(tiers)
    if "economy" in by_name and field_value(by_name["economy"], "table") is None:
        f.warn("economy-no-table-line", "gdd:economy", "no 'Table: <file.csv>' line; the economy numbers should live in the CSV")
    if "scope budget" in by_name:
        check_scope(by_name["scope budget"], f)
    if "playtest plan" in by_name:
        check_playtest(by_name["playtest plan"], f)
    return tiers


def check_core_loop(body, f):
    loop = field_value(body, "loop")
    if loop is None or is_placeholder(loop):
        f.error("core-loop-no-statement", "gdd:core loop", "no 'Loop: step -> step -> step' line")
    else:
        steps = [s.strip() for s in re.split(r"->|→", loop) if s.strip()]
        if not MIN_LOOP_STEPS <= len(steps) <= MAX_LOOP_STEPS:
            f.error("core-loop-steps", "gdd:core loop", "loop has %d steps; write %d to %d steps joined by '->'" % (len(steps), MIN_LOOP_STEPS, MAX_LOOP_STEPS))
    cycle = field_value(body, "cycle time")
    if cycle is None or not re.search(r"\d+(\.\d+)?\s*(s|sec|secs|seconds?|m|min|mins|minutes?|h|hours?)\b", cycle, re.I):
        f.error("core-loop-no-cycle-time", "gdd:core loop", "no 'Cycle time: <number> <unit>' line; state how long one pass of the loop takes")


def check_pillars(body, f):
    if body is None:
        return 0
    items = []
    for ln in body:
        m = re.match(r"^\s{0,1}([-*+]|\d+[.)])\s+(.+)$", ln)
        if m:
            items.append(m.group(2).strip())
    if not items and content_lines(body):
        f.error("pillars-none", "gdd:pillars", "no list items found; write each pillar as a '-' or numbered item")
    if len(items) > MAX_PILLARS:
        f.error("pillars-too-many", "gdd:pillars", "%d pillars; the limit is %d. Merge or cut." % (len(items), MAX_PILLARS))
    for it in items:
        if len(re.findall(r"\w+", it)) < 4:
            f.warn("pillar-thin", "gdd:pillars", "pillar '%s' has under 4 words; add the design decision it settles" % it[:40])
    return len(items)


def split_h3(body):
    subs, cur = [], None
    for ln in body:
        m = re.match(r"^###\s+(.+?)\s*#*\s*$", ln)
        if m:
            cur = (m.group(1).strip(), [])
            subs.append(cur)
        elif cur is not None:
            cur[1].append(ln)
    return subs


def check_mechanics(body, f):
    if body is None:
        return 0
    subs = split_h3(body)
    if not subs and content_lines(body):
        f.error("mechanics-none", "gdd:mechanics", "no '### <Mechanic name>' subsections found")
    for name, lines in subs:
        where = "gdd:mechanics:" + name
        for fld, pattern in FIELDS:
            val = field_value(lines, pattern)
            if val is None:
                f.error("mechanic-missing-" + fld, where, "mechanic '%s' has no '%s:' line" % (name, fld.title()))
            elif is_placeholder(val):
                f.error("mechanic-placeholder-" + fld, where, "mechanic '%s' leaves %s as '%s'; define it" % (name, fld.title(), val))
            elif fld == "feedback" and not any(w in val.lower() for w in FEEDBACK_WORDS):
                f.warn("mechanic-feedback-no-channel", where, "feedback of '%s' names no channel (visual, audio, haptic, UI...)" % name)
    return len(subs)


def check_progression(body, f):
    """Return list of (tier, hours or None)."""
    if body is None:
        return []
    tables = parse_tables(body)
    if not tables:
        f.error("progression-no-table", "gdd:progression", "no table; use columns Tier | Unlock | Target hours")
        return []
    header, rows = tables[0]
    ti, hi = find_col(header, "tier"), find_col(header, "hour")
    if ti is None or hi is None:
        f.error("progression-columns", "gdd:progression", "table needs a 'Tier' column and a 'Target hours' column")
        return []
    tiers = []
    for r in rows:
        m = re.search(r"\d+", r[ti]) if ti < len(r) else None
        hours = to_number(r[hi]) if hi < len(r) else None
        if not m:
            f.error("progression-bad-tier", "gdd:progression", "row has no tier number: %s" % "|".join(r)[:60])
            continue
        if hours is None or hours < 0:
            f.error("progression-bad-hours", "gdd:progression", "tier %s has no numeric target hours" % m.group(0))
        tiers.append((int(m.group(0)), hours))
    nums = sorted(t for t, _ in tiers)
    if len(tiers) < 2:
        f.error("progression-too-few", "gdd:progression", "a progression needs at least 2 tiers")
    if nums and nums != list(range(1, len(nums) + 1)):
        f.error("progression-tier-gap", "gdd:progression", "tiers must be numbered 1..N without gaps or repeats; found %s" % nums)
    return tiers


def check_scope(body, f):
    cap_text = field_value(body, "capacity")
    cap_m = re.search(r"\d+(\.\d+)?", cap_text or "")
    capacity = float(cap_m.group(0)) if cap_m else None
    if capacity is None or capacity <= 0:
        f.error("scope-no-capacity", "gdd:scope budget", "no 'Capacity: <N> weeks' line with a positive number")
    tables = parse_tables(body)
    if not tables:
        f.error("scope-no-table", "gdd:scope budget", "no table; use columns Feature | Weeks | Priority")
        return
    header, rows = tables[0]
    fi, wi, pi = find_col(header, "feature", "item"), find_col(header, "week"), find_col(header, "priority")
    if None in (fi, wi, pi):
        f.error("scope-columns", "gdd:scope budget", "table needs Feature, Weeks and Priority columns")
        return
    must = total = 0.0
    for r in rows:
        weeks = to_number(r[wi]) if wi < len(r) else None
        prio = r[pi].strip().lower() if pi < len(r) else ""
        label = r[fi] if fi < len(r) else "?"
        if weeks is None or weeks <= 0:
            f.error("scope-bad-weeks", "gdd:scope budget", "feature '%s' has no positive numeric weeks" % label)
            continue
        if prio not in ("must", "should", "could"):
            f.error("scope-bad-priority", "gdd:scope budget", "feature '%s' priority '%s' is not must, should or could" % (label, prio))
            continue
        total += weeks
        if prio == "must":
            must += weeks
    if capacity:
        if must > MUST_SHARE_LIMIT * capacity:
            f.error("scope-must-over-limit", "gdd:scope budget", "must-have work is %g weeks, over %d%% of the %g-week capacity (%g)" % (must, MUST_SHARE_LIMIT * 100, capacity, MUST_SHARE_LIMIT * capacity))
        if total > capacity:
            f.warn("scope-total-over-capacity", "gdd:scope budget", "all listed work is %g weeks against %g capacity; the should/could rows are the cut list" % (total, capacity))


def check_playtest(body, f):
    tables = parse_tables(body)
    if not tables:
        f.error("playtest-no-table", "gdd:playtest plan", "no table; use columns Question | Metric | Pass threshold | Sample")
        return
    header, rows = tables[0]
    qi, mi, ti = find_col(header, "question"), find_col(header, "metric"), find_col(header, "threshold", "pass")
    if None in (qi, mi, ti):
        f.error("playtest-columns", "gdd:playtest plan", "table needs Question, Metric and Pass threshold columns")
        return
    if find_col(header, "sample", "player", "participant") is None:
        f.warn("playtest-no-sample", "gdd:playtest plan", "no Sample column; say how many players each question needs")
    good = 0
    for r in rows:
        q = r[qi] if qi < len(r) else "?"
        metric = r[mi] if mi < len(r) else ""
        thr = r[ti] if ti < len(r) else ""
        if is_placeholder(metric):
            f.error("playtest-no-metric", "gdd:playtest plan", "question '%s' has no metric" % q[:50])
        elif not re.search(r"\d", thr):
            f.error("playtest-no-threshold", "gdd:playtest plan", "question '%s' has no numeric pass threshold" % q[:50])
        else:
            good += 1
    if good < MIN_PLAYTEST_QUESTIONS:
        f.error("playtest-too-few", "gdd:playtest plan", "%d measurable questions; need at least %d" % (good, MIN_PLAYTEST_QUESTIONS))


# ---------------------------------------------------------------- economy checks

def check_economy(text, f, max_hours, exempt, targets):
    reader = csv.DictReader(io.StringIO(text))
    cols = [c.strip().lower() for c in (reader.fieldnames or [])]
    missing = [c for c in ("id", "type", "resource", "amount") if c not in cols]
    if missing:
        f.error("economy-columns", "economy", "missing column(s): %s (need id,type,resource,amount[,tier])" % ", ".join(missing))
        return None
    res, tiers, seen = {}, [], set()
    for n, raw in enumerate(reader, 2):
        row = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        where = "economy:line %d" % n
        rid, typ, resource = row.get("id", ""), row.get("type", "").lower(), row.get("resource", "").lower()
        if rid in seen:
            f.error("economy-duplicate-id", where, "id '%s' is used twice" % rid)
        seen.add(rid)
        amount = to_number(row.get("amount", ""))
        if typ not in ECON_TYPES:
            f.error("economy-bad-type", where, "type '%s' is not source, sink or tier" % typ)
            continue
        if not resource or amount is None or amount <= 0:
            f.error("economy-bad-row", where, "row '%s' needs a resource and a positive numeric amount" % rid)
            continue
        ft = to_number(row.get("tier", "")) if row.get("tier", "") else 1
        if ft is None or ft < 1 or ft != int(ft):
            f.error("economy-bad-from-tier", where, "tier '%s' must be a whole number >= 1" % row.get("tier"))
            continue
        ft = int(ft)
        if typ == "tier":
            tiers.append({"tier": ft, "resource": resource, "cost": amount})
        else:
            res.setdefault(resource, []).append((typ, amount, ft))
    summary_res = {}
    for name, flows in sorted(res.items()):
        s = sum(a for t, a, _ in flows if t == "source")
        k = sum(a for t, a, _ in flows if t == "sink")
        summary_res[name] = {"sources": round(s, 4), "sinks": round(k, 4)}
        if name in exempt:
            continue
        if s > 0 and k == 0:
            f.error("source-without-sink", "economy:" + name, "'%s' enters the game (%g per hour) but nothing recurring removes it; add a sink or pass --exempt-resource %s" % (name, s, name))
        elif k > 0 and s == 0:
            f.error("sink-without-source", "economy:" + name, "'%s' is spent (%g per hour) but nothing produces it" % (name, k))
        elif s > INFLATION_RATIO * k:
            f.warn("inflation-risk", "economy:" + name, "sources are %.2fx sinks at full unlock (limit %.1fx); the currency will pile up" % (s / k, INFLATION_RATIO))
    tier_out = check_tiers(tiers, res, f, max_hours, targets)
    return {"resources": summary_res, "tiers": tier_out, "exempt_resources": sorted(exempt)}


def check_tiers(tiers, res, f, max_hours, targets):
    out = []
    nums = sorted(t["tier"] for t in tiers)
    if nums and nums != list(range(2, len(nums) + 2)):
        f.error("tier-gap", "economy", "tier rows must be numbered 2..N without gaps or repeats (tier 1 is the start); found %s" % nums)
    prev_cost = {}
    for t in sorted(tiers, key=lambda x: x["tier"]):
        flows = res.get(t["resource"], [])
        active = [(typ, a) for typ, a, ft in flows if ft <= t["tier"] - 1]
        src = sum(a for typ, a in active if typ == "source")
        snk = sum(a for typ, a in active if typ == "sink")
        net = src - snk
        limit = targets[t["tier"]] * TARGET_TOLERANCE if targets.get(t["tier"]) else max_hours
        where = "economy:tier %d" % t["tier"]
        hours = None
        if not any(typ == "source" for typ, _, _ in flows):
            f.error("tier-unreachable", where, "tier %d costs '%s' but no source of '%s' exists" % (t["tier"], t["resource"], t["resource"]))
        elif net <= 0:
            f.error("tier-unreachable", where, "tier %d: with flows active before it, '%s' nets %g per hour (sources %g, sinks %g); the player can never afford %g" % (t["tier"], t["resource"], net, src, snk, t["cost"]))
        else:
            hours = t["cost"] / net
            if hours > limit:
                f.error("tier-too-slow", where, "tier %d needs %.1f hours of play to afford %g (net %g per hour); limit %.1f" % (t["tier"], hours, t["cost"], net, limit))
        if t["resource"] in prev_cost and t["cost"] < prev_cost[t["resource"]]:
            f.warn("tier-cost-decreases", where, "tier %d costs less than the previous tier paid in '%s'" % (t["tier"], t["resource"]))
        prev_cost[t["resource"]] = t["cost"]
        out.append({"tier": t["tier"], "resource": t["resource"], "cost": t["cost"], "net_per_hour": round(net, 4),
                    "hours": None if hours is None else round(hours, 2), "limit_hours": round(limit, 2)})
    return out


# ---------------------------------------------------------------- main

def build_parser():
    p = argparse.ArgumentParser(prog="gdd_check.py", description="Validate a GDD (Markdown) and an economy table (CSV).")
    p.add_argument("--gdd", help="path to the GDD Markdown file")
    p.add_argument("--economy", help="path to the economy CSV file")
    p.add_argument("--max-hours", type=float, default=DEFAULT_MAX_HOURS, help="hours allowed to afford one tier when no GDD target exists (default 20)")
    p.add_argument("--exempt-resource", action="append", default=[], help="resource allowed to have no sink (repeatable)")
    return p


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=True) + "\n")


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    inputs = {"gdd": args.gdd, "economy": args.economy}
    try:
        if not args.gdd and not args.economy:
            raise Usage("give --gdd, --economy or both")
        gdd_text = read_file(args.gdd) if args.gdd else None
        econ_text = read_file(args.economy) if args.economy else None
    except Usage as exc:
        sys.stderr.write(str(exc) + "\n")
        emit({"schema_version": SCHEMA_VERSION, "tool": "gdd_check", "ok": False, "inputs": inputs, "error": str(exc)})
        return 2
    f = Findings()
    gdd_info, tiers = None, []
    if gdd_text is not None:
        gdd_info = {}
        tiers = check_gdd(gdd_text, f, gdd_info)
    econ_info = None
    if econ_text is not None:
        targets = {t: h for t, h in tiers if h}
        econ_info = check_economy(econ_text, f, args.max_hours, {r.lower() for r in args.exempt_resource}, targets)
        if econ_info is not None and gdd_info is not None and tiers:
            csv_count = 1 + len(econ_info["tiers"])
            if csv_count != len(tiers):
                f.error("tier-count-mismatch", "gdd+economy", "GDD progression lists %d tiers, economy CSV defines %d" % (len(tiers), csv_count))
    items = sorted(f.items, key=lambda x: (x["severity"] != "error", x["where"], x["code"]))
    errors = sum(1 for i in items if i["severity"] == "error")
    emit({"schema_version": SCHEMA_VERSION, "tool": "gdd_check", "ok": errors == 0, "inputs": inputs,
          "summary": {"errors": errors, "warnings": len(items) - errors}, "findings": items,
          "gdd": gdd_info, "economy": econ_info})
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
