#!/usr/bin/env python3
"""Compare two versions of one Python file and report what a refactor changed.

Usage:
    python refactor_diff.py BEFORE.py AFTER.py

Reads the two files (UTF-8, a leading BOM is accepted) and parses them with the
`ast` module. Nothing is written, imported or executed. Prints one JSON object
on stdout (schema in SKILL.md) and nothing else.

Exit codes:
    0  public surface preserved (the AST may still differ inside bodies)
    1  public surface changed: a public name was removed, a public signature
       changed, or the set of top-level definitions differs
    2  usage error, unreadable file or syntax error (JSON {"error": ...} printed)

What "public" means: if the module assigns a literal list or tuple of strings to
`__all__`, those names; otherwise every top-level name that does not start with
an underscore. Methods of a public class are public unless the name starts with
a single underscore (dunder methods such as __init__ count as public).

Limits: static analysis of one file. It cannot see dynamic access (getattr,
monkeypatching), other files that import the changed names, or whether a body
change alters behaviour. It reports where bodies differ; the tests decide the rest.
"""
import ast
import json
import sys

# Param kinds in call order. Reordering across kinds changes how callers can pass args.
KIND_ORDER = ("posonly", "regular", "vararg", "kwonly", "kwarg")


def _src(node):
    """Source text of an expression node, or None."""
    return None if node is None else ast.unparse(node)


def _params(args):
    """Return a list of parameter dicts in declaration order."""
    out = []
    pos = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(pos) - len(args.defaults)) + list(args.defaults)
    n_posonly = len(args.posonlyargs)
    for i, (a, d) in enumerate(zip(pos, defaults)):
        out.append({"name": a.arg, "kind": "posonly" if i < n_posonly else "regular",
                    "default": _src(d), "annotation": _src(a.annotation)})
    if args.vararg:
        out.append({"name": args.vararg.arg, "kind": "vararg", "default": None,
                    "annotation": _src(args.vararg.annotation)})
    for a, d in zip(args.kwonlyargs, args.kw_defaults):
        out.append({"name": a.arg, "kind": "kwonly", "default": _src(d),
                    "annotation": _src(a.annotation)})
    if args.kwarg:
        out.append({"name": args.kwarg.arg, "kind": "kwarg", "default": None,
                    "annotation": _src(args.kwarg.annotation)})
    return out


def _signature(node):
    """Normalised signature record for a function or async function node."""
    return {"async": isinstance(node, ast.AsyncFunctionDef),
            "params": _params(node.args),
            "returns": _src(node.returns),
            "decorators": [_src(d) for d in node.decorator_list]}


def _render(sig):
    """Human-readable one-line signature."""
    parts = []
    has_vararg = any(p["kind"] == "vararg" for p in sig["params"])
    seen_kwonly = False
    last_posonly = max([i for i, p in enumerate(sig["params"]) if p["kind"] == "posonly"], default=-1)
    for idx, p in enumerate(sig["params"]):
        if p["kind"] == "kwonly" and not has_vararg and not seen_kwonly:
            parts.append("*")
        seen_kwonly = seen_kwonly or p["kind"] == "kwonly"
        text = {"vararg": "*", "kwarg": "**"}.get(p["kind"], "") + p["name"]
        if p["annotation"]:
            text += ": " + p["annotation"]
        if p["default"] is not None:
            text += (" = " if p["annotation"] else "=") + p["default"]
        parts.append(text)
        if idx == last_posonly:
            parts.append("/")
    text = ("async " if sig["async"] else "") + "(" + ", ".join(parts) + ")"
    if sig["returns"]:
        text += " -> " + sig["returns"]
    for d in sig["decorators"]:
        text = "@" + d + " " + text
    return text


def _strip_docstring(node):
    """Dump of the statements in the node body, ignoring a leading docstring and the signature."""
    body = list(getattr(node, "body", []))
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant)             and isinstance(body[0].value.value, str):
        body = body[1:]
    return "|".join(ast.dump(stmt) for stmt in body)


def _all_names(tree):
    """Names listed in a literal __all__, or None when absent or not literal."""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)) and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.value.elts):
                return [e.value for e in node.value.elts]
    return None


def _target_names(target):
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            yield from _target_names(elt)


