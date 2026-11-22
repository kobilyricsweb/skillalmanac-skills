#!/usr/bin/env python3
"""Validate a Mermaid diagram file and report its size and structure as JSON.

    python mermaid_check.py <file> [--strict]

<file> is a .mmd/.txt file holding one diagram, or a Markdown file with one or
more ```mermaid fenced blocks (each block is checked on its own).

Reads the file it is given. Writes nothing, renders nothing, uses no network.
Prints one JSON object to stdout. Problems with the call go to stderr.

Supported syntax subset
    flowchart / graph  directions TB TD BT LR RL; node shapes [] () ([]) [()]
                       (()) {} {{}} [[]] > ]; edges --> --- -.-> ==> --o --x <-->
                       with |text| or -- text --> labels; chains and `A & B`;
                       subgraph ... end (also the way to draw C4-style boundaries);
                       classDef/class/style/linkStyle/click lines are skipped.
    sequenceDiagram    participant/actor [as], messages with -> --> ->> -->> -x
                       --x -) --), +/- activation marks, Note, activate,
                       deactivate, loop/alt/opt/par/critical/break/rect/box ... end.
    Other types (classDiagram, erDiagram, C4Context, ...) are reported as
    unsupported, not checked.

JSON contract (schema_version 1)
    {"schema_version": 1, "file": str, "verdict": "pass"|"warn"|"fail",
     "diagrams": [{"index": int, "start_line": int, "type": str,
        "direction": str|null, "verdict": "pass"|"warn"|"fail",
        "metrics": {"nodes": int, "edges": int, "subgraphs": int,
                    "max_nesting": int, "max_degree": int,
                    "unlabeled_edge_ratio": float|null, "max_label_chars": int},
        "orphans": [str], "duplicate_ids": [str],
        "findings": [{"level": "error"|"warn", "code": str,
                      "line": int, "message": str}]}],
     "thresholds": {...}}
    For sequence diagrams, nodes = participants and edges = messages.
    Lines are 1-based line numbers in the input file.

Exit codes
    0  verdict pass or warn
    1  verdict fail (any error finding), or warn when --strict is given
    2  usage error, unreadable file, or empty file

Output is strict JSON (ASCII only, no NaN).
"""
import json
import os
import re
import sys

SCHEMA_VERSION = 1

# Thresholds. A reader can hold about 7 items in short-term memory, and a diagram
# that needs more than one screen stops being read; the numbers below are working
# values for one diagram, not measured optima. Warn = split it soon; error = split it.
FLOW_NODES_WARN, FLOW_NODES_ERROR = 15, 25
FLOW_EDGES_WARN, FLOW_EDGES_ERROR = 25, 40
SEQ_PARTICIPANTS_WARN, SEQ_PARTICIPANTS_ERROR = 7, 10
SEQ_MESSAGES_WARN, SEQ_MESSAGES_ERROR = 20, 30
NESTING_WARN = 2          # subgraph or block depth above this is hard to scan
LABEL_WARN = 40           # characters; longer labels wrap into walls of text
HUB_DEGREE_WARN = 8       # one node touching this many edges is a star, not a design
UNLABELED_RATIO_WARN = 0.5  # share of edges with no label, checked from 4 edges up
OPAQUE_ID_RATIO_WARN = 0.5  # share of one-letter ids, checked from 4 nodes up
STEP_LABELS_WARN = 3      # edge labels that start with a step number

THRESHOLDS = {
    "flowchart_nodes": [FLOW_NODES_WARN, FLOW_NODES_ERROR],
    "flowchart_edges": [FLOW_EDGES_WARN, FLOW_EDGES_ERROR],
    "sequence_participants": [SEQ_PARTICIPANTS_WARN, SEQ_PARTICIPANTS_ERROR],
    "sequence_messages": [SEQ_MESSAGES_WARN, SEQ_MESSAGES_ERROR],
    "nesting_warn_above": NESTING_WARN,
    "label_chars_warn_above": LABEL_WARN,
    "hub_degree_warn_from": HUB_DEGREE_WARN,
    "unlabeled_edge_ratio_warn_above": UNLABELED_RATIO_WARN,
    "opaque_id_ratio_warn_above": OPAQUE_ID_RATIO_WARN,
}

