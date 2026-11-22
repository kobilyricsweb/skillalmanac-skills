#!/usr/bin/env python3
"""Scan Flutter / Dart .dart files for a fixed set of documented anti-patterns.

    python flutter_scan.py <file-or-folder> [<file-or-folder> ...]

Reads the paths it is given (folders are walked for .dart). Writes nothing.
Prints exactly one JSON object to stdout. Errors go to stderr as one plain sentence.

Exit codes
    0 = no finding with severity "warn" (info findings may exist)
    1 = at least one "warn" finding
    2 = usage error, or none of the given paths exists / holds a readable .dart file

JSON contract (schema_version 1)
    {"schema_version": 1, "tool": "flutter_scan", "files_scanned": int,
     "findings": [{"file": str, "line": int, "rule": str,
                   "severity": "warn" | "info", "confidence": "high" | "medium" | "low",
                   "match": str, "why": str, "fix": str}],
     "counts_by_rule": {rule: int}, "summary": {"warn": int, "info": int},
     "skipped": [{"file": str, "reason": str}], "limits": [str]}
    Findings are sorted by file, line, rule. File paths use forward slashes and are
    relative to the path argument they were found under (a file argument keeps the
    path as it was given). Every finding is a prompt to look, not a verdict.

Rules
    missing-const           widget constructor call whose arguments look all-literal, without const
    print-in-lib            print() / debugPrint() outside tests and CLI folders, not guarded by kDebugMode
    setstate-in-build       setState() called directly in a build method (not inside a callback)
    long-build-method       build method longer than a line threshold
    null-assertion-density  many postfix ! null assertions in one file
    unawaited-future        statement that calls a Future-returning function and drops the result

The scan is regex based. It does not parse Dart, resolve types, or read analyzer output.
"""
import json
import os
import re
import sys

SCHEMA_VERSION = 1
EXTENSIONS = (".dart",)
# Folders that never hold the project's own hand-written Dart source.
SKIP_DIRS = {".dart_tool", ".git", ".idea", "build", ".pub-cache", ".symlinks", "Pods",
             "node_modules", "ios", "android", "macos", "linux", "windows"}
GENERATED_SUFFIXES = (".g.dart", ".freezed.dart", ".gr.dart", ".mocks.dart", ".pb.dart",
                      ".chopper.dart", ".config.dart")
GENERATED_NAMES = {"generated_plugin_registrant.dart", "firebase_options.dart"}
# Path segments that mark test code or command-line code, where print is legitimate.
TEST_SEGMENTS = {"test", "integration_test", "test_driver"}
CLI_SEGMENTS = {"bin", "tool", "tools", "scripts"}

# A build method longer than this many lines is reported as info (a prompt to extract widgets)
# and above the second value as warn. Working values from review practice, not measured optima.
BUILD_INFO_LINES = 80
BUILD_WARN_LINES = 150
# Postfix ! assertions per file. Warn needs both the count and the density per 100 code lines,
# so a long file with a few assertions is not flagged. Working values.
BANG_INFO_COUNT = 4
BANG_WARN_COUNT = 8
BANG_WARN_PER_100 = 2.0

# Widgets that have const constructors and are typical const candidates when all arguments are literal.
CONST_WIDGETS = ("Text", "Icon", "SizedBox", "Padding", "Center", "Align", "Divider", "Spacer",
                 "Container", "Row", "Column", "Expanded", "Flexible", "Card", "ListTile",
                 "CircleAvatar", "Placeholder", "VerticalDivider", "Opacity", "ColoredBox")
# Capitalised names that may appear inside a const-able argument list with high confidence.
KNOWN_CONST_ROOTS = {
    "Icons", "Colors", "EdgeInsets", "TextStyle", "FontWeight", "FontStyle", "Alignment", "Duration",
    "Offset", "Size", "Radius", "BorderRadius", "MainAxisAlignment", "CrossAxisAlignment",
    "MainAxisSize", "TextAlign", "TextOverflow", "BoxFit", "Axis", "Clip", "Curves",
    "Color", "BorderSide", "Border", "TextDecoration", "VerticalDirection", "Widget",
} | set(CONST_WIDGETS)
# Roots that are never constant, so an argument list holding them is not const-able.
NEVER_CONST_ROOTS = {"DateTime", "Random", "Uuid", "File", "Directory", "Platform"}
NEVER_CONST_MEMBER = re.compile(r"\.(?:of|maybeOf|now|parse|tryParse)\b")

