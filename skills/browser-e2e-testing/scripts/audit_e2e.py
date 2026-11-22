#!/usr/bin/env python3
"""Statically audit browser end-to-end test files for documented anti-patterns.

Usage:
    python audit_e2e.py PATH [PATH ...] [--disable RULE[,RULE]] [--fail-on error|warn|never]

PATH is a file or a directory. Directories are walked for test files:
*.spec.*, *.test.*, *.e2e.* with a JS/TS extension, and test_*.py, *_test.py,
*.spec.py. A file given explicitly is always scanned, whatever its name.
node_modules, .git, dist, build, venv and similar folders are skipped.

Reads only the files it is given. Writes nothing. No network. Prints one strict
JSON object on stdout (ASCII only, no NaN).

A finding can be silenced on its own line or the line above with a comment:
    // e2e-audit-ignore: hard-sleep        (or: # e2e-audit-ignore: hard-sleep)
Without a rule list the comment silences every rule on that line.

Exit codes: 0 no finding at the --fail-on level (default: error),
            1 at least one such finding,
            2 usage problem, no test file found, or every input over the size caps
              (error "input_too_large": --max-bytes, 20,000 lines, 5,000 characters per line).

Rules (severity): hard-sleep (error), only-left-in (error), debug-leftover
(error), test-without-assertion (error), brittle-selector (warn),
shared-mutable-state (warn), missing-isolation-hooks (warn),
shared-browser-state (warn), serial-order-dependence (warn),
networkidle-wait (warn), force-action (warn).

This is a line and block heuristic, not a parser. See the "limits" array in the
output and the Limits section of SKILL.md for what it gets wrong.
"""
import argparse
import bisect
import json
import os
import re
import sys

VERSION = "0.1.0"

# Folders never worth walking: dependencies, build output, virtual environments.
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "venv", ".venv", "__pycache__",
             ".next", "coverage", "playwright-report", "test-results", "site-packages"}

# Input caps. A file past any of them is almost certainly generated or hostile; scanning it
# only burns time. Such a file is never scanned: it is listed under skipped_files, and when
# nothing else was scanned the run ends with error "input_too_large" and exit 2.
MAX_BYTES = 1_000_000
MAX_LINES = 20_000
MAX_LINE_CHARS = 5_000
MAX_BLOCKS = 5_000   # test plus hook calls; nested blocks make later rules scale with blocks x size


class TooLarge(Exception):
    pass

JS_TEST_FILE = re.compile(r"\.(spec|test|e2e)\.[cm]?[jt]sx?$")
PY_TEST_FILE = re.compile(r"(^test_.*\.py$)|(_test\.py$)|(\.(spec|test|e2e)\.py$)")

SEVERITY = {
    "hard-sleep": "error",
    "only-left-in": "error",
    "debug-leftover": "error",
    "test-without-assertion": "error",
    "brittle-selector": "warn",
    "shared-mutable-state": "warn",
    "missing-isolation-hooks": "warn",
    "shared-browser-state": "warn",
    "serial-order-dependence": "warn",
    "networkidle-wait": "warn",
    "force-action": "warn",
}

LIMITS = [
    "Heuristic text matching, not a parser: regex literals, JSX text and unusual quoting can confuse the comment and string masking.",
    "test-without-assertion counts any call named expect/assert/verify/ensure/validate/check followed by a capital or underscore as an assertion, so a helper with a misleading name hides a real gap; a test whose assertions live in a helper with another name is reported falsely.",
    "brittle-selector only sees selectors passed as string literals to locator-style calls; selectors built from variables or page objects are not inspected, and a stable-looking class can still be generated.",
    "shared-mutable-state only follows variables declared outside test and hook bodies in the same file; state shared through other modules, databases or the application under test is invisible.",
    "missing-isolation-hooks looks for data-creating calls and for any cleanup word in the file; unique per-test data or an environment reset done outside the file is a valid design this rule cannot see.",
    "hard-sleep also flags setTimeout/sleep inside non-test helpers, including legitimate retry utilities.",
    "Only .only in JS/TS is detected; Python focus markers vary by plugin and are not covered.",
    "A clean report does not mean the tests are reliable; it means none of these patterns matched.",
]