def _imports(tree):
    """Set of normalised import statements anywhere in the module."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                found.add("import " + a.name + (" as " + a.asname if a.asname else ""))
        elif isinstance(node, ast.ImportFrom):
            mod = "." * node.level + (node.module or "")
            for a in node.names:
                found.add("from " + mod + " import " + a.name + (" as " + a.asname if a.asname else ""))
    return found


def collect(source):
    """Parse source; return definitions keyed by qualified name."""
    tree = ast.parse(source)
    defs = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs[node.name] = {"kind": "function", "sig": _signature(node), "body": _strip_docstring(node)}
        elif isinstance(node, ast.ClassDef):
            defs[node.name] = {"kind": "class", "sig": {"bases": [_src(b) for b in node.bases],
                                                         "keywords": [k.arg + "=" + _src(k.value) if k.arg else "**" + _src(k.value)
                                                                      for k in node.keywords],
                                                         "decorators": [_src(d) for d in node.decorator_list]},
                               "body": None}
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defs[node.name + "." + sub.name] = {"kind": "method", "sig": _signature(sub),
                                                        "body": _strip_docstring(sub)}
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                for name in _target_names(t):
                    if name not in defs:
                        defs[name] = {"kind": "variable", "sig": None, "body": ast.dump(node.value) if getattr(node, "value", None) else None}
    return tree, defs


def _is_public(qname, kind, allnames):
    top, _, member = qname.partition(".")
    if allnames is not None:
        listed = top in allnames
        if kind == "method":
            return listed and not (member.startswith("_") and not member.startswith("__"))
        return listed
    if top.startswith("_"):
        return False
    if kind == "method":
        return not (member.startswith("_") and not (member.startswith("__") and member.endswith("__")))
    return True


def _function_changes(b, a):
    """Describe how a function signature changed; return (kinds, breaking)."""
    kinds, breaking = [], False
    if b["async"] != a["async"]:
        kinds.append("async_changed")
        breaking = True
    if b["decorators"] != a["decorators"]:
        kinds.append("decorators_changed")
    if b["returns"] != a["returns"]:
        kinds.append("return_annotation_changed")
    bp = {p["name"]: p for p in b["params"]}
    ap = {p["name"]: p for p in a["params"]}
    for name in bp:
        if name not in ap:
            kinds.append("param_removed:" + name)
            breaking = True
    for name, p in ap.items():
        if name not in bp:
            if p["default"] is None and p["kind"] not in ("vararg", "kwarg"):
                kinds.append("required_param_added:" + name)
                breaking = True
            else:
                kinds.append("optional_param_added:" + name)
    for name in bp:
        if name in ap:
            if bp[name]["kind"] != ap[name]["kind"]:
                kinds.append("param_kind_changed:" + name)
                breaking = True
            if bp[name]["default"] != ap[name]["default"]:
                kinds.append("default_changed:" + name)
                if bp[name]["default"] is not None and ap[name]["default"] is None:
                    breaking = True
            if bp[name]["annotation"] != ap[name]["annotation"]:
                kinds.append("annotation_changed:" + name)
    common_b = [p["name"] for p in b["params"] if p["name"] in ap]
    common_a = [p["name"] for p in a["params"] if p["name"] in bp]
    if common_b != common_a:
        kinds.append("param_order_changed")
        if any(bp[n]["kind"] in ("posonly", "regular") for n in common_b):
            breaking = True
    return kinds, breaking


def compare(before_src, after_src):
    """Return the report dict for two sources."""
    tree_b, defs_b = collect(before_src)
    tree_a, defs_a = collect(after_src)
    all_b, all_a = _all_names(tree_b), _all_names(tree_a)

    def public(defs, allnames):
        return {q for q, d in defs.items() if _is_public(q, d["kind"], allnames)}

    pub_b, pub_a = public(defs_b, all_b), public(defs_a, all_a)

    removed = sorted(pub_b - set(defs_a)) + sorted(q for q in (pub_b & set(defs_a)) if q not in pub_a)
    removed = sorted(set(removed))
    added = sorted(pub_a - pub_b - set(defs_b))

    sig_changes, body_changed = [], []
    for q in sorted(set(defs_b) & set(defs_a)):
        db, da = defs_b[q], defs_a[q]
        if db["kind"] != da["kind"]:
            if q in pub_b:
                sig_changes.append({"name": q, "kind": da["kind"], "before": db["kind"], "after": da["kind"],
                                    "changes": ["definition_kind_changed"], "breaking": True})
            continue
        if db["kind"] in ("function", "method"):
            kinds, breaking = _function_changes(db["sig"], da["sig"])
            if kinds and q in pub_b:
                sig_changes.append({"name": q, "kind": db["kind"], "before": _render(db["sig"]),
                                    "after": _render(da["sig"]), "changes": kinds, "breaking": breaking})
        elif db["kind"] == "class" and db["sig"] != da["sig"] and q in pub_b:
            sig_changes.append({"name": q, "kind": "class", "before": "bases=%s keywords=%s decorators=%s" % (
                db["sig"]["bases"], db["sig"]["keywords"], db["sig"]["decorators"]),
                "after": "bases=%s keywords=%s decorators=%s" % (da["sig"]["bases"], da["sig"]["keywords"], da["sig"]["decorators"]),
                "changes": ["class_header_changed"], "breaking": db["sig"]["bases"] != da["sig"]["bases"]})
        if db["body"] != da["body"] and db["kind"] != "class":
            body_changed.append(q)

    # A removed name plus an added name with an identical signature is probably a rename.
    renames = []
    for r in removed:
        if r not in defs_b:
            continue
        for n in added:
            if n not in defs_a or defs_b[r]["kind"] != defs_a[n]["kind"]:
                continue
            kind = defs_b[r]["kind"]
            if kind == "class":
                same = defs_b[r]["sig"] == defs_a[n]["sig"]
            elif kind in ("function", "method"):
                same = defs_b[r]["sig"] == defs_a[n]["sig"] and r.split(".")[:-1] == n.split(".")[:-1]
            else:
                same = False
            if same:
                renames.append({"from": r, "to": n})
                break

    imp_b, imp_a = _imports(tree_b), _imports(tree_a)

    top_b = sorted((d["kind"], q) for q, d in defs_b.items() if d["kind"] != "method")
    top_a = sorted((d["kind"], q) for q, d in defs_a.items() if d["kind"] != "method")
    only_before = [{"kind": k, "name": n} for k, n in top_b if (k, n) not in set(top_a)]
    only_after = [{"kind": k, "name": n} for k, n in top_a if (k, n) not in set(top_b)]
    preserved = not only_before and not only_after

    breaking = [c["name"] for c in sig_changes if c["breaking"]]
    surface_ok = not removed and not breaking and preserved
    identical = ast.dump(tree_b) == ast.dump(tree_a)
    if identical:
        verdict = "ast_identical"
    elif surface_ok:
        verdict = "surface_preserved"
    else:
        verdict = "surface_changed"

    return {
        "verdict": verdict,
        "surface_preserved": surface_ok,
        "ast_identical": identical,
        "removed_public_names": removed,
        "added_public_names": added,
        "possible_renames": renames,
        "changed_signatures": sig_changes,
        "imports": {"added": sorted(imp_a - imp_b), "removed": sorted(imp_b - imp_a)},
        "top_level_definitions": {"preserved": preserved, "only_in_before": only_before, "only_in_after": only_after},
        "bodies_changed": body_changed,
        "public_surface_source": "__all__" if all_b is not None or all_a is not None else "no_underscore_rule",
    }


def _read(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError("cannot read %s as UTF-8 text: %s" % (path, exc))


def _emit(obj):
    sys.stdout.buffer.write((json.dumps(obj, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=True) + "\n").encode("ascii"))


def main(argv):
    if len(argv) != 2:
        _emit({"error": "usage: refactor_diff.py BEFORE.py AFTER.py"})
        return 2
    try:
        before_src, after_src = _read(argv[0]), _read(argv[1])
        report = compare(before_src, after_src)
    except ValueError as exc:
        _emit({"error": str(exc)})
        return 2
    except SyntaxError as exc:
        _emit({"error": "syntax error: %s (line %s). Fix the file so it parses, then re-run." % (exc.msg, exc.lineno)})
        return 2
    report = dict({"before": argv[0].replace("\\", "/"), "after": argv[1].replace("\\", "/")}, **report)
    _emit(report)
    return 0 if report["surface_preserved"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
