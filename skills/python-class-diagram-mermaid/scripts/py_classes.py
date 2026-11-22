"""Generate a Mermaid classDiagram from Python source files.

Usage:
    python -I scripts/py_classes.py <input-file> [<input-file> ...] [--out <output-file.mmd>]

Each input is parsed with the ast module. Inputs are never imported, executed
or modified. The Mermaid text is written to stdout. With --out the same text is
also written to a new file; an existing file is never overwritten.

Exit codes: 0 ok, 1 syntax error findings, 2 usage or input error.
Errors go to stderr as one line of JSON with keys status, code and message.
"""
import argparse
import ast
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
TYPE_DROP = re.compile(r"[^A-Za-z0-9_.~, ]")
NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def fail(code, message):
    sys.stderr.write(json.dumps({"status": "error", "code": code, "message": message}) + "\n")
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("USAGE", message)


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return None if base is None else base + "." + node.attr
    return None


def base_name(node):
    if isinstance(node, ast.Subscript):
        node = node.value
    name = dotted(node)
    return None if name is None else name.split(".")[-1]


def clean_type(annotation):
    text = ast.unparse(annotation)
    text = text.replace("|", " or ").replace("[", "~").replace("]", "~")
    text = " ".join(TYPE_DROP.sub("", text).split())
    return text or None


def visibility(name):
    if name.startswith("__") and name.endswith("__"):
        return "+"
    if name.startswith("__"):
        return "-"
    if name.startswith("_"):
        return "#"
    return "+"


def decorator_names(func):
    names = set()
    for dec in func.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        name = dotted(target)
        if name:
            names.add(name.split(".")[-1])
    return names


def method_line(func):
    names = decorator_names(func)
    if names & {"staticmethod", "classmethod"}:
        marker = "$"
    elif "abstractmethod" in names:
        marker = "*"
    else:
        marker = ""
    params = [p.arg for p in list(func.args.posonlyargs) + list(func.args.args)]
    if params and params[0] in ("self", "cls"):
        params = params[1:]
    params += [p.arg for p in func.args.kwonlyargs]
    line = visibility(func.name) + func.name + "(" + ", ".join(params) + ")" + marker
    if func.returns is not None:
        ret = clean_type(func.returns)
        if ret:
            line += " " + ret
    return line


def annotation_relations(ann, local):
    """Return (kind, target) pairs for local classes named in an annotation."""
    direct = ann
    if isinstance(direct, ast.Subscript) and dotted(direct.value) in ("Optional", "typing.Optional"):
        direct = direct.slice
    if isinstance(direct, ast.Constant) and isinstance(direct.value, str):
        name = direct.value.strip().split(".")[-1]
    else:
        name = base_name(direct)
    if name in local:
        return [("composition", name)]
    mentioned = set()
    for node in ast.walk(ann):
        if isinstance(node, ast.Name) and node.id in local:
            mentioned.add(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in local:
            mentioned.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            mentioned.update(t for t in NAME_RE.findall(node.value) if t in local)
    return [("aggregation", n) for n in sorted(mentioned)]


def analyze_class(node, local):
    owner = node.name
    bases = []
    for b in node.bases:
        n = base_name(b)
        if n and n != "object":
            bases.append(n)
    attrs, methods, relations = [], [], set()
    seen_attr = set()
    annotated = []  # (attr name, annotation node)

    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            tname = clean_type(stmt.annotation)
            attrs.append(visibility(name) + (tname + " " if tname else "") + name)
            seen_attr.add(name)
            annotated.append((name, stmt.annotation))
        elif isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id not in seen_attr:
                    attrs.append(visibility(t.id) + t.id)
                    seen_attr.add(t.id)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(method_line(stmt))
            first = stmt.args.posonlyargs + stmt.args.args
            if not first:
                continue
            self_name = first[0].arg
            for sub in ast.walk(stmt):
                if (isinstance(sub, ast.AnnAssign)
                        and isinstance(sub.target, ast.Attribute)
                        and isinstance(sub.target.value, ast.Name)
                        and sub.target.value.id == self_name
                        and sub.target.attr not in seen_attr):
                    name = sub.target.attr
                    tname = clean_type(sub.annotation)
                    attrs.append(visibility(name) + (tname + " " if tname else "") + name)
                    seen_attr.add(name)
                    annotated.append((name, sub.annotation))

    for b in bases:
        relations.add(b + " <|-- " + owner)
    for attr, ann in annotated:
        for kind, target in annotation_relations(ann, local):
            arrow = "*--" if kind == "composition" else "o--"
            relations.add(owner + " " + arrow + " " + target + " : " + attr)

    return {"name": owner, "attrs": attrs, "methods": methods, "relations": relations}


def read_source(path):
    name = os.path.basename(path)
    if not os.path.isfile(path):
        fail("INPUT_MISSING", "input file not found: " + name)
    if not path.lower().endswith(".py"):
        fail("INPUT_NOT_PY", "input must be a .py file: " + name)
    if os.path.getsize(path) > MAX_BYTES:
        fail("INPUT_TOO_LARGE", "input exceeds 2 MB: " + name)
    with open(path, "rb") as fh:
        raw = fh.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        fail("INPUT_TOO_LARGE", "input exceeds 2 MB: " + name)
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("INPUT_NOT_UTF8", "input is not valid UTF-8: " + name)


def check_output(out):
    if not out.lower().endswith(".mmd"):
        fail("USAGE", "--out must end with .mmd")
    if os.path.exists(out):
        fail("OUTPUT_EXISTS", "output already exists; choose a new file name")


def main(argv=None):
    parser = _Parser(prog="py_classes.py",
                     description="Generate a Mermaid classDiagram from Python files (ast only).")
    parser.add_argument("inputs", nargs="+", metavar="input-file")
    parser.add_argument("--out", metavar="output-file.mmd")
    args = parser.parse_args(argv)

    if args.out:
        check_output(args.out)

    modules, findings = [], []
    for path in args.inputs:
        text = read_source(path)
        name = os.path.basename(path)
        try:
            modules.append((name, ast.parse(text, filename=name)))
        except (SyntaxError, ValueError, RecursionError) as exc:
            findings.append((name, getattr(exc, "lineno", None) or 0))

    local = set()
    for _, tree in modules:
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                local.add(node.name)

    blocks, relations = [], set()
    n_classes = n_attrs = n_methods = 0
    for _, tree in modules:
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            info = analyze_class(node, local)
            n_classes += 1
            n_attrs += len(info["attrs"])
            n_methods += len(info["methods"])
            relations |= info["relations"]
            members = info["attrs"] + info["methods"]
            if members:
                blocks.append("class " + info["name"] + " {")
                blocks.extend("    " + m for m in members)
                blocks.append("}")
            else:
                blocks.append("class " + info["name"])

    header = ["classDiagram",
              "%% py_classes files=%d classes=%d attributes=%d methods=%d relations=%d syntax_errors=%d"
              % (len(args.inputs), n_classes, n_attrs, n_methods, len(relations), len(findings))]
    for name, line in findings:
        header.append("%% SYNTAX_ERROR file=%s line=%d" % (name, line))
    text = "\n".join(header + blocks + sorted(relations)) + "\n"

    if args.out:
        try:
            with open(args.out, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        except FileExistsError:
            fail("OUTPUT_EXISTS", "output already exists; choose a new file name")
        except OSError:
            fail("OUTPUT_WRITE_FAILED", "cannot write the output file")

    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.flush()
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