DIRECTIONS = {"TB", "TD", "BT", "LR", "RL"}
SKIP_FLOW = ("classdef ", "class ", "style ", "linkstyle ", "click ", "acctitle", "accdescr", "direction ")
ID_RE = re.compile(r"\w+(?:-(?![->.=])\w+)*")
# (opener, closers), longest opener first so "((" is not read as "(".
SHAPES = [
    ("(((", [")))"]), ("[[", ["]]"]), ("[(", [")]"]), ("([", ["])"]), ("((", ["))"]),
    ("{{", ["}}"]), ("[/", ["/]", "\\]"]), ("[\\", ["\\]", "/]"]), (">", ["]"]),
    ("[", ["]"]), ("(", [")"]), ("{", ["}"]),
]
EDGE_PLAIN = re.compile(
    r"(?:<|o|x)?(?:-{2,}>|-{3,}|={2,}>|={3,}|-\.+->|-\.+-|--[ox](?!\w))(?:\|(?P<t>[^|]*)\|)?")
EDGE_TEXT = re.compile(
    r"(?:--|==|-\.)\s*(?P<t>.+?)\s*(?:-{2,}[>ox]?|={2,}>?|\.+-+>?)")
INFRA_WORDS = re.compile(
    r"\b(database|db|postgres|mysql|redis|kafka|queue|bucket|s3|load balancer|cdn|gateway|"
    r"kubernetes|k8s|cluster|vpc|server|cache|broker|lambda|container)\b", re.I)
CODE_LABEL = re.compile(r"\w+\(\)|\w+\.(?:py|ts|js|java|go|rs|rb)|\w+::\w+")
STEP_LABEL = re.compile(r"^\s*(\d+)[.):]")

SEQ_ARROW = r"(?:<<-->>|<<->>|-->>|->>|--x|-x|--\)|-\)|-->|->)"
SEQ_MSG = re.compile(
    r"^(?P<a>\w+)\s*(?P<arrow>" + SEQ_ARROW + r")(?P<act>[+-])?\s*(?P<b>\w+)\s*:\s*(?P<text>.*)$")
SEQ_DECL = re.compile(r"^(?:create\s+)?(?P<kw>participant|actor)\s+(?P<id>\w+)(?:\s+as\s+(?P<label>.+))?$")
SEQ_NOTE = re.compile(r"^note\s+(?:left of|right of|over)\s+(?P<who>[\w, ]+?)\s*:", re.I)
SEQ_OPEN = ("loop", "alt", "opt", "par", "critical", "break", "rect", "box")
SEQ_MID = ("else", "and", "option")


class Diagram:
    def __init__(self, index, start_line):
        self.index = index
        self.start_line = start_line
        self.type = None
        self.direction = None
        self.findings = []
        self.nodes = {}            # id -> {"label": str|None, "line": int}
        self.edges = []            # (src, dst, label|None, line)
        self.subgraphs = {}        # id -> {"members": set, "line": int, "depth": int}
        self.sub_stack = []
        self.max_nesting = 0
        self.participants = {}     # id -> {"label": str|None, "line": int, "declared": bool}
        self.messages = 0
        self.used = set()
        self.activations = {}
        self.block_stack = []
        self.max_labels = 0
        self.duplicate_ids = []

    def add(self, level, code, line, message):
        self.findings.append({"level": level, "code": code, "line": line, "message": message})


def split_statements(s):
    """Split a flowchart line on ';' that sits outside quotes."""
    out, buf, quote = [], [], False
    for ch in s:
        if ch == '"':
            quote = not quote
        if ch == ";" and not quote:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    out.append("".join(buf))
    return [p.strip() for p in out if p.strip()]