# Future-returning calls that are almost always a mistake to drop (high confidence).
BUILTIN_FUTURE_CALL = (r"(?:Future\.(?:delayed|wait|value|microtask|sync|forEach|doWhile)"
                       r"|http\.(?:get|post|put|patch|delete|head|read|readBytes|send)"
                       r"|launchUrl|launchUrlString|canLaunchUrl|Clipboard\.setData"
                       r"|SharedPreferences\.getInstance)")
# Declared Future names that are commonly also non-Future methods elsewhere.
FUTURE_NAME_STOPLIST = {"dispose", "close", "cancel", "build", "initState", "main", "reset", "run"}
CONTROL_WORDS = {"if", "for", "while", "switch", "catch"}
BLOCK_WORDS = ("else", "do", "try", "finally")

LIMITS = [
    "Regex scan, not a parser or the Dart analyzer: it can miss patterns built dynamically and can flag harmless code. Run flutter analyze for the authoritative lints.",
    "missing-const only sees calls to a fixed list of common widgets and judges constness from the argument text; it cannot resolve whether a user-defined constructor or constant is const. Confidence low means a non-SDK name appeared.",
    "setstate-in-build only treats code outside any nested closure as direct; a setState reached through a helper method called from build is invisible.",
    "unawaited-future knows only Futures declared in the same file plus a short built-in list; a Future-returning call from another file is invisible, and a same-named non-Future method in the same file can be flagged.",
    "null-assertion-density counts postfix ! outside comments and strings; a ! inside a ${...} interpolation is masked and not counted.",
    "long-build-method measures only methods named build with a BuildContext parameter; helper methods such as _buildHeader are not measured.",
    "A call on the line after a braceless if or else-if condition is not treated as a statement start and is not checked by unawaited-future.",
    "Test and command-line folders (test, integration_test, bin, tool) are exempt from print-in-lib; the decision uses the path as given, so name the folder or file path from the project root. Generated files are skipped.",
    "Absence of findings is not evidence of good performance or correctness; profile and test on a real device.",
]


