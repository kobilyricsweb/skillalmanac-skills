#!/usr/bin/env python3
"""Scan TypeScript sources for a fixed list of anti-patterns, with line numbers.

    python ts_scan.py [paths ...] [--profile library|app] [--min-severity low|medium|high]
                      [--ignore-rule RULE ...] [--include-dts] [--max-findings N]

Paths are files or directories (default: current directory). Directories are
walked for .ts .tsx .mts .cts files; node_modules, dist, build, out, coverage,
.next, .git and *.d.ts files are skipped (--include-dts keeps declaration files).

Reads files, writes nothing, uses no network. Prints ONE strict JSON object to
stdout (sorted keys, ASCII only). Plain-text problems go to stderr.

Exit codes: 0 no findings, 1 at least one finding, 2 usage error or nothing to scan.

How it works: a small tokenizer blanks out comments, string literals, template
literal text and regex literals (keeping line/column positions), then regular
expressions look for the patterns in the masked code. There is no parser and no
type information, so every finding is a candidate for review, not a verdict.
See the "limits" list in the output and in SKILL.md.

Inline suppression: a comment `// ts-scan-ignore` or
`// ts-scan-ignore: rule-a, rule-b -- reason` on the same line as a finding, or
alone on the line before it, silences it. Suppressed findings are still listed
under "suppressed" so they stay visible.
"""
import argparse
import bisect
import json
import os
import re
import sys

VERSION = "1.0.0"
EXTENSIONS = (".ts", ".tsx", ".mts", ".cts")
SKIP_DIRS = {"node_modules", "dist", "build", "out", "coverage", ".next", ".git", ".turbo"}
# A suppression reason shorter than this is treated as no reason: "todo", "fix"
# and "x" explain nothing, while a short real sentence is usually 10+ characters.
MIN_REASON_CHARS = 10
# Characters trimmed around a suppression reason: separators people put after the
# directive (hyphen, colon, en dash, em dash, asterisk) and the byte order mark.
REASON_STRIP = " \t-:*" + chr(0x2013) + chr(0x2014)
BOM = chr(0xFEFF)
SEVERITY_ORDER ={"low": 0, "medium": 1, "high": 2}
# Files where a default export is required by a framework or a tool, so the
# default-export rule would only produce noise there.
DEFAULT_EXPORT_EXEMPT = re.compile(
    r"(?:^|[\\/])(?:page|layout|loading|error|not-found|template|route|middleware|"
    r"default|global-error|opengraph-image|sitemap|robots)\.(?:ts|tsx|mts|cts)$"
    r"|\.config\.(?:ts|mts|cts)$|\.stories\.(?:ts|tsx)$|(?:^|[\\/])pages[\\/]"
)

RULES = {
    "explicit-any": ("medium", "`any` switches type checking off for this value; use `unknown` and narrow, or a generic or a concrete type."),
    "non-null-assertion": ("medium", "Postfix `!` asserts a value is not null or undefined without checking; narrow with a check, an early return or a guard function."),
    "double-assertion": ("high", "`as unknown as T` forces a type with no check; validate the value, fix the source type, or write a guard function."),
    "ts-nocheck": ("high", "`@ts-nocheck` turns off checking for the whole file; fix the errors or scope a typed exception."),
    "ts-suppression-no-reason": ("high", "Suppression directive without a reason of at least %d characters; add what is wrong and when it can go." % MIN_REASON_CHARS),
    "ts-ignore-prefer-expect-error": ("low", "`@ts-ignore` stays silent when the error is fixed; `@ts-expect-error` fails then, so the suppression cannot go stale."),
    "enum": ("low", "`enum` emits runtime code and is not erasable; a string-literal union or an `as const` object usually fits (see references/patterns.md)."),
    "default-export": ("low", "Default export in library code: consumers rename it freely and tools cannot find it by name; use a named export."),
    "definite-assignment": ("low", "`x!: T` promises initialisation the compiler cannot see; initialise in the constructor, make it optional, or restructure."),
}

