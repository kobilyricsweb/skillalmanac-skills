"""Heuristic syntax checker for Mermaid diagram blocks.

Reads one Markdown file (fenced blocks opened by a line that starts with
three backticks followed by the word mermaid are extracted) or one .mmd file
(the whole file is one block). Applies line-level heuristics: known header,
quote balance, bracket balance, subgraph/end balance, arrows without a
target, duplicate node ids with different labels, and unquoted special
characters in flowchart labels.

This is a heuristic. It is not the official Mermaid parser and it renders
nothing. A clean result does not prove that a diagram renders.

Usage:
    python -I scripts/mermaid_check.py <path.md|path.markdown|path.mmd>

Output: one JSON object on stdout. On bad input, one line of JSON with an
"error" key on stdout.
Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
The script writes no files and reads only the path it is given.
"""

import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 64

HEADERS = {
    "flowchart", "flowchart-elk", "graph", "sequenceDiagram", "classDiagram",
    "classDiagram-v2", "stateDiagram", "stateDiagram-v2", "erDiagram", "gantt",
    "pie", "journey", "mindmap", "timeline", "gitGraph", "quadrantChart",
    "requirementDiagram", "C4Context", "C4Container", "C4Component",
    "C4Dynamic", "C4Deployment", "sankey-beta", "xychart-beta", "block-beta",
    "packet-beta", "architecture-beta", "kanban", "zenuml", "info",
    "radar-beta", "treemap-beta",
}
ARROW_HEADERS = {
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "classDiagram-v2",
    "stateDiagram", "stateDiagram-v2",
}
NODE_HEADERS = {"flowchart", "flowchart-elk", "graph"}
CURLY_MULTILINE_HEADERS = {
    "classDiagram", "classDiagram-v2", "stateDiagram", "stateDiagram-v2", "erDiagram",
}
RESERVED = {
    "subgraph", "end", "style", "classDef", "class", "linkStyle", "click", "direction",
}
SPECIAL = set('()[]{}|;#&<>"')
OPEN_FOR = {")": "(", "]": "[", "}": "{"}

QUOTED = re.compile(r'"[^"]*"')
ARROW_END = re.compile(
    r'(?:<?-{2,}>?|<?={2,}>?|-\.+->?|-->>|->>|->|-\)|--[ox])\s*(?:\|[^|]*\|)?\s*$'
)
NODE = re.compile(
    r'([A-Za-z_][A-Za-z0-9_]*)\s*(?:'
    r'\[\[(.*?)\]\]|\[\((.*?)\)\]|\(\[(.*?)\]\)|\(\((.*?)\)\)|'
    r'\{\{(.*?)\}\}|\[(.*?)\]|\((.*?)\)|\{(.*?)\}|>(.*?)\]'
    r')'
)


def fail(message):
    sys.stdout.write(json.dumps({"error": message}) + "\n")
    return 2


def is_comment(text):
    return text.strip().startswith("%%")


def extract_fences(lines):
    """Return mermaid fenced blocks from Markdown lines."""
    blocks = []
    current = None
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if current is None:
            if stripped.startswith("```mermaid"):
                current = {"block": len(blocks) + 1, "fence_line": number,
                           "lines": [], "closed": False}
        elif stripped == "```":
            current["closed"] = True
            blocks.append(current)
            current = None
        else:
            current["lines"].append((number, line))
    if current is not None:
        blocks.append(current)
    return blocks


def bracket_problem(bare, kind):
    """Return a message for the first bracket problem on a line, else None."""
    stack = []
    for ch in bare:
        if kind in CURLY_MULTILINE_HEADERS and ch in "{}":
            continue
        if ch in "([{":
            stack.append(ch)
            if len(stack) > MAX_DEPTH:
                return "nesting deeper than %d" % MAX_DEPTH
        elif ch in ")]}":
            if not stack or stack[-1] != OPEN_FOR[ch]:
                return "unexpected '%s'" % ch
            stack.pop()
    if stack:
        return "unclosed '%s'" % stack[-1]
    return None