def mask(raw):
    """Return text of the same length with comments blanked and string bodies masked.

    String bodies become '_' characters, or '$' characters when the string interpolates,
    so the quotes stay visible and later regexes never match text inside strings.
    Newlines are always kept, so line numbers stay correct.
    """
    out = list(raw)
    n = len(raw)
    i = 0

    def blank(a, b):
        for k in range(a, min(b, n)):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = raw[i]
        if c == "/" and raw.startswith("//", i):
            j = raw.find("\n", i)
            j = n if j == -1 else j
            blank(i, j)
            i = j
            continue
        if c == "/" and raw.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if raw.startswith("/*", j):
                    depth += 1
                    j += 2
                elif raw.startswith("*/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            blank(i, j)
            i = j
            continue
        if c in "'\"":
            is_raw = i > 0 and raw[i - 1] == "r" and (i < 2 or not (raw[i - 2].isalnum() or raw[i - 2] == "_"))
            quote = c * 3 if raw.startswith(c * 3, i) else c
            body_start = i + len(quote)
            j = body_start
            interp = False
            closed = False
            while j < n:
                if not is_raw and raw[j] == "\\":
                    j += 2
                    continue
                if raw.startswith(quote, j):
                    closed = True
                    break
                if len(quote) == 1 and raw[j] == "\n":
                    break
                if not is_raw and raw[j] == "$":
                    interp = True
                    if raw.startswith("${", j):
                        depth = 1
                        j += 2
                        while j < n and depth:
                            if raw[j] == "{":
                                depth += 1
                            elif raw[j] == "}":
                                depth -= 1
                            j += 1
                        continue
                j += 1
            fill = "$" if interp else "_"
            for k in range(body_start, min(j, n)):
                if out[k] != "\n":
                    out[k] = fill
            i = j + len(quote) if closed else j
            continue
        i += 1
    return "".join(out)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def match_forward(text, open_pos):
    """Index of the bracket closing the one at open_pos, or None."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    for i in range(open_pos, len(text)):
        ch = text[i]
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in ")]}":
            if not stack or stack.pop() != ch:
                return None
            if not stack:
                return i
    return None


def match_backward(text, close_pos):
    """Index of the '(' matching the ')' at close_pos, or None."""
    depth = 0
    for i in range(close_pos, -1, -1):
        if text[i] == ")":
            depth += 1
        elif text[i] == "(":
            depth -= 1
            if depth == 0:
                return i
    return None


def finding(rel, line, rule, severity, confidence, match, why, fix):
    return {"file": rel, "line": line, "rule": rule, "severity": severity,
            "confidence": confidence, "match": match, "why": why, "fix": fix}


def squash(s, width=70):
    return " ".join(s.split())[:width]


# ---------------------------------------------------------------- print-in-lib

def path_segments(rel):
    return set(rel.replace("\\", "/").split("/"))


def is_test_path(rel):
    base = os.path.basename(rel)
    return bool(path_segments(rel) & TEST_SEGMENTS) or base.endswith("_test.dart")


def scan_print(rel, text, out):
    if is_test_path(rel) or path_segments(rel) & CLI_SEGMENTS:
        return
    lines = text.split("\n")
    for m in re.finditer(r"(?<![\w.$])(print|debugPrint)\s*\(", text):
        before = text[max(0, m.start() - 40):m.start()]
        if re.search(r"\b(?:void|int|bool|String|dynamic|Future(?:<[^>]*>)?|FutureOr)\s+$", before):
            continue  # a declaration named print, not a call
        ln = line_of(text, m.start())
        window = lines[max(0, ln - 3):ln]
        if any("kDebugMode" in w for w in window):
            continue
        name = m.group(1)
        if name == "print":
            out.append(finding(
                rel, ln, "print-in-lib", "warn", "high", "print(...)",
                "print writes to the device log in release builds too and can leak user data.",
                "Delete it, guard it with if (kDebugMode), or use a logger with levels that is silent in release."))
        else:
            out.append(finding(
                rel, ln, "print-in-lib", "info", "medium", "debugPrint(...)",
                "debugPrint is a throttled print and still writes a log line unless the app replaces it (verify (unconfirmed) for the current release behaviour).",
                "Guard it with if (kDebugMode) or route it through a logger."))


# ------------------------------------------------------------- build methods

BUILD_RE = re.compile(r"\bWidget\s+build\s*\(\s*(?:final\s+)?BuildContext\b")


def build_methods(text):
    """Yield (signature_pos, body_start, body_end) for each build method found."""
    for m in BUILD_RE.finditer(text):
        open_paren = text.find("(", m.start())
        close_paren = match_forward(text, open_paren)
        if close_paren is None:
            continue
        j = close_paren + 1
        while j < len(text) and text[j].isspace():
            j += 1
        if j < len(text) and text[j] == "{":
            end = match_forward(text, j)
            if end is not None:
                yield m.start(), j, end
        elif text.startswith("=>", j):
            k, depth = j + 2, 0
            while k < len(text):
                ch = text[k]
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
                elif ch == ";" and depth <= 0:
                    break
                k += 1
            yield m.start(), j, k


def brace_kind(text, pos, floor):
    """Classify the '{' at pos as 'closure' or 'block' from the text before it."""
    before = text[floor:pos].rstrip()
    if before.endswith("=>"):
        return "closure"
    if re.search(r"\basync\*?$|\bsync\*$", before):
        return "closure"
    if re.search(r"\b(?:" + "|".join(BLOCK_WORDS) + r")$", before):
        return "block"
    if before.endswith(")"):
        op = match_backward(text, floor + len(before) - 1)
        if op is not None:
            word = re.search(r"(\w+)\s*$", text[floor:op])
            if word and word.group(1) in CONTROL_WORDS:
                return "block"
            return "closure"
    return "block"


def scan_build(rel, text, out):
    for sig, start, end in build_methods(text):
        first, last = line_of(text, sig), line_of(text, end)
        length = last - first + 1
        if length > BUILD_INFO_LINES:
            warn = length > BUILD_WARN_LINES
            out.append(finding(
                rel, first, "long-build-method", "warn" if warn else "info", "high",
                "build method is %d lines" % length,
                "A long build method rebuilds as one unit, hides which part changed, and is hard to read and test.",
                "Extract sections into small widget classes (not helper methods) with const constructors; "
                "threshold %d lines info, %d warn." % (BUILD_INFO_LINES, BUILD_WARN_LINES)))
        starts = {m.start() for m in re.finditer(r"\bsetState\s*\(", text[start:end + 1])}
        starts = {s + start for s in starts}
        if not starts:
            continue
        stack = []
        for i in range(start, end + 1):
            ch = text[i]
            if ch == "{":
                stack.append(brace_kind(text, i, start) if i != start else "block")
            elif ch == "}":
                if stack:
                    stack.pop()
            elif i in starts:
                if "closure" in stack:
                    continue
                if re.search(r"=>\s*$", text[start:i]):
                    continue
                out.append(finding(
                    rel, line_of(text, i), "setstate-in-build", "warn", "high", "setState(...) directly in build",
                    "Calling setState while building schedules another build during the build and can loop or throw.",
                    "Move the change to an event handler, initState, or a post-frame callback; derive the value in build instead."))


# ------------------------------------------------------- null-assertion density

def scan_bangs(rel, text, out):
    if is_test_path(rel):
        return
    hits = [m.start() for m in re.finditer(r"(?<=[\w)\]])!(?!=)", text)]
    code_lines = sum(1 for ln in text.split("\n") if ln.strip())
    if not hits or code_lines == 0:
        return
    n = len(hits)
    per100 = n * 100.0 / code_lines
    if n >= BANG_WARN_COUNT and per100 >= BANG_WARN_PER_100:
        sev = "warn"
    elif n >= BANG_INFO_COUNT:
        sev = "info"
    else:
        return
    out.append(finding(
        rel, line_of(text, hits[0]), "null-assertion-density", sev, "medium",
        "%d null assertions (!) in %d code lines (%.1f per 100)" % (n, code_lines, per100),
        "Each ! throws at runtime when the value is null; many of them mean the types are not modelling absence.",
        "Replace with a null check and early return, ?? with a default, a local final after a check, or make the field non-nullable."))


# ----------------------------------------------------------------- missing const

def const_spans(text):
    spans = []
    for m in re.finditer(r"\bconst\s+[\w.<>, ?]*?([(\[{])", text):
        op = m.end() - 1
        cl = match_forward(text, op)
        if cl is not None:
            spans.append((op, cl))
    return spans


def literal_args(args):
    """Return None when args are not const-able, else 'high' or 'low' confidence."""
    if "=>" in args or "{" in args:
        return None
    if NEVER_CONST_MEMBER.search(args):
        return None
    s = re.sub(r"(['\"])[_\s]*\1", " ", args)          # plain, non-interpolated strings
    s = re.sub(r"<[^<>()]*>", " ", s)                    # generic arguments
    roots = re.findall(r"\b([A-Z]\w*)(?:\.\w+)*", s)
    if any(r in NEVER_CONST_ROOTS for r in roots):
        return None
    if re.search(r"\b[A-Z]\w*(?:\.\w+)*\s*\[", s):       # Colors.red[100] is not constant
        return None
    s = re.sub(r"\b[A-Z]\w*(?:\.\w+)*", " ", s)
    s = re.sub(r"\b[a-z]\w*\s*:", " ", s)                # argument labels
    s = re.sub(r"\b(?:true|false|null)\b", " ", s)
    s = re.sub(r"\d+(?:\.\d+)?", " ", s)
    if re.search(r"[A-Za-z_$]", s):
        return None
    return "high" if all(r in KNOWN_CONST_ROOTS for r in roots) else "low"


def scan_const(rel, text, out, raw):
    cspans = const_spans(text)
    kept = []
    pattern = r"(?<![\w.$])(" + "|".join(CONST_WIDGETS) + r")\s*\("
    for m in re.finditer(pattern, text):
        start = m.start()
        if re.search(r"\b(?:const|new)\s+$", text[max(0, start - 8):start]):
            continue
        if any(a < start < b for a, b in cspans) or any(a <= start <= b for a, b in kept):
            continue
        stmt_start = max(text.rfind(";", 0, start), text.rfind("{", 0, start), text.rfind("}", 0, start)) + 1
        if re.match(r"\s*(?:@\w+\s+)?(?:static\s+)?const\b", text[stmt_start:start]):
            continue
        op = m.end() - 1
        cl = match_forward(text, op)
        if cl is None:
            continue
        conf = literal_args(text[op + 1:cl])
        if conf is None:
            continue
        kept.append((start, cl))
        out.append(finding(
            rel, line_of(text, start), "missing-const", "info", conf, squash(raw[start:cl + 1]),
            "A widget built from literal arguments can be a compile-time constant; without const it is rebuilt and reallocated on every parent build.",
            "Add const before the constructor (and to the enclosing widget when every child is const)."
            + (" Confidence is low because a non-SDK name appears; confirm that constructor is const." if conf == "low" else "")))


# ------------------------------------------------------------- unawaited futures

def scan_unawaited(rel, text, out, raw):
    declared = set(re.findall(r"\bFuture(?:<[^;{(=]*?>)?\s+([A-Za-z_]\w*)\s*\(", text))
    declared -= FUTURE_NAME_STOPLIST
    parts = []
    if declared:
        parts.append(r"(?P<dec>(?:[A-Za-z_]\w*\.)*(?:" + "|".join(sorted(map(re.escape, declared))) + r"))")
    parts.append(r"(?P<bi>" + BUILTIN_FUTURE_CALL + r")")
    pattern = re.compile(r"(?m)^[ \t]*(?:" + "|".join(parts) + r")\s*\(")
    lines = text.split("\n")
    for m in pattern.finditer(text):
        ln = line_of(text, m.start())
        prev = ""
        for k in range(ln - 2, -1, -1):
            if lines[k].strip():
                prev = lines[k].rstrip()
                break
        if prev and not (prev.endswith(";") or prev.endswith("{") or prev.endswith("}") or prev.strip() == "else"):
            continue
        op = m.end() - 1
        cl = match_forward(text, op)
        if cl is None:
            continue
        k = cl + 1
        while k < len(text) and text[k].isspace():
            k += 1
        if k >= len(text) or text[k] != ";":
            continue
        builtin = m.group("bi") is not None
        name = (m.group("bi") or m.group("dec")).split(".")[-1]
        out.append(finding(
            rel, ln, "unawaited-future", "warn", "high" if builtin else "medium",
            squash(raw[m.start():cl + 1]),
            "The Future returned by %s() is dropped; its errors surface as unhandled exceptions and the code after it does not wait." % name,
            "await it, or call unawaited(...) from dart:async when fire-and-forget is intended, and handle its errors inside."))


# ------------------------------------------------------------------ plumbing

def collect(paths):
    files, skipped = [], []
    for p in paths:
        if os.path.isfile(p):
            if p.endswith(EXTENSIONS):
                files.append((p.replace("\\", "/"), p))
            else:
                skipped.append({"file": p.replace("\\", "/"), "reason": "not a .dart file"})
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for n in sorted(names):
                    if n.endswith(EXTENSIONS):
                        full = os.path.join(root, n)
                        files.append((os.path.relpath(full, p).replace("\\", "/"), full))
        else:
            skipped.append({"file": p.replace("\\", "/"), "reason": "path does not exist"})
    return files, skipped


def is_generated(rel, raw):
    base = os.path.basename(rel)
    if base.endswith(GENERATED_SUFFIXES) or base in GENERATED_NAMES:
        return True
    head = "\n".join(raw.split("\n")[:5]).upper()
    return "GENERATED CODE" in head or "DO NOT MODIFY BY HAND" in head


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.stderr.write("Usage: flutter_scan.py <file-or-folder> [<file-or-folder> ...]\n")
        return 2
    files, skipped = collect(argv)
    if not files:
        sys.stderr.write("No .dart files found in the given paths; pass a file or a folder that holds some.\n")
        return 2
    findings = []
    scanned = 0
    for rel, full in files:
        try:
            with open(full, encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
        except OSError as exc:
            skipped.append({"file": rel, "reason": "unreadable: %s" % exc.strerror})
            continue
        if not raw.strip():
            skipped.append({"file": rel, "reason": "empty file"})
            continue
        if is_generated(rel, raw):
            skipped.append({"file": rel, "reason": "generated file"})
            continue
        scanned += 1
        text = mask(raw)
        scan_print(rel, text, findings)
        scan_build(rel, text, findings)
        scan_bangs(rel, text, findings)
        scan_const(rel, text, findings, raw)
        scan_unawaited(rel, text, findings, raw)
    if scanned == 0:
        sys.stderr.write("Every .dart file found was empty, unreadable or generated; nothing was scanned.\n")
        return 2
    seen, unique = set(), []
    for f in findings:
        key = (f["file"], f["line"], f["rule"], f["match"])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    unique.sort(key=lambda f: (f["file"], f["line"], f["rule"]))
    counts = {}
    for f in unique:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    summary = {"warn": sum(1 for f in unique if f["severity"] == "warn"),
               "info": sum(1 for f in unique if f["severity"] == "info")}
    report = {"schema_version": SCHEMA_VERSION, "tool": "flutter_scan", "files_scanned": scanned,
              "findings": unique, "counts_by_rule": dict(sorted(counts.items())), "summary": summary,
              "skipped": skipped, "limits": LIMITS}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if summary["warn"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
