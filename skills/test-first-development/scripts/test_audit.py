#!/usr/bin/env python3
"""Audit one test file for defects that make a test worthless.

    python test_audit.py check <file> [--lang python|javascript] [--name-regex REGEX]

Reads the file, writes strict JSON to stdout, changes nothing. Standard library
only, no network. Python files are parsed with `ast` (never imported or run).
JavaScript and TypeScript files are scanned with a small string- and
comment-aware scanner that understands `it(`, `test(`, their `.skip`/`.only`
forms and `xit`/`xtest`; it is a syntax subset, not a full parser.

Rules (see references/audit-rules.md for exact definitions):
  NO_TESTS         error    the file holds no recognised test
  NO_ASSERTION     error    a test with zero assertions
  TRIVIAL_ASSERT   error    every assertion in a test is trivially true
  DUPLICATE_BODY   error    two tests have the same body
  SKIP_NO_REASON   error    skip/xfail/todo-skip without a written reason
  ONLY_LEFT        error    .only / fit left in a JavaScript file
  NAME_CONTRACT    error    the test name does not follow the naming contract
  ASSERT_HEAVY     warning  more than MAX_ASSERTS assertions in one test

Exit codes: 0 no errors (warnings allowed), 1 at least one error finding,
2 usage problem, missing, empty or unparsable file (JSON with an "error" key).
"""
import argparse
import ast
import json
import os
import re
import sys

SCHEMA_VERSION = 1
# More than this many assertions usually means several behaviours in one test.
MAX_ASSERTS = 6
# Segments that say nothing about behaviour.
GENERIC = {"works", "work", "basic", "ok", "okay", "test", "case", "simple", "success",
           "happy", "thing", "stuff", "foo", "bar", "it", "run", "main", "function"}
PY_SEG = r"[a-z0-9]+(?:_[a-z0-9]+)*"
PY_NAME_RE = re.compile(r"^test_(%s)__(%s)__(%s)$" % (PY_SEG, PY_SEG, PY_SEG))
JS_CONDITION_RE = re.compile(r"\b(when|if|given|with|without|after|before|for|on)\b", re.I)
JS_MIN_WORDS = 4
JS_COMMENT_REASON_RE = re.compile(r"(?://|/\*)\s*(?:skip(?:ped)?|reason)\s*:\s*\S{3,}", re.I)


class AuditError(Exception):
    """A problem with the input that stops the audit (exit 2)."""


def finding(rule, severity, test, line, message):
    return {"rule": rule, "severity": severity, "test": test, "line": line, "message": message}


# --------------------------------------------------------------------- Python

def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
        return node.value
    return None


def skip_problem(expr):
    """Return a message when expr is a skip/xfail marker with no reason, else None."""
    call = expr if isinstance(expr, ast.Call) else None
    name = dotted(call.func if call else expr)
    if not name:
        return None
    last = name.split(".")[-1]
    is_pytest = name.startswith("pytest.") or name.startswith("mark.")
    kws = {k.arg: k.value for k in (call.keywords if call else []) if k.arg}
    args = call.args if call else []
    if last == "skip":
        if is_pytest:
            ok = const_str(kws.get("reason")) or (args and const_str(args[0]))
        else:  # unittest.skip(reason)
            ok = args and const_str(args[0]) or const_str(kws.get("reason"))
        return None if ok else "skip without a reason"
    if last in ("skipif", "xfail") and is_pytest:
        return None if const_str(kws.get("reason")) else last + " without reason="
    if last in ("skipIf", "skipUnless") and not is_pytest:
        ok = (len(args) > 1 and const_str(args[1])) or const_str(kws.get("reason"))
        return None if ok else last + " without a reason"
    return None


def is_assert_call(call):
    f = call.func
    if isinstance(f, ast.Attribute):
        if f.attr.startswith("assert"):
            return True
        if f.attr in ("raises", "warns") and dotted(f.value).split(".")[0] == "pytest":
            return True
    if isinstance(f, ast.Name) and f.id.startswith("assert"):
        return True
    return False


