#!/usr/bin/env python3
"""Structural scan of a Markdown plan, and a validator for a risk register.

Usage:
    python plan_scan.py scan <plan.md> [--today YYYY-MM-DD]
    python plan_scan.py register <plan.md> <register.json>

scan       Parses headings, checklist items, numbered items and step tables.
           For every open step it looks for an owner, a date, a verification
           (done) criterion and the dependencies it names, then reports the
           gaps. Prints one JSON object to stdout.
register   Checks a risk register the agent wrote against the output contract
           in SKILL.md: required fields, score arithmetic, rank order, and
           that every quoted piece of evidence really occurs in the plan.

Reads only the files named on the command line. Writes nothing except the
JSON report on stdout. No network.

Exit codes:
    0  scan: no high-severity finding.  register: contract satisfied.
    1  scan: at least one high-severity finding.  register: contract broken.
    2  usage error, missing/empty/unreadable file, or invalid JSON input.
       The message is printed as {"error": "..."} so stdout is always JSON.

All detection is lexical. The report lists what the text says, not whether it
is true; the judgement belongs to the reader (see SKILL.md).
"""
import datetime
import json
import os
import re
import sys

VERSION = "1.0"
MAX_BYTES = 2_000_000  # a plan larger than this is not a plan; refuse rather than hang
CONCENTRATION_SHARE = 0.40  # one owner on 40% or more of open steps is a single point of failure
CONCENTRATION_MIN_STEPS = 4  # ...but only judge it when the plan has at least this many open steps
WEAK_GAP_RATE = 0.50  # share of open steps missing owner, date or verification that makes the plan "weak"
GAPS_GAP_RATE = 0.20  # below this (and no high finding) the structure is "sound"
MATCH_RATIO = 0.67  # share of a dependency phrase's words that must appear in one defined item
MAX_RISKS = 12
MIN_RISKS = 3
CATEGORIES = ("assumption", "dependency", "single_point_of_failure", "ownership",
              "done_criteria", "schedule", "scope", "external", "rollback", "resource")
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
MONTH_NUM = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun",
                                             "jul", "aug", "sep", "oct", "nov", "dec"])}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(?:\[( |x|X)\]\s+)?(.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")

OWNER_KEY = r"(?:owner|assignee|assigned to|assigned|lead|dri|responsible|accountable|resp)"
OWNER_VAL_RE = re.compile(r"\b" + OWNER_KEY + r"\b\s*[:=]\s*([^|;\)\]\n]+)", re.I)
OWNER_CUT_RE = re.compile(r"[,\s]+(?=(?:due|deadline|eta|date|target|depends?|verify|verification)\b)", re.I)
MENTION_RE = re.compile(r"(?<![\w.])@([A-Za-z][\w.\-]*)")
OWNER_SPLIT_RE = re.compile(r"\s*(?:,|&|/|\+|\band\b)\s*", re.I)
OWNER_PLACEHOLDERS = {"tbd", "tba", "tbc", "?", "??", "???", "someone", "anyone", "unassigned",
                      "n/a", "na", "none", "nobody", "-", "unknown", "to be assigned", "to be decided"}
GROUP_OWNERS = {"team", "the team", "teams", "everyone", "all", "we", "us", "engineering", "eng",
                "marketing", "sales", "ops", "operations", "support", "product", "design", "legal",
                "finance", "hr", "it", "management", "leadership", "stakeholders", "business"}

ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
MON_DAY_RE = re.compile(r"\b(" + MONTHS + r")[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\b", re.I)
DAY_MON_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + MONTHS + r")[a-z]*\.?(?:,?\s+(\d{4}))?\b", re.I)
SLASH_RE = re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b")
DOTTED_RE = re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b")
LOOSE_DATE_RES = [
    re.compile(r"\b[QH][1-4]\b(?:\s*\d{4})?", re.I),
    re.compile(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I),
    re.compile(r"\b(?:week|day|sprint|wk)\s*#?\s*\d+\b", re.I),
    re.compile(r"\b[TD]\s?[-+]\s?\d+\b"),
    re.compile(r"\bweek of\b", re.I),
    re.compile(r"\bend of (?:day|week|month|quarter|year)\b", re.I),
    re.compile(r"\b(?:eod|eow|eom|eoq)\b", re.I),
    re.compile(r"\b(?:" + MONTHS + r")[a-z]*\.?\s+\d{4}\b", re.I),
]
DATE_KEY_RE = re.compile(r"\b(?:due|deadline|target date|target|date|eta|when|by)\b\s*[:=]?\s*", re.I)
VAGUE_DATE_RE = re.compile(r"\b(?:asap|soon|tbd|tba|later|eventually|when ready|as needed|ongoing|someday|in due course|at some point)\b", re.I)

