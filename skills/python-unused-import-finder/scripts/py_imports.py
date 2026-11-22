"""py_imports: report unused, duplicate, star and shadowed imports in Python files.

Usage:
    python -I py_imports.py <file.py> [<file.py> ...]

Each file is parsed with ast.parse. The code is never executed. The script
reads the inputs only and writes nothing.

Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
Findings go to stdout as one JSON object. Errors go to stderr as one line of JSON.
"""
import ast
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
NOQA_RE = re.compile(r"#\s*noqa(?::\s*([A-Za-z0-9_,\s]+))?", re.IGNORECASE)
CODE_RE = re.compile(r"[A-Z]+[0-9]+")
NOQA_CODE = {
    "UNUSED_IMPORT": "F401",
    "DUPLICATE_IMPORT": "F811",
    "SHADOWED_IMPORT": "F811",
    "STAR_IMPORT": "F403",
}
SCOPE_TYPES = (
    ast.Module,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)
DEF_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def fail(message):
    sys.stderr.write(json.dumps({"error": message, "exit": 2}) + "\n")
    sys.exit(2)


def read_source(path):
    if not path.lower().endswith(".py"):
        fail("not a .py file: " + path)
    if not os.path.isfile(path):
        fail("file not found: " + path)
    try:
        size = os.path.getsize(path)
        if size > MAX_BYTES:
            fail("file exceeds 2 MB cap: " + path)
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("file unreadable: " + path)
    if len(raw) > MAX_BYTES:
        fail("file exceeds 2 MB cap: " + path)
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("file is not valid UTF-8: " + path)


def noqa_hit(lines, start, end, code):
    """True when a noqa comment on lines start..end suppresses the code."""
    for number in range(start, end + 1):
        if 1 <= number <= len(lines):
            match = NOQA_RE.search(lines[number - 1])
            if match:
                codes = match.group(1)
                if codes is None:
                    return True
                if code in CODE_RE.findall(codes.upper()):
                    return True
    return False


def analyze(path, text):
    """Return (findings, suppressed_count) for one parsed file."""
    lines = text.split("\n")
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        fail("syntax error in %s at line %s" % (path, exc.lineno))
    except ValueError as exc:
        fail("cannot parse %s: %s" % (path, exc))

    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def scope_of(node):
        current = parents.get(node)
        while current is not None and not isinstance(current, SCOPE_TYPES):
            current = parents.get(current)
        return id(current)

    imports = []
    star_imports = []
    loads = {}
    rebinds = {}
    all_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                loads.setdefault(node.id, []).append(node.lineno)
            elif isinstance(node.ctx, ast.Store):
                rebinds.setdefault((scope_of(node), node.id), []).append(("other", node.lineno))
        elif isinstance(node, DEF_TYPES):
            rebinds.setdefault((scope_of(node), node.name), []).append(("other", node.lineno))
        elif isinstance(node, ast.ExceptHandler) and node.name:
            rebinds.setdefault((scope_of(node), node.name), []).append(("other", node.lineno))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                continue
            module_part = ("." * (node.level or 0)) + (node.module or "") if isinstance(node, ast.ImportFrom) else ""
            for alias in node.names:
                if isinstance(node, ast.ImportFrom) and alias.name == "*":
                    star_imports.append({
                        "line": node.lineno,
                        "end_line": node.end_lineno,
                        "module": "from %s import *" % module_part,
                    })
                    continue
                if isinstance(node, ast.Import):
                    bound = alias.asname or alias.name.split(".")[0]
                    target = "import " + alias.name
                else:
                    bound = alias.asname or alias.name
                    target = "from %s import %s" % (module_part, alias.name)
                imports.append({
                    "name": bound,
                    "module": target,
                    "line": node.lineno,
                    "end_line": node.end_lineno,
                    "scope": scope_of(node),
                    "col": node.col_offset,
                })
        elif isinstance(node, ast.Assign):
            if parents.get(node) is tree:
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        for element in node.value.elts:
                            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                                all_names.add(element.value)

    # Duplicate detection: the first occurrence of (scope, module, name) is kept.
    imports.sort(key=lambda item: (item["line"], item["col"]))
    first_seen = {}
    for imp in imports:
        key = (imp["scope"], imp["module"], imp["name"])
        if key in first_seen:
            imp["dup_of"] = first_seen[key]
        else:
            first_seen[key] = imp["line"]
            rebinds.setdefault((imp["scope"], imp["name"]), []).append(("import", imp["line"]))

    findings = []
    suppressed = 0

    def add(line, end_line, code, name, module, detail):
        nonlocal suppressed
        if noqa_hit(lines, line, end_line, NOQA_CODE[code]):
            suppressed += 1
            return
        findings.append({
            "file": path,
            "line": line,
            "code": code,
            "name": name,
            "module": module,
            "detail": detail,
        })

    for star in star_imports:
        add(star["line"], star["end_line"], "STAR_IMPORT", "*", star["module"],
            "names cannot be checked; import the names explicitly")

    for imp in imports:
        if "dup_of" in imp:
            add(imp["line"], imp["end_line"], "DUPLICATE_IMPORT", imp["name"], imp["module"],
                "same import already at line %d" % imp["dup_of"])
            continue
        later = [ln for kind, ln in rebinds.get((imp["scope"], imp["name"]), []) if ln > imp["line"]]
        if later:
            rebound_at = min(later)
            used_between = any(imp["line"] < ln < rebound_at for ln in loads.get(imp["name"], []))
            if not used_between:
                add(imp["line"], imp["end_line"], "SHADOWED_IMPORT", imp["name"], imp["module"],
                    "rebound at line %d before any use" % rebound_at)
            continue
        if imp["name"] in loads or imp["name"] in all_names:
            continue
        add(imp["line"], imp["end_line"], "UNUSED_IMPORT", imp["name"], imp["module"],
            "name never referenced")

    return findings, suppressed


def main(argv):
    if len(argv) < 2:
        fail("usage: py_imports.py <file.py> [<file.py> ...]")
    findings = []
    suppressed = 0
    for path in argv[1:]:
        found, quiet = analyze(path, read_source(path))
        findings.extend(found)
        suppressed += quiet
    findings.sort(key=lambda item: (item["file"], item["line"], item["code"], item["name"]))
    report = {
        "tool": "py_imports",
        "files_checked": len(argv) - 1,
        "finding_count": len(findings),
        "suppressed_by_noqa": suppressed,
        "findings": findings,
    }
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
