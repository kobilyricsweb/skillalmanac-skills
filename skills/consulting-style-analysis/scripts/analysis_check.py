#!/usr/bin/env python3
"""Validate an issue tree, hypotheses, evidence, summary and sections (one JSON file).

Usage:
    python analysis_check.py check <analysis.json>    validate; print one JSON report
    python analysis_check.py template                 print a skeleton input file

Reads only the file you name. Writes nothing. No network.
Exit codes: 0 no errors (warnings allowed), 1 at least one error, 2 usage or unreadable/invalid JSON.

Input shape (all keys required unless marked optional):
  answer      string, the governing answer to the question
  summary     string, executive summary, at most SUMMARY_MAX_WORDS words
  issue_tree  node; node = {id, text, universe?, covers?, children?}
                universe: tags naming everything this node splits into (required on a node with children)
                covers:   tags this child owns (required on every child; must be inside the parent's universe)
  hypotheses  list of {id, node, statement, falsifier, status}  status in open|supported|refuted|inconclusive
  evidence    list of {id, hypothesis, direction, claim, source, source_type, confidence}
                direction in supports|refutes; confidence a number from 0 to 1
  sections    list of {id, title, body, so_what, supports?}   supports: list of hypothesis ids (optional)
"""
import json
import re
import sys

# Executive summary limit; a one-screen summary a busy reader finishes in about a minute.
SUMMARY_MAX_WORDS = 150
# More than this many siblings is rarely MECE in practice and hard to read; warn only.
MAX_SIBLINGS = 7
# Deeper than this the tree is usually a list of tasks, not an issue tree; warn only.
MAX_DEPTH = 4
# A "so what" is one line. Longer than this it is a paragraph; warn only.
SO_WHAT_MAX_WORDS = 40
# A so-what shorter than this is usually a label, not an implication.
SO_WHAT_MIN_WORDS = 4
# Ceilings for how confident a row may claim to be given how it was sourced.
# Reason: an assumption or a rough estimate cannot honestly be called near-certain.
CONFIDENCE_CEILING = {
    "assumption": 0.4,
    "estimate": 0.7,
    "interview": 0.8,
    "published_study": 0.9,
    "filing": 0.95,
    "primary_data": 1.0,
}
STATUSES = {"open", "supported", "refuted", "inconclusive"}
DIRECTIONS = {"supports", "refutes"}

TEMPLATE = {
    "answer": "State the answer to the question in one sentence.",
    "summary": "Answer first. Then the two or three reasons. Then the recommended action. 150 words at most.",
    "issue_tree": {
        "id": "Q",
        "text": "The question as one sentence",
        "universe": ["revenue", "cost"],
        "children": [
            {"id": "A", "text": "Revenue", "covers": ["revenue"]},
            {"id": "B", "text": "Cost", "covers": ["cost"]},
        ],
    },
    "hypotheses": [
        {
            "id": "H1",
            "node": "A",
            "statement": "Revenue fell because of X",
            "falsifier": "If Y is true, this is wrong",
            "status": "open",
        }
    ],
    "evidence": [
        {
            "id": "E1",
            "hypothesis": "H1",
            "direction": "supports",
            "claim": "What the source says",
            "source": "Where it came from (document, page, date)",
            "source_type": "primary_data",
            "confidence": 0.8,
        }
    ],
    "sections": [
        {
            "id": "S1",
            "title": "Section title that states the point",
            "body": "Supporting text",
            "so_what": "What the reader should do or believe because of this",
            "supports": ["H1"],
        }
    ],
}


def words(text):
    return len(text.split()) if isinstance(text, str) else 0


def is_text(value):
    return isinstance(value, str) and value.strip() != ""


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, code, where, message):
        self.errors.append({"code": code, "where": where, "message": message})

    def warn(self, code, where, message):
        self.warnings.append({"code": code, "where": where, "message": message})