# ---------------------------------------------------------------- masking

def _blank(buf, a, b):
    for k in range(a, b):
        if buf[k] not in "\r\n":
            buf[k] = " "


def mask(text, lang):
    """Return (no_comments, structure) texts of the same length as the input.

    no_comments: comments blanked, string contents kept (for selector rules).
    structure: comments and string contents blanked (for brace matching and
    for counting calls without matching text inside strings).
    """
    nc, st = list(text), list(text)
    n, i = len(text), 0
    while i < n:
        c = text[i]
        if lang == "js" and text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            _blank(nc, i, j)
            _blank(st, i, j)
            i = j
            continue
        if lang == "js" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            _blank(nc, i, j)
            _blank(st, i, j)
            i = j
            continue
        if lang == "py" and c == "#":
            j = text.find("\n", i)
            j = n if j < 0 else j
            _blank(nc, i, j)
            _blank(st, i, j)
            i = j
            continue
        if lang == "py" and c in "'\"" and text.startswith(c * 3, i):
            j = text.find(c * 3, i + 3)
            j = n if j < 0 else j + 3
            _blank(st, i + 3, max(i + 3, j - 3))
            i = j
            continue
        if c in "'\"" or (lang == "js" and c == "`"):
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\\":
                    j += 1
                elif text[j] == "\n" and c != "`":
                    break
                j += 1
            end = min(j + 1, n)
            _blank(st, i + 1, max(i + 1, end - 1))
            i = end
            continue
        i += 1
    return "".join(nc), "".join(st)


def paren_pairs(s, o="(", c=")"):
    """Map every opening bracket offset to its matching close offset in one linear pass."""
    pairs, stack = {}, []
    for k, ch in enumerate(s):
        if ch == o:
            stack.append(k)
        elif ch == c and stack:
            pairs[stack.pop()] = k
    return pairs


# ---------------------------------------------------------------- patterns

SLEEP = {
    "js": re.compile(r"\b(?:waitForTimeout|setTimeout|sleep)\s*\(|\bcy\.wait\s*\(\s*\d|\bbrowser\.pause\s*\("),
    "py": re.compile(r"\b(?:wait_for_timeout|sleep)\s*\("),
}
DEBUG = {
    "js": re.compile(r"\bpage\.pause\s*\(|\bdebugger\b|\bcy\.debug\s*\("),
    "py": re.compile(r"\bpage\.pause\s*\(|\bbreakpoint\s*\(|\b(?:i?pdb)\.set_trace\s*\("),
}
ONLY_JS = re.compile(r"\b(?:test|it|describe|context)(?:\.(?:describe|serial|parallel))*\.only\s*\(|\b(?:fdescribe|fit)\s*\(")
NETWORKIDLE = re.compile(r"\bnetworkidle\b")
FORCE = re.compile(r"\bforce\s*:\s*true\b|\bforce\s*=\s*True\b")
SERIAL = re.compile(r"mode\s*:\s*['\"]serial['\"]|\bdescribe\.serial\b|pytest\.mark\.(?:run\s*\(\s*order|order\b|dependency\b)|@pytest\.mark\.incremental")
NTH_CALL = re.compile(r"\.nth\(\s*-?\d+\s*\)")

SEL_CALL = re.compile(
    r"(?:\blocator|\bquerySelector(?:All)?|\bquery_selector(?:_all)?|\bwaitForSelector|\bwait_for_selector"
    r"|\bcy\.get|\bcss_selector|\bfind_elements?|\bBy\.(?:cssSelector|xpath|css)\w*|\bBy\.(?:CSS_SELECTOR|XPATH)"
    r"|\.(?:click|dblclick|fill|check|uncheck|hover|press|type|select_option|selectOption|text_content|textContent|inner_text|innerText|is_visible|isVisible)"
    r"|(?<![\w.])\$\$?)\s*\(\s*(?:By\.\w+\s*,\s*)?(['\"`])(.*?)\1")

HASH_CLASS = re.compile(r"\.(?:css|sc|jsx|emotion|svelte)-[A-Za-z0-9]{4,}\b"
                        r"|\.[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9]+__(?=[A-Za-z_-]*\d)[A-Za-z0-9_-]{5,}")