def parse_node(s, pos, d, lineno):
    """Parse `id` plus optional shape/label at pos. Returns (id, new_pos) or (None, pos)."""
    m = ID_RE.match(s, pos)
    if not m:
        return None, pos
    nid = m.group(0)
    pos = m.end()
    if "-" in nid:
        d.add("warn", "hyphen_id", lineno, "id '%s' contains a hyphen; use letters, digits and underscores" % nid)
    label = None
    if s.startswith("@{", pos):
        end = s.find("}", pos)
        pos = len(s) if end < 0 else end + 1
    else:
        for opener, closers in SHAPES:
            if s.startswith(opener, pos):
                inner = pos + len(opener)
                quoted = s.startswith('"', inner)
                if quoted:
                    q = s.find('"', inner + 1)
                    if q < 0:
                        d.add("error", "unclosed_quote", lineno, "unclosed quote in label of '%s'" % nid)
                        return nid, len(s)
                    text = s[inner + 1:q]
                    search_from = q + 1
                else:
                    text = None
                    search_from = inner
                hits = [(s.find(c, search_from), c) for c in closers if s.find(c, search_from) >= 0]
                if not hits:
                    d.add("error", "unclosed_shape", lineno, "shape opened with '%s' on '%s' is never closed" % (opener, nid))
                    return nid, len(s)
                at, closer = min(hits)
                if text is None:
                    text = s[inner:at]
                    if opener in ("[", "(", "{") and re.search(r"[()\[\]{}]", text):
                        d.add("warn", "risky_unquoted_label", lineno,
                              "label of '%s' has brackets or parentheses; wrap it in double quotes" % nid)
                label = text.strip()
                pos = at + len(closer)
                break
    cls = re.match(r":::\w+", s[pos:])
    if cls:
        pos += cls.end()
    note_node(d, nid, label, lineno)
    return nid, pos


def note_node(d, nid, label, lineno):
    cur = d.nodes.get(nid)
    if cur is None:
        d.nodes[nid] = {"label": label, "line": lineno}
        return
    if label is not None:
        if cur["label"] is not None and cur["label"] != label:
            d.add("error", "duplicate_id", lineno,
                  "id '%s' is defined twice with different labels ('%s' on line %d, '%s' here)" % (nid, cur["label"], cur["line"], label))
            if nid not in d.duplicate_ids:
                d.duplicate_ids.append(nid)
        elif cur["label"] is None:
            cur["label"] = label


def parse_group(s, pos, d, lineno):
    """Parse `A & B & C`. Returns (ids, new_pos)."""
    ids = []
    while True:
        while pos < len(s) and s[pos] == " ":
            pos += 1
        nid, pos = parse_node(s, pos, d, lineno)
        if nid is None:
            return ids, pos
        ids.append(nid)
        probe = pos
        while probe < len(s) and s[probe] == " ":
            probe += 1
        if probe < len(s) and s[probe] == "&":
            pos = probe + 1
            continue
        return ids, pos


def parse_flow_statement(s, d, lineno):
    if re.search(r"---[ox]\w", s):
        d.add("warn", "ox_edge_pitfall", lineno,
              "'---' followed directly by an id starting with o or x is read as a circle or cross edge; add a space")
    pos, prev, edge_label = 0, None, None
    while True:
        ids, pos = parse_group(s, pos, d, lineno)
        if not ids:
            d.add("error", "syntax", lineno, "cannot read a node at column %d of '%s'" % (pos + 1, s[:60]))
            return
        for sid in d.sub_stack[-1:]:
            for nid in ids:
                d.subgraphs[sid]["members"].add(nid)
        if prev is not None:
            for a in prev:
                for b in ids:
                    d.edges.append((a, b, edge_label, lineno))
        while pos < len(s) and s[pos] == " ":
            pos += 1
        if pos >= len(s):
            return
        m = EDGE_PLAIN.match(s, pos)
        if m:
            edge_label = (m.group("t") or "").strip().strip('"') or None
        else:
            m = EDGE_TEXT.match(s, pos)
            if not m:
                d.add("error", "syntax", lineno, "unreadable text after a node: '%s'" % s[pos:pos + 40])
                return
            edge_label = m.group("t").strip() or None
        pos = m.end()
        prev = ids


