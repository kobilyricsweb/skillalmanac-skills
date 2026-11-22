#!/usr/bin/env python3
"""Trace requirements in a Markdown spec to tests (and optionally code).

Usage:
    python spec_trace.py SPEC.md [TESTS_DIR] [--src DIR ...] [--ext .py,.ts]
                         [--require-code]

SPEC.md     Markdown file whose requirements start with an id such as
            "### REQ-004 Title", "- REQ-004: text" or "**REQ-004** text".
TESTS_DIR   Directory searched (recursively) for text files mentioning REQ ids.
            Omit it to check the spec alone (no test coverage fields).
--src DIR   Optional source directory; requirements never mentioned there are
            reported as no_code (a failure only with --require-code).
--ext       Comma-separated extensions to scan (default: common code/test types).

Reads only. Writes strict JSON to stdout, nothing else.

Exit codes: 0 all checks pass, 1 at least one problem found, 2 usage or input error
(missing path, unreadable spec, no requirement ids found).
"""
import json
import os
import re
import sys

# Requirement ids are REQ- plus at least 3 digits so "REQ-1" typos show up as unknown.
DEF_RE = re.compile(r"^\s*(?:>\s*)?(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+)?\**\s*(REQ-\d{3,})\b")
REF_RE = re.compile(r"\bREQ-\d+\b")
HEADING_RE = re.compile(r"^\s*(#{1,6})\s+")
# An acceptance line starts with one of these words (after list/bold markers).
ACC_RE = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?\**\s*(acceptance(?:\s+criteri(?:a|on))?|ac\d*|given|verify|accept)\b\**\s*[:.]?\s*(.*)$",
    re.IGNORECASE,
)
# Open markers block a requirement: the spec itself says it is not settled.
OPEN_RE = re.compile(r"\b(TBD|TBC|TODO|FIXME)\b|\?\?|\[NEEDS CLARIFICATION[^\]]*\]|\bto be decided\b", re.IGNORECASE)
# Vague terms are advisory: they are hard to turn into a pass/fail check.
VAGUE_TERMS = [
    "fast", "quickly", "easy", "easily", "user-friendly", "intuitive", "appropriate",
    "appropriately", "as needed", "etc", "and/or", "robust", "reasonable", "reasonably",
    "seamless", "efficient", "efficiently", "flexible", "modern", "good", "properly",
]
VAGUE_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in VAGUE_TERMS) + r")\b", re.IGNORECASE)
DEFER_RE = re.compile(r"\[(deferred|out[- ]of[- ]scope|dropped)\]", re.IGNORECASE)
# A reference on or just below one of these lines is not a running test.
SKIP_RE = re.compile(
    r"@pytest\.mark\.(?:skip|xfail)|\.skip\(|\bxit\(|\bxdescribe\(|\bit\.todo\(|\btest\.todo\(|"
    r"@Disabled|@Ignore|\bt\.Skip\(|unittest\.skip|\bpytest\.skip\(|\[Ignore\]|\[Fact\(Skip",
    re.IGNORECASE,
)
SKIP_LOOKBACK = 2  # lines above the reference that may hold the skip marker
DEFAULT_EXT = {
    ".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java", ".kt", ".go", ".rb",
    ".rs", ".cs", ".php", ".swift", ".scala", ".feature", ".sh", ".txt", ".yaml", ".yml", ".json",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".tox"}
MAX_FILE_BYTES = 1_000_000  # larger files are almost certainly generated; skipped and counted


def fail(msg):
    sys.stderr.write("spec_trace: " + msg + "\n")
    return 2


