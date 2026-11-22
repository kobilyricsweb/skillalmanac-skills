#!/usr/bin/env python3
"""Arithmetic and structure checks for a founder's weekly operating cadence.

Usage:
    python founder_ops.py metrics <monthly.csv>
    python founder_ops.py review <weekly_review.md>

metrics  Reads a CSV with columns month (YYYY-MM), revenue, cash_out, cash_balance
         (one row per month, oldest first; month-end balance). Prints JSON with gross
         burn, net burn, runway under three burn assumptions, month-over-month and
         3-month compound growth, and a cash reconciliation check per month.
review   Reads a Markdown weekly review and prints JSON listing missing sections,
         a missing north-star line, and decisions without an owner or a valid due date.

Both commands print strict JSON (no NaN or Infinity) to stdout, UTF-8.
Reads only the file given; writes nothing; no network.
Exit codes: 0 = ok, 1 = problems found (listed in JSON), 2 = file or usage error.
This is arithmetic on figures the user supplies. It is not financial advice.
"""
import csv
import datetime
import json
import math
import re
import sys

# Burn is averaged over the last 3 months: one lumpy month (annual prepayment, a refund)
# should not swing runway, and 3 is the shortest window that smooths a single outlier.
BURN_WINDOW = 3
# Cash reconciliation: balance change should equal -net burn. Gaps above this share of
# the previous balance are reported as warnings (a funding round or loan repayment
# is a legitimate cause, so this is never an error).
RECON_TOLERANCE = 0.01
# Runway below this many months is flagged, because a raise or cost cut usually takes
# longer than that to complete. A prompt to decide early, not a prediction.
LOW_RUNWAY_MONTHS = 6.0
# A weekly review with more priorities than this is a list, not a priority.
MAX_PRIORITIES = 3

REQUIRED_COLUMNS = ["month", "revenue", "cash_out", "cash_balance"]
REQUIRED_SECTIONS = ["Metrics", "Wins", "Misses", "Decisions", "Risks", "Priorities"]
SECTION_ALIASES = {
    "priorities": "Priorities", "next week priorities": "Priorities", "next week": "Priorities",
    "metrics": "Metrics", "wins": "Wins", "misses": "Misses", "decisions": "Decisions", "risks": "Risks",
}
PLACEHOLDERS = {"", "tbd", "tba", "?", "??", "todo", "none", "n/a", "na", "-", "someone", "team", "everyone", "we", "all", "founders", "company", "management"}


def emit(obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))


def fail(msg):
    sys.stderr.write(msg + "\n")
    return 2


def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc.strerror}")
    if not raw.strip():
        raise ValueError(f"{path} is empty")
    return raw.decode("utf-8-sig", errors="replace")


def err(code, message, line=None):
    item = {"code": code, "message": message}
    if line is not None:
        item["line"] = line
    return item


def round_or_none(value, places):
    if value is None or math.isnan(value) or math.isinf(value):
        return None
    return round(value, places)


def parse_month(text):
    m = re.fullmatch(r"(\d{4})-(\d{2})", text.strip())
    if not m or not 1 <= int(m.group(2)) <= 12:
        return None
    return int(m.group(1)) * 12 + int(m.group(2)) - 1  # months since year 0


def month_label(index):
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def parse_number(text):
    t = text.strip().replace(",", "").replace("$", "")
    if re.fullmatch(r"-?\d+(\.\d+)?", t):
        return float(t)
    return None


