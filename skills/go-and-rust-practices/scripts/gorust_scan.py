#!/usr/bin/env python3
"""Scan .go and .rs files for a documented list of anti-patterns (regex based, no compiler).

Usage:
    python gorust_scan.py scan PATH [PATH ...] [--only go|rust]
    python gorust_scan.py rules

PATH is a file or a directory (searched recursively). Reads files, writes nothing,
uses no network. Output is one JSON object on stdout.

Exit codes: 0 no high or medium findings (low findings may exist), 1 at least one
high or medium finding, 2 usage error (missing path, nothing to scan).

How it works: comments and string literals are blanked out of a copy of each file
(same offsets, same line numbers) and the rules run on that copy, so a pattern
inside a comment or a string is not reported. This is a lexical pass, not a parser:
see the "limits" field of the output and the Limits section of SKILL.md.

A line that contains the text gorust:ignore is skipped and counted under "suppressed".
"""
import argparse
import bisect
import json
import os
import re
import sys

VERSION = "0.1.0"
SKIP_DIRS = {"vendor", "target", "node_modules", ".git", "testdata"}  # third-party, build output, fixtures of other tools
MAX_TEXT = 160  # characters of the source line echoed in a finding
GO_GOROUTINE_SEARCH_CAP = 4000  # a goroutine body longer than this is not searched further (keeps runtime linear)
IGNORE_MARK = "gorust:ignore"
BOM = chr(0xFEFF)  # byte order mark some editors put at the start of a file

# rule id -> (language, severity, one-line meaning)
RULES = {
    "go-ignored-error": ("go", "high", "result of a call assigned to the blank identifier (`_ = f()`), which hides an error; errcheck does not flag explicit blanks by default"),
    "go-blank-result": ("go", "low", "last result of a call dropped with `v, _ := f()`; many are fine (map, type assertion), so review only"),
    "go-errorf-no-wrap": ("go", "medium", "fmt.Errorf formats an error with %v or %s and no %w, so errors.Is and errors.As cannot see the cause"),
    "go-panic-in-library": ("go", "medium", "panic( in a non-main, non-test package, outside a Must* function"),
    "go-goroutine-no-context": ("go", "medium", "go statement whose body or arguments mention no ctx, context, errgroup or channel receive"),
    "rust-unwrap": ("rust", "high", ".unwrap() outside test code"),
    "rust-expect": ("rust", "medium", ".expect( outside test code; acceptable only for a proven invariant with a message that says why"),
    "rust-clone-in-loop": ("rust", "low", ".clone() lexically inside for, while or loop; a heuristic for hot-loop allocation, not proof"),
    "rust-unsafe-no-safety": ("rust", "high", "unsafe block, unsafe impl or unsafe extern block with no SAFETY comment"),
}
SEVERITY_FAILS = {"high", "medium"}

LIMITS = [
    "Lexical scan: no types, no macros expansion, no build tags. A match is a place to look, not a verdict.",
    "Go goroutine rule cannot see a context carried in a struct field or a closed-over channel that is not received from inside the body.",
    "Rust test regions are found from #[test] and #[cfg(test)] attributes and tests/, benches/, examples/ directories; cfg(any(test, ..)) is not recognised.",
    "rust-clone-in-loop cannot tell a cheap Arc or Rc clone from a deep copy.",
    "Multi-line fmt.Errorf calls are not checked for %w.",
]

IDENT = re.compile(r"[A-Za-z0-9_]")


def mask(text, lang):
    """Return text with comments and string/char literals replaced by spaces. Newlines are kept."""
    out = list(text)
    n = len(text)

    def blank(a, b):
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    i = 0
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "//":
            j = text.find("\n", i)
            j = n if j < 0 else j
            blank(i, j)
            i = j
        elif two == "/*":
            if lang == "rust":
                depth, j = 1, i + 2
                while j < n and depth:
                    if text.startswith("/*", j):
                        depth, j = depth + 1, j + 2
                    elif text.startswith("*/", j):
                        depth, j = depth - 1, j + 2
                    else:
                        j += 1
            else:
                j = text.find("*/", i + 2)
                j = n if j < 0 else j + 2
            blank(i, j)
            i = j
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if lang == "go" and text[j] == "\n":
                    break
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            blank(i, j)
            i = j
        elif c == "`" and lang == "go":
            j = text.find("`", i + 1)
            j = n if j < 0 else j + 1
            blank(i, j)
            i = j
        elif lang == "rust" and c == "r" and _raw_string_start(text, i):
            hashes = 0
            j = i + 1
            while text[j] == "#":
                hashes += 1
                j += 1
            end = text.find('"' + "#" * hashes, j + 1)
            end = n if end < 0 else end + 1 + hashes
            blank(i, end)
            i = end
        elif c == "'":
            if i + 1 < n and text[i + 1] == "\\":
                j = text.find("'", i + 2)
                j = n if j < 0 else j + 1
                blank(i, j)
                i = j
            elif i + 2 < n and text[i + 2] == "'" and text[i + 1] != "'":
                blank(i, i + 3)
                i += 3
            else:
                i += 1  # a Rust lifetime such as 'a
        else:
            i += 1
    return "".join(out)


