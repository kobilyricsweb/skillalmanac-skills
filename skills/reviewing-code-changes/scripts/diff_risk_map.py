#!/usr/bin/env python3
"""Map a unified diff for review: files by risk, changed definitions, and signal lines.

    python diff_risk_map.py <diff-file | -> [--json]

Reads a unified diff from the file, or from standard input when the argument is
"-". Writes nothing and runs nothing.
Exit codes: 0 = map printed, 2 = usage error, unreadable or empty input.

The map is a reading order and a list of leads. It works on diff text, not on
parsed code: it does not find callers, and a diff with no signals is not a
clean diff.
"""
import json
import re
import sys

# Category weights order the reading list: where a mistake costs most comes first.
CATEGORY_WEIGHT = {"migration": 50, "auth": 40, "config": 20, "dependency": 20, "source": 10, "test": 8, "docs": 0}
# Weight added per signal so a small file with a risky line outranks a large tidy one.
SIGNAL_WEIGHT = 15
DEF_PATTERNS = [
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\("),
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"),
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\("),
    re.compile(r"^\s*(?:public|private|protected|internal|static|final|\s)+[\w<>\[\], ]+\s+([A-Za-z_]\w*)\s*\([^;]*$"),
    re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)"),
    re.compile(r"^\s*class\s+([A-Za-z_]\w*)"),
]
CONST = re.compile(r"^\s*(?:export\s+)?(?:const\s+|let\s+|var\s+|final\s+|static\s+)*([A-Z][A-Z0-9_]{2,})\s*(?::\s*[\w\[\], ]+)?\s*=\s*(-?\d[\d_.]*)\b")
TEST_DEF = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)|^\s*(?:it|test)\s*\(\s*['\"`]([^'\"`]+)|^\s*func\s+(Test\w+)")
STRONG_ASSERT = re.compile(r"assertEqual|assertAlmostEqual|assertDictEqual|assertListEqual|\.toBe\(|\.toEqual\(|\.toStrictEqual\(|assert\s+\S+\s*==|assert_eq!|Assert\.Equal|assertEquals")
WEAK_ASSERT = re.compile(r"assertIsNotNone|assertTrue\(\s*\w+\s*\)|\.toBeDefined\(|\.toBeTruthy\(|\.not\.toThrow\(|assert\s+\w+\s*$|assert\s+\S+\s+is not None|assertNotNull|Assert\.NotNull")
SIGNALS = [
    ("swallowed error", re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}|except[^:]*:\s*pass\b|rescue\s*=>\s*\w+\s*;?\s*end")),
    ("broad exception caught", re.compile(r"except\s+(Exception|BaseException)\b|except\s*:|catch\s*\(\s*(Throwable|Exception)\s+\w+\s*\)")),
    ("SQL built from a string", re.compile(r"(`[^`]*\b(SELECT|INSERT|UPDATE|DELETE)\b[^`]*\$\{)|(f[\"'][^\"']*\b(SELECT|INSERT|UPDATE|DELETE)\b[^\"']*\{)|(\b(SELECT|INSERT|UPDATE|DELETE)\b[^\"']*[\"']\s*(\+|%|\.format\())", re.I)),
    ("NOT NULL column added without a default", re.compile(r"ADD\s+(COLUMN\s+)?(?!.*\bDEFAULT\b).*\bNOT\s+NULL\b", re.I)),
    ("index built without the online option", re.compile(r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY)", re.I)),
    ("drop or rename in schema", re.compile(r"\b(DROP\s+(TABLE|COLUMN)|RENAME\s+(TO|COLUMN)|ALTER\s+COLUMN\s+\w+\s+(SET\s+DATA\s+)?TYPE)\b", re.I)),
    ("test skipped", re.compile(r"@(pytest\.mark\.skip|unittest\.skip|Disabled|Ignore)\b|\b(it|describe|test)\.skip\(|\bxit\(|\bt\.Skip\(")),
    ("debug leftover", re.compile(r"\bconsole\.log\(|\bdebugger\b|\bbreakpoint\(\)|\bpdb\.set_trace\(|\bdbg!\(")),
    ("TODO or FIXME added", re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")),
    ("possible credential", re.compile(r"(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|(?i:password|secret|token|api_?key)\s*[=:]\s*['\"][^'\"]{8,}['\"])")),
    ("TLS or auth check disabled", re.compile(r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false|InsecureSkipVerify\s*:\s*true|@csrf_exempt|permission_classes\s*=\s*\[\s*AllowAny", re.I)),
    ("shell command built from input", re.compile(r"shell\s*=\s*True|child_process\.exec\(|os\.system\(")),
]


def category(path):
    p = path.lower()
    name = p.rsplit("/", 1)[-1]
    if re.search(r"(^|/)(migrations?|migrate|alembic|schema)(/|$)", p) or name.endswith(".sql"):
        return "migration"
    if re.search(r"(^|/)(tests?|__tests__|spec)(/|$)|(_test|\.test|\.spec|_spec)\.[a-z]+$|(^|/)test_[^/]+$", p):
        return "test"
    if re.search(r"auth|permission|session|login|token|password|acl|rbac|security|crypto", p):
        return "auth"
    if name in ("package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "requirements.txt", "pyproject.toml",
                "poetry.lock", "go.mod", "go.sum", "cargo.toml", "cargo.lock", "gemfile", "gemfile.lock", "pom.xml", "build.gradle"):
        return "dependency"
    if name.endswith((".yml", ".yaml", ".toml", ".ini", ".env", ".cfg", ".conf", ".tf")) or "dockerfile" in name or "settings" in name or "config" in name:
        return "config"
    if name.endswith((".md", ".rst", ".txt")):
        return "docs"
    return "source"


def parse(text):
    files, cur, new_line = [], None, 0
    for raw in text.split("\n"):
        if raw.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+?) b/(.+)$", raw)
            cur = {"path": m.group(2) if m else raw[11:], "added": [], "removed": [], "status": "modified"}
            files.append(cur)
            continue
        if raw.startswith("+++ "):
            path = raw[4:].strip()
            if cur is None or (cur["added"] or cur["removed"]):
                cur = {"path": path[2:] if path.startswith("b/") else path, "added": [], "removed": [], "status": "modified"}
                files.append(cur)
            elif path != "/dev/null":
                cur["path"] = path[2:] if path.startswith("b/") else path
            continue
        if cur is None:
            continue
        if raw.startswith("new file mode"):
            cur["status"] = "new"
        elif raw.startswith("deleted file mode"):
            cur["status"] = "deleted"
        elif raw.startswith("rename to "):
            cur["status"] = "renamed"
        elif raw.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", raw)
            new_line = int(m.group(1)) if m else 0
        elif raw.startswith("--- "):
            continue
        elif raw.startswith("+"):
            cur["added"].append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-"):
            cur["removed"].append((new_line, raw[1:]))
        elif raw.startswith(" ") or raw == "":
            new_line += 1
    return [f for f in files if f["added"] or f["removed"] or f["status"] != "modified"]


def names(lines, patterns):
    out = []
    for _, line in lines:
        for rx in patterns:
            m = rx.match(line)
            if m:
                out.append(next(g for g in m.groups() if g))
                break
    return out


def analyse(files):
    report = []
    removed_consts, added_consts = {}, {}
    for f in files:
        cat = category(f["path"])
        sig = []
        for n, line in f["added"]:
            for label, rx in SIGNALS:
                if rx.search(line):
                    if label == "debug leftover" and cat == "test":
                        continue
                    sig.append({"line": n, "signal": label, "text": line.strip()[:120]})
        if cat == "test":
            gone = [t for t in names(f["removed"], [TEST_DEF]) if t not in names(f["added"], [TEST_DEF])]
            for t in gone:
                sig.append({"line": 0, "signal": "test removed", "text": t})
            strong_removed = [l for _, l in f["removed"] if STRONG_ASSERT.search(l)]
            weak_added = [(n, l) for n, l in f["added"] if WEAK_ASSERT.search(l) and not STRONG_ASSERT.search(l)]
            if strong_removed and weak_added:
                for n, l in weak_added:
                    sig.append({"line": n, "signal": "assertion weakened", "text": l.strip()[:120]})
        if f["status"] == "deleted" and cat == "test":
            sig.append({"line": 0, "signal": "test file deleted", "text": f["path"]})
        defs_added, defs_removed = set(names(f["added"], DEF_PATTERNS)), set(names(f["removed"], DEF_PATTERNS))
        for n, line in f["removed"]:
            m = CONST.match(line)
            if m:
                removed_consts.setdefault(m.group(2).replace("_", ""), []).append((m.group(1), f["path"]))
        for n, line in f["added"]:
            m = CONST.match(line)
            if m:
                added_consts.setdefault(m.group(2).replace("_", ""), []).append((m.group(1), f["path"], n))
        score = CATEGORY_WEIGHT[cat] + SIGNAL_WEIGHT * len(sig) + min(len(f["added"]) + len(f["removed"]), 200) // 10
        report.append({"path": f["path"], "status": f["status"], "category": cat, "added": len(f["added"]),
                       "removed": len(f["removed"]), "signals": sig, "score": score,
                       "changed_definitions": sorted(defs_added & defs_removed),
                       "removed_definitions": sorted(defs_removed - defs_added),
                       "new_definitions": sorted(defs_added - defs_removed)})
    # Numeric constants whose value is not carried over anywhere: either changed or dropped.
    const_changes = []
    for value, items in removed_consts.items():
        if value not in added_consts:
            for name, path in items:
                same_name = [(v, a) for v, lst in added_consts.items() for a in lst if a[0] == name]
                near = [(v, a) for v, lst in added_consts.items() for a in lst if set(a[0].split("_")) & set(name.split("_"))]
                hit = same_name or near
                const_changes.append({"removed": f"{name} = {value}", "in": path,
                                      "possible_replacement": [f"{a[0]} = {v} ({a[1]}:{a[2]})" for v, a in hit]})
    report.sort(key=lambda r: -r["score"])
    return report, const_changes


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args = [a for a in argv if not a.startswith("--") or a == "-"]
    if len(args) != 1:
        print(__doc__)
        return 2
    try:
        text = sys.stdin.read() if args[0] == "-" else open(args[0], encoding="utf-8", errors="replace").read()
    except OSError as e:
        print(f"cannot read {args[0]}: {e}", file=sys.stderr)
        return 2
    files = parse(text.replace("\r\n", "\n"))
    if not files:
        print("no file changes found; the input must be a unified diff (git diff output)", file=sys.stderr)
        return 2
    report, const_changes = analyse(files)
    if "--json" in argv:
        print(json.dumps({"files": report, "numeric_constants_changed_or_dropped": const_changes}, indent=2))
        return 0
    total_add, total_rem = sum(r["added"] for r in report), sum(r["removed"] for r in report)
    print(f"{len(report)} file(s), +{total_add} -{total_rem}\n")
    print("Read in this order:")
    for i, r in enumerate(report, 1):
        print(f"{i}. {r['path']}  [{r['category']}, {r['status']}, +{r['added']} -{r['removed']}]")
        for s in r["signals"]:
            loc = f":{s['line']}" if s["line"] else ""
            print(f"     ! {s['signal']}{loc}: {s['text']}")
    changed = sorted({d for r in report for d in r["changed_definitions"] + r["removed_definitions"]})
    if changed:
        print("\nDefinitions changed or removed. Search the whole repo for every use, including files outside the diff:")
        print("  " + ", ".join(changed))
    if const_changes:
        print("\nNumeric constants whose old value does not reappear (changed or dropped):")
        for c in const_changes:
            extra = "; now possibly " + ", ".join(c["possible_replacement"]) if c["possible_replacement"] else ""
            print(f"  {c['removed']} (was in {c['in']}){extra}")
    tests = [r for r in report if r["category"] == "test"]
    src = [r for r in report if r["category"] in ("source", "auth")]
    if src and not tests:
        print("\nNo test file is touched by this change.")
    print("\nLeads only: confirm each in the code. Not detected: callers, logic errors, anything needing the code to be understood.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
