#!/usr/bin/env python3
"""Check a research report against its source ledger: no figure without a source (offline).

Usage:
    python claim_ledger_check.py report.md sources.csv [--json]

Reads:  report.md   the research report. Claims cite sources as [S1], [S2, S5] ...
        sources.csv the ledger, header: id,status,date_read,url,title,note
                    status is one of: opened | snippet | unverified
Writes: nothing. Network: none.
Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = input problem.

Rules checked (see SKILL.md): every line that states a figure cites a ledger source or is
tagged [estimate] or [calc]; every cited id exists; a line that rests only on snippet or
unverified sources says so in the line; the ledger rows are complete; the report has a
"Not obtained" section. The script cannot tell whether a source really supports a claim:
that needs the read-back step in the skill. Do not edit this script to make a report pass.
"""
import csv
import json
import os
import re
import sys

STATUSES = ("opened", "snippet", "unverified")
CITE = re.compile(r"\[((?:S\d+)(?:\s*,\s*S\d+)*)\]")
TAG = re.compile(r"\[(estimate|calc)\]", re.I)
# A figure: money, percentages, numbers with a magnitude word, or any number of two or more
# digits. Single digits without a unit ("3 vendors") are too noisy to police by script.
FIGURE = re.compile(
    r"(?<![\w.])(?:[$€£₪]\s?\d[\d,.]*\s?(?:k|m|b|bn|million|billion|thousand)?|\d[\d,.]*\s?%|"
    r"\d[\d,.]*\s?(?:k|m|bn|million|billion|thousand)\b|\d{2,}[\d,.]*)(?![\w])", re.I)