GEN_ID = re.compile(r"#:r[0-9a-z]+:|#(?:radix|headlessui|mui|react-select|rc)-[\w:-]*|\[id\^?=['\"]?(?:radix|headlessui)")
POSITIONAL = re.compile(r":nth-(?:child|of-type|last-child|last-of-type)\(|:(?:first|last)-child\b")
XPATH_POS = re.compile(r"^\s*(?:xpath=)?/html|/[a-z*][\w-]*\[\d+\]|\]\[\d+\]")
CLASS_ATTR = re.compile(r"\[class\s*[*^$~|]?=")
TAG_CHAIN = re.compile(r"(?:^|[\s>])(?:div|span|ul|ol|li|tr|td|tbody|section|form|p)(?=[\s>.#\[:]|$)")

JS_ASSERT = re.compile(
    r"\bexpect(?:\.\w+)?\s*\(|\bassert(?:\.\w+)?\s*\(|\.should\b|\bcy\.contains\s*\(|\bt\.(?:is|true|false|equal|deepEqual|truthy|falsy)\w*\s*\("
    r"|\b(?:expect|assert|verify|ensure|validate|check)[A-Z_]\w*\s*\(|\.(?:expect|assert|verify)\w*\s*\(")
PY_ASSERT = re.compile(
    r"\bassert\b|\bexpect\s*\(|pytest\.raises|pytest\.fail|\.assert\w*\(|\bassert_\w+\(|\.until\(|\b(?:verify|check|ensure|validate)_\w+\(")

JS_TEST_CALL = re.compile(r"(?<![\w.$])(test|it)(?:\.(only|skip|fixme|fail|slow))?\s*\(")
JS_HOOK_CALL = re.compile(r"(?<![\w$])(?:\w+\.)?(beforeAll|afterAll|beforeEach|afterEach|before|after)\s*\(")
PY_DEF = re.compile(r"^([ \t]*)(?:async\s+)?def\s+(test\w*)\s*\(", re.M)

CREATE_CALL = re.compile(
    r"\b(?:create|register|signup|sign_up|signUp|seed|insert)\w*\s*\(|\.post\s*\(|\bmethod\s*:\s*['\"]POST['\"]|\brequest\.(?:post|put)\b")
CREATE_UI = re.compile(r"click.*(?:create|sign ?up|register|place order|add new)", re.I)
CLEANUP = re.compile(
    r"\b(?:afterEach|afterAll|after_each|after_all|teardown\w*|tearDown\w*|addCleanup|addfinalizer|cleanup\w*|truncate\w*|reset\w*|drop\w*)\b"
    r"|\byield\b|\.delete\s*\(|\bdelete[A-Z_]\w*\s*\(|\bawait\s+use\s*\(|\buse\s*\(")


def _line_starts(text):
    starts, pos = [0], 0
    for part in text.split("\n"):
        pos += len(part) + 1
        starts.append(pos)
    return starts


# ---------------------------------------------------------------- audit