def _raw_string_start(text, i):
    p = i - 1
    if p >= 0 and text[p] == "b":
        p -= 1
    if p >= 0 and IDENT.match(text[p]):
        return False
    j = i + 1
    while j < len(text) and text[j] == "#":
        j += 1
    return j < len(text) and text[j] == '"'


def match_close(masked, start, open_ch, close_ch):
    """Index of the bracket closing the one at `start`; last index when unbalanced."""
    depth = 0
    for k in range(start, len(masked)):
        ch = masked[k]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return k
    return len(masked) - 1


class Source:
    def __init__(self, path, text, lang):
        self.path = path
        self.lang = lang
        self.text = text
        self.lines = text.split("\n")
        self.masked = mask(text, lang)
        self.mlines = self.masked.split("\n")
        self.starts = [0]
        for m in re.finditer("\n", text):
            self.starts.append(m.end())

    def line_of(self, offset):
        return bisect.bisect_right(self.starts, offset)  # 1-based


def finding(src, line, rule):
    lang, sev, _ = RULES[rule]
    return {"file": src.path, "line": line, "language": lang, "rule": rule, "severity": sev,
            "text": src.lines[line - 1].strip()[:MAX_TEXT]}


# ---------------------------------------------------------------- Go

GO_IGNORED = re.compile(r"^\s*_(?:\s*,\s*_)*\s*=\s*[A-Za-z_](?:[\w.]*\w)?\(")
GO_BLANK_RESULT = re.compile(r"^\s*[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*,\s*_\s*:?=\s*[A-Za-z_](?:[\w.]*\w)?\(")
GO_ERRORF = re.compile(r'Errorf\(\s*"((?:[^"\\]|\\.)*)"\s*,(.*)\)')
GO_ERR_ARG = re.compile(r"\berr\b|\berr[A-Z]\w*|\w+Err\b|\w+Error\(\)")
GO_FUNC = re.compile(r"^func\s+(?:\([^)]*\)\s*)?(\w+)")
GO_STMT = re.compile(r"(?:^|[;{}])[ \t]*go[ \t]+(func\b|[A-Za-z_][\w.]*[ \t]*\()", re.M)
GO_CTX = re.compile(r"\bctx\w*|\bcontext\.|\berrgroup\b|\bg\.Go\b")
GO_PACKAGE = re.compile(r"^\s*package\s+(\w+)", re.M)


def has_receive(region):
    """True when the region contains a channel receive (`<-ch`), not a send (`ch <- v`)."""
    for m in re.finditer(r"<-", region):
        k = m.start() - 1
        while k >= 0 and region[k] in " \t\r\n":
            k -= 1
        if k < 0:
            return True
        prev = region[k]
        if prev in ")]" or (IDENT.match(prev) and not re.search(r"\b(?:case|return)$", region[:k + 1])):
            continue  # an operand before the arrow: a send
        return True
    return False