def cmd_metrics(path):
    text = read_text(path)
    reader = csv.DictReader(text.splitlines())
    header = [h.strip().lower() for h in (reader.fieldnames or [])]
    errors, warnings, rows = [], [], []
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        errors.append(err("missing_columns", "missing column(s): " + ", ".join(missing) + "; header is: " + ",".join(header)))
        return {"command": "metrics", "ok": False, "errors": errors, "warnings": warnings}
    reader.fieldnames = header
    for n, raw in enumerate(reader, start=2):
        if not any((v or "").strip() for v in raw.values()):
            continue
        month = parse_month(raw.get("month") or "")
        if month is None:
            errors.append(err("bad_month", f"month '{raw.get('month')}' is not YYYY-MM", n))
            continue
        vals = {}
        for col in ("revenue", "cash_out", "cash_balance"):
            num = parse_number(raw.get(col) or "")
            if num is None:
                errors.append(err("bad_number", f"{col} '{raw.get(col)}' is not a number", n))
            elif num < 0:
                errors.append(err("negative_value", f"{col} is negative ({num:g}); enter money out as a positive cash_out", n))
            else:
                vals[col] = num
        if len(vals) == 3:
            rows.append({"line": n, "m": month, **vals})
    if not rows and not errors:
        errors.append(err("no_rows", "no data rows"))
    for a, b in zip(rows, rows[1:]):
        if b["m"] == a["m"]:
            errors.append(err("duplicate_month", f"month {month_label(b['m'])} appears twice", b["line"]))
        elif b["m"] < a["m"]:
            errors.append(err("not_sorted", "rows must run oldest to newest", b["line"]))
        elif b["m"] != a["m"] + 1:
            errors.append(err("month_gap", f"months jump from {month_label(a['m'])} to {month_label(b['m'])}; add the missing month(s)", b["line"]))
    if errors:
        return {"command": "metrics", "ok": False, "errors": errors, "warnings": warnings}

    for r in rows:
        r["net_burn"] = r["cash_out"] - r["revenue"]
    recon = []
    for a, b in zip(rows, rows[1:]):
        expected = a["cash_balance"] - b["net_burn"]
        gap = b["cash_balance"] - expected
        share = abs(gap) / a["cash_balance"] if a["cash_balance"] else None
        if share is None or share > RECON_TOLERANCE:
            recon.append({"month": month_label(b["m"]), "expected_balance": round(expected, 2),
                          "reported_balance": round(b["cash_balance"], 2), "gap": round(gap, 2)})
            warnings.append(err("cash_reconciliation_gap",
                                f"{month_label(b['m'])}: balance differs from previous balance minus net burn by {gap:,.2f}; confirm a funding event, debt repayment or data entry error", b["line"]))
    window = rows[-BURN_WINDOW:]
    if len(rows) < BURN_WINDOW:
        warnings.append(err("short_history", f"only {len(rows)} month(s) of data; the burn average uses what exists"))
    latest = rows[-1]
    avg_net = sum(r["net_burn"] for r in window) / len(window)
    worst_net = max(r["net_burn"] for r in window)

    def runway(burn):
        if burn <= 0:
            return None
        return latest["cash_balance"] / burn

    runs = {"last_month": runway(latest["net_burn"]), "avg_last_3": runway(avg_net), "worst_of_last_3": runway(worst_net)}
    cash_flow_positive = avg_net <= 0
    zero_month = None
    if runs["avg_last_3"] is not None:
        zero_month = month_label(latest["m"] + int(math.floor(runs["avg_last_3"])) + 1)  # balance is month-end, so cash runs out during the month after the whole months of runway
    growth = {"mom_latest": None, "cmgr_3m": None, "mom_history": []}
    for a, b in zip(rows, rows[1:]):
        g = (b["revenue"] / a["revenue"] - 1) if a["revenue"] > 0 else None
        growth["mom_history"].append({"month": month_label(b["m"]), "mom": round_or_none(g, 4)})
    if growth["mom_history"]:
        growth["mom_latest"] = growth["mom_history"][-1]["mom"]
    if len(rows) > 3 and rows[-4]["revenue"] > 0 and latest["revenue"] > 0:
        growth["cmgr_3m"] = round_or_none((latest["revenue"] / rows[-4]["revenue"]) ** (1.0 / 3) - 1, 4)
    elif len(rows) > 3:
        warnings.append(err("growth_undefined", "revenue is zero at the start or end of the 3-month window; compound growth is not defined"))
    flags = []
    if runs["avg_last_3"] is not None and runs["avg_last_3"] < LOW_RUNWAY_MONTHS:
        flags.append("runway_under_%d_months" % LOW_RUNWAY_MONTHS)
    if cash_flow_positive:
        flags.append("cash_flow_positive_on_window")
    return {
        "command": "metrics", "ok": True, "errors": [], "warnings": warnings,
        "months": len(rows), "first_month": month_label(rows[0]["m"]), "latest_month": month_label(latest["m"]),
        "latest": {"revenue": round(latest["revenue"], 2), "cash_out": round(latest["cash_out"], 2),
                   "cash_balance": round(latest["cash_balance"], 2)},
        "burn": {"gross_burn_latest": round(latest["cash_out"], 2), "net_burn_latest": round(latest["net_burn"], 2),
                 "net_burn_avg_last_3": round(avg_net, 2), "net_burn_worst_of_last_3": round(worst_net, 2)},
        "runway_months": {k: round_or_none(v, 2) for k, v in runs.items()},
        "cash_zero_month_at_avg_burn": zero_month,
        "growth": growth, "flags": flags, "reconciliation_gaps": recon,
        "formulas": {
            "gross_burn": "cash_out in the month",
            "net_burn": "cash_out - revenue",
            "runway_months": "latest cash_balance / net burn, null when net burn <= 0",
            "mom": "revenue_t / revenue_t-1 - 1",
            "cmgr_3m": "(revenue_t / revenue_t-3) ^ (1/3) - 1",
        },
    }


