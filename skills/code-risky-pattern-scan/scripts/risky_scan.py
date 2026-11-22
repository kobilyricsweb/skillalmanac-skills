"""risky_scan: first-pass, read-only pattern scan of a source-code folder.

Walks a folder, matches a fixed list of risky code patterns line by line and
prints one JSON object to stdout. The scanned code is never executed, imported
or sent anywhere, and no files are written. Matches are pattern hits for triage,
not a vulnerability assessment.

Usage:
    python -I scripts/risky_scan.py <code-folder>

Exit codes:
    0  scan completed, no findings
    1  scan completed, one or more findings
    2  usage or input error (one-line JSON error object on stderr)
"""

import json
import os
import re
import sys

TOOL = "risky_scan"
TOOL_VERSION = "0.1.0"
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_FILES = 5000
MAX_LINE_CHARS = 4000
SNIPPET_CHARS = 160
MASK_MAX_STARS = 12
DISCLAIMER = "Pattern matches for first-pass review only. Not a vulnerability assessment."

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
TEXT_EXTS = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".java", ".kt", ".php",
    ".rb", ".go", ".cs", ".sh", ".ps1", ".sql", ".yml", ".yaml", ".json", ".toml",
    ".ini", ".cfg", ".conf", ".xml", ".env",
}

SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}

# (pattern_id, severity [working value], compiled regex)
# A named group "v" marks the secret value; it is masked in the snippet.
PATTERNS = [
    ("EVAL_EXEC", "high",
     re.compile(r"(?<![\w.])(?:eval|exec)\s*\(")),
    ("SHELL_TRUE", "high",
     re.compile(r"shell\s*=\s*True")),
    ("SQL_STRING_BUILD", "high",
     re.compile(r"(?i)(?:[\"'](?:select|insert|update|delete)\s[^\"'\n]*[\"']\s*(?:\+|%|\.format\()"
                r"|\bf[\"'](?:select|insert|update|delete)\s)")),
    ("AWS_ACCESS_KEY", "high",
     re.compile(r"(?P<v>\bAKIA[0-9A-Z]{16}\b)")),
    ("SECRET_ASSIGNMENT", "high",
     re.compile(r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token"
                r"|client[_-]?secret)\b\s*[:=]\s*[\"'](?P<v>[^\"'\s<${][^\"'\s]{7,})[\"']")),
    ("PRIVATE_KEY_BLOCK", "high",
     re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----")),
    ("TLS_VERIFY_OFF", "high",
     re.compile(r"verify\s*=\s*False|CERT_NONE|_create_unverified_context"
                r"|rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*[\"']?0")),
    ("PICKLE_LOAD", "medium",
     re.compile(r"\b(?:c?[Pp]ickle|dill)\.loads?\s*\(")),
    ("WEAK_HASH", "low",
     re.compile(r"hashlib\.(?:md5|sha1)\s*\(|createHash\(\s*[\"'](?:md5|sha1)[\"']")),
]


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def mask(value):
    """Keep at most two leading characters; hide the rest (working value)."""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * min(len(value) - 2, MASK_MAX_STARS)


def make_snippet(line, match):
    text = line
    if "v" in match.re.groupindex and match.group("v") is not None:
        start, end = match.start("v"), match.end("v")
        text = line[:start] + mask(match.group("v")) + line[end:]
    return " ".join(text.split())[:SNIPPET_CHARS]


def collect(root):
    """Return (candidate file paths, truncated flag). Symlinks are never followed."""
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            ext = os.path.splitext(name)[1].lower() or name.lower()
            if ext not in TEXT_EXTS or os.path.islink(full):
                continue
            if len(paths) >= MAX_FILES:
                return paths, True
            paths.append(full)
    return paths, False


def main(argv):
    if len(argv) != 2:
        fail("usage: python -I scripts/risky_scan.py <code-folder>")
    root = argv[1]
    if not os.path.exists(root):
        fail("path does not exist")
    if not os.path.isdir(root):
        fail("path is not a folder")
    root = os.path.abspath(root)

    paths, truncated = collect(root)
    skipped = {"too_large": 0, "not_utf8": 0, "unreadable": 0}
    findings = []
    examined = 0

    for full in paths:
        rel = os.path.relpath(full, root).replace(os.sep, "/")
        try:
            size = os.path.getsize(full)
            if size > MAX_FILE_BYTES:
                skipped["too_large"] += 1
                continue
            with open(full, "rb") as handle:
                raw = handle.read(MAX_FILE_BYTES + 1)
        except OSError:
            skipped["unreadable"] += 1
            continue
        if len(raw) > MAX_FILE_BYTES:
            skipped["too_large"] += 1
            continue
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            skipped["not_utf8"] += 1
            continue

        examined += 1
        for lineno, line in enumerate(text.splitlines(), start=1):
            chunk = line[:MAX_LINE_CHARS]
            for pattern_id, severity, regex in PATTERNS:
                match = regex.search(chunk)
                if match is None:
                    continue
                findings.append({
                    "rank": 0,
                    "severity": severity,
                    "pattern_id": pattern_id,
                    "file": rel,
                    "line": lineno,
                    "snippet": make_snippet(chunk, match),
                })

    findings.sort(key=lambda f: (-SEVERITY_RANK[f["severity"]], f["pattern_id"], f["file"], f["line"]))
    for position, finding in enumerate(findings, start=1):
        finding["rank"] = position

    report = {
        "tool": TOOL,
        "tool_version": TOOL_VERSION,
        "disclaimer": DISCLAIMER,
        "limits": {"max_files": MAX_FILES, "max_file_bytes": MAX_FILE_BYTES},
        "files_examined": examined,
        "files_skipped": skipped,
        "truncated": truncated,
        "finding_count": len(findings),
        "findings": findings,
    }
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
