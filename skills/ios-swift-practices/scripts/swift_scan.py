#!/usr/bin/env python3
"""Scan .swift files for six documented anti-patterns. Read-only, standard library only.

Usage:
    python swift_scan.py PATH [PATH ...] [--max-body-lines N] [--force-density X]
                         [--include-tests] [--max-per-rule N]

PATH is a .swift file or a directory (searched recursively; .build, Pods, Carthage,
DerivedData, SourcePackages, .git and node_modules are skipped).

Reads the given paths only; writes nothing, no network. Output is one JSON object on
stdout (see SKILL.md for the schema). Errors are also JSON, with an "error" key.

Exit codes: 0 no findings, 1 at least one finding, 2 usage error or no .swift files.

Rules (ids as printed in the JSON):
    force-unwrap-density   file has >= MIN_FORCE_COUNT force unwraps/casts AND density >= threshold
    try-bang               every `try!`
    main-queue-in-async    `DispatchQueue.main.async` inside an async func, Task, .task or .refreshable body
    print-in-app-code      `print(` / `debugPrint(` outside tests and outside `#if DEBUG`
    giant-view-body        `var body: some View` with too many non-blank code lines
    state-reference-type   `@State` holding a class that is ObservableObject or plain (not @Observable)

Test files (path has a Tests directory, name ends Tests.swift/Test.swift, or the file imports
XCTest/Testing) are skipped for force-unwrap, try-bang and print rules unless --include-tests.
Comments and string literals are blanked before matching. This is a lexical scan, not a compiler.
"""
import argparse
import json
import os
import re
import sys

VERSION = "0.1.0"

# A file needs at least this many force unwraps/casts before density is judged;
# one or two in a long file are usually a deliberate literal-URL or similar case.
MIN_FORCE_COUNT = 3
# Force unwraps/casts per 100 non-blank code lines. 1.0 means one per screenful of
# code; chosen as a working value, not a measured optimum.
DEFAULT_FORCE_DENSITY = 1.0
# A body longer than this many non-blank lines rarely fits in one editor screen
# (about 50-60 lines), so it is hard to review as one unit.
DEFAULT_MAX_BODY_LINES = 60
# Twice the warn limit is reported as high severity.
BODY_HIGH_FACTOR = 2
DEFAULT_MAX_PER_RULE = 50
SKIP_DIRS = {".build", "Pods", "Carthage", "DerivedData", "SourcePackages", ".git", "node_modules"}

SUFFIX_HINT = ("ViewModel", "Manager", "Service", "Store", "Controller", "Coordinator",
               "Client", "Repository")


class ScanArgError(Exception):
    pass


class JsonArgParser(argparse.ArgumentParser):
    def error(self, message):
        raise ScanArgError(message)


# ----------------------------------------------------------------------------- lexing

def _blank(s, a, b):
    return "".join(c if c == "\n" else " " for c in s[a:b])


def _skip_string(s, i, hashes, multiline):
    """s[i] is just after the opening quote(s). Return index just after the closing delimiter."""
    n = len(s)
    close = ('"""' if multiline else '"') + "#" * hashes
    esc = "\\" + "#" * hashes
    while i < n:
        if s.startswith(esc, i):
            j = i + len(esc)
            if j < n and s[j] == "(":
                depth, j = 1, j + 1
                while j < n and depth:
                    c = s[j]
                    if c == '"':
                        ml = s.startswith('"""', j)
                        j = _skip_string(s, j + (3 if ml else 1), 0, ml)
                        continue
                    if c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                    j += 1
                i = j
                continue
            i = j + 1
            continue
        if s.startswith(close, i):
            return i + len(close)
        if not multiline and s[i] == "\n":
            return i  # unterminated single-line string: stop at end of line
        i += 1
    return n