def parse_flowchart(lines, d):
    header = lines[0][1].split()
    if len(header) > 1:
        if header[1].upper() in DIRECTIONS:
            d.direction = header[1].upper()
        else:
            d.add("error", "bad_direction", lines[0][0], "'%s' is not a direction; use TB, TD, BT, LR or RL" % header[1])
    else:
        d.add("warn", "no_direction", lines[0][0], "no direction after '%s'; state one (TB or LR) so the layout is a decision" % header[0])
    for lineno, raw in lines[1:]:
        low = raw.lower()
        if low.startswith("subgraph"):
            rest = raw[8:].strip()
            m = re.match(r"(\w+)\s*\[(.*)\]\s*$", rest)
            sid = m.group(1) if m else (re.sub(r"\W+", "_", rest.strip('"')) or "subgraph")
            if sid in d.subgraphs:
                d.add("error", "duplicate_id", lineno, "subgraph id '%s' is used twice" % sid)
                if sid not in d.duplicate_ids:
                    d.duplicate_ids.append(sid)
            d.subgraphs[sid] = {"members": set(), "line": lineno, "depth": len(d.sub_stack) + 1}
            d.sub_stack.append(sid)
            d.max_nesting = max(d.max_nesting, len(d.sub_stack))
            continue
        if low == "end":
            if not d.sub_stack:
                d.add("error", "unbalanced_end", lineno, "'end' with no open subgraph")
            else:
                d.sub_stack.pop()
            continue
        if low.startswith(SKIP_FLOW):
            continue
        for stmt in split_statements(raw):
            if stmt.lower() == "end":
                if d.sub_stack:
                    d.sub_stack.pop()
                continue
            parse_flow_statement(stmt, d, lineno)
    for sid in d.sub_stack:
        d.add("error", "unbalanced_subgraph", d.subgraphs[sid]["line"], "subgraph '%s' has no matching 'end'" % sid)
    finish_flowchart(d)


def finish_flowchart(d):
    sub_ids = set(d.subgraphs)
    for sid in sub_ids:
        info = d.nodes.get(sid)
        if info is not None and info["label"] is not None:
            d.add("error", "duplicate_id", info["line"], "id '%s' is both a subgraph and a node" % sid)
            if sid not in d.duplicate_ids:
                d.duplicate_ids.append(sid)
    for nid in list(d.nodes):
        if nid in sub_ids and d.nodes[nid]["label"] is None:
            del d.nodes[nid]
    for nid, info in d.nodes.items():
        if nid == "end":
            d.add("error", "reserved_id", info["line"], "'end' as a node id breaks Mermaid; rename it")
    lowered = {}
    for nid in d.nodes:
        lowered.setdefault(nid.lower(), []).append(nid)
    for group in lowered.values():
        if len(group) > 1:
            d.add("warn", "case_variant_ids", d.nodes[group[0]]["line"],
                  "ids differing only by case: %s; they are different nodes in Mermaid" % ", ".join(sorted(group)))
    by_label = {}
    for nid, info in d.nodes.items():
        if info["label"]:
            by_label.setdefault(info["label"].lower(), []).append(nid)
    for label, group in by_label.items():
        if len(group) > 1:
            d.add("warn", "duplicate_label", d.nodes[group[1]]["line"],
                  "ids %s all carry the label '%s'; one thing drawn twice" % (", ".join(sorted(group)), label))
            for nid in group:
                if nid not in d.duplicate_ids:
                    d.duplicate_ids.append(nid)
    deg = {nid: 0 for nid in d.nodes}
    for a, b, _label, _ln in d.edges:
        for x in (a, b):
            if x in deg:
                deg[x] += 1
    d.degree = deg
    d.orphans = sorted(nid for nid, n in deg.items() if n == 0)
    for nid in d.orphans:
        d.add("warn", "orphan_node", d.nodes[nid]["line"], "node '%s' has no edges" % nid)
    for sid, info in d.subgraphs.items():
        members = [m for m in info["members"] if m in d.nodes or m in sub_ids]
        if not members:
            d.add("warn", "empty_subgraph", info["line"], "subgraph '%s' is empty" % sid)
        elif len(members) == 1:
            d.add("warn", "singleton_subgraph", info["line"], "subgraph '%s' holds one node; a box around one thing adds nothing" % sid)
    labels = [i["label"] or nid for nid, i in d.nodes.items()]
    d.max_labels = max([len(x) for x in labels] + [len(e[2] or "") for e in d.edges] + [0])
    for nid, info in d.nodes.items():
        if info["label"] and len(info["label"]) > LABEL_WARN:
            d.add("warn", "long_label", info["line"], "label of '%s' is %d characters; keep it under %d" % (nid, len(info["label"]), LABEL_WARN))
    n, e = len(d.nodes), len(d.edges)
    density(d, n, e, FLOW_NODES_WARN, FLOW_NODES_ERROR, FLOW_EDGES_WARN, FLOW_EDGES_ERROR, "nodes", "edges")
    if d.max_nesting > NESTING_WARN:
        d.add("warn", "deep_nesting", d.start_line, "subgraphs nest %d deep; more than %d levels is hard to read" % (d.max_nesting, NESTING_WARN))
    if e:
        hub = max(deg, key=lambda k: deg[k])
        if deg[hub] >= HUB_DEGREE_WARN:
            d.add("warn", "hub_node", d.nodes[hub]["line"], "node '%s' touches %d edges; a star usually hides the real structure" % (hub, deg[hub]))
    if e >= 4:
        unl = sum(1 for x in d.edges if not x[2])
        if unl / e > UNLABELED_RATIO_WARN:
            d.add("warn", "unlabeled_edges", d.start_line, "%d of %d edges have no label; say what flows or which protocol" % (unl, e))
    steps = sum(1 for x in d.edges if x[2] and STEP_LABEL.match(x[2]))
    if steps >= STEP_LABELS_WARN:
        d.add("warn", "sequence_in_flowchart", d.start_line, "%d edges carry step numbers; order over time belongs in a sequenceDiagram" % steps)
    if n >= 4 and sum(1 for nid in d.nodes if len(nid) == 1) / n > OPAQUE_ID_RATIO_WARN:
        d.add("warn", "opaque_ids", d.start_line, "most ids are one letter; use ids that name the thing so the source can be reviewed")
    code_like = [x for x in labels if CODE_LABEL.search(x)]
    infra_like = [x for x in labels if INFRA_WORDS.search(x)]
    if code_like and infra_like:
        d.add("warn", "mixed_levels", d.start_line,
              "code-level labels (%s) share a diagram with infrastructure labels (%s); one diagram, one level" % (code_like[0], infra_like[0]))