LIMITS = [
    "Token-level scan, not a parser: no type information, so an identifier that is literally named `any` or a JSX text word such as `any` after a comma can be flagged.",
    "In .tsx files a postfix `!` is reported only when the next character is one of . [ ( ) ; , ] } ? : so that JSX text such as 'Hello!' is not flagged; the cost is that `value!` at the end of a line or before an operator in a .tsx file is missed, and JSX text like 'Done!)' can still be flagged.",
    "Regex literals are recognised by the preceding token; an unusual regex after `)` or `}` can be mis-read as division and may hide or invent findings on that line.",
    "JSX text containing `//` or an apostrophe can be read as a comment or string; strings end at the line break so the damage stays on that line.",
    "Template literal expressions are scanned as code; nested template literals deeper than normal use are handled, but tagged templates are treated as plain templates.",
    "Default exports are flagged by syntax only; the script cannot know whether the file belongs to a library. Use --profile app to turn the rule off, or ts-scan-ignore.",
    "Only the listed rules are checked. A clean report does not mean the code is type-safe; run the project's own tsc and linter.",
    "Types that hide `any` (for example JSON.parse results, untyped library returns) are not found because they never write the word.",
]


def mask_source(src):
    """Return (masked, comments). masked has the same length and newlines as src;
    comments, strings, template text and regex literals are replaced by spaces.
    comments is a list of (start_offset, text)."""
    n = len(src)
    out = list(src)
    comments = []
    stack = []  # one int per open template expression: brace depth inside ${ }
    i = 0
    prev = ""  # previous significant token: an identifier run or one punctuation char
    regex_after_punct = set("(,=:[!&|?{;+-*%^~")
    regex_after_word = {"return", "typeof", "case", "in", "of", "delete", "void", "throw",
                        "new", "else", "do", "instanceof", "yield", "await"}

    def blank(a, b):
        for k in range(a, min(b, n)):
            if out[k] not in "\r\n":
                out[k] = " "

    def read_template(j):
        # j is just after a backtick or after the closing } of an expression.
        start = j
        while j < n:
            ch = src[j]
            if ch == "\\":
                j += 2
                continue
            if ch == "`":
                blank(start, j + 1)
                return j + 1
            if ch == "$" and j + 1 < n and src[j + 1] == "{":
                blank(start, j + 2)
                stack.append(0)
                return j + 2
            j += 1
        blank(start, n)
        return n

    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c in " \t\r\n":
            i += 1
            continue
        if c == "/" and nxt == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            comments.append((i, src[i:j]))
            blank(i, j)
            i = j
            continue
        if c == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            comments.append((i, src[i:j]))
            blank(i, j)
            i = j
            continue
        if c in "'\"":
            j = i + 1
            while j < n and src[j] != c and src[j] not in "\r\n":
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n) if j < n and src[j] == c else j
            blank(i, j)
            i = j
            prev = '"'
            continue
        if c == "`":
            blank(i, i + 1)
            i = read_template(i + 1)
            prev = '"'
            continue
        if stack:
            if c == "{":
                stack[-1] += 1
            elif c == "}":
                if stack[-1] == 0:
                    stack.pop()
                    blank(i, i + 1)
                    i = read_template(i + 1)
                    prev = '"'
                    continue
                stack[-1] -= 1
        if c == "/":
            if prev == "" or prev in regex_after_punct or prev == "=>" or prev in regex_after_word:
                j = i + 1
                in_class = False
                ok = False
                while j < n and src[j] not in "\r\n":
                    ch = src[j]
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == "[":
                        in_class = True
                    elif ch == "]":
                        in_class = False
                    elif ch == "/" and not in_class:
                        ok = True
                        break
                    j += 1
                if ok:
                    j += 1
                    while j < n and (src[j].isalpha()):
                        j += 1
                    blank(i, j)
                    i = j
                    prev = '"'
                    continue
            prev = "/"
            i += 1
            continue
        if c.isalnum() or c in "_$":
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] in "_$"):
                j += 1
            prev = src[i:j]
            i = j
            continue
        if c == ">" and i > 0 and src[i - 1] == "=":
            prev = "=>"
        else:
            prev = c
        i += 1
    return "".join(out), comments


