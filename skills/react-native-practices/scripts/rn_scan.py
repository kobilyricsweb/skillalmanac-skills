#!/usr/bin/env python3
"""Scan React Native / Expo .tsx and .jsx files for a fixed set of documented anti-patterns.

    python rn_scan.py <file-or-folder> [<file-or-folder> ...]

Reads the paths it is given (folders are walked for .tsx and .jsx). Writes nothing.
Prints exactly one JSON object to stdout. Errors go to stderr as one plain sentence.

Exit codes
    0 = no finding with severity "warn" (info findings may exist)
    1 = at least one "warn" finding
    2 = usage error, or none of the given paths exists / holds a .tsx or .jsx file

JSON contract (schema_version 1)
    {"schema_version": 1, "tool": "rn_scan", "files_scanned": int,
     "findings": [{"file": str, "line": int, "rule": str,
                   "severity": "warn" | "info", "confidence": "high" | "medium" | "low",
                   "match": str, "why": str, "fix": str}],
     "counts_by_rule": {rule: int}, "summary": {"warn": int, "info": int},
     "skipped": [{"file": str, "reason": str}], "limits": [str]}
    Findings are sorted by file, line, rule. File paths use forward slashes and are
    relative to the path argument they were found under (a file argument keeps its
    base name). Every finding is a prompt for a human or agent to look, not a verdict.

Rules
    scrollview-map          .map() inside a ScrollView body (renders every row at once)
    inline-renderitem       renderItem given an inline function instead of a stable reference
    missing-keyextractor    list component without keyExtractor
    index-as-key            keyExtractor or key= built from the row index
    console-log             console.log / debug / info left in code (not guarded by __DEV__)
    platform-literal-invalid  Platform.OS compared with a string that is not a real value
    platform-magic-number   Platform.OS ternary that hard-codes a number
    platform-branch-density a file with many Platform.OS checks

The scan is regex-based. It does not parse TypeScript and cannot know array sizes,
types, memoisation, or whether a prop arrives through a spread.
"""
import json
import os
import re
import sys

SCHEMA_VERSION = 1
EXTENSIONS = (".tsx", ".jsx")
# Folders that never hold the project's own source.
SKIP_DIRS = {"node_modules", ".git", ".expo", "build", "dist", "Pods", ".next", "coverage", "web-build"}
# Values Platform.OS can actually take in React Native / Expo.
REAL_PLATFORMS = {"ios", "android", "web", "windows", "macos"}
LIST_COMPONENTS = ("FlatList", "SectionList", "FlashList", "MasonryFlashList", "VirtualizedList")
# More than this many Platform.OS checks in one file suggests a platform split
# (Platform.select in one style module, or .ios/.android files). Working value, not measured.
PLATFORM_DENSITY_LIMIT = 3
# An inline renderItem body longer than this many characters is treated as a warn,
# because a big un-memoised row is where the cost shows up. Working value, not measured.
BIG_INLINE_RENDER_CHARS = 400
# Array.from({length: N}).map with N at or above this is treated as a large list.
LARGE_LITERAL_LENGTH = 50
# Names that usually hold server or user data (likely to grow) versus short static lists.
DATA_HINT = re.compile(r"(data|items|results|list|rows|users|posts|messages|products|feed|comments|orders|notifications|history|songs|contacts|entries|records)$", re.I)
STATIC_HINT = re.compile(r"(tabs|options|steps|links|menu|categories|chips|filters|tags|buttons|icons|sections|slides|faq|faqs)$", re.I)

LIMITS = [
    "Regex scan, not a parser: it can miss patterns that are built dynamically and can flag harmless code.",
    "It cannot know how long an array is; scrollview-map confidence is a naming guess unless a literal length is visible.",
    "Props arriving through a spread ({...props}) are invisible; such tags get confidence low.",
    "Only .tsx and .jsx files are read; .ts, .js and generated files are not.",
    "Comments are masked with a simple rule, and console-log / Platform.OS matches that start inside a quoted string literal are ignored (a ' or \" string ends at the line end; a template literal is treated as one string, so a Platform.OS check inside ${...} is missed).",
    "Absence of findings is not evidence of good performance; measure on a release build on a real device.",
]


