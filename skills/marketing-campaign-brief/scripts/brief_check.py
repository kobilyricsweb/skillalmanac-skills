#!/usr/bin/env python3
"""Check a marketing campaign brief for completeness, arithmetic and untagged figures (offline).

Usage:
    python brief_check.py brief.md [--json]

Reads:  one Markdown brief written to the layout in SKILL.md. Writes: nothing. Network: none.
Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = input problem.

Checks: the nine sections exist; the objective has a number, a deadline and a baseline; the
channel table has a budget and a KPI in every row and its budgets add up to the stated total;
every line with a money amount or a percentage, and every channel target, is tagged [given],
[assumption] or [calc]; assumptions are listed
for the owner; measurement names data sources and a decision rule.
The script cannot judge whether the strategy is good. Do not edit it to make a brief pass.
"""
import json
import os
import re
import sys

SECTIONS = [
    ("objective", r"objective|goal"),
    ("audience", r"audience|who"),
    ("offer", r"offer|message|proposition"),
    ("channels", r"channel"),
    ("budget", r"budget"),
    ("measurement", r"measure|tracking|kpi"),
    ("timeline", r"timeline|schedule|calendar"),
    ("risks", r"risk|guardrail"),
    ("assumptions", r"assumption|open question"),
]
TAG = re.compile(r"\[(given|assumption|calc)\]", re.I)
MONEY = re.compile(r"(?<![\w.])([$€£₪])\s?(\d[\d,]*(?:\.\d+)?)\s?(k|m)?\b", re.I)
# Figures the script polices for a tag: money and percentages. Plain counts and durations
# ("30-day trial", "6 weeks") are too varied to police by pattern; the rule still applies by hand.
FIGURE = re.compile(r"(?<![\w.])(?:[$€£₪]\s?\d[\d,.]*\s?(?:k|m)?|\d[\d,.]*\s?%)(?![\w])", re.I)
ANY_NUMBER = re.compile(r"\d")
RESERVE_ROW = re.compile(r"reserve|contingency|buffer", re.I)
YEAR = re.compile(r"^(19|20)\d{2}$")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?(?:\s\d{4})?\b|"
                  r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s\d{1,2}(?:,?\s\d{4})?\b|\b(?:Q[1-4]|week\s\d+)\b", re.I)
PROMISE = re.compile(r"\b(guarantee[ds]?|go viral|viral|will definitely|risk-free|sure to)\b", re.I)
# Budget lines may differ from the total by rounding of this many currency units.
SUM_TOLERANCE = 1.0


def money(text):
    m = MONEY.search(text)
    if not m:
        return None
    value = float(m.group(2).replace(",", ""))
    if m.group(3):
        value *= 1000 if m.group(3).lower() == "k" else 1000000
    return value


def figures(line):
    text = DATE.sub(" ", line)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", text)
    return [m.group(0).strip() for m in FIGURE.finditer(text) if not YEAR.match(m.group(0).strip())]


def cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1 or not os.path.isfile(args[0]):
        print(__doc__)
        return 2
    lines = open(args[0], "rb").read().decode("utf-8-sig", "replace").splitlines()
    findings = []

    def add(level, code, msg):
        findings.append({"level": level, "code": code, "message": msg})

    # split into sections by H2 (H1 is the title)
    sections, current, order = {}, None, []
    for n, line in enumerate(lines, 1):
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            title = m.group(1).strip()
            key = next((k for k, rx in SECTIONS if re.search(rx, title, re.I) and k not in sections), None)
            current = key or ("other:" + title)
            sections.setdefault(current, [])
            order.append(current)
            continue
        if current:
            sections[current].append((n, line))
    for key, _ in SECTIONS:
        if key not in sections:
            add("FAIL", "SECTION", "missing section: %s" % key)

    def text_of(key):
        return "\n".join(l for _, l in sections.get(key, []))

    # objective
    obj = text_of("objective")
    if "objective" in sections:
        if not ANY_NUMBER.search(DATE.sub(" ", obj)):
            add("FAIL", "OBJECTIVE", "the objective has no number; state the metric, the target value and the baseline")
        if not DATE.search(obj):
            add("FAIL", "OBJECTIVE", "the objective has no deadline (a date, month or quarter)")
        if not re.search(r"baseline|from\s+\S+.*\bto\b|currently|today|no baseline", obj, re.I):
            add("WARN", "OBJECTIVE", "no baseline in the objective; write the current value or 'no baseline: first weeks establish it'")
        if len(re.findall(r"primary objective", obj, re.I)) > 1:
            add("WARN", "OBJECTIVE", "more than one primary objective; pick one and demote the rest to secondary")

    # channel table and budget arithmetic
    table = [(n, l) for n, l in sections.get("channels", []) if l.strip().startswith("|")]
    channel_total, rows = 0.0, 0
    if "channels" in sections:
        if len(table) < 3:
            add("FAIL", "CHANNELS", "no channel table; use columns Channel | Role | Budget | KPI | Target | Owner")
        else:
            header = [c.lower() for c in cells(table[0][1])]
            col = {name: next((i for i, h in enumerate(header) if name in h), None) for name in ("channel", "budget", "kpi", "target")}
            for name in ("channel", "budget", "kpi"):
                if col[name] is None:
                    add("FAIL", "CHANNELS", "the channel table has no '%s' column" % name)
            for n, row in table[2:]:
                c = cells(row)
                if len(c) < len(header):
                    add("WARN", "CHANNELS", "line %d: row has fewer cells than the header" % n)
                    continue
                rows += 1
                name = c[col["channel"]] if col["channel"] is not None else "row"
                if col["budget"] is not None:
                    value = money(c[col["budget"]])
                    if value is None and not re.search(r"^(0|none|n/a|-|free|organic|in-house)", c[col["budget"]], re.I):
                        add("FAIL", "CHANNELS", "line %d (%s): budget cell has no amount: %r" % (n, name, c[col["budget"]]))
                    channel_total += value or 0
                if RESERVE_ROW.search(name):
                    continue
                if col["kpi"] is not None and not re.sub(r"[-\s]", "", c[col["kpi"]]):
                    add("FAIL", "CHANNELS", "line %d (%s): no KPI; a channel without a KPI cannot be judged" % (n, name))
                if col["target"] is not None and not re.sub(r"[-\s]", "", c[col["target"]]):
                    add("WARN", "CHANNELS", "line %d (%s): no target value for its KPI" % (n, name))
                elif col["target"] is not None and ANY_NUMBER.search(c[col["target"]]) and not TAG.search(c[col["target"]]):
                    add("FAIL", "UNTAGGED", "line %d (%s): target %r is not tagged [given], [assumption] or [calc]" % (n, name, c[col["target"]]))
    total_match = re.search(r"total budget[^\n]*", text_of("budget"), re.I)
    stated_total = money(total_match.group(0)) if total_match else None
    if "budget" in sections:
        if stated_total is None:
            add("FAIL", "BUDGET", "no 'Total budget: <amount>' line in the budget section")
        elif rows and abs(stated_total - channel_total) > SUM_TOLERANCE:
            add("FAIL", "BUDGET", "channel budgets add up to %s but the stated total is %s; fix the lines or add a reserve row"
                % ("{:,.0f}".format(channel_total), "{:,.0f}".format(stated_total)))

    # figure tags
    untagged, assumption_lines = 0, 0
    for key in order:
        if key == "assumptions":
            continue
        for n, line in sections[key]:
            if not line.strip() or re.match(r"^\s*\|?\s*:?-{3,}", line):
                continue
            if TAG.search(line) and re.search(r"\[assumption\]", line, re.I):
                assumption_lines += 1
            if figures(line) and not TAG.search(line):
                untagged += 1
                add("FAIL", "UNTAGGED", "line %d: figure %s is not tagged [given], [assumption] or [calc]: %s" % (n, ", ".join(figures(line)[:3]), line.strip()[:80]))
    listed = sum(1 for _, l in sections.get("assumptions", []) if re.match(r"^\s*(?:[-*]|\d+[.)])\s+\S", l))
    if "assumptions" in sections:
        if listed == 0 and not re.search(r"\bnone\b", text_of("assumptions"), re.I):
            add("FAIL", "ASSUMPTIONS", "the assumptions and open questions section lists nothing; write the items or 'none'")
        elif assumption_lines and listed == 0:
            add("FAIL", "ASSUMPTIONS", "%d lines carry [assumption] but none is listed for the owner to confirm" % assumption_lines)

    # measurement
    meas = text_of("measurement")
    if "measurement" in sections:
        if not re.search(r"source|tool|tracked|tracking|report|dashboard|analytics|crm|utm|survey|log", meas, re.I):
            add("WARN", "MEASUREMENT", "measurement names no data source for the KPIs")
        if not re.search(r"\bif\b.*\b(pause|stop|shift|reallocate|cut|review|scale|move)\b", meas, re.I | re.S):
            add("WARN", "MEASUREMENT", "no decision rule (for example: 'if cost per lead is above X after 2 weeks, pause the channel')")
    if "timeline" in sections and len(DATE.findall(text_of("timeline"))) < 2:
        add("WARN", "TIMELINE", "the timeline has fewer than two dates")
    for n, line in enumerate(lines, 1):
        m = PROMISE.search(line)
        if m:
            add("WARN", "PROMISE", "line %d: outcome promise '%s'; a brief states targets, not guarantees" % (n, m.group(0)))

    level_order = {"FAIL": 0, "WARN": 1, "NOTE": 2}
    findings.sort(key=lambda f: level_order[f["level"]])
    counts = {k: sum(1 for f in findings if f["level"] == k) for k in level_order}
    stats = {"channel_rows": rows, "channel_budget_sum": channel_total, "stated_total": stated_total,
             "assumption_lines": assumption_lines, "assumptions_listed": listed, "untagged_figure_lines": untagged}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--json" in argv:
        print(json.dumps({"counts": counts, "stats": stats, "findings": findings}, indent=2))
    else:
        print("BRIEF CHECK: %d FAIL, %d WARN" % (counts["FAIL"], counts["WARN"]))
        print("Channels: %d rows, budgets sum %s, stated total %s; [assumption] lines: %d, listed for owner: %d"
              % (rows, "{:,.0f}".format(channel_total), "{:,.0f}".format(stated_total) if stated_total is not None else "none", assumption_lines, listed))
        for f in findings:
            print("%-4s %-12s %s" % (f["level"], f["code"], f["message"]))
        print("\nThis check covers completeness and arithmetic. Whether the plan is the right plan is the owner's call.")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