def scan_go(src):
    path_base = os.path.basename(src.path)
    if path_base.endswith("_test.go"):
        return [], "test file"
    head = "\n".join(src.lines[:20])
    if "Code generated" in head and "DO NOT EDIT" in head:
        return [], "generated file"
    out = []
    pm = GO_PACKAGE.search(src.masked)
    is_main = bool(pm and pm.group(1) == "main")
    func_at = []  # enclosing top-level func name per line (1-based index)
    cur = ""
    for ln in src.mlines:
        m = GO_FUNC.match(ln)
        if m:
            cur = m.group(1)
        func_at.append(cur)
    for idx, ln in enumerate(src.mlines, start=1):
        if GO_IGNORED.match(ln):
            out.append(finding(src, idx, "go-ignored-error"))
        elif GO_BLANK_RESULT.match(ln):
            out.append(finding(src, idx, "go-blank-result"))
        if "Errorf(" in ln:
            m = GO_ERRORF.search(src.lines[idx - 1])
            if m and re.search(r"%[vs]", m.group(1)) and "%w" not in m.group(1) and GO_ERR_ARG.search(m.group(2)):
                out.append(finding(src, idx, "go-errorf-no-wrap"))
        if not is_main and re.search(r"\bpanic\(", ln) and not func_at[idx - 1].startswith("Must"):
            out.append(finding(src, idx, "go-panic-in-library"))
    masked = src.masked
    n = len(masked)
    for m in GO_STMT.finditer(masked):
        start = m.start(1)
        if m.group(1).startswith("func"):
            p = masked.find("(", start)
            if p < 0:
                continue
            pe = match_close(masked, p, "(", ")")
            b = masked.find("{", pe)
            if b < 0:
                continue
            end = match_close(masked, b, "{", "}") + 1
            k = end
            while k < n and masked[k] in " \t":
                k += 1
            if k < n and masked[k] == "(":
                end = match_close(masked, k, "(", ")") + 1
        else:
            p = masked.find("(", m.end(1) - 1)
            end = match_close(masked, p, "(", ")") + 1
        region = masked[start:min(end, start + GO_GOROUTINE_SEARCH_CAP)]
        if not GO_CTX.search(region) and not has_receive(region):
            out.append(finding(src, src.line_of(start), "go-goroutine-no-context"))
    return out, None


# ---------------------------------------------------------------- Rust

RUST_TEST_ATTR = re.compile(r"#\[\s*cfg\s*\(\s*test\s*\)\s*\]|#\[\s*(?:[A-Za-z_]\w*::)*test\b[^\]]*\]")
RUST_INNER_TEST = re.compile(r"#!\[\s*cfg\s*\(\s*test\s*\)\s*\]")
RUST_UNWRAP = re.compile(r"\.\s*unwrap\s*\(\s*\)")
RUST_EXPECT = re.compile(r"\.\s*expect\s*\(")
RUST_CLONE = re.compile(r"\.\s*clone\s*\(\s*\)")
RUST_UNSAFE = re.compile(r"\bunsafe\s*\{|\bunsafe\s+impl\b|\bunsafe\s+extern\b[^{;]*\{")
RUST_LOOP = re.compile(r"(?:^|[;{}])[ \t]*(?:'[A-Za-z_]\w*[ \t]*:[ \t]*)?(for|while|loop)\b(?![ \t]*<)", re.M)
RUST_SAFETY = re.compile(r"safety\s*:", re.I)
TEST_DIRS = {"tests", "benches", "examples"}


def rust_test_lines(src):
    """Set of 1-based line numbers that sit inside test code."""
    lines = set()
    if RUST_INNER_TEST.search(src.masked):
        return set(range(1, len(src.lines) + 1))
    masked = src.masked
    for m in RUST_TEST_ATTR.finditer(masked):
        brace = masked.find("{", m.end())
        semi = masked.find(";", m.end())
        if brace < 0 or (0 <= semi < brace):
            continue
        end = match_close(masked, brace, "{", "}")
        lines.update(range(src.line_of(m.start()), src.line_of(end) + 1))
    return lines


def rust_loop_regions(masked):
    regions = []
    for m in RUST_LOOP.finditer(masked):
        depth = 0
        k = m.end(1)
        body = -1
        while k < len(masked):
            ch = masked[k]
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            elif ch == "{" and depth <= 0:
                body = k
                break
            elif ch == ";" and depth <= 0:
                break
            k += 1
        if body >= 0:
            regions.append((body, match_close(masked, body, "{", "}")))
    return regions


def has_safety_comment(src, line):
    """SAFETY note on the same line, on the contiguous comment lines right above, or on the first line inside."""
    idx = line - 1
    if RUST_SAFETY.search(src.lines[idx]):
        return True
    k = idx - 1
    while k >= 0 and re.match(r"\s*(//|/\*|\*)", src.lines[k]):
        if RUST_SAFETY.search(src.lines[k]):
            return True
        k -= 1
    if idx + 1 < len(src.lines) and re.match(r"\s*(//|/\*)", src.lines[idx + 1]) and RUST_SAFETY.search(src.lines[idx + 1]):
        return True
    return False