VERIFY_RE = re.compile(
    r"\b(?:verif\w*|validat\w*|accept\w*|done (?:when|if|=)|definition of done|dod|success criteri\w*|exit criteri\w*|"
    r"pass(?:es|ed)?|sign[- ]?off|signed off|approved by|confirm\w*|reconcil\w*|measured|metrics?|kpis?|threshold|"
    r"smoke test|evidence|expected)\b|[<>≤≥]=?\s*\d|\d+(?:\.\d+)?\s*%", re.I)

DEP_RE = re.compile(
    r"\b(?:depends? on|dependent on|dependency|blocked by|waiting (?:on|for)|requires?|needs?|only after|after|once|"
    r"prerequisites?|prereq|contingent on|gated by|until)\b\s*[:\-]?\s*([^,;.|()\[\]\n]+)", re.I)
DEP_STRICT_RE = re.compile(  # used on continuation lines, where "after" is usually prose, not a dependency
    r"\b(?:depends? on|dependent on|blocked by|waiting (?:on|for)|requires?|needs?|prerequisites?|prereq|contingent on|gated by)\b"
    r"\s*[:\-]?\s*([^,;.|()\[\]\n]+)", re.I)
DEP_CUT_RE = re.compile(r"\s+(?:then|and then|so that|so|and)\s+", re.I)
DEP_SPLIT_RE = re.compile(r"\s+(then|and then|so that|so|and)\s+", re.I)
AND_CLAUSE_STARTS = {"it", "we", "they", "he", "she", "i", "you", "is", "are", "was", "were", "will", "can", "must",
                     "should", "would", "may", "might", "has", "have", "had", "do", "does", "not", "also", "then"}
ID_REF_RE = re.compile(r"(?:\bstep|\btask|\bitem)\s+(\d+)\b|#(\d+)\b|\b([A-Z]{1,4}-?\d{1,3})\b")
LEAD_ID_RE = re.compile(r"^\**([A-Z]{1,4}-?\d{1,3})\**\s*[:.)\-–—]\s+|^\[([A-Z]{1,4}-?\d{1,3})\]\s*")
PLACEHOLDER_RE = re.compile(r"\b(?:tbd|tba|todo|to be (?:decided|determined|confirmed))\b|\?\?+", re.I)

STOPWORDS = set("a an the of to for in on at by with from as is are be been it its this that these those our your their "
                "we you they or if then than so not no any all each per via into out up down over under complete completes "
                "completed completion done finish finishes finished ready approved approval signed merged ships shipped "
                "lands landed begins begin start starts started has have had will can may should must".split())

GOAL_RE = re.compile(r"\b(?:goals?|objectives?|success (?:criteria|metrics?|measures?)|definition of done|outcomes?|"
                     r"target state|exit criteria|acceptance criteria)\b", re.I)
RISK_RE = re.compile(r"\b(?:risks?|assumptions?|open questions|constraints|unknowns)\b", re.I)
ROLLBACK_RE = re.compile(r"\b(?:roll ?back|fall ?back|contingency|revert\w*|back ?out|abort criteri\w*|kill switch|plan b|restore)\b", re.I)
SCOPE_RE = re.compile(r"\b(?:out of scope|non-goals?|not in scope|out-of-scope)\b", re.I)
DEPSEC_RE = re.compile(r"\b(?:dependenc\w*|prerequisites?|inputs|external)\b", re.I)

TABLE_COLS = {
    "title": ("step", "task", "action", "milestone", "deliverable", "item", "activity", "work"),
    "owner": ("owner", "assignee", "lead", "dri", "responsible", "who"),
    "date": ("date", "due", "deadline", "when", "target", "eta"),
    "verify": ("verification", "verify", "done", "acceptance", "criteria", "check", "exit", "definition"),
    "deps": ("depends", "dependency", "dependencies", "blocked", "prereq", "requires"),
}


class UsageError(Exception):
    pass


def emit(obj):
    """Print strict JSON (no NaN, ASCII only) so every consumer can parse it."""
    sys.stdout.write(json.dumps(obj, indent=2, sort_keys=False, ensure_ascii=True, allow_nan=False) + "\n")


