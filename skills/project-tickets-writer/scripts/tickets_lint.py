#!/usr/bin/env python3
"""Validate a tickets file (JSON or Markdown) and print one JSON report.

    python scripts/tickets_lint.py FILE [--max-criteria N] [--max-size-days D] [--strict]

Reads FILE (UTF-8). Writes nothing, uses no network. Stdout is always exactly
one JSON object; nothing else is printed there.

Exit codes: 0 no errors (warnings allowed unless --strict), 1 at least one
error (or a warning under --strict), 2 the file could not be read or parsed.

Formats are described in references/ticket-format.md.
JSON: {"tickets": [ {id, title, outcome, size, depends_on, non_goals,
acceptance_criteria, definition_of_done} ]} or a bare list of such objects.
Markdown: one "## ID: Title" heading per ticket followed by "Field: value"
lines; list fields use bullet or numbered items.
"""
import json
import re
import sys

# Default limits. Reasons are in references/splitting-and-criteria.md.
DEFAULT_MAX_CRITERIA = 6   # beyond ~6 checks a ticket is almost always two outcomes
DEFAULT_MAX_SIZE_DAYS = 3  # one engineer, ideal days; over this a ticket is not finishable in one review cycle
TSHIRT_DAYS = {"XS": 0.5, "S": 1.0, "M": 3.0, "L": 8.0, "XL": 13.0}
NEAR_DUP_JACCARD = 0.8     # title word overlap that reads as the same ticket

# Leading verbs that say nothing checkable, whatever follows.
ALWAYS_VAGUE_LEADING = {"handle", "improve", "enhance", "optimize", "optimise", "streamline",
                        "revamp", "polish", "tweak", "address", "look", "work", "deal"}
# Leading verbs that are fine with a concrete object and vague without one.
CONDITIONAL_LEADING = {"fix", "update", "support", "refactor", "rework", "clean", "cleanup", "make", "improve"}
VAGUE_OBJECTS = {"stuff", "things", "thing", "issues", "bugs", "errors", "problems", "everything",
                 "misc", "various", "ux", "ui", "flow", "performance", "it", "them", "edge", "cases"}
VAGUE_ANYWHERE_TITLE = [r"\bstuff\b", r"\bmisc(?:ellaneous)?\b", r"\bvarious\b", r"\betc\b\.?",
                        r"\band more\b", r"\bgeneral (?:cleanup|improvements?)\b", r"\bminor (?:fixes|tweaks)\b"]
# Words that make a criterion or outcome unverifiable.
VAGUE_CRITERION = [r"\bhandles?\b", r"\bhandling\b", r"\bproperly\b", r"\bcorrectly\b", r"\bas expected\b",
                   r"\bappropriate(?:ly)?\b", r"\betc\b\.?", r"\buser[- ]friendly\b", r"\bseamless(?:ly)?\b",
                   r"\brobust\b", r"\bintuitive(?:ly)?\b", r"\bgood performance\b", r"\bworks? well\b",
                   r"\bshould work\b", r"\bsmooth(?:ly)?\b",
                   r"\bshould be (?:ok|okay|fine|good|better)\b", r"\b(?:ok|okay|fine|good|better)\s*[.!]?\s*$"]
SECOND_VERBS = {"add", "create", "remove", "update", "send", "show", "allow", "enable", "display", "delete",
                "export", "import", "migrate", "change", "set", "build", "disable", "rename", "replace",
                "move", "notify", "validate", "log", "track", "store", "sync", "email"}

FIELD_ALIASES = {
    "outcome": "outcome",
    "size": "size", "estimate": "size",
    "depends on": "depends_on", "depends": "depends_on", "dependencies": "depends_on", "blocked by": "depends_on",
    "non-goals": "non_goals", "non goals": "non_goals", "nongoals": "non_goals", "out of scope": "non_goals",
    "acceptance criteria": "acceptance_criteria", "acceptance": "acceptance_criteria", "criteria": "acceptance_criteria",
    "definition of done": "definition_of_done", "dod": "definition_of_done", "done when": "definition_of_done",
}
LIST_FIELDS = {"non_goals", "acceptance_criteria", "definition_of_done"}
HEADING_RE = re.compile(r"^##\s+\[?([A-Za-z][A-Za-z0-9]*-?\d+)\]?\s*[:.\-–—]\s*(.+?)\s*$")
FIELD_RE = re.compile(r"^\**([A-Za-z][A-Za-z \-]*?)\**\s*:\s*\**\s*(.*)$")
ITEM_RE = re.compile(r"^(?:[-*]|\d+[.)])\s+(.*)$")
GWT_RE = re.compile(r"\bgiven\b.+?\bwhen\b.+?\bthen\b", re.I | re.S)