def walk_tree(node, rep, path, depth, ids, leaves):
    """Check one node and recurse. Appends node ids to `ids` and leaf ids to `leaves`."""
    if not isinstance(node, dict):
        rep.error("tree-node-invalid", path, "node must be an object")
        return
    nid = node.get("id")
    where = "tree:" + (str(nid) if nid else path)
    if not is_text(nid):
        rep.error("tree-id-missing", where, "node has no id")
    elif nid in ids:
        rep.error("tree-id-duplicate", where, "id '%s' is used twice" % nid)
    else:
        ids.add(nid)
    if not is_text(node.get("text")):
        rep.error("tree-text-missing", where, "node has no text")
    if depth > MAX_DEPTH:
        rep.warn("tree-too-deep", where, "depth %d exceeds %d; this is probably a task list" % (depth, MAX_DEPTH))
    children = node.get("children")
    if not children:
        if is_text(nid):
            leaves.append(nid)
        return
    if not isinstance(children, list):
        rep.error("tree-children-invalid", where, "children must be a list")
        return
    if len(children) == 1:
        rep.warn("tree-single-child", where, "one child is not a split; merge it or add the missing branch")
    if len(children) > MAX_SIBLINGS:
        rep.warn("tree-too-wide", where, "%d siblings; group them so no level has more than %d" % (len(children), MAX_SIBLINGS))
    universe = node.get("universe")
    if not isinstance(universe, list) or not universe or not all(is_text(t) for t in universe):
        rep.error("tree-universe-missing", where, "a node with children needs a non-empty 'universe' list of tags")
        universe = None
    owner = {}
    seen_text = {}
    for i, child in enumerate(children):
        if not isinstance(child, dict):
            rep.error("tree-node-invalid", "%s/children[%d]" % (where, i), "node must be an object")
            continue
        cid = child.get("id") or "%s/children[%d]" % (where, i)
        covers = child.get("covers")
        if not isinstance(covers, list) or not covers or not all(is_text(t) for t in covers):
            rep.error("tree-covers-missing", "tree:%s" % cid, "child needs a non-empty 'covers' list of tags")
            covers = []
        for tag in covers:
            if universe is not None and tag not in universe:
                rep.error("tree-tag-unknown", "tree:%s" % cid, "tag '%s' is not in the parent's universe" % tag)
            if tag in owner and owner[tag] != cid:
                rep.error(
                    "tree-overlap", where,
                    "tag '%s' is covered by both '%s' and '%s' (not mutually exclusive)" % (tag, owner[tag], cid),
                )
            else:
                owner[tag] = cid
        key = re.sub(r"\W+", " ", str(child.get("text", "")).lower()).strip()
        if key:
            if key in seen_text:
                rep.error("tree-duplicate-sibling", where, "'%s' and '%s' have the same text" % (seen_text[key], cid))
            else:
                seen_text[key] = cid
    if universe is not None:
        for tag in universe:
            if tag not in owner:
                rep.error("tree-gap", where, "tag '%s' is in the universe but no child covers it (not exhaustive)" % tag)
    for i, child in enumerate(children):
        walk_tree(child, rep, "%s/children[%d]" % (where, i), depth + 1, ids, leaves)


