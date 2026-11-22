"""Draw a Mermaid graph of Terraform resources and data sources and their references.

Regex based, not a full HCL parser. Reads one .tf file, or every *.tf file directly
inside one directory (not recursive), finds resource and data blocks, finds
references of the form type.name or data.type.name inside block bodies, and prints
a Mermaid "graph LR" diagram to stdout. Findings are written as Mermaid comment
lines (%%) directly under the first line, so the stdout stays valid Mermaid.

Usage:
  python -I tf_graph.py <input-file-or-dir> [--out <output-file>]

--out writes the same text to a NEW file. It refuses (exit 2) when the file already
exists, when the path is one of the inputs, or when the path is a .tf file inside
the input directory.

Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
Errors are one line of JSON on stderr, for example {"error": "invalid_utf8"}.
Stdout is Mermaid text only. No network, no subprocess, read-only on inputs.
"""
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_NODES = 150

HEADER_RE = re.compile(
    r'^[ \t]*(resource|data)[ \t]+"([A-Za-z0-9_\-]+)"[ \t]+"([A-Za-z0-9_\-]+)"[ \t]*\{',
    re.M,
)
# Reference: optional data. prefix, provider type with at least one underscore,
# then resource name. Bare words such as var, local, module, each, count are skipped
# because they have no underscore in their first segment.
REF_RE = re.compile(
    r"(?<![A-Za-z0-9_.\-])(data\.)?([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\.([A-Za-z_][A-Za-z0-9_\-]*)"
)


def fail(code):
    sys.stderr.write(json.dumps({"error": code}) + "\n")
    sys.exit(2)


def parse_args(argv):
    args = argv[1:]
    if not args or len(args) > 3 or args[0].startswith("--"):
        fail("usage")
    if len(args) == 2:
        fail("usage")
    out = None
    if len(args) == 3:
        if args[1] != "--out":
            fail("usage")
        out = args[2]
    return args[0], out


def collect_inputs(path):
    if os.path.isdir(path):
        names = sorted(
            n for n in os.listdir(path)
            if n.endswith(".tf") and os.path.isfile(os.path.join(path, n))
        )
        files = [os.path.join(path, n) for n in names]
    elif os.path.isfile(path):
        if not path.endswith(".tf"):
            fail("not_tf_file")
        files = [path]
    else:
        fail("input_missing")
    if not files:
        fail("no_tf_files")
    return files


def read_inputs(files):
    total = 0
    parts = []
    for f in files:
        try:
            total += os.path.getsize(f)
            if total > MAX_BYTES:
                fail("input_too_large")
            with open(f, "rb") as fh:
                raw = fh.read(MAX_BYTES + 1)
        except OSError:
            fail("unreadable")
        try:
            parts.append(raw.decode("utf-8-sig"))
        except UnicodeDecodeError:
            fail("invalid_utf8")
    return "\n".join(parts)


def strip_comments(src):
    """Blank out #, // and /* */ comments, keeping newlines. Strings are kept intact."""
    out = []
    i = 0
    n = len(src)
    in_str = False
    while i < n:
        c = src[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == '"' or c == "\n":
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "#" or (c == "/" and i + 1 < n and src[i + 1] == "/"):
            while i < n and src[i] != "\n":
                out.append(" ")
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            end = src.find("*/", i + 2)
            end = n - 2 if end < 0 else end
            for ch in src[i:end + 2]:
                out.append("\n" if ch == "\n" else " ")
            i = end + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def match_brace(text, open_idx):
    depth = 0
    for j in range(open_idx, len(text)):
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return j
    return -1


def find_cycles(order, adj, findings):
    color = {k: 0 for k in order}
    for start in order:
        if color[start]:
            continue
        color[start] = 1
        stack = [(start, iter(adj[start]))]
        path = [start]
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                color[node] = 2
                stack.pop()
                path.pop()
                continue
            if color[nxt] == 0:
                color[nxt] = 1
                stack.append((nxt, iter(adj[nxt])))
                path.append(nxt)
            elif color[nxt] == 1:
                i = path.index(nxt)
                findings.append(("C001", "cycle " + " -> ".join(path[i:] + [nxt])))


def build(text):
    bodies = {}
    order = []
    findings = []
    for m in HEADER_RE.finditer(text):
        kind, rtype, name = m.group(1), m.group(2), m.group(3)
        key = ("data." if kind == "data" else "") + rtype + "." + name
        open_idx = m.end() - 1
        close = match_brace(text, open_idx)
        if close < 0:
            fail("unbalanced_braces")
        if key in bodies:
            findings.append(("D001", "duplicate declaration " + key + " (second block ignored)"))
            continue
        bodies[key] = text[open_idx + 1:close]
        order.append(key)

    if not order:
        findings.append(("N001", "no resource or data blocks found"))
        return [], [], [], findings

    shown_keys = order[:MAX_NODES]
    shown = set(shown_keys)
    if len(order) > MAX_NODES:
        findings.append(("L001", "node cap reached: rendered %d of %d nodes" % (MAX_NODES, len(order))))

    edges = []
    unresolved = []  # (owner, key) pairs, source order
    adj = {k: [] for k in order}
    for owner in order:
        seen = set()
        for m in REF_RE.finditer(bodies[owner]):
            key = ("data." if m.group(1) else "") + m.group(2) + "." + m.group(3)
            if key in seen:
                continue
            seen.add(key)
            if key in bodies:
                adj[owner].append(key)
                if owner in shown and key in shown:
                    edges.append((owner, key))
            else:
                unresolved.append((owner, key))
                findings.append(("U001", "unresolved reference " + key + " in " + owner))

    find_cycles(order, adj, findings)
    return shown_keys, edges, unresolved, findings


def render(shown_keys, edges, unresolved, findings):
    shown = set(shown_keys)
    lines = ["graph LR"]
    for code, detail in findings:
        lines.append("%% " + code + " " + detail)
    ids = {}
    for idx, key in enumerate(shown_keys):
        ids[key] = "n%d" % idx
        lines.append('  n%d["%s"]' % (idx, key))
    uids = {}
    for owner, key in unresolved:
        if key not in uids:
            uids[key] = "u%d" % len(uids)
            lines.append('  %s["%s (unresolved)"]' % (uids[key], key))
    for src, dst in edges:
        lines.append("  %s --> %s" % (ids[src], ids[dst]))
    for owner, key in unresolved:
        if owner in shown:
            lines.append("  %s -.-> %s" % (ids[owner], uids[key]))
    return "\n".join(lines) + "\n"


def main(argv):
    inp, out_path = parse_args(argv)
    files = collect_inputs(inp)
    text = strip_comments(read_inputs(files))
    shown_keys, edges, unresolved, findings = build(text)
    out_text = render(shown_keys, edges, unresolved, findings)

    if out_path is not None:
        ap = os.path.abspath(out_path)
        for f in files:
            if os.path.abspath(f) == ap:
                fail("output_is_input")
        if os.path.isdir(inp) and os.path.dirname(ap) == os.path.abspath(inp) and ap.endswith(".tf"):
            fail("output_is_input")
        if not os.path.isdir(os.path.dirname(ap)):
            fail("output_dir_missing")
        try:
            with open(ap, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(out_text)
        except FileExistsError:
            fail("output_exists")
        except OSError:
            fail("output_error")

    sys.stdout.write(out_text)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