def density(d, n, e, nw, ne_, ew, ee, noun_n, noun_e):
    if n > ne_:
        d.add("error", "too_dense", d.start_line, "%d %s; split the diagram (hard limit %d)" % (n, noun_n, ne_))
    elif n > nw:
        d.add("warn", "dense", d.start_line, "%d %s; consider splitting (soft limit %d)" % (n, noun_n, nw))
    if e > ee:
        d.add("error", "too_dense", d.start_line, "%d %s; split the diagram (hard limit %d)" % (e, noun_e, ee))
    elif e > ew:
        d.add("warn", "dense", d.start_line, "%d %s; consider splitting (soft limit %d)" % (e, noun_e, ew))


def seq_use(d, pid, lineno):
    if pid not in d.participants:
        d.participants[pid] = {"label": None, "line": lineno, "declared": False}
    d.used.add(pid)


def parse_sequence(lines, d):
    for lineno, raw in lines[1:]:
        low = raw.lower()
        if low.startswith(("autonumber", "title", "link ", "links ", "accdescr", "acctitle")):
            continue
        m = SEQ_DECL.match(raw)
        if m:
            pid = m.group("id")
            label = (m.group("label") or "").strip() or None
            if pid in d.participants and d.participants[pid]["declared"]:
                d.add("error", "duplicate_id", lineno, "participant '%s' is declared twice" % pid)
                if pid not in d.duplicate_ids:
                    d.duplicate_ids.append(pid)
            elif pid in d.participants:
                d.add("warn", "late_declaration", lineno, "participant '%s' is declared after it is first used" % pid)
            d.participants[pid] = {"label": label, "line": lineno, "declared": True}
            continue
        m = SEQ_NOTE.match(raw)
        if m:
            for who in m.group("who").split(","):
                if who.strip():
                    seq_use(d, who.strip(), lineno)
            continue
        m = re.match(r"^(activate|deactivate|destroy)\s+(\w+)\s*$", raw, re.I)
        if m:
            seq_use(d, m.group(2), lineno)
            if m.group(1).lower() == "activate":
                d.activations[m.group(2)] = d.activations.get(m.group(2), 0) + 1
            elif m.group(1).lower() == "deactivate":
                d.activations[m.group(2)] = d.activations.get(m.group(2), 0) - 1
            continue
        word = low.split(None, 1)[0] if low.split() else ""
        if word in SEQ_OPEN:
            d.block_stack.append((word, lineno))
            d.max_nesting = max(d.max_nesting, len(d.block_stack))
            continue
        if low == "end":
            if not d.block_stack:
                d.add("error", "unbalanced_end", lineno, "'end' with no open block")
            else:
                d.block_stack.pop()
            continue
        if word in SEQ_MID:
            if not d.block_stack:
                d.add("error", "stray_branch", lineno, "'%s' outside a block" % word)
            continue
        m = SEQ_MSG.match(raw)
        if m:
            a, b, act = m.group("a"), m.group("b"), m.group("act")
            seq_use(d, a, lineno)
            seq_use(d, b, lineno)
            d.messages += 1
            if act == "+":
                d.activations[b] = d.activations.get(b, 0) + 1
            elif act == "-":
                d.activations[a] = d.activations.get(a, 0) - 1
            text = m.group("text").strip()
            if not text:
                d.add("warn", "empty_message", lineno, "message %s to %s has no text" % (a, b))
            d.max_labels = max(d.max_labels, len(text))
            if len(text) > LABEL_WARN:
                d.add("warn", "long_label", lineno, "message text is %d characters; keep it under %d" % (len(text), LABEL_WARN))
            continue
        d.add("error", "syntax", lineno, "cannot read sequence line '%s'" % raw[:60])
    for kind, ln in d.block_stack:
        d.add("error", "unbalanced_block", ln, "'%s' block has no matching 'end'" % kind)
    declared = [p for p, v in d.participants.items() if v["declared"]]
    implicit = [p for p, v in d.participants.items() if not v["declared"]]
    if declared and implicit:
        d.add("warn", "undeclared_participant", d.participants[implicit[0]]["line"],
              "participant(s) %s are used without a declaration; declare all or none" % ", ".join(sorted(implicit)))
    msg_ends = set()
    for lineno, raw in lines[1:]:
        m = SEQ_MSG.match(raw)
        if m:
            msg_ends.add(m.group("a"))
            msg_ends.add(m.group("b"))
    d.orphans = sorted(p for p in d.participants if p not in msg_ends)
    for p in d.orphans:
        d.add("warn", "orphan_node", d.participants[p]["line"], "participant '%s' sends and receives no message" % p)
    for p, n in d.activations.items():
        if n != 0:
            d.add("warn", "unbalanced_activation", d.start_line, "participant '%s' has %d more %s than %s" % (p, abs(n), "activations" if n > 0 else "deactivations", "deactivations" if n > 0 else "activations"))
    labels = [v["label"] or p for p, v in d.participants.items()]
    by_label = {}
    for p, v in d.participants.items():
        by_label.setdefault((v["label"] or "").lower(), []).append(p)
    for label, group in by_label.items():
        if label and len(group) > 1:
            d.add("warn", "duplicate_label", d.participants[group[1]]["line"], "participants %s share the label '%s'" % (", ".join(sorted(group)), label))
            for p in group:
                if p not in d.duplicate_ids:
                    d.duplicate_ids.append(p)
    d.max_labels = max([d.max_labels] + [len(x) for x in labels])
    density(d, len(d.participants), d.messages, SEQ_PARTICIPANTS_WARN, SEQ_PARTICIPANTS_ERROR,
            SEQ_MESSAGES_WARN, SEQ_MESSAGES_ERROR, "participants", "messages")
    if d.max_nesting > NESTING_WARN:
        d.add("warn", "deep_nesting", d.start_line, "blocks nest %d deep; more than %d levels is hard to read" % (d.max_nesting, NESTING_WARN))
    if d.messages == 0:
        d.add("error", "empty_diagram", d.start_line, "sequence diagram has no messages")