class Source:
    def __init__(self, text):
        self.text = text
        self.masked, self.comments = mask_source(text)
        self.starts = [0]
        for m in re.finditer("\n", text):
            self.starts.append(m.end())
        self.lines = text.split("\n")

    def pos(self, offset):
        line = bisect.bisect_right(self.starts, offset) - 1
        return line + 1, offset - self.starts[line] + 1

    def snippet(self, line):
        s = self.lines[line - 1].strip()
        return s if len(s) <= 160 else s[:157] + "..."

    def prev_nonspace(self, offset):
        k = offset - 1
        while k >= 0 and self.masked[k] in " \t\r\n":
            k -= 1
        return k

    def next_nonspace(self, offset):
        k = offset
        m = self.masked
        while k < len(m) and m[k] in " \t\r\n":
            k += 1
        return k


ANY_RE = re.compile(r"(?<![\w$.#])any(?![\w$])")
ANY_PREV_CHARS = set(":<,|&(=[")
ANY_PREV_WORDS = {"as", "extends", "keyof", "is", "satisfies", "typeof"}
ENUM_RE = re.compile(r"(?<![\w$.])((?:const\s+|declare\s+)?)enum\s+[A-Za-z_$][\w$]*\s*\{")
DOUBLE_RE = re.compile(r"(?<![\w$.])as\s+unknown\s+as\b")
DEFAULT_RE = re.compile(r"(?<![\w$.])export\s+default\b")
DEFAULT_AS_RE = re.compile(r"(?<![\w$.])export\s*\{[^}]*\bas\s+default\b[^}]*\}")
DIRECTIVE_RE = re.compile(r"@ts-(ignore|expect-error|nocheck)\b(.*)", re.S)


def find_any(src, add):
    for m in ANY_RE.finditer(src.masked):
        p = src.prev_nonspace(m.start())
        if p < 0:
            continue
        ch = src.masked[p]
        ok = ch in ANY_PREV_CHARS
        if not ok and (ch.isalnum() or ch in "_$"):
            q = p
            while q >= 0 and (src.masked[q].isalnum() or src.masked[q] in "_$"):
                q -= 1
            ok = src.masked[q + 1:p + 1] in ANY_PREV_WORDS
        if not ok:
            continue
        n = src.next_nonspace(m.end())
        if n < len(src.masked) and src.masked[n] == ":":
            continue  # parameter or property named any
        add("explicit-any", m.start())


def find_non_null(src, add, is_tsx):
    m = src.masked
    for k, ch in enumerate(m):
        if ch != "!" or k == 0:
            continue
        before = m[k - 1]
        after = m[k + 1] if k + 1 < len(m) else "\n"
        if not (before.isalnum() or before in "_$)]"):
            continue
        if after == "=":
            continue
        if after == ":":
            add("definite-assignment", k)
            continue
        if is_tsx and after not in ".[()];,]}?":
            continue
        add("non-null-assertion", k)


def find_regex(src, add):
    for m in ENUM_RE.finditer(src.masked):
        if m.group(1).strip() == "declare":
            continue
        add("enum", m.start())
    for m in DOUBLE_RE.finditer(src.masked):
        add("double-assertion", m.start())


def find_defaults(src, add):
    for m in DEFAULT_RE.finditer(src.masked):
        add("default-export", m.start())
    for m in DEFAULT_AS_RE.finditer(src.masked):
        add("default-export", m.start())


def find_directives(src, add):
    for off, text in src.comments:
        m = DIRECTIVE_RE.search(text)
        if not m:
            continue
        kind, rest = m.group(1), m.group(2)
        at = off + m.start()
        if kind == "nocheck":
            add("ts-nocheck", at)
            continue
        rest = rest.split("\n", 1)[0].replace("*/", "")
        reason = rest.strip(REASON_STRIP)
        if len(reason) < MIN_REASON_CHARS or not re.search(r"[A-Za-z]", reason):
            add("ts-suppression-no-reason", at)
        elif kind == "ignore":
            add("ts-ignore-prefer-expect-error", at)