def check(data):
    rep = Report()
    if not isinstance(data, dict):
        rep.error("input-invalid", "file", "top level must be a JSON object")
        return rep, {}
    counts = {}

    if not is_text(data.get("answer")):
        rep.error("answer-missing", "answer", "no governing answer; the analysis must state the answer first")

    summary = data.get("summary")
    if not is_text(summary):
        rep.error("summary-missing", "summary", "no executive summary")
    else:
        n = words(summary)
        counts["summary_words"] = n
        if n > SUMMARY_MAX_WORDS:
            rep.error("summary-too-long", "summary", "%d words; limit is %d" % (n, SUMMARY_MAX_WORDS))

    ids, leaves = set(), []
    tree = data.get("issue_tree")
    if tree is None:
        rep.error("tree-missing", "issue_tree", "no issue tree")
    else:
        walk_tree(tree, rep, "issue_tree", 1, ids, leaves)
    counts["tree_nodes"] = len(ids)
    counts["tree_leaves"] = len(leaves)

    # Evidence rows
    evidence = data.get("evidence")
    if not isinstance(evidence, list):
        rep.error("evidence-missing", "evidence", "evidence must be a list")
        evidence = []
    hyps = data.get("hypotheses")
    if not isinstance(hyps, list):
        rep.error("hypotheses-missing", "hypotheses", "hypotheses must be a list")
        hyps = []
    hyp_ids = {}
    for h in hyps:
        if isinstance(h, dict) and is_text(h.get("id")):
            if h["id"] in hyp_ids:
                rep.error("hypothesis-id-duplicate", "hypothesis:" + h["id"], "id used twice")
            hyp_ids[h["id"]] = h
    counts["hypotheses"] = len(hyp_ids)
    counts["evidence"] = len(evidence)

    rows_for = {}
    seen_ev = set()
    for i, e in enumerate(evidence):
        if not isinstance(e, dict):
            rep.error("evidence-invalid", "evidence[%d]" % i, "row must be an object")
            continue
        eid = e.get("id")
        where = "evidence:" + (str(eid) if eid else "[%d]" % i)
        if not is_text(eid):
            rep.error("evidence-id-missing", where, "row has no id")
        elif eid in seen_ev:
            rep.error("evidence-id-duplicate", where, "id used twice")
        else:
            seen_ev.add(eid)
        if not is_text(e.get("claim")):
            rep.error("evidence-claim-missing", where, "row has no claim")
        if not is_text(e.get("source")):
            rep.error("evidence-no-source", where, "row has no source; an unsourced claim is not evidence")
        conf = e.get("confidence")
        if not is_number(conf) or not (0 <= conf <= 1):
            rep.error("evidence-confidence-range", where, "confidence must be a number from 0 to 1, got %r" % (conf,))
            conf = None
        stype = e.get("source_type")
        if stype not in CONFIDENCE_CEILING:
            rep.error(
                "evidence-source-type", where,
                "source_type must be one of %s" % ", ".join(sorted(CONFIDENCE_CEILING)),
            )
        elif conf is not None and conf > CONFIDENCE_CEILING[stype]:
            rep.warn(
                "evidence-confidence-high", where,
                "confidence %s is above the %s ceiling for source_type '%s'" % (conf, CONFIDENCE_CEILING[stype], stype),
            )
        if e.get("direction") not in DIRECTIONS:
            rep.error("evidence-direction", where, "direction must be 'supports' or 'refutes'")
        hid = e.get("hypothesis")
        if hid not in hyp_ids:
            rep.error("evidence-hypothesis-unknown", where, "hypothesis '%s' does not exist" % (hid,))
        else:
            rows_for.setdefault(hid, []).append(e)

    # Hypotheses
    covered_nodes = set()
    for hid, h in hyp_ids.items():
        where = "hypothesis:" + hid
        if not is_text(h.get("statement")):
            rep.error("hypothesis-statement-missing", where, "no statement")
        if not is_text(h.get("falsifier")):
            rep.error("hypothesis-no-falsifier", where, "state what result would prove it wrong")
        if h.get("status") not in STATUSES:
            rep.error("hypothesis-status", where, "status must be one of %s" % ", ".join(sorted(STATUSES)))
        node = h.get("node")
        if node not in ids:
            rep.error("hypothesis-node-unknown", where, "node '%s' is not in the issue tree" % (node,))
        else:
            covered_nodes.add(node)
        rows = rows_for.get(hid, [])
        if not rows:
            rep.error("hypothesis-no-evidence", where, "no evidence rows point at this hypothesis")
        else:
            dirs = {r.get("direction") for r in rows}
            if h.get("status") == "supported" and "supports" not in dirs:
                rep.error("hypothesis-status-unbacked", where, "status is supported but no row supports it")
            if h.get("status") == "refuted" and "refutes" not in dirs:
                rep.error("hypothesis-status-unbacked", where, "status is refuted but no row refutes it")
            if h.get("status") == "supported" and "refutes" in dirs:
                rep.warn("hypothesis-contested", where, "marked supported but also has refuting evidence; say why it still holds")
    for leaf in leaves:
        if leaf not in covered_nodes:
            rep.warn("leaf-no-hypothesis", "tree:" + leaf, "leaf has no hypothesis; test it or prune it")

    # Sections
    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        rep.error("sections-missing", "sections", "no sections")
        sections = []
    counts["sections"] = len(sections)
    reported = set()
    for i, s in enumerate(sections):
        if not isinstance(s, dict):
            rep.error("section-invalid", "sections[%d]" % i, "section must be an object")
            continue
        sid = s.get("id")
        where = "section:" + (str(sid) if sid else "[%d]" % i)
        if not is_text(s.get("title")):
            rep.error("section-title-missing", where, "no title")
        if not is_text(s.get("body")):
            rep.warn("section-body-empty", where, "no body text")
        sw = s.get("so_what")
        if not is_text(sw):
            rep.error("section-no-so-what", where, "no so_what line")
        else:
            n = words(sw)
            if n < SO_WHAT_MIN_WORDS:
                rep.error("section-so-what-thin", where, "so_what is %d words; state the implication, not a label" % n)
            elif n > SO_WHAT_MAX_WORDS:
                rep.warn("section-so-what-long", where, "so_what is %d words; keep it to one line" % n)
            if is_text(s.get("title")) and sw.strip().lower() == s["title"].strip().lower():
                rep.error("section-so-what-restates-title", where, "so_what repeats the title")
        for ref in s.get("supports") or []:
            if ref not in hyp_ids:
                rep.error("section-supports-unknown", where, "supports unknown hypothesis '%s'" % ref)
            else:
                reported.add(ref)
    for hid in hyp_ids:
        if hid not in reported:
            rep.warn("hypothesis-not-reported", "hypothesis:" + hid, "no section lists it under 'supports'")
    return rep, counts


def cmd_check(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except OSError as exc:
        sys.stderr.write("cannot read %s: %s\n" % (path, exc))
        return 2
    if not raw.strip():
        sys.stderr.write("%s is empty; run 'template' for a skeleton\n" % path)
        return 2
    try:
        data = json.loads(raw)
    except ValueError as exc:
        sys.stderr.write("%s is not valid JSON: %s\n" % (path, exc))
        return 2
    rep, counts = check(data)
    out = {
        "ok": not rep.errors,
        "error_count": len(rep.errors),
        "warning_count": len(rep.warnings),
        "counts": counts,
        "errors": rep.errors,
        "warnings": rep.warnings,
    }
    sys.stdout.write(json.dumps(out, indent=2, ensure_ascii=True) + "\n")
    return 1 if rep.errors else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 2 and argv[0] == "check":
        return cmd_check(argv[1])
    if len(argv) == 1 and argv[0] == "template":
        sys.stdout.write(json.dumps(TEMPLATE, indent=2, ensure_ascii=True) + "\n")
        return 0
    sys.stderr.write("usage: analysis_check.py check <analysis.json> | template\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