def falsy_const(node):
    return isinstance(node, ast.Constant) and not node.value


def truthy_const(node):
    return isinstance(node, ast.Constant) and bool(node.value)


def trivial_assert_stmt(node):
    t = node.test
    if truthy_const(t):
        return True
    if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Not) and falsy_const(t.operand):
        return True
    if (isinstance(t, ast.Compare) and len(t.ops) == 1 and isinstance(t.ops[0], (ast.Eq, ast.Is, ast.LtE, ast.GtE))
            and ast.dump(t.left) == ast.dump(t.comparators[0])):
        return True
    return False


def trivial_assert_call(call):
    f = call.func
    name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
    a = call.args
    if name in ("assertTrue", "assert_") and a and truthy_const(a[0]):
        return True
    if name == "assertFalse" and a and falsy_const(a[0]):
        return True
    if name in ("assertEqual", "assertEquals", "assertIs") and len(a) >= 2 and ast.dump(a[0]) == ast.dump(a[1]):
        return True
    return False


def py_tests(tree):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            yield node, None
        elif isinstance(node, ast.ClassDef):
            bases = [dotted(b) for b in node.bases]
            if node.name.startswith("Test") or any(b.endswith("TestCase") for b in bases):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name.startswith("test"):
                        yield sub, node


def body_without_docstring(fn):
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    return body


def audit_python(src, name_regex):
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        raise AuditError("syntax error at line %s: %s" % (exc.lineno, exc.msg))
    tests, findings, seen = [], [], {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets):
            exprs = node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else [node.value]
            for e in exprs:
                msg = skip_problem(e)
                if msg:
                    findings.append(finding("SKIP_NO_REASON", "error", "<module>", node.lineno, "pytestmark: " + msg))
    for fn, cls in py_tests(tree):
        asserts = trivial = 0
        for n in ast.walk(fn):
            if isinstance(n, ast.Assert):
                asserts += 1
                trivial += trivial_assert_stmt(n)
            elif isinstance(n, ast.Call):
                if is_assert_call(n):
                    asserts += 1
                    trivial += trivial_assert_call(n)
        skipped = False
        decos = list(fn.decorator_list) + (list(cls.decorator_list) if cls else [])
        for d in decos:
            msg = skip_problem(d)
            name = dotted(d.func if isinstance(d, ast.Call) else d).split(".")[-1]
            if name in ("skip", "skipif", "skipIf", "skipUnless", "xfail"):
                skipped = skipped or name in ("skip",)
            if msg:
                findings.append(finding("SKIP_NO_REASON", "error", fn.name, d.lineno, msg))
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and dotted(n.func) in ("pytest.skip", "self.skipTest", "pytest.xfail"):
                kw = {k.arg: k.value for k in n.keywords if k.arg}
                if not ((n.args and const_str(n.args[0])) or const_str(kw.get("reason")) or const_str(kw.get("msg"))):
                    findings.append(finding("SKIP_NO_REASON", "error", fn.name, n.lineno, dotted(n.func) + " called without a reason"))
        label = (cls.name + "." if cls else "") + fn.name
        tests.append({"name": label, "line": fn.lineno, "assertions": asserts, "trivial_assertions": trivial, "skipped": skipped})
        check_common(findings, label, fn.lineno, asserts, trivial)
        if name_regex:
            if not name_regex.search(fn.name):
                findings.append(finding("NAME_CONTRACT", "error", label, fn.lineno, "name does not match --name-regex"))
        else:
            m = PY_NAME_RE.match(fn.name)
            if not m:
                findings.append(finding("NAME_CONTRACT", "error", label, fn.lineno,
                                        "expected test_<unit>__<condition>__<outcome> in lowercase snake_case"))
            else:
                bad = [s for s in m.groups() if all(p in GENERIC or p.isdigit() for p in s.split("_"))]
                if bad:
                    findings.append(finding("NAME_CONTRACT", "error", label, fn.lineno,
                                            "segment(s) %s say nothing about behaviour" % bad))
        if asserts:
            key = (tuple(ast.dump(d) for d in decos), tuple(ast.dump(s) for s in body_without_docstring(fn)))
            if key in seen:
                findings.append(finding("DUPLICATE_BODY", "error", label, fn.lineno, "same body as %s (line %d)" % seen[key]))
            else:
                seen[key] = (label, fn.lineno)
    return tests, findings


