"""py_dead.py: list Python functions, classes, methods and modules that no
scanned file references.

Each .py file under the project folder is parsed with ast. Nothing is imported
or executed. A definition counts as used when its name appears anywhere in the
folder as a Load-context Name, a Load-context Attribute attribute, an import
name or module segment, or a string inside an __all__ list. Matching is by
name only, so same-named definitions in different files count as one name.

Usage:
    python -I scripts/py_dead.py <project-dir> [--include-decorated]

Exit codes: 0 no findings, 1 findings, 2 usage or input error.
Output: JSON on stdout. Paths are relative to <project-dir>, with forward slashes.
Errors: one line of JSON on stderr, {"error": "<code>", "detail": "<text>"}.
"""

import ast
import json
import os
import sys

MAX_BYTES = 2 * 1024 * 1024
SKIP_DIRS = {"__pycache__", "venv", "node_modules", "build", "dist", "site-packages"}
MODULE_EXCLUDE = {"__init__.py", "__main__.py", "main.py", "conftest.py", "setup.py"}
FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
USAGE = "python -I scripts/py_dead.py <project-dir> [--include-decorated]"


def fail(code, detail):
    sys.stderr.write(json.dumps({"error": code, "detail": detail}) + "\n")
    sys.exit(2)


def iter_py_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS
        )
        for name in sorted(filenames):
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


def read_source(path, rel):
    try:
        size = os.path.getsize(path)
        if size > MAX_BYTES:
            fail("file_too_large", "%s is %d bytes; limit is %d" % (rel, size, MAX_BYTES))
        with open(path, "rb") as fh:
            data = fh.read(MAX_BYTES + 1)
    except OSError as exc:
        fail("read_error", "%s: %s" % (rel, exc.strerror or exc.__class__.__name__))
    if len(data) > MAX_BYTES:
        fail("file_too_large", "%s grew past %d bytes while reading" % (rel, MAX_BYTES))
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        fail("invalid_utf8", "%s at byte %d" % (rel, exc.start))


def parse(text, rel):
    try:
        return ast.parse(text, filename=rel)
    except SyntaxError as exc:
        fail("syntax_error", "%s line %s" % (rel, exc.lineno))
    except ValueError:
        fail("syntax_error", "%s contains a null byte" % rel)


def collect_refs(tree, refs):
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            refs.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            refs.add(node.attr)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                refs.update(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                refs.update(node.module.split("."))
            refs.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Tuple)):
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                refs.update(
                    e.value for e in node.value.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                )


def candidates(tree):
    """Yield (name, line, kind, decorated) for top-level and class-level definitions."""
    for node in tree.body:
        if isinstance(node, FUNC_NODES):
            yield node.name, node.lineno, "function", bool(node.decorator_list)
        elif isinstance(node, ast.ClassDef):
            yield node.name, node.lineno, "class", bool(node.decorator_list)
            for sub in node.body:
                if isinstance(sub, FUNC_NODES):
                    yield sub.name, sub.lineno, "method", bool(sub.decorator_list)


def main(argv):
    flags = [a for a in argv[1:] if a == "--include-decorated"]
    args = [a for a in argv[1:] if a != "--include-decorated"]
    if len(args) != 1 or any(a.startswith("-") for a in args):
        fail("usage", USAGE)
    include_decorated = bool(flags)
    root = args[0]
    if not os.path.isdir(root):
        fail("not_a_directory", "the project-dir argument is not a directory")

    files = list(iter_py_files(root))
    if not files:
        fail("no_python_files", "no .py files found under the project-dir")

    parsed = []
    refs = set()
    for path in files:
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        tree = parse(read_source(path, rel), rel)
        collect_refs(tree, refs)
        parsed.append((rel, tree))

    total = 0
    excluded = {"dunder": 0, "test_prefix": 0, "decorated": 0, "module_entry": 0}
    findings = []
    for rel, tree in parsed:
        base = rel.rsplit("/", 1)[-1]
        stem = base[:-3]
        total += 1
        if base in MODULE_EXCLUDE or stem.startswith("test_") or stem.endswith("_test"):
            excluded["module_entry"] += 1
        elif stem not in refs:
            findings.append({"file": rel, "line": 1, "kind": "module", "name": stem})

        for name, line, kind, decorated in candidates(tree):
            total += 1
            if name.startswith("__") and name.endswith("__"):
                excluded["dunder"] += 1
            elif kind in ("function", "method") and name.startswith("test_"):
                excluded["test_prefix"] += 1
            elif decorated and not include_decorated:
                excluded["decorated"] += 1
            elif name not in refs:
                findings.append({"file": rel, "line": line, "kind": kind, "name": name})

    findings.sort(key=lambda f: (f["file"], f["line"], f["name"]))
    result = {
        "files_scanned": len(parsed),
        "definitions": total,
        "excluded": excluded,
        "findings": findings,
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