def scan_rust(src):
    parts = set(re.split(r"[\\/]", src.path)[:-1])
    path_is_test = bool(parts & TEST_DIRS) or os.path.basename(src.path) == "build.rs"
    test_lines = set(range(1, len(src.lines) + 1)) if path_is_test else rust_test_lines(src)
    out = []
    masked = src.masked
    for m in RUST_UNWRAP.finditer(masked):
        ln = src.line_of(m.start())
        if ln not in test_lines:
            out.append(finding(src, ln, "rust-unwrap"))
    for m in RUST_EXPECT.finditer(masked):
        ln = src.line_of(m.start())
        if ln not in test_lines:
            out.append(finding(src, ln, "rust-expect"))
    regions = rust_loop_regions(masked)
    seen = set()
    for m in RUST_CLONE.finditer(masked):
        ln = src.line_of(m.start())
        if ln in test_lines or ln in seen:
            continue
        if any(a < m.start() < b for a, b in regions):
            seen.add(ln)
            out.append(finding(src, ln, "rust-clone-in-loop"))
    for m in RUST_UNSAFE.finditer(masked):
        ln = src.line_of(m.start())
        if not has_safety_comment(src, ln):
            out.append(finding(src, ln, "rust-unsafe-no-safety"))
    return out, None


# ---------------------------------------------------------------- driver

def collect(paths, only):
    files = []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for nm in sorted(names):
                    files.append(os.path.join(root, nm))
        else:
            raise FileNotFoundError(p)
    keep = []
    for f in files:
        ext = os.path.splitext(f)[1]
        if ext == ".go" and only in (None, "go"):
            keep.append((f, "go"))
        elif ext == ".rs" and only in (None, "rust"):
            keep.append((f, "rust"))
    return keep


def read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    if text.startswith(BOM):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


def cmd_scan(args):
    try:
        targets = collect(args.paths, args.only)
    except FileNotFoundError as exc:
        print(f"error: path not found: {exc}. Pass an existing .go/.rs file or a directory.", file=sys.stderr)
        return 2
    if not targets:
        print("error: no .go or .rs files found under the given paths (vendor, target, node_modules, .git and testdata are skipped).", file=sys.stderr)
        return 2
    findings, skipped, suppressed, scanned = [], [], 0, 0
    for path, lang in targets:
        shown = path.replace("\\", "/")
        src = Source(shown, read_text(path), lang)
        found, why = (scan_go if lang == "go" else scan_rust)(src)
        if why:
            skipped.append({"file": shown, "reason": why})
            continue
        scanned += 1
        for f in found:
            if IGNORE_MARK in src.lines[f["line"] - 1]:
                suppressed += 1
            else:
                findings.append(f)
    findings.sort(key=lambda f: (f["file"], f["line"], f["rule"]))
    counts = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    sev = {}
    for f in findings:
        sev[f["severity"]] = sev.get(f["severity"], 0) + 1
    failing = sum(v for k, v in sev.items() if k in SEVERITY_FAILS)
    report = {
        "command": "scan", "tool": "gorust_scan", "version": VERSION,
        "files_scanned": scanned, "files_skipped": skipped, "suppressed": suppressed,
        "counts_by_rule": dict(sorted(counts.items())), "counts_by_severity": dict(sorted(sev.items())),
        "verdict": "findings" if failing else ("review" if findings else "clean"),
        "findings": findings, "limits": LIMITS,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if failing else 0


def cmd_rules(_args):
    rules = [{"rule": r, "language": v[0], "severity": v[1], "meaning": v[2]} for r, v in sorted(RULES.items())]
    print(json.dumps({"command": "rules", "tool": "gorust_scan", "version": VERSION, "rules": rules, "limits": LIMITS},
                     indent=2, ensure_ascii=False))
    return 0


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Scan .go and .rs files for documented anti-patterns.")
    sub = ap.add_subparsers(dest="command", required=True)
    sc = sub.add_parser("scan", help="scan files or directories")
    sc.add_argument("paths", nargs="+")
    sc.add_argument("--only", choices=["go", "rust"], default=None)
    sc.set_defaults(func=cmd_scan)
    ru = sub.add_parser("rules", help="print the rule list as JSON")
    ru.set_defaults(func=cmd_rules)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