def check_common(findings, label, line, asserts, trivial):
    if asserts == 0:
        findings.append(finding("NO_ASSERTION", "error", label, line, "test has no assertion"))
    elif trivial >= asserts:
        findings.append(finding("TRIVIAL_ASSERT", "error", label, line, "every assertion is trivially true"))
    if asserts > MAX_ASSERTS:
        findings.append(finding("ASSERT_HEAVY", "warning", label, line,
                                "%d assertions; more than %d usually means several behaviours" % (asserts, MAX_ASSERTS)))


# ----------------------------------------------------------------- JavaScript

def strip_comments(src):
    """Blank out comments (keeping newlines and string contents) so offsets stay valid."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1])
            i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in src[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def match_paren(s, i):
    """s[i] is '('; return the index of its matching ')' or -1. String-aware."""
    depth, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"`":
            j = i + 1
            while j < n and s[j] != c:
                j += 2 if s[j] == "\\" else 1
            i = j
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


JS_CALL_RE = re.compile(r"(?<![\w.$])(it|test|xit|xtest|fit|ftest|describe|xdescribe|fdescribe)((?:\.(?:skip|only|concurrent|failing))*)\s*\(")
LITERAL = r"""(?:true|false|null|undefined|-?\d+(?:\.\d+)?|'[^'\n]*'|"[^"\n]*")"""
JS_ASSERT_RE = re.compile(r"\bexpect\s*\(|\bassert(?:\.\w+)?\s*\(|\.should\b|\bt\.(?:is|not|true|false|truthy|falsy|deepEqual|throws|throwsAsync|notThrows|regex|snapshot|assert)\s*\(")
JS_TRIVIAL_RES = [
    re.compile(r"\bexpect\s*\(\s*%s\s*\)\s*\." % LITERAL),
    re.compile(r"\bexpect\s*\(\s*([\w$.]+)\s*\)\s*\.(?:toBe|toEqual|toStrictEqual)\s*\(\s*\1\s*\)"),
    re.compile(r"\bassert(?:\.ok)?\s*\(\s*(?:true|1)\s*\)"),
    re.compile(r"\bassert\.(?:equal|strictEqual|deepEqual|deepStrictEqual)\s*\(\s*([\w$.]+)\s*,\s*\1\s*\)"),
]


