#!/usr/bin/env python3
"""Scan a Next.js App Router `app/` directory for structural mistakes.

Usage:
    python scripts/next_scan.py scan <app_dir> [--strict]

Reads every .js .jsx .ts .tsx .mjs file under <app_dir> (skipping node_modules,
.next and dot folders). Writes nothing. Prints one JSON object to stdout.

Rules (id: severity):
    client-imports-server  error  a 'use client' file imports `server-only`,
                                  next/headers, fs, a database driver, or a
                                  local module that does (one level deep).
    client-at-tree-top     warn   page.* or layout.* starts with 'use client'.
    missing-loading        warn   a page that fetches has no loading.* in its
                                  folder or any ancestor folder.
    missing-error          warn   same, for error.*.
    missing-metadata       warn   a server page exports neither `metadata` nor
                                  `generateMetadata`.
    img-tag                warn   a raw <img> tag where next/image would apply.
    possible-waterfall     info   two independent `await` assignments in a row
                                  in a page or layout (not run in parallel).
    route-page-conflict    error  route.* and page.* in the same folder.

JSON contract (stable):
    {"tool": "next_scan", "version": 1, "root": str, "files_scanned": int,
     "findings": [{"rule", "severity", "file", "line", "message"}],
     "counts_by_rule": {rule: int}, "suppressed": int, "strict": bool, "ok": bool}
`file` is relative to <app_dir> with forward slashes. Findings are sorted by
file, line, rule. `ok` is false when any error exists, or any warn in --strict.

Exit codes: 0 ok, 1 findings that fail the run, 2 usage error or missing dir.
"""
import json
import os
import re
import sys

VERSION = 1
EXTS = (".js", ".jsx", ".ts", ".tsx", ".mjs")
SKIP_DIRS = {"node_modules", ".next"}
# Files above this size are skipped: generated bundles, not hand-written routes.
MAX_BYTES = 1_000_000

# Modules that cannot run in the browser bundle. Package names are matched
# exactly or by the prefix before a slash (e.g. "pg" and "pg/lib").
SERVER_ONLY_MODULES = {
    "server-only", "next/headers", "fs", "fs/promises", "child_process",
    "pg", "mysql", "mysql2", "mongodb", "mongoose", "@prisma/client",
    "drizzle-orm", "ioredis", "better-sqlite3", "knex", "sequelize",
    "@neondatabase/serverless", "@libsql/client", "@vercel/postgres",
}
# Metadata-only files: <img> is correct there (ImageResponse markup).
IMG_EXEMPT_NAMES = ("opengraph-image", "twitter-image", "icon", "apple-icon")

IMPORT_RE = re.compile(
    r"""(?:^|[;\s])(?:import\s+(?:type\s+)?(?:[\w*{}\s,$]+?\s+from\s+)?|export\s+(?:type\s+)?[\w*{}\s,$]+?\s+from\s+|require\s*\(\s*|import\s*\(\s*)(['"])([^'"\n]+)\1""",
    re.M)
USE_CLIENT_RE = re.compile(r"""\A\s*(['"])use client\1""")
USE_SERVER_RE = re.compile(r"""\A\s*(['"])use server\1""")
METADATA_RE = re.compile(
    r"export\s+(?:const|let|var)\s+metadata\b"
    r"|export\s+(?:async\s+)?function\s+generateMetadata\b"
    r"|export\s+(?:const|let)\s+generateMetadata\b"
    r"|export\s*\{[^}]*\b(?:metadata|generateMetadata)\b[^}]*\}")
FETCHES_RE = re.compile(r"\bawait\b|\bfetch\s*\(")
IMG_RE = re.compile(r"<img(?=[\s/>])")
AWAIT_ASSIGN_RE = re.compile(
    r"^(\s*)(?:const|let)\s+(?:(\w+)|\{([^}]*)\}|\[([^\]]*)\])\s*=\s*await\b(.*)$")
CHEAP_AWAIT_RE = re.compile(r"await\s+(?:props\.)?(?:params|searchParams|cookies\(\)|headers\(\))")