def read_text(path):
    if not os.path.isfile(path):
        raise UsageError(f"file not found: {path}")
    if os.path.getsize(path) == 0:
        raise UsageError(f"file is empty: {path}")
    if os.path.getsize(path) > MAX_BYTES:
        raise UsageError(f"file is larger than {MAX_BYTES} bytes: {path}")
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        text = fh.read()
    if not text.strip():
        raise UsageError(f"file has no text: {path}")
    return text


def tokens(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) < 3 or w in STOPWORDS:
            continue
        for suf in ("ing", "ed", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                w = w[: -len(suf)]
                break
        out.add(w)
    return out


def clip(text, n=110):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[: n - 3] + "..."


def parse_date_match(text):
    """Return (kind, iso_or_None, matched_text). kind: exact, approximate, none."""
    m = ISO_RE.search(text)
    if m:
        try:
            d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return "exact", d.isoformat(), m.group(0)
        except ValueError:
            return "approximate", None, m.group(0)
    for rx, mon_i, day_i in ((MON_DAY_RE, 1, 2), (DAY_MON_RE, 2, 1)):
        m = rx.search(text)
        if m:
            year = m.group(3)
            mon = MONTH_NUM.get(m.group(mon_i).lower()[:3])
            if year and mon:
                try:
                    return "exact", datetime.date(int(year), mon, int(m.group(day_i))).isoformat(), m.group(0)
                except ValueError:
                    pass
            return "approximate", None, m.group(0)
    for rx in (SLASH_RE, DOTTED_RE, *LOOSE_DATE_RES):
        m = rx.search(text)
        if m:
            return "approximate", None, m.group(0)
    return "none", None, None


def extract_owners(text):
    """Return (owners, placeholders, groups)."""
    names = []
    for m in OWNER_VAL_RE.finditer(text):
        val = OWNER_CUT_RE.split(m.group(1))[0]
        for part in OWNER_SPLIT_RE.split(val):
            part = part.strip(" \t.*_`\"'@")
            if part:
                names.append(part)
    for m in MENTION_RE.finditer(text):
        names.append(m.group(1).rstrip(".-"))
    seen, owners = set(), []
    for n in names:
        key = n.lower()
        if key not in seen:
            seen.add(key)
            owners.append(n)
    placeholders = [o for o in owners if o.lower() in OWNER_PLACEHOLDERS]
    groups = [o for o in owners if o.lower() in GROUP_OWNERS]
    real = [o for o in owners if o.lower() not in OWNER_PLACEHOLDERS]
    return real, placeholders, groups


def extract_deps(text, strict=False):
    deps = []
    for m in (DEP_STRICT_RE if strict else DEP_RE).finditer(text):
        parts = DEP_SPLIT_RE.split(m.group(1))  # text, separator, text, separator, ...
        segments = parts[0::2]
        seps = [s.strip().lower() for s in parts[1::2]]
        phrase = segments[0].strip(" 	:-*_`\"'")
        for seg, sep in zip(segments[1:], seps):
            if seg.lower().startswith("on "):  # "depends on A and on B" names a second dependency
                deps.append(" ".join(seg[3:].split()[:10]).strip(" 	:-*_`\"'"))
            elif sep == "and":  # "A and B": a short noun phrase after a plain "and" is a second dependency
                words = seg.split()
                if 1 <= len(words) <= 8 and words[0].lower() not in AND_CLAUSE_STARTS:
                    deps.append(" ".join(words).strip(" 	:-*_`\"'"))
        words = phrase.split()
        if not words or len(words) > 10:
            words = words[:10]
            phrase = " ".join(words)
        if not words or words[0].lower() in {"it", "that", "this", "them", "which"}:
            continue
        if not tokens(phrase) and not ID_REF_RE.search(phrase):
            continue
        kind, _, _ = parse_date_match(phrase)
        if kind != "none" and len(tokens(phrase)) <= 1:
            continue  # "after Friday" is a date, not a dependency
        deps.append(phrase)
    out, seen = [], set()
    for d in deps:
        if d.lower() not in seen:
            seen.add(d.lower())
            out.append(d)
    return out


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def map_columns(header):
    cols = {}
    for i, cell in enumerate(header):
        low = cell.lower()
        for field, keys in TABLE_COLS.items():
            if field not in cols and any(k in low for k in keys):
                cols[field] = i
                break
    return cols


def synth_row_text(cells, cols):
    def cell(field):
        i = cols.get(field)
        if i is None or i >= len(cells):
            return None
        v = cells[i].strip()
        return v if v and v not in ("-", "—", "–") else None
    title = cell("title") or ""
    parts = [title]
    for field, label in (("owner", "owner"), ("date", "due"), ("verify", "verify"), ("deps", "depends on")):
        v = cell(field)
        if v:
            parts.append(f"{label}: {v}")
    return " | ".join(parts)


def parse_plan(text):
    """Return (headings, steps, defined_items, section_notes, plan_lines)."""
    lines = text.splitlines()
    headings, steps, defined = [], [], []
    stack = []  # (level, title, owner, date)
    in_fence = False
    last_step = None
    table = None  # dict(cols=..., ) while inside a step table
    pending_header = None
    for n, raw in enumerate(lines, 1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = raw.rstrip()
        if not line.strip():
            continue
        hm = HEADING_RE.match(line)
        if hm:
            level, title = len(hm.group(1)), hm.group(2).strip()
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            owners, _, _ = extract_owners(title)
            dkind, diso, dtxt = parse_date_match(title)
            stack.append({"level": level, "title": title, "owner": owners[0] if owners else None,
                          "date": dtxt if dkind != "none" else None})
            headings.append({"line": n, "level": level, "title": title})
            last_step, table, pending_header = None, None, None
            continue
        section = [s["title"] for s in stack]
        in_dep_section = any(DEPSEC_RE.search(t) for t in section)
        sec_title = section[-1] if section else ""

        if line.lstrip().startswith("|"):
            cells = split_row(line)
            if TABLE_SEP_RE.match(line):
                if pending_header is not None:
                    cols = map_columns(pending_header)
                    table = cols if "title" in cols else None
                pending_header = None
                continue
            if table is None and pending_header is None:
                pending_header = cells
                continue
            if table is not None:
                text_row = synth_row_text(cells, table)
                if text_row.strip(" |"):
                    steps.append(make_step(n, sec_title, stack, None, False, text_row, "table", len(raw) - len(raw.lstrip())))
                    last_step = None
                continue
            pending_header = None
            continue
        pending_header, table = None, None

        im = ITEM_RE.match(line)
        if im:
            indent, marker, box, body = len(im.group(1).expandtabs(4)), im.group(2), im.group(3), im.group(4)
            is_step = box is not None or marker[0].isdigit()
            if last_step is not None and indent > last_step["indent"] and not is_step:
                last_step["text"] += " " + body.strip()
                last_step["last_line"] = n
                continue
            if is_step:
                num = int(re.match(r"\d+", marker).group(0)) if marker[0].isdigit() else None
                typed = re.match(r"(\d+)[.)]\s", body)  # "- [ ] 4. Do it": number typed inside a checklist item
                if num is None and typed:
                    num = int(typed.group(1))
                step = make_step(n, sec_title, stack, num, box is not None and box.lower() == "x", body, marker, indent)
                steps.append(step)
                last_step = step
                if in_dep_section:
                    defined.append({"line": n, "text": body})
                continue
            if in_dep_section:
                defined.append({"line": n, "text": body})
            note_section(stack, body)
            last_step = None
            continue
        # paragraph or continuation line
        indent = len(line) - len(line.lstrip())
        if last_step is not None and indent > last_step["indent"]:
            last_step["text"] += " " + line.strip()
            last_step["last_line"] = n
            continue
        note_section(stack, line.strip())
        last_step = None
    return headings, steps, defined


def note_section(stack, body):
    """A line such as 'Owner: Dana' or 'Due: 2026-04-01' sets the section default."""
    if not stack:
        return
    top = stack[-1]
    owners, _, _ = extract_owners(body)
    if owners and top["owner"] is None and re.match(r"^\W*" + OWNER_KEY + r"\b", body, re.I):
        top["owner"] = owners[0]
    if top["date"] is None and re.match(r"^\W*(?:due|deadline|target date|target|date|eta)\b", body, re.I):
        kind, _, txt = parse_date_match(body)
        if kind != "none":
            top["date"] = txt


def make_step(line, section, stack, number, done, text, marker, indent):
    return {"line": line, "last_line": line, "section": section, "number": number, "done": done,
            "text": text.strip(), "head": text.strip(), "table": marker == "table", "indent": indent, "marker": marker,
            "inherit_owner": next((s["owner"] for s in reversed(stack) if s["owner"]), None),
            "inherit_date": next((s["date"] for s in reversed(stack) if s["date"]), None)}


def enrich(steps, today):
    """Add id, owners, date, verification and dependencies to each step."""
    used = {}
    for st in steps:
        text = st["text"]
        m = LEAD_ID_RE.match(text)
        st["explicit_id"] = (m.group(1) or m.group(2)) if m else None
        st["id"] = st["explicit_id"] or f"L{st['line']}"
        st["title"] = clip(LEAD_ID_RE.sub("", text, count=1) if m else text, 140)
        if st["table"]:
            st["title"] = clip(text.split(" | ")[0], 140)
        st["title"] = re.sub(r"^\d+[.)]\s+", "", st["title"])
        used.setdefault(st["id"], []).append(st)
        owners, placeholders, groups = extract_owners(text)
        st["owners"], st["owner_placeholders"], st["group_owners"] = owners, placeholders, groups
        st["owner_source"] = "step" if owners else None
        if not owners and not placeholders and st["inherit_owner"]:
            inh = st["inherit_owner"]
            if inh.lower() not in OWNER_PLACEHOLDERS:
                st["owners"], st["owner_source"] = [inh], "section"
                if inh.lower() in GROUP_OWNERS:
                    st["group_owners"] = [inh]
        kind, iso, dtxt = parse_date_match(text)
        st["date_text"], st["date_iso"], st["date_kind"], st["date_source"] = dtxt, iso, kind, ("step" if kind != "none" else None)
        if kind == "none" and st["inherit_date"]:
            k2, i2, t2 = parse_date_match(st["inherit_date"])
            st["date_text"], st["date_iso"], st["date_kind"], st["date_source"] = t2, i2, k2, "section"
        st["vague_date"] = st["date_kind"] == "none" and bool(VAGUE_DATE_RE.search(text))
        st["has_verification"] = bool(VERIFY_RE.search(text))
        st["dep_phrases"] = extract_deps(st["head"])
        for extra in extract_deps(text[len(st["head"]):], strict=True):
            if extra.lower() not in [p.lower() for p in st["dep_phrases"]]:
                st["dep_phrases"].append(extra)
        st["has_placeholder"] = bool(PLACEHOLDER_RE.search(text))
    return used


def resolve_dependencies(steps, defined, headings):
    by_id = {}
    by_num = {}
    for st in steps:
        by_id.setdefault(st["id"].upper(), st)
        if st["number"] is not None:
            by_num.setdefault(st["number"], []).append(st)
    corpus = [("step", st, tokens(st["title"])) for st in steps]
    corpus += [("heading", h, tokens(h["title"])) for h in headings]
    corpus += [("defined", d, tokens(d["text"])) for d in defined]
    findings_extra = []
    for st in steps:
        st["deps"] = []
        for phrase in st["dep_phrases"]:
            target, how = None, None
            ref = ID_REF_RE.search(phrase)
            if ref:
                if ref.group(1) or ref.group(2):
                    num = int(ref.group(1) or ref.group(2))
                    cands = [c for c in by_num.get(num, []) if c is not st]
                    same = [c for c in cands if c["section"] == st["section"]]
                    target = (same or cands or [None])[0]
                    how = "number"
                    if len(cands) > 1 and not same:
                        findings_extra.append(("ambiguous_reference", "low", st, f"'{phrase}' matches numbered items in several sections"))
                else:
                    target = by_id.get(ref.group(3).upper())
                    how = "id"
                    if target is st:
                        target = None
                if target is None:
                    st["deps"].append({"text": phrase, "resolved": False, "target": None, "how": "unknown_id"})
                    continue
            else:
                want = tokens(phrase)
                best, best_score = None, 0.0
                for kind, obj, toks in corpus:
                    if obj is st:
                        continue
                    if not want:
                        break
                    score = len(want & toks) / len(want)
                    if score > best_score or (score == best_score and best is not None and kind == "step" and best[0] != "step"):
                        best, best_score = (kind, obj), score
                if best is not None and best_score >= MATCH_RATIO:
                    kind, obj = best
                    target = obj if kind == "step" else None
                    how = "step" if kind == "step" else kind
                    st["deps"].append({"text": phrase, "resolved": True, "target": obj["id"] if kind == "step" else None, "how": how})
                    continue
                st["deps"].append({"text": phrase, "resolved": False, "target": None, "how": "no_match"})
                continue
            st["deps"].append({"text": phrase, "resolved": True, "target": target["id"], "how": how})
    return findings_extra


def find_cycles(steps):
    graph = {st["id"]: [d["target"] for d in st["deps"] if d["target"]] for st in steps}
    cycles, seen_keys = [], set()
    color = {}

    def visit(node, path):
        color[node] = 1
        for nxt in graph.get(node, []):
            if color.get(nxt, 0) == 0:
                visit(nxt, path + [nxt])
            elif color.get(nxt) == 1 and nxt in path:
                cyc = path[path.index(nxt):]
                key = tuple(sorted(cyc))
                if key not in seen_keys:
                    seen_keys.add(key)
                    cycles.append(cyc + [nxt])
        color[node] = 2

    for node in list(graph):
        if color.get(node, 0) == 0:
            visit(node, [node])
    return cycles


def plan_level(text, headings):
    def first(rx, only_headings=False):
        pool = [(h["line"], h["title"]) for h in headings] if only_headings else list(enumerate(text.splitlines(), 1))
        for ln, body in pool:
            if rx.search(body):
                return {"present": True, "line": ln}
        return {"present": False, "line": None}
    return {"goal_or_success_criteria": first(GOAL_RE), "risks_or_assumptions_section": first(RISK_RE, True),
            "rollback_or_fallback": first(ROLLBACK_RE), "out_of_scope": first(SCOPE_RE)}


def scan(text, today):
    headings, steps, defined = parse_plan(text)
    enrich(steps, today)
    extra = resolve_dependencies(steps, defined, headings)
    cycles = find_cycles(steps)
    by_id = {s["id"]: s for s in steps}
    findings = []

    def add(kind, severity, st, detail, line=None):
        findings.append({"kind": kind, "severity": severity, "line": line if line is not None else (st["line"] if st else 0),
                         "step_id": st["id"] if st else None, "detail": detail})

    open_steps = [s for s in steps if not s["done"]]
    for kind, sev, st, detail in extra:
        add(kind, sev, st, detail)
    ids = {}
    for s in steps:
        ids.setdefault(s["id"], []).append(s)
    for sid, group in ids.items():
        if len(group) > 1 and group[0]["explicit_id"]:
            add("duplicate_id", "medium", group[1], f"id {sid} is also used on line {group[0]['line']}")
    for s in open_steps:
        if s["owner_placeholders"] and not s["owners"]:
            add("owner_placeholder", "high", s, f"owner is a placeholder ({s['owner_placeholders'][0]})")
        elif not s["owners"]:
            add("no_owner", "high", s, "no owner named on the step or its section: " + clip(s["title"], 80))
        else:
            if len(s["owners"]) > 1:
                add("multiple_owners", "medium", s, "several owners, none accountable: " + ", ".join(s["owners"]))
            if s["group_owners"] and len(s["group_owners"]) == len(s["owners"]):
                add("group_owner", "low", s, f"owner is a group, not a person ({s['group_owners'][0]})")
        if s["date_kind"] == "none":
            if s["vague_date"]:
                add("vague_date", "medium", s, "date is a vague word, not a date: " + clip(s["title"], 80))
            else:
                add("no_date", "medium", s, "no date or time marker: " + clip(s["title"], 80))
        if not s["has_verification"]:
            add("no_verification", "medium", s, "no done criterion or check named: " + clip(s["title"], 80))
        for d in s["deps"]:
            if not d["resolved"]:
                if d["how"] == "unknown_id":
                    add("undefined_dependency", "medium", s, f"references '{d['text']}' but no step has that id or number")
                else:
                    add("undefined_dependency", "medium", s, f"names '{d['text']}' as a dependency but no step, heading or dependency item defines it")
        if s["has_placeholder"] and not s["owner_placeholders"] and not s["vague_date"]:
            add("open_placeholder", "medium", s, "contains TBD/TODO/??: " + clip(s["title"], 80))
        if today and s["date_iso"] and s["date_iso"] < today.isoformat():
            add("overdue", "high", s, f"open step dated {s['date_iso']} is before today ({today.isoformat()})")
    for cyc in cycles:
        first = by_id[cyc[0]]
        add("dependency_cycle", "high", first, "circular dependency: " + " -> ".join(cyc))
    for s in steps:
        if s["date_iso"] is None:
            continue
        for d in s["deps"]:
            t = by_id.get(d["target"]) if d["target"] else None
            if t and t["date_iso"] and s["date_iso"] < t["date_iso"]:
                add("date_before_dependency", "high", s,
                    f"dated {s['date_iso']} but depends on {t['id']} dated {t['date_iso']}")
    load, shown = {}, {}
    for s in open_steps:
        for o in s["owners"]:
            key = shown.setdefault(o.lower(), o)
            load[key] = load.get(key, 0) + 1
    if len(open_steps) >= CONCENTRATION_MIN_STEPS:
        for o, c in sorted(load.items()):
            if c / len(open_steps) >= CONCENTRATION_SHARE:
                add("owner_concentration", "medium", None,
                    f"{o} owns {c} of {len(open_steps)} open steps; if they are out, the plan stalls", line=0)
    pl = plan_level(text, headings)
    if not steps:
        add("no_steps", "high", None, "no checklist items, numbered items or step table rows found", line=0)
    if not pl["goal_or_success_criteria"]["present"]:
        add("no_success_criteria", "high", None, "no goal, objective or success-criteria wording anywhere in the plan", line=0)
    if not pl["rollback_or_fallback"]["present"]:
        add("no_rollback", "medium", None, "no rollback, fallback or contingency wording anywhere in the plan", line=0)
    if not pl["risks_or_assumptions_section"]["present"]:
        add("no_risk_section", "low", None, "no heading about risks, assumptions or open questions", line=0)
    findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["line"], f["kind"]))
    gap_steps = [s for s in open_steps if (not s["owners"]) or s["date_kind"] == "none" or not s["has_verification"]]
    gap_rate = round(len(gap_steps) / len(open_steps), 2) if open_steps else 0.0
    has_high = any(f["severity"] == "high" for f in findings)
    verdict = "weak" if gap_rate >= WEAK_GAP_RATE else ("sound" if (not has_high and gap_rate < GAPS_GAP_RATE) else "gaps")
    if not steps:
        verdict = "unstructured"  # prose plan: nothing to score, the judgement procedure must do all the work
    counts = {}
    for f in findings:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    report = {
        "tool": "plan_scan", "version": VERSION, "command": "scan",
        "summary": {"headings": len(headings), "steps": len(steps), "open_steps": len(open_steps),
                    "done_steps": len(steps) - len(open_steps),
                    "open_with_owner": sum(1 for s in open_steps if s["owners"]),
                    "open_with_date": sum(1 for s in open_steps if s["date_kind"] != "none"),
                    "open_with_verification": sum(1 for s in open_steps if s["has_verification"]),
                    "dependencies_named": sum(len(s["deps"]) for s in steps),
                    "dependencies_undefined": sum(1 for s in steps for d in s["deps"] if not d["resolved"]),
                    "gap_rate": gap_rate, "verdict": verdict, "today": today.isoformat() if today else None},
        "counts_by_kind": dict(sorted(counts.items())),
        "plan_level": pl,
        "owner_load": dict(sorted(load.items())),
        "steps": [{"id": s["id"], "line": s["line"], "section": s["section"], "title": s["title"],
                   "status": "done" if s["done"] else "open", "owners": s["owners"], "owner_source": s["owner_source"],
                   "date": s["date_text"], "date_iso": s["date_iso"], "date_kind": s["date_kind"],
                   "has_verification": s["has_verification"],
                   "dependencies": s["deps"]} for s in steps],
        "findings": findings,
    }
    return report, has_high


