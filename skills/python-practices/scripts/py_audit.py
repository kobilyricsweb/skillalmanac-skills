#!/usr/bin/env python3
"""Audit Python source for a fixed list of anti-patterns, using ast only.

Usage:
    python py_audit.py <file-or-folder> [<file-or-folder> ...]
    python py_audit.py --rules            # print the rule list as JSON

Reads the given .py files (folders are walked; virtualenv, VCS, build and
cache folders are skipped). Writes nothing and runs none of the code it reads.
Prints one JSON object to stdout, nothing else.

Rules (id: what it flags):
    bare-except        `except:` with no exception type
    mutable-default    a list, dict or set literal or call (list(), dict(),
                       set(), defaultdict(), deque()) as a parameter default
    print-in-library   print() in a file that is not a script (no main guard,
                       not __main__.py, not test_*.py / *_test.py / conftest.py)
    os-path            os.path.<anything> or `from os.path import ...`
    missing-main-guard module-level code that runs on import (a bare call
                       statement, or a function named main that is never
                       guarded) in a file with no `if __name__ == "__main__"`
    unused-import      an imported name never used in the module
                       (skipped in __init__.py, `from __future__`, and names
                       listed in __all__)

A finding is suppressed by a comment on its line: `# noqa` (any rule) or
`# audit: ignore <rule-id>`.

Output contract (strict JSON, UTF-8):
    {"tool": "py_audit", "version": 1, "files_scanned": int,
     "findings": [{"file", "line", "col", "rule", "message"}, ...],
     "counts": {rule: int}, "errors": [{"file", "error"}, ...],
     "verdict": "clean" | "findings" | "incomplete"}
Findings are sorted by file, line, column.

Exit codes: 0 clean, 1 findings (or unreadable/unparsable files),
2 usage error or no Python file found.
"""
import ast
import json
import re
import sys
from pathlib import Path

VERSION = 1
MAX_BYTES = 1_000_000  # larger files are almost always generated; skip and report
SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
             "site-packages", "build", "dist", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
RULES = {
    "bare-except": "except: with no exception type also catches KeyboardInterrupt and SystemExit",
    "mutable-default": "a mutable default argument is created once and shared across calls",
    "print-in-library": "print() in importable code cannot be filtered, redirected or levelled; use logging",
    "os-path": "os.path string handling; pathlib.Path covers it",
    "missing-main-guard": "code that runs at import time; wrap the entry point in if __name__ == '__main__'",
    "unused-import": "imported name is never used",
}
MUTABLE_CALLS = {"list", "dict", "set", "defaultdict", "deque", "bytearray", "Counter", "OrderedDict"}
SUPPRESS = re.compile(r"#\s*(noqa\b|audit:\s*ignore\s+([a-z-]+))")


def is_test_or_entry(path):
    base = Path(path).name
    return base == "__main__.py" or base == "conftest.py" or base.startswith("test_") or base.endswith("_test.py")


def has_main_guard(tree):
    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            t = node.test
            names = [t.left] + list(t.comparators)
            has_name = any(isinstance(n, ast.Name) and n.id == "__name__" for n in names)
            has_main = any(isinstance(n, ast.Constant) and n.value == "__main__" for n in names)
            if has_name and has_main:
                return True
    return False


def default_is_mutable(node):
    if isinstance(node, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)):
        return True
    if isinstance(node, ast.Call):
        f = node.func
        name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
        return name in MUTABLE_CALLS
    return False