def audit_text(path, text):
    """Return (findings, tests_found, suppressed) for one file's text."""
    lang = "py" if path.endswith(".py") else "js"
    nc, st = mask(text, lang)
    raw_lines = text.split("\n")
    nc_lines = nc.split("\n")
    starts = _line_starts(text)
    findings, counter = [], {"suppressed": 0}

    def line_of(off):
        return bisect.bisect_right(starts, off)

    def add(rule, line, msg):
        for ln in (line, line - 1):
            if 1 <= ln <= len(raw_lines):
                m = re.search(r"e2e-audit-ignore(?:\s*:\s*([\w,\- ]+))?", raw_lines[ln - 1])
                if m and (not m.group(1) or rule in [r.strip() for r in m.group(1).split(",")]):
                    counter["suppressed"] += 1
                    return
        snippet = raw_lines[line - 1].strip()[:120] if 1 <= line <= len(raw_lines) else ""
        findings.append({"file": path.replace("\\", "/"), "line": line, "rule": rule,
                         "severity": SEVERITY[rule], "message": msg, "snippet": snippet})

    # ---- line rules
    for idx, line in enumerate(nc_lines, start=1):
        if not line.strip():
            continue
        if SLEEP[lang].search(line):
            add("hard-sleep", idx, "Fixed delay. Wait on a condition instead: a web-first assertion, a locator wait or a response wait.")
        if DEBUG[lang].search(line):
            add("debug-leftover", idx, "Debugger or pause call left in a test; it hangs a headless CI run.")
        if lang == "js" and ONLY_JS.search(line):
            add("only-left-in", idx, "Focus marker (.only/fit/fdescribe) silently skips every other test in the run.")
        if NETWORKIDLE.search(line):
            add("networkidle-wait", idx, "networkidle waits for a quiet network, which polling, analytics or websockets can prevent; wait for the element or response the test needs.")
        if FORCE.search(line):
            add("force-action", idx, "force skips the actionability checks (visible, enabled, stable); it can hide a real defect or a missing wait.")
        if SERIAL.search(line):
            add("serial-order-dependence", idx, "Tests are ordered or chained; one failure cascades and parallel runs are impossible. Make each test set up its own state.")
        for m in SEL_CALL.finditer(line):
            sel, reasons = m.group(2), []
            if POSITIONAL.search(sel):
                reasons.append("positional pseudo-class")
            if HASH_CLASS.search(sel):
                reasons.append("generated class hash")
            if GEN_ID.search(sel):
                reasons.append("generated id")
            if XPATH_POS.search(sel):
                reasons.append("absolute or indexed xpath")
            if CLASS_ATTR.search(sel):
                reasons.append("class attribute match")
            if sel.count(">") >= 3 or len(TAG_CHAIN.findall(sel)) >= 4:
                reasons.append("deep structural chain")
            if reasons:
                add("brittle-selector", idx, "Selector breaks on markup or styling changes (" + ", ".join(reasons) + "); prefer role, label, text or a test id.")
        if NTH_CALL.search(line):
            add("brittle-selector", idx, "Positional .nth(N) breaks when list order or length changes; filter by text or role name instead.")

    # ---- test and hook blocks
    tests, hooks = [], []
    if lang == "js":
        pairs = paren_pairs(st)
        for m in JS_TEST_CALL.finditer(st):
            op = m.end() - 1
            cl = pairs.get(op, -1)
            if cl < 0:
                continue
            seg = st[op:cl + 1]
            if "=>" not in seg and "function" not in seg:
                continue
            tests.append({"line": line_of(m.start()), "mod": m.group(2) or "", "a": op, "b": cl})
        for m in JS_HOOK_CALL.finditer(st):
            op = m.end() - 1
            cl = pairs.get(op, -1)
            if cl >= 0:
                hooks.append({"name": m.group(1), "line": line_of(m.start()), "a": op, "b": cl})
    else:
        lines_st = st.split("\n")
        for m in PY_DEF.finditer(st):
            ind = len(m.group(1).expandtabs(4))
            first = line_of(m.start())
            body_lines, k = [], first
            while k < len(lines_st):
                cur = lines_st[k]
                if cur.strip() and len(cur) - len(cur.lstrip()) <= ind:
                    break
                body_lines.append(cur)
                k += 1
            deco, j = "", first - 2
            while j >= 0 and lines_st[j].lstrip().startswith("@"):
                deco += lines_st[j]
                j -= 1
            mod = "skip" if re.search(r"skip|xfail", deco) else ""
            tests.append({"line": first, "mod": mod, "body": "\n".join(body_lines),
                          "body_raw": "\n".join(nc_lines[first:first + len(body_lines)]),
                          "a": starts[first - 1], "b": starts[min(first - 1 + len(body_lines), len(starts) - 1)]})

    if len(tests) + len(hooks) > MAX_BLOCKS:
        raise TooLarge("more than %d test or hook blocks" % MAX_BLOCKS)
    assert_re = JS_ASSERT if lang == "js" else PY_ASSERT
    for t in tests:
        body = t["body"] if lang == "py" else st[t["a"]:t["b"] + 1]
        t["body_st"] = body
        t["body_nc"] = nc[t["a"]:t["b"] + 1] if lang == "js" else t["body_raw"]
        if t["mod"] in ("skip", "fixme"):
            continue
        if not assert_re.search(body):
            add("test-without-assertion", t["line"], "Test body has no assertion; it passes whenever nothing throws. End each test with an assertion on the outcome a user would see.")

    # ---- shared mutable state
    def in_span(off, spans):
        return any(s["a"] <= off <= s["b"] for s in spans)

    if lang == "js":
        decls = []
        for m in re.finditer(r"\b(?:let|var)\s+(\w+)", st):
            decls.append((m.group(1), m.start()))
        for m in re.finditer(r"\bconst\s+(\w+)(?:\s*:\s*[^=;]+)?\s*=\s*(?:\[\s*\]|\{\s*\}|new\s+(?:Map|Set|Array)\b)", st):
            decls.append((m.group(1), m.start()))
        seen = set()
        for name, off in decls:
            if name in seen or in_span(off, tests) or in_span(off, hooks):
                continue
            ref = re.compile(r"\b" + re.escape(name) + r"\b")
            assign = re.compile(r"\b" + re.escape(name) + r"(?:\s*(?:=(?!=)|\+=|-=|\|\|=|\?\?=)|\+\+|--|\.(?:push|set|add|splice|pop|shift|unshift)\s*\(|\[[^\]\n]*\]\s*=(?!=))")
            using = [t for t in tests if ref.search(t["body_st"])]
            writers = [t for t in tests if assign.search(t["body_st"])]
            if writers and len(using) >= 2:
                seen.add(name)
                add("shared-mutable-state", line_of(off),
                    "'%s' is declared outside the tests, written in one test and used by %d tests; results depend on run order. Create the value inside each test or a fixture." % (name, len(using)))
    else:
        for m in re.finditer(r"^([A-Za-z_]\w*)\s*(?::[^=\n]+)?=\s*(?:\[|\{|dict\(|list\(|set\(|None\b)", st, re.M):
            name = m.group(1)
            mut = re.compile(r"\b" + re.escape(name) + r"(?:\.(?:append|extend|update|add|pop|clear|insert|remove)\s*\(|\[[^\]\n]*\]\s*=(?!=)|\s*\+=)|\bglobal\s+[\w, ]*\b" + re.escape(name) + r"\b")
            writers = [t for t in tests if mut.search(t["body_st"])]
            if writers:
                add("shared-mutable-state", line_of(m.start()),
                    "Module-level '%s' is changed inside %d test(s); results depend on run order. Build the value inside each test or a fixture." % (name, len(writers)))

    # ---- shared browser or login state
    if lang == "js":
        for h in hooks:
            if h["name"] in ("beforeAll", "before"):
                body = nc[h["a"]:h["b"] + 1]
                if re.search(r"\b(?:newPage|newContext|launch)\s*\(|\.goto\s*\(|\b(?:login|signIn|sign_in)\w*\s*\(", body):
                    add("shared-browser-state", h["line"], "beforeAll opens a page, navigates or logs in once for every test; tests then share cookies, storage and page state. Use per-test fixtures or a stored auth state that tests only read.")
    else:
        for m in re.finditer(r"@pytest\.fixture\s*\([^)]*scope\s*=\s*['\"](?:module|session|class)['\"][^)]*\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)", nc):
            blob = nc[m.start():m.end() + 600]
            if re.search(r"\bpage\b|\bdriver\b|browser_context|\bcontext\b|login|\.goto\(|\.get\(", blob):
                add("shared-browser-state", line_of(m.start()), "Fixture '%s' has module/session/class scope and holds a page, driver or login; tests share browser state. Use function scope for anything stateful." % m.group(1))

    # ---- missing isolation hooks
    creators = []
    for t in tests:
        if t["mod"] in ("skip", "fixme"):
            continue
        if CREATE_CALL.search(t["body_nc"]) or any(CREATE_UI.search(l) for l in t["body_nc"].split("\n")):
            creators.append(t["line"])
    if creators and not CLEANUP.search(st):
        shown = ", ".join(str(n) for n in creators[:5])
        add("missing-isolation-hooks", creators[0],
            "%d test(s) create data (lines %s) but the file has no teardown, cleanup or fixture-with-cleanup; unless data is unique per test or the environment is reset elsewhere, runs will collide." % (len(creators), shown))

    return findings, len(tests), counter["suppressed"]