def strip_code(s):
    """Return s with comments and string contents replaced by spaces; same length, same newlines."""
    out = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            j = s.find("\n", i)
            j = n if j < 0 else j
            out.append(_blank(s, i, j))
            i = j
        elif c == "/" and i + 1 < n and s[i + 1] == "*":
            depth, j = 1, i + 2
            while j < n and depth:
                if s.startswith("/*", j):
                    depth += 1
                    j += 2
                elif s.startswith("*/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            out.append(_blank(s, i, j))
            i = j
        elif c == '"' or (c == "#" and re.match(r'#+"', s[i:i + 40])):
            m = re.match(r"(#*)(\"\"\"|\")", s[i:i + 40])
            hashes = len(m.group(1))
            multiline = m.group(2) == '"""'
            j = _skip_string(s, i + len(m.group(0)), hashes, multiline)
            out.append(_blank(s, i, j))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def line_of(starts, pos):
    lo, hi = 0, len(starts)
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if starts[mid] <= pos:
            lo = mid
        else:
            hi = mid
    return lo + 1


# ----------------------------------------------------------------------------- helpers

def is_test_file(path, text):
    parts = re.split(r"[\\/]", path)
    base = parts[-1]
    if any(p.endswith("Tests") or p.endswith("UITests") for p in parts[:-1]):
        return True
    if base.endswith("Tests.swift") or base.endswith("Test.swift"):
        return True
    return bool(re.search(r"^\s*(?:@testable\s+)?import\s+(?:XCTest|Testing)\b", text, re.M))


FORCE_RE = re.compile(r"(?<=[\w\)\]])!(?!=)")
IUO_DECL_RE = re.compile(r"\b(?:var|let)\s+\w+\s*:\s*[\w.<>\[\]]+!(?!=)")


def find_force_ops(code):
    """Positions of postfix `!` (force unwrap) and `as!` (force cast); `try!` is a separate rule."""
    hits = []
    for m in FORCE_RE.finditer(code):
        p = m.start()
        before = code[max(0, p - 4):p]
        if re.search(r"\btry$", before):
            continue
        ls = code.rfind("\n", 0, p) + 1
        le = code.find("\n", p)
        le = len(code) if le < 0 else le
        line = code[ls:le]
        if IUO_DECL_RE.search(line):
            continue  # implicitly unwrapped declaration, not a use
        hits.append(p)
    return hits


def brace_pass(code, starts, async_probe_positions, body_limit):
    """One pass over braces. Returns (async_hits, bodies).

    async_hits: subset of async_probe_positions that sit inside an async context.
    bodies: list of (start_line, end_line, nonblank_line_count) for `var body: some View`.
    """
    stack = []  # frames: dict(async=bool, body_start=int|None)
    probes = sorted(async_probe_positions)
    pi = 0
    boundary = 0
    hits = []
    bodies = []
    n = len(code)
    for i in range(n):
        while pi < len(probes) and probes[pi] <= i:
            if stack and stack[-1]["async"]:
                hits.append(probes[pi])
            pi += 1
        c = code[i]
        if c == "{":
            header = code[boundary:i]
            parent_async = stack[-1]["async"] if stack else False
            funcs = list(re.finditer(r"\b(?:func|init)\b", header))
            last_line = header.rstrip().rsplit("\n", 1)[-1] if header.strip() else ""
            if funcs:
                is_async = bool(re.search(r"\basync\b", header[funcs[-1].end():]))
            elif re.search(r"\bTask\b|\.task\b|\.refreshable\b|\baddTask\b|\bwithTaskGroup\b|\bwithThrowingTaskGroup\b", last_line):
                is_async = True
            else:
                is_async = parent_async
            body_start = None
            if re.search(r"\bvar\s+body\s*:\s*some\s+View\b[^{}]*$", header):
                body_start = line_of(starts, i)
            stack.append({"async": is_async, "body_start": body_start, "open": i})
            boundary = i + 1
        elif c == "}":
            if stack:
                fr = stack.pop()
                if fr["body_start"] is not None:
                    end_line = line_of(starts, i)
                    seg = code[fr["open"] + 1:i]
                    nonblank = sum(1 for ln in seg.split("\n") if ln.strip())
                    bodies.append((fr["body_start"], end_line, nonblank))
            boundary = i + 1
        elif c == ";":
            boundary = i + 1
    return hits, bodies


CLASS_RE = re.compile(
    r"^[ \t]*((?:@[\w.]+(?:\([^)\n]*\))?[ \t]+)*)"
    r"(?:(?:public|internal|private|fileprivate|open|final|package)[ \t]+)*"
    r"class[ \t]+(\w+)[ \t]*(?:<[^>\n]*>)?[ \t]*(?::[ \t]*([^{\n]*))?",
    re.M)
STATE_RE = re.compile(
    r"@State\b[^\n]*?\bvar[ \t]+(\w+)[ \t]*(?::[ \t]*([A-Z][\w.]*))?[ \t]*\??[ \t]*(?:=[ \t]*([A-Z][\w.]*)[ \t]*[(\{])?")


def collect_classes(code):
    """Return {name: (kind, parent_names)} with kind in observable|object|plain."""
    found = {}
    lines = code.split("\n")
    for m in CLASS_RE.finditer(code):
        attrs = m.group(1) or ""
        name = m.group(2)
        inherits = [x.strip().split("<")[0].strip() for x in (m.group(3) or "").split(",") if x.strip()]
        ln = code.count("\n", 0, m.start())
        prev = lines[ln - 1] if ln > 0 else ""
        has_obs = "@Observable" in attrs or bool(re.match(r"\s*(?:@\w+\s+)*@Observable\b", prev))
        if has_obs:
            kind = "observable"
        elif "ObservableObject" in inherits:
            kind = "object"
        else:
            kind = "plain"
        found[name] = (kind, inherits)
    return found


def resolve_kind(name, classes, depth=0):
    kind, inherits = classes[name]
    if kind != "plain" or depth > 5:
        return kind
    for p in inherits:
        if p in classes:
            k = resolve_kind(p, classes, depth + 1)
            if k != "plain":
                return k
    return "plain"


def debug_lines(code):
    """Set of 1-based line numbers inside `#if DEBUG ... #endif` (innermost-aware, simple)."""
    inside = set()
    stack = []  # True when that #if is a DEBUG block
    for no, line in enumerate(code.split("\n"), 1):
        s = line.strip()
        if s.startswith("#if"):
            stack.append(re.match(r"#if\s+DEBUG\b", s) is not None)
        elif s.startswith("#else") or s.startswith("#elseif"):
            if stack:
                stack[-1] = False
        elif s.startswith("#endif"):
            if stack:
                stack.pop()
        if any(stack):
            inside.add(no)
    return inside


# ----------------------------------------------------------------------------- scan

def collect_files(paths):
    files = []
    for p in paths:
        if os.path.isfile(p):
            if p.endswith(".swift"):
                files.append(p)
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for nme in sorted(names):
                    if nme.endswith(".swift"):
                        files.append(os.path.join(root, nme))
        else:
            raise ScanArgError("path not found: " + p)
    return files


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def scan(paths, max_body, density_limit, include_tests, max_per_rule):
    files = collect_files(paths)
    if not files:
        raise ScanArgError("no .swift files found under the given paths")
    data = []
    classes = {}
    for f in files:
        text = read_text(f)
        code = strip_code(text)
        data.append((f, text, code))
        classes.update(collect_classes(code))

    findings = []
    per_file = []
    tests_skipped = 0
    for f, text, code in data:
        shown = f.replace("\\", "/")
        starts = [0]
        for i, ch in enumerate(code):
            if ch == "\n":
                starts.append(i + 1)
        lines = code.split("\n")
        code_lines = sum(1 for ln in lines if ln.strip())
        test = is_test_file(f, text)
        skip_rules = test and not include_tests
        if skip_rules:
            tests_skipped += 1
        srclines = text.split("\n")

        def add(pos_or_line, rule, severity, message, line=None, **extra):
            ln = line if line is not None else line_of(starts, pos_or_line)
            snippet = srclines[ln - 1].strip()[:120] if 0 < ln <= len(srclines) else ""
            d = {"file": shown, "line": ln, "rule": rule, "severity": severity,
                 "message": message, "snippet": snippet}
            d.update(extra)
            findings.append(d)

        # force unwrap density
        force_count = 0
        density = 0.0
        if not skip_rules:
            ops = find_force_ops(code)
            force_count = len(ops)
            density = round(force_count * 100.0 / code_lines, 2) if code_lines else 0.0
            if force_count >= MIN_FORCE_COUNT and density >= density_limit:
                first = line_of(starts, ops[0])
                add(None, "force-unwrap-density", "warn",
                    "%d force unwraps/casts in %d code lines (%.2f per 100; limit %.2f)"
                    % (force_count, code_lines, density, density_limit),
                    line=first, count=force_count, per_100_lines=density,
                    lines=[line_of(starts, p) for p in ops][:20])
            for m in re.finditer(r"\btry!", code):
                add(m.start(), "try-bang", "high",
                    "try! crashes on any thrown error; use do/catch, try?, or propagate")

        # main queue inside async
        probes = [m.start() for m in re.finditer(r"\bDispatchQueue\s*\.\s*main\s*\.\s*async\b", code)]
        hits, bodies = brace_pass(code, starts, probes, max_body)
        for p in hits:
            add(p, "main-queue-in-async", "warn",
                "DispatchQueue.main.async inside an async context; annotate the code @MainActor or await a @MainActor function")

        # print
        if not skip_rules and os.path.basename(f) != "Package.swift":
            dbg = debug_lines(code)
            for m in re.finditer(r"(?<![\w.])(?:print|debugPrint)\s*\(", code):
                ls = code.rfind("\n", 0, m.start()) + 1
                if re.search(r"\bfunc\s+$", code[ls:m.start()]):
                    continue
                if line_of(starts, m.start()) in dbg:
                    continue
                add(m.start(), "print-in-app-code", "warn",
                    "print in non-test code; use os.Logger (or wrap in #if DEBUG)")

        # giant bodies
        for start, end, nonblank in bodies:
            if nonblank > max_body:
                sev = "high" if nonblank > max_body * BODY_HIGH_FACTOR else "warn"
                add(None, "giant-view-body", sev,
                    "var body has %d non-blank code lines (limit %d); extract subviews as separate structs"
                    % (nonblank, max_body),
                    line=start, body_lines=nonblank, end_line=end)

        # @State reference types
        for m in STATE_RE.finditer(code):
            tname = m.group(2) or m.group(3)
            if not tname:
                continue
            tname = tname.split(".")[-1]
            if tname in classes:
                kind = resolve_kind(tname, classes)
                if kind == "observable":
                    continue
                if kind == "object":
                    add(m.start(), "state-reference-type", "high",
                        "@State holds ObservableObject class %s; use @StateObject, or migrate the class to @Observable (verify minimum OS)" % tname,
                        confidence="high")
                else:
                    add(m.start(), "state-reference-type", "high",
                        "@State holds class %s that is neither @Observable nor ObservableObject; mutations will not refresh the view and the instance is not owned reliably" % tname,
                        confidence="high")
            elif tname.endswith(SUFFIX_HINT):
                add(m.start(), "state-reference-type", "warn",
                    "@State holds %s, which looks like a reference-type model by name (class not found in scanned files); check it is @Observable" % tname,
                    confidence="medium")

        per_file.append({"file": shown, "code_lines": code_lines, "is_test_file": test,
                         "force_unwraps": force_count, "force_unwraps_per_100_lines": density})

    findings.sort(key=lambda d: (d["file"], d["line"], d["rule"]))
    counts = {}
    for d in findings:
        counts[d["rule"]] = counts.get(d["rule"], 0) + 1
    kept, seen, omitted = [], {}, {}
    for d in findings:
        seen[d["rule"]] = seen.get(d["rule"], 0) + 1
        if seen[d["rule"]] <= max_per_rule:
            kept.append(d)
        else:
            omitted[d["rule"]] = omitted.get(d["rule"], 0) + 1
    return {
        "tool": "swift_scan",
        "version": VERSION,
        "files_scanned": len(files),
        "test_files_skipped_for_rules": tests_skipped,
        "thresholds": {"min_force_count": MIN_FORCE_COUNT, "force_per_100_lines": density_limit,
                       "max_body_lines": max_body, "body_high_factor": BODY_HIGH_FACTOR},
        "total_findings": len(findings),
        "counts_by_rule": dict(sorted(counts.items())),
        "omitted_by_rule": omitted,
        "findings": kept,
        "per_file": sorted(per_file, key=lambda d: d["file"]),
        "limits": "lexical scan: no type information; see SKILL.md Limits",
    }


def main(argv=None):
    ap = JsonArgParser(description="Scan Swift files for documented anti-patterns.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--max-body-lines", type=int, default=DEFAULT_MAX_BODY_LINES)
    ap.add_argument("--force-density", type=float, default=DEFAULT_FORCE_DENSITY)
    ap.add_argument("--include-tests", action="store_true")
    ap.add_argument("--max-per-rule", type=int, default=DEFAULT_MAX_PER_RULE)
    try:
        args = ap.parse_args(argv)
        report = scan(args.paths, args.max_body_lines, args.force_density,
                      args.include_tests, args.max_per_rule)
    except ScanArgError as exc:
        print(json.dumps({"error": str(exc)}, allow_nan=False))
        return 2
    print(json.dumps(report, indent=2, allow_nan=False, ensure_ascii=True))
    return 1 if report["total_findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