def annotation_strings(tree):
    """Identifiers inside string annotations, so 'Foo' in -> "Foo" counts as a use."""
    found = set()

    def grab(node):
        if node is None:
            return
        for sub in ast.walk(node):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                found.update(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", sub.value))

    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            grab(node.annotation)
        elif isinstance(node, ast.AnnAssign):
            grab(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            grab(node.returns)
    return found


def dunder_all(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                names.update(e.value for e in node.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str))
    return names


def audit_tree(tree, path):
    out = []

    def add(node, rule, msg):
        out.append((node.lineno, node.col_offset + 1, rule, msg))

    base = Path(path).name
    guard = has_main_guard(tree)
    library = not guard and not is_test_or_entry(path)

    # imports and name usage
    imported = []  # (bound name, node, description)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "os.path":
                    add(node, "os-path", "import os.path; use pathlib.Path")
                bound = a.asname or a.name.split(".")[0]
                imported.append((bound, node, a.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            if node.module == "os.path" or (node.module == "os" and any(a.name == "path" for a in node.names)):
                add(node, "os-path", "import of os.path; use pathlib.Path")
            for a in node.names:
                if a.name == "*":
                    continue
                imported.append((a.asname or a.name, node, f"{node.module or '.'}.{a.name}"))

    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used |= annotation_strings(tree)
    used |= dunder_all(tree)
    if base != "__init__.py":
        for bound, node, desc in imported:
            if bound not in used:
                add(node, "unused-import", f"'{desc}' imported as '{bound}' but never used")

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            add(node, "bare-except", "bare except: catches KeyboardInterrupt and SystemExit; name the exception")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            for d in list(a.defaults) + [k for k in a.kw_defaults if k is not None]:
                if default_is_mutable(d):
                    add(d, "mutable-default", "mutable default argument is shared across calls; use None and create inside")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print" and library:
            add(node, "print-in-library", "print() in library code; use logging.getLogger(__name__)")
        elif isinstance(node, ast.Attribute) and node.attr and isinstance(node.value, ast.Attribute):
            v = node.value
            if v.attr == "path" and isinstance(v.value, ast.Name) and v.value.id == "os":
                add(node, "os-path", f"os.path.{node.attr}; use pathlib.Path")

    if not guard and not is_test_or_entry(path):
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                add(node, "missing-main-guard", "module-level call runs on import; wrap in if __name__ == '__main__'")
                break
        else:
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == "main":
                    add(node, "missing-main-guard", "main() defined but no if __name__ == '__main__' guard calls it")
                    break
    return out


def collect_files(paths):
    files = []
    for p in map(Path, paths):
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*.py")):
                rel_dirs = f.relative_to(p).parts[:-1]
                if any(d in SKIP_DIRS or d.endswith(".egg-info") for d in rel_dirs):
                    continue
                files.append(f)
    return files


def read_source(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"file larger than {MAX_BYTES} bytes; skipped")
    return path.read_bytes().decode("utf-8-sig")


def main(argv):
    if argv == ["--rules"]:
        print(json.dumps({"rules": RULES}, indent=2))
        return 0
    paths = [a for a in argv if not a.startswith("--")]
    if not paths or len(paths) != len(argv):
        print("usage: py_audit.py <file-or-folder> [...] | --rules", file=sys.stderr)
        return 2
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        print("no such path: " + ", ".join(missing), file=sys.stderr)
        return 2
    files = collect_files(paths)
    if not files:
        print("no .py files found under: " + ", ".join(paths), file=sys.stderr)
        return 2

    findings, errors, scanned = [], [], 0
    for path in files:
        shown = path.as_posix()
        try:
            text = read_source(path)
            tree = ast.parse(text, filename=path)
        except (OSError, UnicodeDecodeError, ValueError, SyntaxError) as exc:
            errors.append({"file": shown, "error": f"{type(exc).__name__}: {exc}"})
            continue
        scanned += 1
        lines = text.splitlines()
        for line, col, rule, msg in audit_tree(tree, path):
            src = lines[line - 1] if 0 < line <= len(lines) else ""
            m = SUPPRESS.search(src)
            if m and (m.group(1).startswith("noqa") or m.group(2) == rule):
                continue
            findings.append({"file": shown, "line": line, "col": col, "rule": rule, "message": msg})
    findings.sort(key=lambda f: (f["file"], f["line"], f["col"], f["rule"]))
    counts = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    verdict = "findings" if findings else ("incomplete" if errors else "clean")
    report = {"tool": "py_audit", "version": VERSION, "files_scanned": scanned, "findings": findings,
              "counts": dict(sorted(counts.items())), "errors": errors, "verdict": verdict}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if verdict == "clean" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
