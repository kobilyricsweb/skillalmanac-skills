"""Lint YAML-style front matter across a folder of Markdown notes.

Read-only: the script opens input files for reading only and writes nothing
except the JSON report on stdout. It walks the notes folder for *.md files,
skipping hidden directories and symbolic links, and parses each front matter
block with the standard library only (no PyYAML).

Usage:
    python -I scripts/frontmatter_lint.py <notes-folder> [--required KEYS]

    --required KEYS   comma-separated key names that must be present
                      (default: title,date,tags)

Exit codes:
    0  no findings
    1  one or more findings (JSON report on stdout)
    2  usage or input error (one line of JSON on stderr)
"""

import datetime
import json
import os
import re
import sys

VERSION = "0.1.0"
MAX_BYTES = 2 * 1024 * 1024
DEFAULT_REQUIRED = ["title", "date", "tags"]
DATE_KEYS = ("date", "updated")
TAG_KEYS = ("tags",)

RULES = {
    "FM001": "no_front_matter",
    "FM002": "unclosed_front_matter",
    "FM003": "duplicate_key",
    "FM004": "missing_required_key",
    "FM005": "bad_date",
    "FM006": "bad_tag",
    "FM007": "empty_value",
    "FM008": "invalid_line",
    "FM009": "file_too_large",
    "FM010": "invalid_utf8",
    "FM011": "unreadable_file",
}

READ_MESSAGES = {
    "FM009": "file is larger than 2 MB and was skipped",
    "FM010": "file is not valid UTF-8 and was skipped",
    "FM011": "file could not be read and was skipped",
}

KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?$")
ITEM_RE = re.compile(r"^\s*-(?:\s+(.*))?$")
DATE_RE = re.compile(r"^([0-9]{4})-([0-9]{2})-([0-9]{2})$")


def fail(message):
    sys.stderr.write(json.dumps({"error": message, "exit": 2}) + "\n")
    return 2


def finding(rel, line, code, key, message):
    return {
        "file": rel,
        "line": line,
        "code": code,
        "rule": RULES[code],
        "key": key,
        "message": message,
    }


def relpath(root, full):
    return os.path.relpath(full, root).replace(os.sep, "/")


def unquote(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def iter_markdown(root):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if not name.lower().endswith(".md"):
                continue
            full = os.path.join(dirpath, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            found.append(full)
    return sorted(found, key=lambda p: relpath(root, p))


def read_note(full):
    """Return (text, None) when usable, or (None, code) when skipped."""
    try:
        if os.path.getsize(full) > MAX_BYTES:
            return None, "FM009"
        with open(full, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        return None, "FM011"
    if len(raw) > MAX_BYTES:
        return None, "FM009"
    try:
        return raw.decode("utf-8-sig"), None
    except UnicodeDecodeError:
        return None, "FM010"


def valid_date(text):
    match = DATE_RE.match(text)
    if not match:
        return False
    try:
        datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return False
    return True


def lint_note(rel, text, required):
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return [finding(rel, 1, "FM001", None, "file does not start with a --- line")]

    close = None
    for index in range(1, len(lines)):
        if lines[index].rstrip() == "---":
            close = index
            break
    if close is None:
        return [finding(rel, 1, "FM002", None, "front matter has no closing --- line")]

    findings = []
    entries = {}
    order = []
    current = None
    for index in range(1, close):
        lineno = index + 1
        raw = lines[index].rstrip()
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        key_match = KEY_RE.match(raw)
        if key_match:
            key = key_match.group(1)
            entry = {
                "line": lineno,
                "value": (key_match.group(2) or "").strip(),
                "items": [],
            }
            if key in entries:
                findings.append(finding(
                    rel, lineno, "FM003", key,
                    "key repeats; first seen on line %d" % entries[key]["line"]))
            else:
                entries[key] = entry
                order.append(key)
            current = entry
            continue
        item_match = ITEM_RE.match(raw)
        if item_match and current is not None and current["value"] == "":
            current["items"].append((lineno, item_match.group(1) or ""))
            continue
        findings.append(finding(
            rel, lineno, "FM008", None,
            "line is not a valid key, list item or comment"))

    for key in order:
        entry = entries[key]
        if entry["value"] == "" and not entry["items"]:
            findings.append(finding(rel, entry["line"], "FM007", key, "key has no value"))
            continue
        if entry["items"]:
            values = entry["items"]
        elif entry["value"].startswith("[") and entry["value"].endswith("]"):
            inner = entry["value"][1:-1]
            if not inner.strip():
                findings.append(finding(rel, entry["line"], "FM007", key, "inline list has no items"))
                continue
            values = [(entry["line"], part) for part in inner.split(",")]
        else:
            values = [(entry["line"], entry["value"])]

        for lineno, raw_text in values:
            text = unquote(raw_text)
            if text == "":
                findings.append(finding(rel, lineno, "FM007", key, "value is empty"))
                continue
            if key in DATE_KEYS and not valid_date(text):
                findings.append(finding(
                    rel, lineno, "FM005", key,
                    "value is not a valid YYYY-MM-DD date"))
            if key in TAG_KEYS:
                problems = []
                if any(ch.isspace() for ch in text):
                    problems.append("tag contains whitespace")
                if text != text.lower():
                    problems.append("tag is not lowercase")
                if problems:
                    findings.append(finding(rel, lineno, "FM006", key, "; ".join(problems)))

    for key in required:
        if key not in entries:
            findings.append(finding(rel, close + 1, "FM004", key, "required key is missing"))

    findings.sort(key=lambda f: (f["line"], f["code"]))
    return findings


def main(argv):
    required = list(DEFAULT_REQUIRED)
    positional = []
    args = argv[1:]
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--required":
            if index + 1 >= len(args):
                return fail("--required needs a comma-separated value")
            required = [k.strip() for k in args[index + 1].split(",") if k.strip()]
            index += 2
            continue
        if arg.startswith("-"):
            return fail("unknown option")
        positional.append(arg)
        index += 1

    if len(positional) != 1:
        return fail("usage: frontmatter_lint.py <notes-folder> [--required KEYS]")
    root = positional[0]
    if not os.path.isdir(root):
        return fail("notes folder not found or not a directory")
    if not required or not all(KEY_RE.match(k + ":") for k in required):
        return fail("--required must list plain key names")

    files = iter_markdown(root)
    if not files:
        return fail("no .md files found in notes folder")

    findings = []
    for full in files:
        rel = relpath(root, full)
        text, code = read_note(full)
        if code is not None:
            findings.append(finding(rel, 1, code, None, READ_MESSAGES[code]))
            continue
        findings.extend(lint_note(rel, text, required))

    report = {
        "tool": "frontmatter_lint",
        "version": VERSION,
        "required_keys": required,
        "files_scanned": len(files),
        "files_with_findings": len({f["file"] for f in findings}),
        "findings_count": len(findings),
        "status": "findings" if findings else "clean",
        "findings": findings,
    }
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