# ---------------------------------------------------------------- driver

def collect(paths):
    files, problems = [], []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for nm in sorted(names):
                    if JS_TEST_FILE.search(nm) or PY_TEST_FILE.search(nm):
                        files.append(os.path.join(root, nm))
        else:
            problems.append({"path": p.replace("\\", "/"), "reason": "not found"})
    return files, problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit browser e2e test files for anti-patterns; prints JSON.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--disable", default="", help="comma-separated rule ids to skip")
    ap.add_argument("--fail-on", choices=("error", "warn", "never"), default="error")
    ap.add_argument("--max-bytes", type=int, default=MAX_BYTES, help="skip files larger than this (default %d)" % MAX_BYTES)
    args = ap.parse_args(argv)
    disabled = {r.strip() for r in args.disable.split(",") if r.strip()}
    unknown = sorted(disabled - set(SEVERITY))
    if unknown:
        sys.stderr.write("Unknown rule id(s): %s. Valid: %s\n" % (", ".join(unknown), ", ".join(sorted(SEVERITY))))
        return 2

    files, skipped = collect(args.paths)
    findings, total_tests, suppressed, scanned, too_large = [], 0, 0, [], 0
    for f in files:
        try:
            if os.path.getsize(f) > args.max_bytes:
                skipped.append({"path": f.replace("\\", "/"), "reason": "input_too_large: larger than %d bytes" % args.max_bytes})
                too_large += 1
                continue
            with open(f, "rb") as fh:
                text = fh.read().decode("utf-8-sig", errors="replace")
        except OSError as exc:
            skipped.append({"path": f.replace("\\", "/"), "reason": "unreadable: %s" % exc.__class__.__name__})
            continue
        if not text.strip():
            skipped.append({"path": f.replace("\\", "/"), "reason": "empty file"})
            continue
        line_list = text.split("\n")
        if len(line_list) > MAX_LINES or max(map(len, line_list)) > MAX_LINE_CHARS:
            skipped.append({"path": f.replace("\\", "/"), "reason": "input_too_large: more than %d lines or a line over %d characters" % (MAX_LINES, MAX_LINE_CHARS)})
            too_large += 1
            continue
        try:
            fnd, nt, sup = audit_text(f, text)
        except TooLarge as exc:
            skipped.append({"path": f.replace("\\", "/"), "reason": "input_too_large: %s" % exc})
            too_large += 1
            continue
        scanned.append(f.replace("\\", "/"))
        total_tests += nt
        suppressed += sup
        findings.extend(x for x in fnd if x["rule"] not in disabled)

    if not scanned and too_large:
        sys.stdout.write(json.dumps({"tool": "audit_e2e", "version": VERSION, "ok": False, "error": "input_too_large",
                                     "skipped_files": skipped}, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
        sys.stderr.write("input_too_large: every input exceeded the size caps (see skipped_files).\n")
        return 2
    if not scanned:
        sys.stderr.write("No test files scanned. Pass a test file, or a folder containing *.spec.*, *.test.*, *.e2e.*, test_*.py or *_test.py files.\n")
        return 2

    findings.sort(key=lambda x: (x["file"], x["line"], x["rule"]))
    by_rule, by_sev = {}, {"error": 0, "warn": 0}
    for x in findings:
        by_rule[x["rule"]] = by_rule.get(x["rule"], 0) + 1
        by_sev[x["severity"]] += 1
    report = {
        "tool": "audit_e2e", "version": VERSION,
        "ok": by_sev["error"] == 0,
        "files_scanned": len(scanned), "tests_found": total_tests,
        "counts_by_severity": by_sev, "counts_by_rule": by_rule,
        "suppressed_by_comment": suppressed,
        "findings": findings, "skipped_files": skipped, "limits": LIMITS,
    }
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
    if args.fail_on == "never":
        return 0
    bad = by_sev["error"] + (by_sev["warn"] if args.fail_on == "warn" else 0)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
