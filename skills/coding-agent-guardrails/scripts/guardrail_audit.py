#!/usr/bin/env python3
"""Read-only audit of a repository's coding-agent guardrail setup.

    python guardrail_audit.py <repo-dir> [--strict]

Reads the directory tree under <repo-dir> (text files only, size-capped) and
prints ONE JSON object on stdout. It never writes, deletes, runs or contacts
anything. Checks: secret patterns in .gitignore, credential patterns
(AKIA keys, private key blocks, sk- and ghp_ tokens, password=) inside file contents, secret-looking files that are
present but not ignored, agent instruction files, declared protected paths,
a declared test command, lockfiles, and generated or vendored directories.

Exit codes: 0 = no check failed (with --strict: no fail and no warn),
1 = at least one fail (or warn under --strict), 2 = usage error or the path
is not a readable directory.
"""
import fnmatch
import json
import os
import re
import sys

# Cap on files visited so a huge monorepo cannot hang the audit (reason: the
# checks only need the root and the first levels).
MAX_FILES = 5000
# Cap on bytes read from any one file (reason: instruction and manifest files
# are small; larger files are skipped, not truncated, to avoid half-parsing).
MAX_READ = 200_000
# Directories never walked into (reason: huge, not the repo's own code).
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}

INSTRUCTION_FILES = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules",
                     ".windsurfrules", ".github/copilot-instructions.md"]
INSTRUCTION_DIRS = [".cursor/rules"]

# (check id, severity if missing, sample file names the ignore rules must cover)
SECRET_SAMPLES = [
    ("gitignore-env", "fail", [".env", ".env.local"]),
    ("gitignore-keys", "warn", ["server.pem", "server.key", "id_rsa"]),
    ("gitignore-credentials", "warn", ["credentials.json"]),
]

LOCKFILES = {
    "package.json": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "npm-shrinkwrap.json"],
    "pyproject.toml": ["poetry.lock", "uv.lock", "pdm.lock"],
    "Pipfile": ["Pipfile.lock"],
    "Cargo.toml": ["Cargo.lock"],
    "go.mod": ["go.sum"],
    "Gemfile": ["Gemfile.lock"],
    "composer.json": ["composer.lock"],
}

GENERATED_DIRS = ["dist", "build", "out", "generated", "__generated__", "gen",
                  "vendor", "third_party", ".next", "coverage"]
GENERATED_MARK = re.compile(r"do not edit|generated (by|file)|auto-?generated|@generated", re.I)
PROTECT_RE = re.compile(
    r"(do not|don't|never|must not)\s+(edit|modify|touch|change|commit|delete)"
    r"|off[- ]limits|protected (paths?|files?)|read[- ]only (paths?|files?)", re.I)
TEST_MENTION = re.compile(r"\b(npm (run )?test|yarn test|pnpm test|pytest|go test|cargo test|make test|tox|rspec|mvn test|gradle test)\b", re.I)
SECRET_NAME = re.compile(r"^(\.env(\..+)?|.+\.pem|.+\.key|id_rsa.*|.+\.p12)$")
SAFE_SUFFIX = re.compile(r"\.(example|sample|template|dist)$")