def check_block(bno, items):
    """Return finding dicts for one block given (line_no, text) pairs."""
    out = []

    def add(line, code, message):
        out.append({"block": bno, "line": line, "code": code, "message": message})

    body = [(ln, tx) for ln, tx in items if tx.strip() and not is_comment(tx)]
    if body and body[0][1].strip() == "---":
        close = next((i for i in range(1, len(body)) if body[i][1].strip() == "---"), None)
        if close is None:
            add(body[0][0], "FRONT_MATTER_NOT_CLOSED",
                "front matter opened with --- has no closing ---")
            return out
        body = body[close + 1:]

    if not body:
        add(items[0][0] if items else 1, "EMPTY_BLOCK", "block has no content")
        return out

    head_line, head_text = body[0]
    head_token = head_text.split()[0]
    if head_token in HEADERS:
        kind = head_token
    else:
        kind = None
        add(head_line, "UNKNOWN_HEADER",
            "first token '%s' is not a supported header (%s)"
            % (head_token, ", ".join(sorted(HEADERS))))

    seen = {}
    sub_stack = []
    for ln, raw in body:
        tx = raw.rstrip()
        words = tx.split()
        if tx.count('"') % 2:
            add(ln, "UNBALANCED_QUOTE", "odd number of double quotes on this line")
        bare = QUOTED.sub('""', tx)
        problem = bracket_problem(bare, kind)
        if problem:
            add(ln, "UNBALANCED_BRACKET", problem)
        if kind in ARROW_HEADERS and ARROW_END.search(bare):
            add(ln, "ARROW_NO_TARGET", "line ends with an arrow and no target")
        if kind in ("flowchart", "graph"):
            if words[0] == "subgraph":
                sub_stack.append(ln)
            elif tx.strip() == "end":
                if sub_stack:
                    sub_stack.pop()
                else:
                    add(ln, "END_WITHOUT_SUBGRAPH", "'end' has no open subgraph")
        if kind in NODE_HEADERS and words[0] not in RESERVED:
            for m in NODE.finditer(raw):
                nid = m.group(1)
                label = next((g for g in m.groups()[1:] if g is not None), "")
                if label and not label.startswith('"'):
                    bad = sorted(set(c for c in label if c in SPECIAL))
                    if bad:
                        add(ln, "LABEL_SPECIAL_CHARS",
                            "unquoted label of %s contains %s; wrap the label in double quotes"
                            % (nid, " ".join(bad)))
                prev = seen.get(nid)
                if prev is None:
                    seen[nid] = (label, ln)
                elif prev[0] != label:
                    add(ln, "DUPLICATE_NODE_ID",
                        "node %s redefined with a different label (first at line %d)"
                        % (nid, prev[1]))
    for ln in sub_stack:
        add(ln, "SUBGRAPH_NOT_CLOSED", "subgraph has no matching 'end'")
    return out


def main(argv):
    if len(argv) != 2:
        return fail("usage: mermaid_check.py <path.md|path.markdown|path.mmd>")
    path = argv[1]
    if not os.path.isfile(path):
        return fail("input file not found")
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".md", ".markdown", ".mmd"):
        return fail("input must end in .md, .markdown or .mmd")
    if os.path.getsize(path) > MAX_BYTES:
        return fail("input exceeds 2 MB limit")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_BYTES + 1)
    except OSError:
        return fail("cannot read input file")
    if len(raw) > MAX_BYTES:
        return fail("input exceeds 2 MB limit")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return fail("input is not valid UTF-8")

    lines = text.splitlines()
    if ext == ".mmd":
        blocks = [{"block": 1, "fence_line": 1,
                   "lines": list(enumerate(lines, 1)), "closed": True}]
    else:
        blocks = extract_fences(lines)
        if not blocks:
            return fail("no mermaid fenced blocks found in file")

    findings = []
    for block in blocks:
        findings.extend(check_block(block["block"], block["lines"]))
        if not block["closed"]:
            findings.append({"block": block["block"], "line": block["fence_line"],
                             "code": "UNCLOSED_FENCE",
                             "message": "mermaid fence has no closing line of three backticks"})

    result = {
        "file": path,
        "mode": "heuristic",
        "blocks": len(blocks),
        "finding_count": len(findings),
        "findings": findings,
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