def section_key(title):
    t = re.sub(r"[^a-z ]", "", title.lower()).strip()
    return SECTION_ALIASES.get(t)


def cmd_review(path):
    text = read_text(path)
    lines = text.splitlines()
    errors, warnings = [], []
    sections, current = {}, None
    week_start = None
    for n, line in enumerate(lines, start=1):
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            current = section_key(m.group(1))
            if current:
                if current in sections:
                    warnings.append(err("duplicate_section", f"section '{current}' appears twice", n))
                sections.setdefault(current, {"line": n, "body": []})
            continue
        if line.startswith("# "):
            current = None
            continue
        if current:
            sections[current]["body"].append((n, line))
        w = re.match(r"^\s*week of\s*:\s*(\S+)", line, re.I)
        if w and week_start is None:
            try:
                week_start = datetime.date.fromisoformat(w.group(1))
            except ValueError:
                errors.append(err("bad_week_date", f"'Week of' value '{w.group(1)}' is not YYYY-MM-DD", n))
                week_start = False
    if week_start is None:
        errors.append(err("week_missing", "no 'Week of: YYYY-MM-DD' line"))
    elif week_start and week_start.weekday() != 0:
        warnings.append(err("week_not_monday", f"{week_start.isoformat()} is a {week_start.strftime('%A')}; use the Monday that starts the week so reviews compare cleanly"))
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            errors.append(err("missing_section", f"missing '## {name}' section"))
        elif not any(l.strip() for _, l in sections[name]["body"]):
            errors.append(err("empty_section", f"section '{name}' has no content", sections[name]["line"]))
    if "Metrics" in sections:
        body = "\n".join(l for _, l in sections["Metrics"]["body"])
        m = re.search(r"north[ -]?star\s*:\s*(.+)", body, re.I)
        if not m or not re.search(r"\d", m.group(1)):
            errors.append(err("north_star_missing", "Metrics needs a 'North star: <name> = <number>' line with a number", sections["Metrics"]["line"]))
    decisions = 0
    if "Decisions" in sections:
        body = sections["Decisions"]["body"]
        items = [(n, l) for n, l in body if re.match(r"^\s*(?:[-*]|\d+[.)])\s+\S", l)]
        text_only = " ".join(l for _, l in body).lower()
        if not items and re.search(r"no decisions", text_only):
            pass
        elif not items and any(l.strip() for _, l in body):
            errors.append(err("decisions_not_listed", "write each decision as a list item: '- <decision> | owner: <name> | due: YYYY-MM-DD'", sections["Decisions"]["line"]))
        for n, l in items:
            decisions += 1
            om = re.search(r"owner\s*:\s*([^|;,]*)", l, re.I)
            dm = re.search(r"due\s*:\s*([^|;,\s]*)", l, re.I)
            owner = om.group(1).strip() if om else None
            if owner is None or re.sub(r"^the\s+", "", owner.lower()) in PLACEHOLDERS:
                errors.append(err("decision_no_owner", "decision has no named owner (a person, not a team or TBD)", n))
            if dm is None or not dm.group(1):
                errors.append(err("decision_no_due", "decision has no 'due: YYYY-MM-DD'", n))
            else:
                try:
                    due = datetime.date.fromisoformat(dm.group(1))
                    if week_start and due < week_start:
                        errors.append(err("decision_due_before_week", f"due {due.isoformat()} is before the week starts", n))
                except ValueError:
                    errors.append(err("decision_bad_due", f"due '{dm.group(1)}' is not a YYYY-MM-DD date", n))
    if "Priorities" in sections:
        count = sum(1 for _, l in sections["Priorities"]["body"] if re.match(r"^\s*(?:[-*]|\d+[.)])\s+\S", l))
        if count > MAX_PRIORITIES:
            warnings.append(err("too_many_priorities", f"{count} priorities listed; keep {MAX_PRIORITIES} or fewer"))
    return {"command": "review", "ok": not errors, "errors": errors, "warnings": warnings,
            "sections_found": sorted(sections), "decisions_counted": decisions}


def main(argv):
    if len(argv) != 2 or argv[0] not in ("metrics", "review"):
        return fail("usage: founder_ops.py metrics <monthly.csv> | review <weekly_review.md>")
    try:
        report = cmd_metrics(argv[1]) if argv[0] == "metrics" else cmd_review(argv[1])
    except ValueError as exc:
        return fail(str(exc))
    emit(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