def mask_comments(text):
    """Blank out comments but keep newlines, so line numbers stay correct."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"/\*.*?\*/", blank, text, flags=re.S)
    # A // starts a comment only after whitespace or punctuation, so "https://x" survives.
    return re.sub(r"(?m)(^|(?<=[\s;,{}()]))//.*$", blank, text)


def string_spans(text):
    """Return (start, end) spans of quoted string literals in comment-masked text.

    ' and " strings end at the line end (an apostrophe in JSX text such as
    "Don't" then cannot swallow later code); backtick strings may span lines.
    """
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"`":
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\\":
                    j += 1
                elif text[j] == "\n" and c != "`":
                    j = -1
                    break
                j += 1
            if j == -1 or j >= n:
                i += 1
                continue
            spans.append((i, j + 1))
            i = j + 1
        else:
            i += 1
    return spans


def in_string(spans, pos):
    return any(a <= pos < b for a, b in spans)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def tag_end(text, start):
    """Return the index just past the '>' that closes the JSX opening tag starting at `start`."""
    i = start + 1
    n = len(text)
    # skip the tag name
    while i < n and (text[i].isalnum() or text[i] in "._"):
        i += 1
    # TypeScript generic such as <FlatList<Item>
    if i < n and text[i] == "<":
        depth = 0
        while i < n:
            if text[i] == "<":
                depth += 1
            elif text[i] == ">":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
    brace = 0
    quote = None
    while i < n:
        c = text[i]
        if quote:
            if c == quote and text[i - 1] != "\\":
                quote = None
        elif c in "\"'" and brace == 0:
            quote = c
        elif c == "{":
            brace += 1
        elif c == "}":
            brace -= 1
        elif c == ">" and brace == 0:
            return i + 1
        i += 1
    return None


def balanced(text, open_pos):
    """Given the index of '{', return the index of its matching '}' or None."""
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return None


def snippet(text, start, width=70):
    s = " ".join(text[start:start + width].split())
    return s


def finding(rel, line, rule, severity, confidence, match, why, fix):
    return {"file": rel, "line": line, "rule": rule, "severity": severity,
            "confidence": confidence, "match": match, "why": why, "fix": fix}


def scan_scrollview(rel, text, out):
    for m in re.finditer(r"<ScrollView\b", text):
        end = tag_end(text, m.start())
        if end is None or text[end - 2:end] == "/>":
            continue
        close = text.find("</ScrollView>", end)
        if close == -1:
            continue
        body = text[end:close]
        for mm in re.finditer(r"([\w$.?\[\]]*(?:\([^()]*\))?)\.map\(", body):
            src = mm.group(1) or "(expression)"
            tail = src.split(".")[-1]
            lit = re.search(r"length:\s*(\d+)", mm.group(0))
            if lit and int(lit.group(1)) >= LARGE_LITERAL_LENGTH:
                conf = "high"
            elif STATIC_HINT.search(tail):
                conf = "low"
            elif DATA_HINT.search(tail):
                conf = "high"
            else:
                conf = "medium"
            sev = "warn" if conf in ("high", "medium") else "info"
            out.append(finding(
                rel, line_of(text, end + mm.start()), "scrollview-map", sev, conf,
                snippet(body, mm.start()),
                "ScrollView mounts every child at once; a long mapped list costs memory and first-render time.",
                "Use FlatList or FlashList when the list can exceed about a screenful or two; keep ScrollView for short, fixed content."))


def scan_lists(rel, text, out):
    pattern = r"<(?:Animated\.)?(?:" + "|".join(LIST_COMPONENTS) + r")\b"
    for m in re.finditer(pattern, text):
        end = tag_end(text, m.start())
        if end is None:
            continue
        tag = text[m.start():end]
        spread = bool(re.search(r"\{\s*\.\.\.", tag))
        name = re.match(r"<([\w.]+)", tag).group(1)
        line = line_of(text, m.start())
        # keyExtractor
        if not re.search(r"\bkeyExtractor\s*=", tag):
            conf = "low" if spread else "medium"
            out.append(finding(
                rel, line, "missing-keyextractor", "warn" if conf == "medium" else "info", conf,
                "<%s ... (no keyExtractor)" % name,
                "Without keyExtractor the list falls back to item.key, then item.id, then the row index; rows lose state when data is reordered or removed.",
                "Add keyExtractor={(item) => item.id} using a stable unique field."))
        else:
            km = re.search(r"\bkeyExtractor\s*=\s*\{", tag)
            ob = tag.find("{", km.start())
            cb = balanced(tag, ob)
            expr = tag[ob + 1:cb] if cb else ""
            ix = re.search(r"\(\s*_\w*\s*,\s*(\w+)\s*\)\s*=>\s*(?:String\(|`\$\{)?\s*\1\b", expr)
            if ix:
                out.append(finding(
                    rel, line_of(text, m.start() + km.start()), "index-as-key", "warn", "high",
                    snippet(tag, km.start()),
                    "An index key changes identity when rows are inserted, removed or reordered.",
                    "Return a stable id from the item instead of its position."))
        # renderItem
        rm = re.search(r"\brenderItem\s*=\s*\{", tag)
        if rm:
            ob = tag.find("{", rm.start())
            cb = balanced(tag, ob)
            expr = tag[ob + 1:cb] if cb else ""
            stripped = expr.strip()
            if re.match(r"(?:async\s+)?(?:\(|function\b|\w+\s*=>)", stripped):
                big = len(stripped) > BIG_INLINE_RENDER_CHARS
                out.append(finding(
                    rel, line_of(text, m.start() + rm.start()), "inline-renderitem",
                    "warn" if big else "info", "high" if big else "medium",
                    snippet(tag, rm.start()),
                    "A new function is created on every parent render; with a large inline row, every row re-renders each time.",
                    "Move the row to a component wrapped in React.memo and pass a stable renderItem (module-level function or useCallback)."))


def scan_index_keys(rel, text, out):
    for m in re.finditer(r"\bkey=\{\s*(?:index|idx|i)\s*\}", text):
        out.append(finding(
            rel, line_of(text, m.start()), "index-as-key", "info", "medium", m.group(0),
            "An index key is only safe for lists that are never reordered, filtered or edited.",
            "Use a stable id from the data when the list can change."))


def scan_console(rel, text, out, spans):
    base = os.path.basename(rel)
    if re.search(r"\.(test|spec|stories)\.|__tests__|__mocks__", rel):
        return
    lines = text.split("\n")
    for m in re.finditer(r"\bconsole\.(log|debug|info)\s*\(", text):
        if in_string(spans, m.start()):
            continue
        ln = line_of(text, m.start())
        here = lines[ln - 1]
        prev = lines[ln - 2] if ln >= 2 else ""
        if "__DEV__" in here or "__DEV__" in prev:
            continue
        out.append(finding(
            rel, ln, "console-log", "warn", "high", m.group(0) + "...)",
            "Console calls run in release builds too and can leak data into device logs.",
            "Delete it, wrap it in if (__DEV__), or strip console calls in the production Babel config."))


def scan_platform(rel, text, out, spans):
    count = 0
    first = None
    for m in re.finditer(r"\bPlatform\.OS\s*([!=]==?)\s*(['\"`])([^'\"`]*)\2", text):
        if in_string(spans, m.start()):
            continue
        count += 1
        first = first or line_of(text, m.start())
        val = m.group(3)
        if val not in REAL_PLATFORMS:
            out.append(finding(
                rel, line_of(text, m.start()), "platform-literal-invalid", "warn", "high", m.group(0),
                "Platform.OS is lowercase and limited to ios, android, web, windows, macos; this comparison is never what you intend.",
                "Compare with one of: %s." % ", ".join(sorted(REAL_PLATFORMS))))
        tern = re.match(r"\s*\?\s*-?\d+(?:\.\d+)?\s*:\s*-?\d+(?:\.\d+)?", text[m.end():m.end() + 40])
        if tern:
            out.append(finding(
                rel, line_of(text, m.start()), "platform-magic-number", "info", "medium",
                " ".join(text[m.start():m.end() + tern.end()].split()),
                "A fixed number per platform usually stands in for status bar, notch or keyboard height, which vary by device.",
                "Use useSafeAreaInsets() or a named Platform.select constant with a comment; avoid bare numbers."))
    for m in re.finditer(r"\bPlatform\.select\s*\(", text):
        if in_string(spans, m.start()):
            continue
        count += 1
        first = first or line_of(text, m.start())
    if count > PLATFORM_DENSITY_LIMIT:
        out.append(finding(
            rel, first, "platform-branch-density", "info", "medium",
            "%d Platform.OS / Platform.select uses" % count,
            "Many scattered platform checks in one file make behaviour hard to follow and test.",
            "Gather them in one module, or split into .ios.tsx / .android.tsx files when the branches differ a lot."))


def collect(paths):
    files, skipped = [], []
    for p in paths:
        if os.path.isfile(p):
            if p.endswith(EXTENSIONS):
                files.append((os.path.basename(p), p))
            else:
                skipped.append({"file": p.replace("\\", "/"), "reason": "not a .tsx or .jsx file"})
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


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.stderr.write("Usage: rn_scan.py <file-or-folder> [<file-or-folder> ...]\n")
        return 2
    files, skipped = collect(argv)
    if not files:
        sys.stderr.write("No .tsx or .jsx files found in the given paths; pass a file or a folder that holds some.\n")
        return 2
    findings = []
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
        text = mask_comments(raw)
        scan_scrollview(rel, text, findings)
        scan_lists(rel, text, findings)
        scan_index_keys(rel, text, findings)
        spans = string_spans(text)
        scan_console(rel, text, findings, spans)
        scan_platform(rel, text, findings, spans)
    # one finding per (file, line, rule, match) is enough
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
    report = {"schema_version": SCHEMA_VERSION, "tool": "rn_scan", "files_scanned": len(files) - sum(1 for s in skipped if s["reason"].startswith(("unreadable", "empty"))),
              "findings": unique, "counts_by_rule": dict(sorted(counts.items())), "summary": summary,
              "skipped": skipped, "limits": LIMITS}
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if summary["warn"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