def audit_js(src, name_regex):
    clean = strip_comments(src)
    lines = src.split("\n")
    tests, findings, seen = [], [], {}
    for m in JS_CALL_RE.finditer(clean):
        base, mods = m.group(1), m.group(2)
        suite = base in ("describe", "xdescribe", "fdescribe")
        skipped = ".skip" in mods or base in ("xit", "xtest", "xdescribe")
        only = ".only" in mods or base in ("fit", "ftest", "fdescribe")
        line = clean.count("\n", 0, m.start()) + 1
        open_i = m.end() - 1
        close_i = match_paren(clean, open_i)
        if close_i < 0:
            continue
        inner = clean[open_i + 1:close_i]
        lead = len(inner) - len(inner.lstrip())
        title = None
        rest = inner
        if inner.lstrip()[:1] in ("'", '"', "`"):
            q = inner.lstrip()[0]
            j = lead + 1
            while j < len(inner) and inner[j] != q:
                j += 2 if inner[j] == "\\" else 1
            title = inner[lead + 1:j]
            rest = inner[j + 1:]
        label = title if title is not None else "<dynamic title>"
        if only:
            findings.append(finding("ONLY_LEFT", "error", label, line, ".only/fit left in; the rest of the file is silently not run"))
        if skipped:
            here = lines[line - 1] if line - 1 < len(lines) else ""
            prev = next((l for l in reversed(lines[:line - 1]) if l.strip()), "")
            if not (JS_COMMENT_REASON_RE.search(here) or JS_COMMENT_REASON_RE.search(prev)):
                findings.append(finding("SKIP_NO_REASON", "error", label, line, "skipped without a '// skip: <reason>' comment on this or the previous line"))
        if suite:
            continue
        asserts = len(JS_ASSERT_RE.findall(rest))
        trivial = sum(len(r.findall(rest)) for r in JS_TRIVIAL_RES)
        tests.append({"name": label, "line": line, "assertions": asserts, "trivial_assertions": min(trivial, asserts), "skipped": skipped})
        check_common(findings, label, line, asserts, min(trivial, asserts))
        if title is not None:
            if name_regex:
                if not name_regex.search(title):
                    findings.append(finding("NAME_CONTRACT", "error", label, line, "title does not match --name-regex"))
            else:
                words = re.findall(r"[\w$.]+", title)
                low = [w.lower() for w in words]
                problems = []
                if len(words) < JS_MIN_WORDS:
                    problems.append("fewer than %d words" % JS_MIN_WORDS)
                if not JS_CONDITION_RE.search(title):
                    problems.append("no condition word (when, if, given, with, without, after, before, for, on)")
                if low and (low[0] in GENERIC or low[:2] == ["should", "work"]):
                    problems.append("starts with a generic word")
                if problems:
                    findings.append(finding("NAME_CONTRACT", "error", label, line,
                                            "expected '<unit> <outcome> when <condition>': " + "; ".join(problems)))
        if asserts:
            key = re.sub(r"\s+", "", rest)
            if key in seen:
                findings.append(finding("DUPLICATE_BODY", "error", label, line, "same body as '%s' (line %d)" % seen[key]))
            else:
                seen[key] = (label, line)
    return tests, findings


# ------------------------------------------------------------------- driver

class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        emit({"tool": "test_audit", "schema_version": SCHEMA_VERSION, "ok": False, "error": message})
        raise SystemExit(2)


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2) + "\n")


def run_check(path, lang, name_regex):
    if not os.path.isfile(path):
        raise AuditError("file not found: %s" % path)
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        src = fh.read()
    if not src.strip():
        raise AuditError("file is empty: %s" % path)
    ext = os.path.splitext(path)[1].lower()
    if lang is None:
        if ext == ".py":
            lang = "python"
        elif ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
            lang = "javascript"
        else:
            raise AuditError("cannot infer language from extension %r; pass --lang" % ext)
    rx = None
    if name_regex:
        try:
            rx = re.compile(name_regex)
        except re.error as exc:
            raise AuditError("bad --name-regex: %s" % exc)
    tests, findings = (audit_python if lang == "python" else audit_js)(src, rx)
    if not tests:
        findings.append(finding("NO_TESTS", "error", None, 1, "no recognised test found"))
    findings.sort(key=lambda f: (f["line"], f["rule"], f["test"] or ""))
    errors = sum(f["severity"] == "error" for f in findings)
    by_rule = {}
    for f in findings:
        by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
    return {
        "tool": "test_audit", "schema_version": SCHEMA_VERSION, "file": os.path.basename(path), "language": lang,
        "ok": errors == 0,
        "summary": {"tests": len(tests), "skipped": sum(t["skipped"] for t in tests), "errors": errors,
                    "warnings": len(findings) - errors, "by_rule": dict(sorted(by_rule.items()))},
        "tests": tests, "findings": findings,
    }


def main(argv=None):
    p = JsonArgumentParser(prog="test_audit.py", description="Audit a test file; prints strict JSON.")
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=JsonArgumentParser)
    c = sub.add_parser("check", help="audit one test file")
    c.add_argument("file")
    c.add_argument("--lang", choices=["python", "javascript"])
    c.add_argument("--name-regex", help="replace the built-in naming contract with this regex (searched in the name or title)")
    args = p.parse_args(argv)
    try:
        report = run_check(args.file, args.lang, args.name_regex)
    except AuditError as exc:
        emit({"tool": "test_audit", "schema_version": SCHEMA_VERSION, "ok": False, "error": str(exc)})
        return 2
    emit(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