def clean_lines(raw_lines, first_no):
    """Strip frontmatter, comments and blanks. Returns [(file_line_no, text)]."""
    out, i, n = [], 0, len(raw_lines)
    while i < n and not raw_lines[i].strip():
        i += 1
    if i < n and raw_lines[i].strip() == "---":
        j = i + 1
        while j < n and raw_lines[j].strip() != "---":
            j += 1
        i = j + 1
    for k in range(i, n):
        t = raw_lines[k].strip()
        if not t or t.startswith("%%"):
            continue
        out.append((first_no + k, t))
    return out


def check_diagram(index, first_no, raw_lines):
    d = Diagram(index, first_no)
    lines = clean_lines(raw_lines, first_no)
    if not lines:
        d.type = "empty"
        d.add("error", "empty_diagram", first_no, "no diagram text found")
        return d
    head = lines[0][1].split()[0]
    low = head.lower()
    if low in ("flowchart", "graph", "flowchart-elk"):
        d.type = "flowchart"
        d.start_line = lines[0][0]
        parse_flowchart(lines, d)
    elif low == "sequencediagram":
        d.type = "sequence"
        d.start_line = lines[0][0]
        parse_sequence(lines, d)
    else:
        d.type = head
        d.start_line = lines[0][0]
        hint = " For C4-style views use a flowchart with subgraphs." if low.startswith("c4") else ""
        d.add("warn", "unsupported_type", lines[0][0],
              "diagram type '%s' is not checked by this script (supported: flowchart, graph, sequenceDiagram).%s" % (head, hint))
    return d