def parse_today(value):
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise UsageError(f"--today must be YYYY-MM-DD, got {value!r}")


def norm(s):
    s = re.sub(r"[*_`]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def check_register(plan_text, reg_text):
    errors, warnings = [], []
    try:
        reg = json.loads(reg_text)
    except ValueError as exc:
        raise UsageError(f"register is not valid JSON: {exc}")
    if not isinstance(reg, dict):
        raise UsageError("register must be a JSON object")
    plan_norm = norm(plan_text)
    plan_lines = plan_text.splitlines()
    for key in ("plan", "risks", "not_checked"):
        if key not in reg:
            errors.append(f"missing top-level key '{key}'")
    extra_top = set(reg) - {"plan", "risks", "not_checked"}
    if extra_top:
        errors.append("unknown top-level keys: " + ", ".join(sorted(extra_top)))
    risks = reg.get("risks")
    if not isinstance(risks, list):
        errors.append("'risks' must be a list")
        risks = []
    if not isinstance(reg.get("not_checked", []), list) or not reg.get("not_checked"):
        errors.append("'not_checked' must be a non-empty list of strings")
    if not (MIN_RISKS <= len(risks) <= MAX_RISKS):
        errors.append(f"register needs {MIN_RISKS} to {MAX_RISKS} risks, has {len(risks)}")
    required = ("rank", "id", "title", "category", "evidence", "scenario", "likelihood", "impact", "score",
                "detection", "mitigation", "source")
    seen_ids, prev_score, covered_lines = set(), None, set()
    for i, r in enumerate(risks, 1):
        tag = f"risks[{i}]"
        if not isinstance(r, dict):
            errors.append(f"{tag} must be an object")
            continue
        missing = [k for k in required if k not in r]
        if missing:
            errors.append(f"{tag} missing fields: {', '.join(missing)}")
            continue
        if r["rank"] != i:
            errors.append(f"{tag} rank is {r['rank']}, expected {i} (ranks run 1..n in order)")
        if r["id"] in seen_ids or not isinstance(r["id"], str) or not r["id"]:
            errors.append(f"{tag} id must be a unique non-empty string")
        seen_ids.add(r["id"])
        if r["category"] not in CATEGORIES:
            errors.append(f"{tag} category '{r['category']}' not in {list(CATEGORIES)}")
        if r["source"] not in ("script", "judgement"):
            errors.append(f"{tag} source must be 'script' or 'judgement'")
        ints_ok = True
        for k in ("likelihood", "impact"):
            if not (isinstance(r[k], int) and not isinstance(r[k], bool) and 1 <= r[k] <= 5):
                errors.append(f"{tag} {k} must be an integer 1 to 5")
                ints_ok = False
        if ints_ok:
            if r["score"] != r["likelihood"] * r["impact"]:
                errors.append(f"{tag} score {r['score']} is not likelihood x impact = {r['likelihood'] * r['impact']}")
            elif prev_score is not None and r["score"] > prev_score:
                errors.append(f"{tag} score {r['score']} is higher than the risk above it; sort by score, highest first")
            prev_score = r["score"]
        for k in ("title", "scenario", "detection", "mitigation"):
            if not isinstance(r[k], str) or len(r[k].split()) < 3:
                errors.append(f"{tag} {k} must be a sentence (at least 3 words)")
        ev = r["evidence"]
        if not isinstance(ev, dict) or (("quote" in ev) == ("absent" in ev)):
            errors.append(f"{tag} evidence must be an object with exactly one of 'quote' or 'absent'")
        elif "quote" in ev:
            q = ev["quote"]
            if not isinstance(q, str) or len(q.strip()) < 8:
                errors.append(f"{tag} evidence.quote must be a string of at least 8 characters")
            elif norm(q) not in plan_norm:
                errors.append(f"{tag} evidence.quote does not occur in the plan: {clip(q, 60)!r}")
            ln = ev.get("line")
            if ln is not None:
                if not (isinstance(ln, int) and 1 <= ln <= len(plan_lines)):
                    errors.append(f"{tag} evidence.line must be a line number inside the plan (1..{len(plan_lines)})")
                else:
                    covered_lines.add(ln)
        else:
            if not isinstance(ev["absent"], str) or len(ev["absent"].split()) < 3:
                errors.append(f"{tag} evidence.absent must say what the plan lacks (at least 3 words)")
        if i <= 3 and isinstance(r.get("mitigation"), str) and not r["mitigation"].strip():
            errors.append(f"{tag} top-3 risks need a mitigation")
    report, _ = scan(plan_text, None)
    uncovered = sorted({f["line"] for f in report["findings"] if f["severity"] == "high" and f["line"] > 0} - covered_lines)
    if uncovered:
        warnings.append("high-severity scan findings on these lines are not cited by any risk: " + ", ".join(map(str, uncovered)))
    return {"tool": "plan_scan", "version": VERSION, "command": "register", "ok": not errors,
            "risk_count": len(risks), "errors": errors, "warnings": warnings,
            "uncovered_high_lines": uncovered}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except (OSError, ValueError):
        pass
    try:
        if not argv or argv[0] not in ("scan", "register"):
            raise UsageError("usage: plan_scan.py scan <plan.md> [--today YYYY-MM-DD] | register <plan.md> <register.json>")
        cmd, rest = argv[0], argv[1:]
        if cmd == "scan":
            today = None
            if "--today" in rest:
                i = rest.index("--today")
                if i + 1 >= len(rest):
                    raise UsageError("--today needs a value YYYY-MM-DD")
                today = parse_today(rest[i + 1])
                rest = rest[:i] + rest[i + 2:]
            if len(rest) != 1:
                raise UsageError("scan takes exactly one plan file")
            report, has_high = scan(read_text(rest[0]), today)
            report["file"] = os.path.basename(rest[0])
            emit(report)
            return 1 if has_high else 0
        if len(rest) != 2:
            raise UsageError("register takes a plan file and a register JSON file")
        result = check_register(read_text(rest[0]), read_text(rest[1]))
        emit(result)
        return 0 if result["ok"] else 1
    except UsageError as exc:
        emit({"error": str(exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main())
