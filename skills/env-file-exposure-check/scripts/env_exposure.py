"""env_exposure: report committed environment files and secret-shaped values.

Usage:
    python -I scripts/env_exposure.py DIR

Reads DIR and never writes to it. Reports:
  - files whose names look like secret stores: .env*, *.pem, id_rsa,
    credentials* (names ending in .example, .sample or .template are exempt);
  - files whose text matches a secret-shaped pattern, with the line number
    and a masked value: the first 4 characters then *** for token-shaped
    matches, and only the value's length for key=value matches.
Each flagged file is checked against the root .gitignore using simple glob
rules. A flagged file that is not ignored counts as an exposure.

Exit codes: 0 no exposure, 1 at least one exposure, 2 usage or input error
(a one-line JSON error is written to stderr). Standard library only.
"""
import fnmatch
import json
import os
import re
import sys

MAX_FILE_BYTES = 2 * 1024 * 1024  # larger files are checked by name only
MAX_FILES = 5000                  # files listed before the walk stops
MAX_DEPTH = 12                    # directory levels descended
MAX_MATCHES_PER_FILE = 20
MIN_SECRET_VALUE_LEN = 16         # working value for key=value secrets
SKIP_DIRS = {".git", "node_modules"}
SENSITIVE_NAMES = [".env*", "*.pem", "id_rsa", "credentials*"]
TEMPLATE_SUFFIXES = (".example", ".sample", ".template")
PATTERNS = [
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", re.compile(r"-----BEGIN .*PRIVATE KEY-----")),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("key_value_secret", re.compile(
        r"(?i)(?:secret|token|passw(?:or)?d|api[_-]?key|access[_-]?key)"
        r"[A-Za-z0-9_-]*\s*[:=]\s*[\"']?([A-Za-z0-9_\-+/=.]{%d,})" % MIN_SECRET_VALUE_LEN)),
]


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    return 2


def mask(text):
    """Prefix-shaped tokens (AWS key IDs, GitHub tokens): first 4 characters only."""
    return text[:4] + "***"


def mask_length(text):
    """key=value secrets: the value's length only, no characters shown."""
    return "*** (%d chars)" % len(text)


def load_gitignore(root):
    """Return a list of (negate, pattern, anchored) rules, or None if absent or unusable."""
    path = os.path.join(root, ".gitignore")
    if not os.path.isfile(path) or os.path.islink(path):
        return None
    try:
        with open(path, "rb") as fh:
            data = fh.read(MAX_FILE_BYTES + 1)
    except OSError:
        return None
    if len(data) > MAX_FILE_BYTES:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    rules = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        if negate:
            line = line[1:]
        anchored = "/" in line.rstrip("/")
        pattern = line.strip("/")
        if pattern:
            rules.append((negate, pattern, anchored))
    return rules


def rule_matches(rel, pattern, anchored):
    parts = rel.split("/")
    if anchored:
        prefixes = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
        return any(fnmatch.fnmatchcase(p, pattern) for p in prefixes)
    return any(fnmatch.fnmatchcase(p, pattern) for p in parts)


def is_ignored(rel, rules):
    if not rules:
        return False
    ignored = False
    for negate, pattern, anchored in rules:
        if rule_matches(rel, pattern, anchored):
            ignored = not negate
    return ignored


def sensitive_name(basename):
    low = basename.lower()
    if low.endswith(TEMPLATE_SUFFIXES):
        return False
    return any(fnmatch.fnmatchcase(low, pattern) for pattern in SENSITIVE_NAMES)


def read_text(path):
    """Return the file as UTF-8 text, or None when it is skipped."""
    if os.path.islink(path):
        return None
    try:
        with open(path, "rb") as fh:
            data = fh.read(MAX_FILE_BYTES + 1)
    except OSError:
        return None
    if len(data) > MAX_FILE_BYTES or b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_text(text):
    matches = []
    for lineno, line in enumerate(text.split("\n"), 1):
        line = line[:4096]
        hit_on_line = False
        for name, rx in PATTERNS:
            if name == "key_value_secret" and hit_on_line:
                continue
            for m in rx.finditer(line):
                if name == "key_value_secret":
                    value = m.group(1)
                    masked = mask_length(value)
                else:
                    masked = mask(m.group(0))
                matches.append({"line": lineno, "pattern": name, "masked": masked})
                hit_on_line = True
    return matches


def collect_files(root):
    files = []
    truncated = False
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        depth = 0 if rel_dir == os.curdir else len(rel_dir.split(os.sep))
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        if depth >= MAX_DEPTH:
            truncated = truncated or bool(dirnames)
            dirnames[:] = []
        for name in sorted(filenames):
            if len(files) >= MAX_FILES:
                return files, True
            files.append(os.path.join(dirpath, name))
    return files, truncated


def main(argv):
    if len(argv) != 2:
        return fail("usage: env_exposure.py DIR")
    root = argv[1]
    if not os.path.isdir(root):
        return fail("not a directory")
    rules = load_gitignore(root)
    paths, truncated = collect_files(root)
    findings = []
    scanned = 0
    skipped = 0
    for full in paths:
        rel = os.path.relpath(full, root).replace(os.sep, "/")
        reasons = []
        matches = []
        if sensitive_name(os.path.basename(full)):
            reasons.append("sensitive_filename")
        text = read_text(full)
        if text is None:
            skipped += 1
        else:
            scanned += 1
            matches = scan_text(text)
            for m in matches:
                if m["pattern"] not in reasons:
                    reasons.append(m["pattern"])
        if reasons:
            findings.append({
                "file": rel,
                "ignored_by_gitignore": is_ignored(rel, rules),
                "reasons": reasons,
                "matches": matches[:MAX_MATCHES_PER_FILE],
            })
    findings.sort(key=lambda f: f["file"])
    exposures = sum(1 for f in findings if not f["ignored_by_gitignore"])
    result = {
        "tool": "env_exposure",
        "root": root,
        "gitignore_present": rules is not None,
        "files_visited": len(paths),
        "files_content_scanned": scanned,
        "files_skipped": skipped,
        "truncated": truncated,
        "exposure_count": exposures,
        "findings": findings,
    }
    print(json.dumps(result, indent=2))
    return 1 if exposures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