def diagram_to_json(d):
    n = len(d.nodes) if d.type == "flowchart" else len(d.participants)
    e = len(d.edges) if d.type == "flowchart" else d.messages
    unl = None
    if d.type == "flowchart" and d.edges:
        unl = round(sum(1 for x in d.edges if not x[2]) / len(d.edges), 2)
    deg = getattr(d, "degree", {})
    errors = any(f["level"] == "error" for f in d.findings)
    warns = any(f["level"] == "warn" for f in d.findings)
    d.findings.sort(key=lambda f: (f["line"], f["code"]))
    return {
        "index": d.index, "start_line": d.start_line, "type": d.type, "direction": d.direction,
        "verdict": "fail" if errors else ("warn" if warns else "pass"),
        "metrics": {"nodes": n, "edges": e, "subgraphs": len(d.subgraphs), "max_nesting": d.max_nesting,
                    "max_degree": max(deg.values()) if deg else 0, "unlabeled_edge_ratio": unl,
                    "max_label_chars": d.max_labels},
        "orphans": getattr(d, "orphans", []), "duplicate_ids": sorted(d.duplicate_ids),
        "findings": d.findings,
    }


def extract_blocks(lines):
    """Return [(first_line_no, [lines])]. A file with no mermaid fence is one block."""
    blocks, cur, start = [], None, 0
    fenced = any(l.strip().startswith(("```mermaid", ":::mermaid")) for l in lines)
    if not fenced:
        return [(1, lines)]
    for i, l in enumerate(lines):
        t = l.strip()
        if cur is None and t.startswith(("```mermaid", ":::mermaid")):
            cur, start = [], i + 2
        elif cur is not None and t in ("```", ":::"):
            blocks.append((start, cur))
            cur = None
        elif cur is not None:
            cur.append(l)
    if cur is not None:
        blocks.append((start, cur))
    return blocks


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    strict = "--strict" in argv
    if len(args) != 1 or any(a.startswith("--") and a != "--strict" for a in argv):
        sys.stderr.write("usage: mermaid_check.py <file> [--strict]\n")
        return 2
    path = args[0]
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write("cannot read %s as UTF-8 text: %s\n" % (path, exc))
        return 2
    if not text.strip():
        sys.stderr.write("%s is empty; give it a Mermaid diagram\n" % path)
        return 2
    diagrams = [diagram_to_json(check_diagram(i + 1, start, blk)) for i, (start, blk) in enumerate(extract_blocks(text.splitlines()))]
    if not diagrams:
        sys.stderr.write("%s has a mermaid fence but no closed block\n" % path)
        return 2
    verdicts = [x["verdict"] for x in diagrams]
    verdict = "fail" if "fail" in verdicts else ("warn" if "warn" in verdicts else "pass")
    report = {"schema_version": SCHEMA_VERSION, "file": os.path.basename(path), "verdict": verdict,
              "diagrams": diagrams, "thresholds": THRESHOLDS}
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    return 1 if verdict == "fail" or (strict and verdict == "warn") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