YEAR = re.compile(r"^(19|20)\d{2}$")
DATE = re.compile(r"\b\d{4}-\d{2}(-\d{2})?\b|\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s\d{4}\b|"
                  r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s\d{1,2},\s\d{4}\b", re.I)
# Sections where figures are not claims about the market.
EXEMPT_SECTIONS = re.compile(r"^(sources?|source ledger|not obtained|method|methodology|open questions|appendix)\b", re.I)
SUMMARY_SECTIONS = re.compile(r"^(summary|takeaways?|key findings|bottom line|recommendation|recommendations|executive summary)\b", re.I)
WEAK_MARK = re.compile(r"\((?:[^)]*\b)?(snippet|unverified|not opened|search summary)\b[^)]*\)", re.I)


def figures_in(line):
    text = CITE.sub(" ", line)
    text = DATE.sub(" ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", text)
    out = []
    for m in FIGURE.finditer(text):
        token = m.group(0).strip()
        if YEAR.match(token):
            continue
        out.append(token)
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    for p in args:
        if not os.path.isfile(p):
            sys.stderr.write("ERROR: file not found: %s\n" % p)
            return 2
    report = open(args[0], "rb").read().decode("utf-8-sig", "replace")
    findings = []

    def add(level, code, where, msg):
        findings.append({"level": level, "code": code, "where": where, "message": msg})

    ledger = {}
    with open(args[1], encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = [f.strip().lower() for f in (reader.fieldnames or [])]
        missing = [c for c in ("id", "status", "date_read", "url", "title") if c not in fields]
        if missing:
            sys.stderr.write("ERROR: sources.csv needs the columns id,status,date_read,url,title,note; missing: %s\n" % ", ".join(missing))
            return 2
        for n, row in enumerate(reader, 2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            sid = row.get("id", "")
            if not re.fullmatch(r"S\d+", sid):
                add("FAIL", "LEDGER", "sources.csv line %d" % n, "id must look like S1, S2 ...; got %r" % sid)
                continue
            if sid in ledger:
                add("FAIL", "LEDGER", "sources.csv line %d" % n, "duplicate id %s" % sid)
            ledger[sid] = row
            if row["status"].lower() not in STATUSES:
                add("FAIL", "LEDGER", sid, "status must be opened, snippet or unverified; got %r" % row["status"])
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date_read"]):
                add("FAIL", "LEDGER", sid, "date_read must be YYYY-MM-DD; got %r" % row["date_read"])
            if row["status"].lower() == "opened" and not row["url"]:
                add("FAIL", "LEDGER", sid, "an opened source needs its URL or file path")
            if not row["title"]:
                add("WARN", "LEDGER", sid, "no title")

    section, in_code, cited_anywhere, has_not_obtained = "", False, set(), False
    stats = {"claim_lines": 0, "cited": 0, "tagged_estimate": 0, "uncited": 0}
    for n, raw in enumerate(report.splitlines(), 1):
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line.strip():
            continue
        head = re.match(r"^#{1,6}\s+(.*)$", line)
        if head:
            section = re.sub(r"^[\d.\s]+", "", head.group(1)).strip()
            if re.match(r"^not obtained\b", section, re.I):
                has_not_obtained = True
            continue
        if re.match(r"^\s*\|?\s*:?-{3,}", line):
            continue
        cites = [s.strip() for grp in CITE.findall(line) for s in grp.split(",")]
        cited_anywhere.update(cites)
        for sid in cites:
            if sid not in ledger:
                add("FAIL", "CITE", "report line %d" % n, "cites %s, which is not in the ledger" % sid)
        if EXEMPT_SECTIONS.match(section):
            continue
        figs = figures_in(line)
        if not figs:
            continue
        stats["claim_lines"] += 1
        known = [s for s in cites if s in ledger]
        if known:
            stats["cited"] += 1
            statuses = {ledger[s]["status"].lower() for s in known}
            if "opened" not in statuses and not WEAK_MARK.search(line):
                add("FAIL", "WEAK", "report line %d" % n, "rests only on %s source(s) %s but the line does not say so; add '(snippet)' or '(unverified)': %s"
                    % ("/".join(sorted(statuses)), ", ".join(known), line.strip()[:90]))
            if "opened" not in statuses and SUMMARY_SECTIONS.match(section):
                add("WARN", "WEAK-SUMMARY", "report line %d" % n, "a summary line rests on no opened source: %s" % line.strip()[:90])
        elif TAG.search(line):
            stats["tagged_estimate"] += 1
        else:
            stats["uncited"] += 1
            add("FAIL", "UNCITED", "report line %d" % n, "figure %s without a source, [estimate] or [calc]: %s" % (", ".join(figs[:3]), line.strip()[:90]))
    for sid in sorted(set(ledger) - cited_anywhere, key=lambda s: int(s[1:])):
        add("NOTE", "UNUSED", sid, "in the ledger but never cited")
    if not has_not_obtained:
        add("WARN", "SECTION", "report", "no 'Not obtained' section; say what could not be found or opened")
    by_status = {s: sum(1 for r in ledger.values() if r["status"].lower() == s) for s in STATUSES}

    order = {"FAIL": 0, "WARN": 1, "NOTE": 2}
    findings.sort(key=lambda f: order[f["level"]])
    counts = {k: sum(1 for f in findings if f["level"] == k) for k in order}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--json" in argv:
        print(json.dumps({"counts": counts, "stats": stats, "ledger": by_status, "findings": findings}, indent=2))
    else:
        print("CLAIM LEDGER CHECK: %d FAIL, %d WARN, %d NOTE" % (counts["FAIL"], counts["WARN"], counts["NOTE"]))
        print("Lines with figures: %d (cited %d, tagged estimate/calc %d, uncited %d)" % (stats["claim_lines"], stats["cited"], stats["tagged_estimate"], stats["uncited"]))
        print("Ledger: %d opened, %d snippet, %d unverified" % (by_status["opened"], by_status["snippet"], by_status["unverified"]))
        for f in findings:
            print("%-4s %-12s %s: %s" % (f["level"], f["code"], f["where"], f["message"]))
        print("\nThis check proves that figures carry sources, not that the sources say what the report says. Do the read-back.")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