def suppressions(src):
    """Map line number -> set of rule names, or None meaning all rules."""
    result = {}
    for off, text in src.comments:
        if "ts-scan-ignore" not in text:
            continue
        m = re.search(r"ts-scan-ignore(?:\s*:\s*([A-Za-z0-9_,\- ]*))?", text)
        rules = None
        if m and m.group(1) and m.group(1).strip():
            raw = m.group(1).split("--")[0]
            rules = {r.strip() for r in raw.split(",") if r.strip()}
        line, _ = src.pos(off)
        own_line = src.lines[line - 1].strip().startswith(("//", "/*"))
        targets = [line] + ([line + 1] if own_line else [])
        for t in targets:
            cur = result.get(t, set())
            if cur is None or rules is None:
                result[t] = None
            else:
                result[t] = cur | rules
    return result


def scan_text(text, path, profile="library", ignored=()):
    is_tsx = path.lower().endswith(".tsx")
    src = Source(text)
    found = []

    def add(rule, offset):
        line, col = src.pos(offset)
        found.append((line, col, rule))

    find_any(src, add)
    find_non_null(src, add, is_tsx)
    find_regex(src, add)
    find_directives(src, add)
    if profile == "library" and not DEFAULT_EXPORT_EXEMPT.search(path):
        find_defaults(src, add)
    sup = suppressions(src)
    findings, suppressed = [], []
    for line, col, rule in sorted(set(found)):
        if rule in ignored:
            continue
        item = {"file": path, "line": line, "column": col, "rule": rule,
                "severity": RULES[rule][0], "message": RULES[rule][1], "snippet": src.snippet(line)}
        rules_here = sup.get(line, False)
        if rules_here is None or (rules_here is not False and rule in rules_here):
            suppressed.append({"file": path, "line": line, "rule": rule})
        else:
            findings.append(item)
    return findings, suppressed


def collect(paths, include_dts):
    files, problems = [], []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for name in sorted(names):
                    low = name.lower()
                    if not low.endswith(EXTENSIONS):
                        continue
                    if not include_dts and (low.endswith(".d.ts") or low.endswith(".d.mts") or low.endswith(".d.cts")):
                        continue
                    files.append(os.path.join(root, name))
        else:
            problems.append("path not found: %s" % p)
    return files, problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scan .ts/.tsx files for TypeScript anti-patterns.")
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--profile", choices=["library", "app"], default="library",
                    help="library (default) also flags default exports; app does not")
    ap.add_argument("--min-severity", choices=list(SEVERITY_ORDER), default="low")
    ap.add_argument("--ignore-rule", action="append", default=[], choices=sorted(RULES))
    ap.add_argument("--include-dts", action="store_true")
    ap.add_argument("--max-findings", type=int, default=0, help="cap the findings list (0 = no cap); counts stay complete")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    files, problems = collect(args.paths, args.include_dts)
    for pr in problems:
        sys.stderr.write(pr + "\n")
    if not files:
        sys.stderr.write("no .ts/.tsx/.mts/.cts files to scan; pass a file or a directory that contains them\n")
        return 2
    min_rank = SEVERITY_ORDER[args.min_severity]
    findings, suppressed, skipped = [], [], []
    for path in files:
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            skipped.append({"file": path, "reason": "unreadable: %s" % exc.__class__.__name__})
            continue
        text = raw.decode("utf-8", errors="replace").lstrip(BOM)
        f, s = scan_text(text, path.replace("\\", "/"), args.profile, set(args.ignore_rule))
        findings.extend(x for x in f if SEVERITY_ORDER[x["severity"]] >= min_rank)
        suppressed.extend(s)
    counts = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    shown = findings[:args.max_findings] if args.max_findings > 0 else findings
    report = {
        "tool": "ts_scan", "version": VERSION, "profile": args.profile,
        "files_scanned": len(files), "files_skipped": skipped,
        "total_findings": len(findings), "counts_by_rule": counts,
        "truncated": len(shown) < len(findings),
        "findings": shown, "suppressed": suppressed,
        "rules": {k: {"severity": v[0], "message": v[1]} for k, v in sorted(RULES.items())},
        "limits": LIMITS,
    }
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