# Content patterns (reason: a secret in a normally named file such as
# config.txt is invisible to name checks). Only the kind and line number are
# reported, never the matched value.
PLACEHOLDER = re.compile(r"^(changeme|change-me|placeholder|example|your|xxx+|\*+|<|\$\{|\{\{|%|none|null|true|false|test$)", re.I)
SECRET_PATTERNS = [
    ("aws-access-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private-key-block", re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY(?: BLOCK)?-----")),
    ("sk-token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
]
PASSWORD_ASSIGN = re.compile(r"(?i)\b(password|passwd|pwd|secret|api[_-]?key)\b[\"']?\s*[:=]\s*[\"']?([^\s\"',;]{8,})")


def scan_secret_values(text):
    """Return sorted (line_no, kind) for credential-looking values in text."""
    hits = set()
    for no, line in enumerate(text.splitlines(), 1):
        for kind, rx in SECRET_PATTERNS:
            if rx.search(line):
                hits.add((no, kind))
        m = PASSWORD_ASSIGN.search(line)
        if m and not PLACEHOLDER.match(m.group(2)):
            hits.add((no, "password-assignment"))
    return sorted(hits)


def read_text(path):
    """Return file text, or '' when unreadable, binary or over MAX_READ."""
    try:
        if os.path.getsize(path) > MAX_READ:
            return ""
        with open(path, "rb") as fh:
            raw = fh.read()
        if b"\x00" in raw:
            return ""
        return raw.decode("utf-8", errors="replace")
    except OSError:
        return ""


def ignore_patterns(root):
    """Positive patterns from the root .gitignore (negations are skipped)."""
    pats = []
    for line in read_text(os.path.join(root, ".gitignore")).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        line = line.lstrip("/")
        if line.startswith("**/"):
            line = line[3:]
        pats.append(line.rstrip("/"))
    return pats


def is_ignored(rel, pats):
    """True when a relative posix path matches a .gitignore pattern."""
    base = rel.rsplit("/", 1)[-1]
    parts = rel.split("/")
    for p in pats:
        if fnmatch.fnmatch(base, p) or fnmatch.fnmatch(rel, p):
            return True
        if any(fnmatch.fnmatch(seg, p) for seg in parts[:-1]):
            return True
    return False


def walk(root):
    """Return sorted relative posix paths of files (capped) and a truncated flag."""
    out = []
    truncated = False
    for cur, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(cur, f), root).replace(os.sep, "/")
            out.append(rel)
            if len(out) >= MAX_FILES:
                return out, True
    return out, truncated


def add(checks, cid, status, detail):
    checks.append({"id": cid, "status": status, "detail": detail})


def audit(root):
    files, truncated = walk(root)
    fileset = set(files)
    checks = []
    pats = ignore_patterns(root)

    # 1. .gitignore secret coverage
    if ".gitignore" not in fileset:
        add(checks, "gitignore-present", "fail", "no .gitignore at the repo root")
    else:
        add(checks, "gitignore-present", "pass", ".gitignore found")
    for cid, sev, samples in SECRET_SAMPLES:
        missing = [s for s in samples if not is_ignored(s, pats)]
        if missing:
            add(checks, cid, sev, "not ignored: " + ", ".join(missing))
        else:
            add(checks, cid, "pass", "covered: " + ", ".join(samples))

    # 2. secret-looking files present and not ignored
    exposed, ignored = [], []
    for rel in files:
        name = rel.rsplit("/", 1)[-1]
        if SECRET_NAME.match(name) and not SAFE_SUFFIX.search(name):
            (ignored if is_ignored(rel, pats) else exposed).append(rel)
    if exposed:
        add(checks, "secret-files-exposed", "fail", "present and not ignored: " + ", ".join(exposed))
    elif ignored:
        add(checks, "secret-files-exposed", "pass", "present but ignored: " + ", ".join(ignored))
    else:
        add(checks, "secret-files-exposed", "pass", "no secret-looking files found")

    # 2b. credential-looking VALUES inside any readable text file that git
    # would not ignore (file contents, not names)
    leaks = []
    for rel in files:
        if is_ignored(rel, pats):
            continue
        for no, kind in scan_secret_values(read_text(os.path.join(root, rel))):
            leaks.append("%s:%d %s" % (rel, no, kind))
    if leaks:
        add(checks, "secret-values-in-files", "fail", "credential-like value in non-ignored file: " + ", ".join(leaks[:20]))
    else:
        add(checks, "secret-values-in-files", "pass", "no credential patterns in non-ignored text files")

    # 3. agent instruction files
    instr = [f for f in INSTRUCTION_FILES if f in fileset]
    for d in INSTRUCTION_DIRS:
        instr += [f for f in files if f.startswith(d + "/")]
    text = "\n".join(read_text(os.path.join(root, f)) for f in instr)
    if instr:
        add(checks, "instructions-present", "pass", "found: " + ", ".join(instr))
    else:
        add(checks, "instructions-present", "warn", "no AGENTS.md, CLAUDE.md or equivalent instruction file")

    # 4. enforcement and protected paths
    deny, hooks = 0, False
    for rel in (".claude/settings.json", ".claude/settings.local.json"):
        if rel in fileset:
            try:
                data = json.loads(read_text(os.path.join(root, rel)) or "{}")
            except ValueError:
                add(checks, "settings-valid-json", "fail", rel + " is not valid JSON")
                continue
            if isinstance(data, dict):
                perms = data.get("permissions")
                if isinstance(perms, dict) and isinstance(perms.get("deny"), list):
                    deny += len(perms["deny"])
                if data.get("hooks"):
                    hooks = True
    enforce = []
    if deny:
        enforce.append("%d permission deny rules" % deny)
    if hooks:
        enforce.append("hooks configured")
    if enforce:
        add(checks, "enforcement-configured", "pass", ", ".join(enforce))
    else:
        add(checks, "enforcement-configured", "warn", "no deny rules or hooks found; rules rely on instructions alone")
    if PROTECT_RE.search(text) or deny:
        add(checks, "protected-paths-declared", "pass", "protected or do-not-edit paths are declared")
    else:
        add(checks, "protected-paths-declared", "warn", "no protected-path list in instruction files or deny rules")

    # 5. test command
    found = []
    pkg = read_text(os.path.join(root, "package.json"))
    if pkg:
        try:
            t = (json.loads(pkg).get("scripts") or {}).get("test")
            if isinstance(t, str) and "no test specified" not in t:
                found.append("package.json scripts.test")
        except (ValueError, AttributeError):
            pass
    mk = read_text(os.path.join(root, "Makefile"))
    if re.search(r"^test\s*:", mk, re.M):
        found.append("Makefile test target")
    py = read_text(os.path.join(root, "pyproject.toml")) + read_text(os.path.join(root, "setup.cfg"))
    if "pytest.ini" in fileset or "tox.ini" in fileset or re.search(r"pytest", py):
        found.append("python test config")
    if "Cargo.toml" in fileset:
        found.append("cargo test")
    if "go.mod" in fileset:
        found.append("go test")
    if TEST_MENTION.search(text):
        found.append("test command named in instruction file")
    manifests = [m for m in list(LOCKFILES) + ["Makefile", "setup.cfg", "requirements.txt"] if m in fileset]
    if found:
        add(checks, "test-command", "pass", "; ".join(found))
    elif manifests:
        add(checks, "test-command", "warn", "project manifest present but no test command declared")
    else:
        add(checks, "test-command", "info", "no project manifest found; nothing to declare")

    # 6. lockfiles
    problems, ok = [], []
    for manifest, locks in LOCKFILES.items():
        if manifest in fileset:
            have = [x for x in locks if x in fileset]
            (ok if have else problems).append(manifest if not have else have[0])
    if problems:
        add(checks, "lockfile", "warn", "manifest without lockfile: " + ", ".join(problems))
    elif ok:
        add(checks, "lockfile", "pass", "lockfile present: " + ", ".join(ok))
    else:
        add(checks, "lockfile", "info", "no dependency manifest found")

    # 7. generated or vendored directories (root and one level under src/lib/app)
    gattr = read_text(os.path.join(root, ".gitattributes"))
    candidates = set()
    for rel in files:
        parts = rel.split("/")
        for depth in (1, 2):
            if len(parts) > depth and parts[depth - 1 if depth == 1 else 1] in GENERATED_DIRS:
                if depth == 1 or parts[0] in ("src", "lib", "app", "packages"):
                    candidates.add("/".join(parts[:depth]))
    undeclared, declared = [], []
    for d in sorted(candidates):
        name = d.rsplit("/", 1)[-1]
        inside = [f for f in files if f.startswith(d + "/")][:5]
        marked = any(GENERATED_MARK.search("\n".join(read_text(os.path.join(root, f)).splitlines()[:5])) for f in inside)
        mentioned = d in text or name + "/" in text or ("linguist-generated" in gattr and name in gattr)
        if is_ignored(d, pats) or marked or mentioned:
            declared.append(d)
        else:
            undeclared.append(d)
    if undeclared:
        add(checks, "generated-dirs", "warn", "not marked, ignored or declared: " + ", ".join(undeclared))
    elif declared:
        add(checks, "generated-dirs", "pass", "declared: " + ", ".join(declared))
    else:
        add(checks, "generated-dirs", "info", "no generated or vendored directories found")

    summary = {s: sum(1 for c in checks if c["status"] == s) for s in ("pass", "info", "warn", "fail")}
    return {"repo": os.path.basename(os.path.abspath(root)), "files_seen": len(files),
            "truncated": truncated, "checks": checks, "summary": summary}


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    strict = "--strict" in argv
    if len(args) != 1 or not os.path.isdir(args[0]):
        sys.stderr.write("usage: guardrail_audit.py <repo-dir> [--strict]  (path must be a directory)\n")
        return 2
    result = audit(args[0])
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    s = result["summary"]
    return 1 if s["fail"] or (strict and s["warn"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