class InputProblem(Exception):
    pass


def norm_id(s):
    return str(s).strip().upper()


def norm_title(s):
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", str(s).lower()).split())


def parse_markdown(text):
    tickets, cur, field, in_fence = [], None, None, False
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## ") or line == "##":
            m = HEADING_RE.match(line)
            cur = {"id": m.group(1) if m else "", "title": m.group(2) if m else line[2:].strip(),
                   "_line": no, "_heading_ok": bool(m), "_items": {}}
            tickets.append(cur)
            field = None
            continue
        if cur is None or not line:
            continue
        body = ITEM_RE.sub(lambda mm: mm.group(1), line) if ITEM_RE.match(line) and FIELD_RE.match(ITEM_RE.match(line).group(1)) else line
        fm = FIELD_RE.match(body)
        key = FIELD_ALIASES.get(fm.group(1).strip().lower()) if fm else None
        if key:
            field = key
            cur["_items"][field] = []
            if fm.group(2).strip():
                cur["_items"][field].append(fm.group(2).strip())
            continue
        if field is None:
            continue
        im = ITEM_RE.match(line)
        if im:
            cur["_items"][field].append(im.group(1).strip())
        elif cur["_items"][field]:
            cur["_items"][field][-1] += " " + line
        else:
            cur["_items"][field].append(line)
    out = []
    for t in tickets:
        it = t.pop("_items")
        t["outcome"] = " ".join(it.get("outcome", []))
        t["size"] = " ".join(it.get("size", []))
        t["depends_on"] = re.split(r"[,;\s]+", " ".join(it.get("depends_on", [])).strip()) if it.get("depends_on") else []
        for k in LIST_FIELDS:
            t[k] = it.get(k, [])
        t["_present"] = set(it)
        out.append(t)
    return out


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def parse_json(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InputProblem("invalid JSON: %s" % exc)
    if isinstance(data, dict):
        data = data.get("tickets")
    if not isinstance(data, list):
        raise InputProblem('JSON must be a list of tickets or an object with a "tickets" list')
    out = []
    for i, d in enumerate(data):
        if not isinstance(d, dict):
            raise InputProblem("tickets[%d] is not an object" % i)
        t = {"id": d.get("id", ""), "title": d.get("title", ""), "outcome": d.get("outcome", ""),
             "size": d.get("size", ""), "_line": None, "_heading_ok": True, "_bad_types": []}
        t["depends_on"] = as_list(d.get("depends_on", d.get("dependsOn")))
        t["non_goals"] = as_list(d.get("non_goals", d.get("nonGoals")))
        t["acceptance_criteria"] = as_list(d.get("acceptance_criteria", d.get("acceptanceCriteria")))
        t["definition_of_done"] = as_list(d.get("definition_of_done", d.get("definitionOfDone")))
        for k in ("title", "outcome"):
            if not isinstance(t[k], str):
                t["_bad_types"].append(k)
                t[k] = ""
        for k in ("depends_on", "non_goals", "acceptance_criteria", "definition_of_done"):
            if not all(isinstance(x, str) for x in t[k]):
                t["_bad_types"].append(k)
                t[k] = [x for x in t[k] if isinstance(x, str)]
        if isinstance(t["size"], (int, float)) and not isinstance(t["size"], bool):
            t["size"] = str(t["size"])
        elif not isinstance(t["size"], str):
            t["_bad_types"].append("size")
            t["size"] = ""
        t["id"] = str(t["id"])
        out.append(t)
    return out


def parse_size(s):
    """Return days as a float, or None if unreadable or empty."""
    s = str(s).strip().upper().replace("DAYS", "D").replace("DAY", "D")
    if not s:
        return None
    if s in TSHIRT_DAYS:
        return TSHIRT_DAYS[s]
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*D?", s)
    return float(m.group(1)) if m else None


def find_cycles(graph):
    """Return a list of cycles (each a list of ids, first id repeated at the end)."""
    cycles, state, stack = [], {}, []

    def visit(n):
        state[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            if m not in graph:
                continue
            if state.get(m) == 1:
                cycles.append(stack[stack.index(m):] + [m])
            elif state.get(m) is None:
                visit(m)
        stack.pop()
        state[n] = 2

    for n in sorted(graph):
        if state.get(n) is None:
            visit(n)
    return cycles


def topo_order(graph):
    done, order = set(), []

    def visit(n):
        if n in done:
            return
        done.add(n)
        for m in sorted(graph.get(n, [])):
            if m in graph:
                visit(m)
        order.append(n)

    for n in sorted(graph):
        visit(n)
    return order


def lint(tickets, max_criteria, max_days):
    findings = []

    def add(sev, rule, t, msg):
        f = {"severity": sev, "rule": rule, "ticket": t.get("id") or t.get("title") or "?", "message": msg}
        if t.get("_line"):
            f["line"] = t["_line"]
        findings.append(f)

    seen_ids, seen_titles, shown = {}, {}, {}
    for t in tickets:
        tid, title = norm_id(t["id"]), t["title"].strip()
        if not t.get("_heading_ok") or not tid:
            add("error", "missing-id", t, 'heading must look like "## T1: Short title" (id, then colon, then title)')
        elif tid in seen_ids:
            add("error", "duplicate-id", t, "id %s is used by more than one ticket" % t["id"])
        seen_ids[tid] = t
        for k in t.get("_bad_types", []):
            add("error", "bad-field-type", t, "field %s has the wrong type" % k)
        if not title:
            add("error", "missing-title", t, "ticket has no title")
        key = norm_title(title)
        if key and key in seen_titles:
            add("error", "duplicate-title", t, "title duplicates ticket %s" % seen_titles[key])
        elif key:
            for other, oid in seen_titles.items():
                a, b = set(key.split()), set(other.split())
                if len(a) >= 3 and len(a | b) and len(a & b) / len(a | b) >= NEAR_DUP_JACCARD:
                    add("warning", "near-duplicate-title", t, "title is very close to ticket %s" % oid)
                    break
            seen_titles[key] = t["id"]
        words = re.findall(r"[A-Za-z']+", title.lower())
        lead = words[0] if words else ""
        vague = any(re.search(p, title, re.I) for p in VAGUE_ANYWHERE_TITLE)
        if lead in ALWAYS_VAGUE_LEADING:
            vague = True
        elif lead in CONDITIONAL_LEADING and (len(words) <= 2 or set(words[1:]) & VAGUE_OBJECTS):
            vague = True
        if vague:
            add("error", "vague-title", t, 'title "%s" names no checkable change; start with a concrete verb and object' % title)
        parts = re.split(r"\s+(?:and|&|plus)\s+", title, flags=re.I)
        if len(parts) > 1 and any(p.split()[:1] and p.split()[0].lower() in SECOND_VERBS for p in parts[1:]):
            add("warning", "multiple-outcomes", t, "title joins two actions with 'and'; probably two tickets")
        if not t["outcome"].strip():
            add("error", "missing-outcome", t, "no outcome sentence")
        elif len(re.findall(r"[.!?](?:\s|$)", t["outcome"].strip())) > 1:
            add("warning", "outcome-not-one-sentence", t, "outcome has more than one sentence")
        for p in VAGUE_CRITERION[:2] + VAGUE_CRITERION[-2:]:
            if re.search(p, t["outcome"], re.I):
                add("warning", "vague-outcome", t, "outcome uses a word that cannot be checked")
                break
        days = parse_size(t["size"])
        if not str(t["size"]).strip():
            add("error", "missing-size", t, "no size; use XS, S, M, L, XL or a number of engineer-days")
        elif days is None:
            add("error", "bad-size", t, 'size "%s" is not XS/S/M/L/XL or a number of days' % t["size"])
        elif days > max_days:
            add("error", "too-large", t, "size %s is %s days, over the limit of %s; split it" % (t["size"], days, max_days))
        ac = [c for c in t["acceptance_criteria"] if c.strip()]
        if not ac:
            add("error", "missing-acceptance-criteria", t, "no acceptance criteria")
        if len(ac) > max_criteria:
            add("error", "too-many-criteria", t, "%d criteria, limit %d; split along the criteria groups" % (len(ac), max_criteria))
        for i, c in enumerate(ac, 1):
            if not GWT_RE.search(c):
                add("error", "criterion-not-gwt", t, "criterion %d lacks Given, When, Then in that order" % i)
            elif len(re.findall(r"\bwhen\b", c, re.I)) > 1:
                add("warning", "criterion-multiple-when", t, "criterion %d has more than one 'when'; one trigger per criterion" % i)
            for p in VAGUE_CRITERION:
                m = re.search(p, c, re.I)
                if m:
                    add("warning", "vague-criterion", t, 'criterion %d uses "%s", which cannot be checked' % (i, m.group(0)))
                    break
        if len(set(" ".join(c.lower().split()) for c in ac)) < len(ac):
            add("warning", "duplicate-criterion", t, "two criteria are identical")
        if not [x for x in t["non_goals"] if x.strip() and x.strip().strip(".-* ").lower() not in ("none", "n/a", "na", "nothing", "no", "tbd")]:
            add("warning", "missing-non-goals", t, "no non-goals (empty, none, n/a or tbd do not count); name what a reader might assume is included")
        if not [x for x in t["definition_of_done"] if x.strip()]:
            add("warning", "missing-definition-of-done", t, "no definition of done")

    graph = {}
    for t in tickets:
        tid = norm_id(t["id"])
        deps = []
        for d in t["depends_on"]:
            d = str(d).strip()
            if not d or d.lower() in ("none", "n/a", "-", "no"):
                continue
            nd = norm_id(d)
            if nd == tid:
                add("error", "self-dependency", t, "ticket depends on itself")
            elif nd not in seen_ids:
                add("error", "unknown-dependency", t, "depends on %s, which is not in the file" % d)
            else:
                deps.append(nd)
        graph[tid] = deps
    cycles = find_cycles(graph)
    for cyc in cycles:
        add("error", "dependency-cycle", seen_ids.get(cyc[0], {"id": cyc[0]}), "cycle: " + " -> ".join(cyc))
    order = None if cycles else topo_order(graph)
    return findings, order


def build_report(path, fmt, tickets, findings, order, max_c, max_d):
    errs = sum(1 for f in findings if f["severity"] == "error")
    warns = sum(1 for f in findings if f["severity"] == "warning")
    return {"tool": "tickets_lint", "version": 1, "file": path, "format": fmt, "ok": errs == 0,
            "limits": {"max_criteria": max_c, "max_size_days": max_d}, "ticket_count": len(tickets),
            "errors": errs, "warnings": warns, "findings": findings, "build_order": order}


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, sort_keys=False) + "\n")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    max_c, max_d, strict, path = DEFAULT_MAX_CRITERIA, DEFAULT_MAX_SIZE_DAYS, False, None
    try:
        i = 0
        while i < len(argv):
            a = argv[i]
            if a == "--max-criteria":
                max_c = int(argv[i + 1]); i += 2
            elif a == "--max-size-days":
                max_d = float(argv[i + 1]); i += 2
            elif a == "--strict":
                strict = True; i += 1
            elif path is None and not a.startswith("--"):
                path = a; i += 1
            else:
                raise ValueError("unknown argument %s" % a)
        if path is None:
            raise ValueError("no file given")
    except (ValueError, IndexError) as exc:
        emit({"tool": "tickets_lint", "version": 1, "ok": False, "input_error": "usage: tickets_lint.py FILE [--max-criteria N] [--max-size-days D] [--strict] (%s)" % exc})
        return 2
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8-sig")
        if not text.strip():
            raise InputProblem("file is empty")
        if text.lstrip().startswith(("{", "[")):
            fmt, tickets = "json", parse_json(text)
        else:
            fmt, tickets = "markdown", parse_markdown(text)
        if not tickets:
            raise InputProblem('no tickets found; Markdown tickets start with a "## T1: Title" heading')
    except (OSError, UnicodeDecodeError, InputProblem) as exc:
        emit({"tool": "tickets_lint", "version": 1, "file": path, "ok": False, "input_error": str(exc)})
        return 2
    findings, order = lint(tickets, max_c, max_d)
    rep = build_report(path, fmt, tickets, findings, order, max_c, max_d)
    emit(rep)
    return 1 if rep["errors"] or (strict and rep["warnings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