def read_lines(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if b"\x00" in raw[:4096]:
        return None
    return raw.decode("utf-8", errors="replace").splitlines()


def parse_spec(lines):
    """Return (requirements dict in order, duplicate id list)."""
    reqs = {}
    dups = []
    current = None
    in_fence = False
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if in_fence:
            if current:
                current["body"].append((n, line))
            continue
        m = DEF_RE.match(line)
        if m:
            rid = m.group(1)
            hm = HEADING_RE.match(line)
            if rid in reqs:
                dups.append(rid)
                current = None
                continue
            current = {"id": rid, "line": n, "level": len(hm.group(1)) if hm else None,
                       "head": line, "body": []}
            reqs[rid] = current
            continue
        hm = HEADING_RE.match(line)
        if hm and current is not None:
            # A heading ends the block of a list-style requirement, and a same-or-higher
            # level heading ends the block of a heading-style requirement.
            if current["level"] is None or len(hm.group(1)) <= current["level"]:
                current = None
                continue
        if current:
            current["body"].append((n, line))
    return reqs, sorted(set(dups))


def check_requirement(req):
    """Return (has_acceptance, open_markers, vague_terms) for one requirement block."""
    lines = [(req["line"], req["head"])] + req["body"]
    has_acc = False
    for i, (_, text) in enumerate(req["body"]):
        m = ACC_RE.match(text)
        if not m:
            continue
        tail = m.group(2).strip()
        keyword = m.group(1).lower()
        if keyword.startswith("given"):
            has_acc = True  # "Given ..." carries its own content
            break
        if len(tail.split()) >= 3:
            has_acc = True
            break
        # Marker alone ("Acceptance:"): content must follow on a later non-blank line.
        for _, nxt in req["body"][i + 1:]:
            if nxt.strip():
                has_acc = len(nxt.split()) >= 3
                break
        if has_acc:
            break
    opens, vague = [], []
    for n, text in lines:
        for m in OPEN_RE.finditer(text):
            opens.append({"line": n, "marker": m.group(0)})
        for m in VAGUE_RE.finditer(text):
            vague.append({"line": n, "term": m.group(0).lower()})
    deferred = bool(DEFER_RE.search(req["head"]))
    return has_acc, opens, vague, deferred


def iter_files(root, exts, spec_path):
    skipped_large = 0
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.path.abspath(full) == spec_path:
                continue
            if os.path.splitext(name)[1].lower() not in exts:
                continue
            try:
                if os.path.getsize(full) > MAX_FILE_BYTES:
                    skipped_large += 1
                    continue
            except OSError:
                continue
            out.append(full)
    return out, skipped_large


def scan_refs(root, exts, spec_path):
    """Map id -> list of (relative path, line, skipped bool). Also unreadable count."""
    refs = {}
    files, big = iter_files(root, exts, spec_path)
    for full in files:
        try:
            lines = read_lines(full)
        except OSError:
            continue
        if lines is None:
            continue
        rel = os.path.relpath(full, root).replace(os.sep, "/")
        for n, line in enumerate(lines, 1):
            for m in REF_RE.finditer(line):
                window = lines[max(0, n - 1 - SKIP_LOOKBACK):n]
                skipped = any(SKIP_RE.search(w) for w in window)
                refs.setdefault(m.group(0), []).append((rel, n, skipped))
    return refs, len(files), big


def main(argv):
    args = list(argv)
    exts = set(DEFAULT_EXT)
    src_dirs, positional = [], []
    require_code = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--require-code":
            require_code = True
        elif a == "--src" and i + 1 < len(args):
            i += 1
            src_dirs.append(args[i])
        elif a == "--ext" and i + 1 < len(args):
            i += 1
            exts = {e if e.startswith(".") else "." + e for e in args[i].lower().split(",") if e}
        elif a.startswith("--"):
            return fail("unknown option " + a)
        else:
            positional.append(a)
        i += 1
    if not 1 <= len(positional) <= 2:
        return fail("usage: spec_trace.py SPEC.md [TESTS_DIR] [--src DIR] [--ext .py,.ts] [--require-code]")
    spec_path = os.path.abspath(positional[0])
    if not os.path.isfile(spec_path):
        return fail("spec file not found: " + positional[0])
    try:
        spec_lines = read_lines(spec_path)
    except OSError as exc:
        return fail("cannot read spec: " + str(exc))
    if spec_lines is None:
        return fail("spec looks binary, expected Markdown text")
    reqs, dups = parse_spec(spec_lines)
    if not reqs:
        return fail("no requirement ids found; start each requirement with an id like REQ-001 "
                    "(heading, list item or bold) at the beginning of a line")
    tests_dir = positional[1] if len(positional) == 2 else None
    if tests_dir and not os.path.isdir(tests_dir):
        return fail("tests directory not found: " + tests_dir)
    for d in src_dirs:
        if not os.path.isdir(d):
            return fail("source directory not found: " + d)

    report = {"command": "spec_trace", "spec": positional[0], "tests_dir": tests_dir,
              "requirements_total": len(reqs), "requirements": list(reqs)}
    no_acc, open_markers, vague, deferred = [], [], [], []
    for rid, req in reqs.items():
        has_acc, opens, vg, is_def = check_requirement(req)
        if is_def:
            deferred.append(rid)
        if not has_acc and not is_def:
            no_acc.append(rid)
        for o in opens:
            if not is_def:
                open_markers.append({"id": rid, **o})
        for v in vg:
            vague.append({"id": rid, **v})
    report["no_acceptance"] = no_acc
    report["open_markers"] = open_markers
    report["duplicate_ids"] = dups
    report["deferred"] = deferred
    report["vague_terms"] = vague
    problems = bool(no_acc or open_markers or dups)

    if tests_dir:
        refs, scanned, big = scan_refs(tests_dir, exts, spec_path)
        no_test, only_skipped, trace = [], [], {}
        for rid in reqs:
            if rid in deferred:
                continue
            hits = refs.get(rid, [])
            live = [h for h in hits if not h[2]]
            trace[rid] = sorted({h[0] for h in live})
            if not hits:
                no_test.append(rid)
            elif not live:
                only_skipped.append(rid)
        unknown = []
        for rid in sorted(refs, key=lambda r: (len(r), r)):
            if rid not in reqs:
                unknown.append({"id": rid, "at": [f"{p}:{n}" for p, n, _ in refs[rid]][:10]})
        report.update({"files_scanned": scanned, "files_skipped_too_large": big,
                       "no_test": no_test, "only_skipped_tests": only_skipped,
                       "unknown_in_tests": unknown, "traceability": trace})
        problems = problems or bool(no_test or only_skipped or unknown)
    if src_dirs:
        code_refs = {}
        for d in src_dirs:
            r, _, _ = scan_refs(d, exts, spec_path)
            for k, v in r.items():
                code_refs.setdefault(k, []).extend(v)
        no_code = [rid for rid in reqs if rid not in deferred and rid not in code_refs]
        report["no_code"] = no_code
        if require_code and no_code:
            problems = True
    report["ok"] = not problems
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return 1 if problems else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