def strip_code(src, blank_templates=False):
    """Blank out comments (and optionally template-literal text), keep newlines.

    A small state machine, not a parser: regex literals containing quotes can
    confuse it. Line numbers are always preserved.
    """
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            while i < n and src[i] != "\n":
                out.append(" ")
                i += 1
        elif c == "/" and nxt == "*":
            out.append("  ")
            i += 2
            while i < n and not (src[i] == "*" and i + 1 < n and src[i + 1] == "/"):
                out.append("\n" if src[i] == "\n" else " ")
                i += 1
            out.append("  ")
            i += 2
        elif c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            blank = blank_templates and quote == "`"
            while i < n and src[i] != quote:
                if src[i] == "\n" and quote != "`":
                    break  # unterminated quote: stop at end of line
                step = 2 if src[i] == "\\" and i + 1 < n else 1
                for ch in src[i:i + step]:
                    out.append(("\n" if ch == "\n" else " ") if blank else ch)
                i += step
            if i < n and src[i] == quote:
                out.append(quote)
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def read(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def is_server_module(name):
    if name.startswith("node:"):
        name = name[5:]
    if name in SERVER_ONLY_MODULES:
        return True
    return name.split("/")[0] in SERVER_ONLY_MODULES and not name.startswith("@")


def resolve_local(spec, from_file, app_dir):
    """Return an existing file for a relative or @/ import, else None."""
    if spec.startswith("."):
        bases = [os.path.normpath(os.path.join(os.path.dirname(from_file), spec))]
    elif spec.startswith("@/") or spec.startswith("~/"):
        rest = spec[2:]
        parent = os.path.dirname(app_dir)
        bases = [os.path.normpath(os.path.join(parent, rest)),
                 os.path.normpath(os.path.join(os.path.dirname(parent), rest))]
    else:
        return None
    for base in bases:
        candidates = [base] + [base + e for e in EXTS] + [os.path.join(base, "index" + e) for e in EXTS]
        for cand in candidates:
            if os.path.isfile(cand):
                return cand
    return None


def collect_files(app_dir):
    found = []
    for dirpath, dirnames, filenames in os.walk(app_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if name.endswith(EXTS):
                found.append(os.path.join(dirpath, name))
    return found


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]


def scan(app_dir, strict=False):
    app_dir = os.path.abspath(app_dir)
    files = collect_files(app_dir)
    findings, suppressed = [], 0
    cache = {}

    def rel(p):
        return os.path.relpath(p, app_dir).replace(os.sep, "/")

    def add(rule, severity, path, line, message):
        findings.append({"rule": rule, "severity": severity, "file": rel(path),
                         "line": line, "message": message})

    def code_of(path):
        if path not in cache:
            raw = read(path)
            cache[path] = None if raw is None else (raw, strip_code(raw))
        return cache[path]

    dirs_with = {}  # dir -> set of special stems present
    for p in files:
        dirs_with.setdefault(os.path.dirname(p), set()).add(stem(p))

    def covered(dirpath, special):
        cur = dirpath
        while True:
            if special in dirs_with.get(cur, ()):
                return True
            if cur == app_dir or len(cur) <= len(app_dir):
                return False
            cur = os.path.dirname(cur)

    for path in files:
        entry = code_of(path)
        if entry is None:
            continue
        raw, code = entry
        name = stem(path)
        is_client = bool(USE_CLIENT_RE.match(code))
        folder = os.path.dirname(path)
        rel_parts = rel(path).split("/")[:-1]
        in_slot_or_intercept = any(part.startswith("@") or part.startswith("(.") or part.startswith("(..") for part in rel_parts)
        private = any(part.startswith("_") for part in rel_parts)

        # client-imports-server
        if is_client:
            for m in IMPORT_RE.finditer(code):
                spec = m.group(2)
                ln = line_of(code, m.start(2))
                if is_server_module(spec):
                    add("client-imports-server", "error", path, ln,
                        f"client component imports server-only module '{spec}'")
                    continue
                target = resolve_local(spec, path, app_dir)
                if not target:
                    continue
                t_entry = code_of(target)
                if t_entry is None:
                    continue
                t_code = t_entry[1]
                if USE_SERVER_RE.match(t_code):
                    continue  # server action module: callable from the client
                reasons = []
                for tm in IMPORT_RE.finditer(t_code):
                    if is_server_module(tm.group(2)):
                        reasons.append(tm.group(2))
                if reasons:
                    add("client-imports-server", "error", path, ln,
                        f"client component imports '{spec}', which imports server-only module '{sorted(set(reasons))[0]}'")

        # client-at-tree-top
        if is_client and name in ("page", "layout") and not private:
            add("client-at-tree-top", "warn", path, 1,
                f"{name} is a client component: it cannot export metadata or fetch on the server; move 'use client' into a leaf component")

        # route-page-conflict
        if name == "route" and "page" in dirs_with.get(folder, ()):
            add("route-page-conflict", "error", path, 1, "route file and page file in the same folder")

        if name == "page" and not private:
            fetches = (not is_client) and bool(FETCHES_RE.search(code))
            if fetches:
                if not covered(folder, "loading"):
                    add("missing-loading", "warn", path, 1,
                        "page fetches data but no loading file exists in this folder or any parent")
                if not covered(folder, "error"):
                    add("missing-error", "warn", path, 1,
                        "page fetches data but no error file exists in this folder or any parent")
            if not is_client and not in_slot_or_intercept and not METADATA_RE.search(code):
                add("missing-metadata", "warn", path, 1,
                    "page exports neither metadata nor generateMetadata")

        # possible-waterfall (server pages and layouts only)
        if name in ("page", "layout") and not is_client:
            lines = code.split("\n")
            prev = None  # (index, indent, names)
            for idx, text in enumerate(lines):
                m = AWAIT_ASSIGN_RE.match(text)
                if not m:
                    continue
                indent = m.group(1)
                names = {x.strip().split(":")[-1].strip() for x in
                         re.split(r"[,\s]+", (m.group(2) or m.group(3) or m.group(4) or "")) if x.strip()}
                names = {x for x in names if re.match(r"^\w+$", x)}
                stmt = " ".join(lines[idx:idx + 4]).split(";")[0]
                if "Promise.all" in stmt or CHEAP_AWAIT_RE.search(stmt):
                    prev = (idx, indent, names) if not CHEAP_AWAIT_RE.search(stmt) else None
                    continue
                if prev and prev[1] == indent and idx - prev[0] <= 8:
                    body = stmt.split("await", 1)[1]
                    if not any(re.search(r"\b" + re.escape(v) + r"\b", body) for v in prev[2]):
                        add("possible-waterfall", "info", path, idx + 1,
                            "this await does not use the previous await's result; start both before awaiting (Promise.all)")
                prev = (idx, indent, names)

        # img-tag
        if not name.startswith(IMG_EXEMPT_NAMES) and ".test." not in path and ".stories." not in path:
            _, nostr = raw, strip_code(raw, blank_templates=True)
            raw_lines = raw.split("\n")
            for m in IMG_RE.finditer(nostr):
                ln = line_of(nostr, m.start())
                tag = nostr[m.start():m.start() + 400].split(">", 1)[0]
                if re.search(r"""src\s*=\s*\{?\s*['"`]data:""", tag):
                    continue
                prior = raw_lines[ln - 2] if ln >= 2 else ""
                if "no-img-element" in prior or "no-img-element" in raw_lines[ln - 1]:
                    suppressed += 1
                    continue
                add("img-tag", "warn", path, ln, "raw <img>: next/image gives sizing, lazy loading and responsive srcset")

    findings.sort(key=lambda f: (f["file"], f["line"], f["rule"]))
    counts = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    failing = any(f["severity"] == "error" for f in findings) or (strict and any(f["severity"] == "warn" for f in findings))
    return {"tool": "next_scan", "version": VERSION, "root": os.path.basename(app_dir),
            "files_scanned": len(files), "findings": findings,
            "counts_by_rule": dict(sorted(counts.items())), "suppressed": suppressed,
            "strict": strict, "ok": not failing}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    strict = "--strict" in argv
    argv = [a for a in argv if a != "--strict"]
    if len(argv) != 2 or argv[0] != "scan":
        print("usage: next_scan.py scan <app_dir> [--strict]", file=sys.stderr)
        return 2
    if not os.path.isdir(argv[1]):
        print(f"error: '{argv[1]}' is not a directory. Pass the app/ folder (or src/app).", file=sys.stderr)
        return 2
    report = scan(argv[1], strict)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
