"""token_lint: check a design-token JSON file for naming, duplicates and references.

Usage:
    python -I scripts/token_lint.py <tokens.json>

The input may use nested objects (color -> brand -> 500 -> value) or flat
objects with dotted keys. A leaf is a string or number, or an object whose
"value" key holds a string or number. Output is one JSON report on stdout.

Read-only: the input file is opened once and no file is written.
Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
"""
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 8
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*$")
HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
REF_RE = re.compile(r"\{([^{}\s]+)\}")
SEMANTIC_PREFIXES = ("semantic.", "alias.")


def fail(message):
    sys.stdout.write(json.dumps({"error": message, "exit": 2}) + "\n")
    sys.exit(2)


def is_scalar(value):
    return isinstance(value, (str, int, float)) and not isinstance(value, bool)


def finding(code, token, detail):
    return {"code": code, "token": token, "detail": detail}


def load(path):
    if not os.path.isfile(path):
        fail("file not found")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("cannot read file")
    if len(raw) > MAX_BYTES:
        fail("input larger than 2097152 bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")
    try:
        data = json.loads(text)
    except (ValueError, RecursionError, MemoryError):
        fail("input is not valid JSON or is nested too deeply")
    return data


def depth_of(root):
    deepest = 0
    stack = [(root, 1)]
    while stack:
        node, level = stack.pop()
        if isinstance(node, dict):
            deepest = max(deepest, level)
            stack.extend((child, level + 1) for child in node.values())
    return deepest


def collect(node, prefix, tokens, findings):
    for key in sorted(node):
        child = node[key]
        name = prefix + "." + key if prefix else key
        if isinstance(child, dict) and "value" in child and is_scalar(child["value"]):
            child = child["value"]
        if isinstance(child, dict):
            collect(child, name, tokens, findings)
        elif is_scalar(child):
            if name in tokens:
                findings.append(finding("DUPLICATE_NAME", name, "name is defined more than once"))
            else:
                tokens[name] = str(child)
        else:
            fail("unsupported value at " + name + ": only strings, numbers and objects are allowed")


def find_cycles(tokens):
    graph = {}
    for name, value in tokens.items():
        graph[name] = [t for t in REF_RE.findall(value) if t in tokens]
    state = {}
    seen = set()
    found = []
    for start in sorted(graph):
        if state.get(start):
            continue
        state[start] = 1
        path = [start]
        stack = [(start, iter(sorted(graph[start])))]
        while stack:
            node, children = stack[-1]
            nxt = next(children, None)
            if nxt is None:
                state[node] = 2
                path.pop()
                stack.pop()
            elif state.get(nxt) == 1:
                cycle = path[path.index(nxt):]
                key = tuple(sorted(cycle))
                if key not in seen:
                    seen.add(key)
                    detail = "cycle: " + " -> ".join(cycle + [nxt])
                    found.append(finding("CIRCULAR_REFERENCE", min(cycle), detail))
            elif not state.get(nxt):
                state[nxt] = 1
                path.append(nxt)
                stack.append((nxt, iter(sorted(graph[nxt]))))
    return found


def check(tokens):
    findings = []
    for name in sorted(tokens):
        value = tokens[name]
        if not NAME_RE.match(name):
            findings.append(finding("NAME_PATTERN", name, "name must be lowercase kebab-case segments joined by dots"))
        if name.startswith(SEMANTIC_PREFIXES) and HEX_RE.match(value.strip()):
            detail = "semantic or alias token holds a raw hex value " + value.strip()
            findings.append(finding("RAW_HEX_IN_SEMANTIC", name, detail))
        for target in REF_RE.findall(value):
            if target not in tokens:
                findings.append(finding("DANGLING_REFERENCE", name, "references missing token " + target))
    groups = {}
    for name in sorted(tokens):
        value = tokens[name]
        if REF_RE.search(value):
            continue
        groups.setdefault(value.strip().lower(), []).append(name)
    for value, names in sorted(groups.items()):
        if len(names) > 1:
            findings.append(finding("DUPLICATE_VALUE", names[0], "raw value " + value + " is used by " + ", ".join(names)))
    findings.extend(find_cycles(tokens))
    return findings


def main(argv):
    if len(argv) != 2:
        fail("usage: python -I scripts/token_lint.py <tokens.json>")
    path = argv[1]
    data = load(path)
    if not isinstance(data, dict):
        fail("root must be a JSON object")
    if depth_of(data) > MAX_DEPTH:
        fail("nesting deeper than 8 object levels")
    tokens = {}
    findings = []
    collect(data, "", tokens, findings)
    findings.extend(check(tokens))
    findings.sort(key=lambda item: (item["code"], item["token"], item["detail"]))
    summary = {}
    for item in findings:
        summary[item["code"]] = summary.get(item["code"], 0) + 1
    report = {
        "tool": "token_lint",
        "file": os.path.basename(path),
        "token_count": len(tokens),
        "finding_count": len(findings),
        "summary": dict(sorted(summary.items())),
        "findings": findings,
    }
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
