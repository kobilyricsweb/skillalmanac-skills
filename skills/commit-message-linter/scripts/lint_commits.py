#!/usr/bin/env python3
"""Commit message linter for the Conventional Commits layout.

Usage:
    python -I scripts/lint_commits.py INPUT [--types LIST] [--max-subject N] [--max-body N]

INPUT is a UTF-8 text file. Messages are separated by lines that contain only
three hyphens. Each message is checked and a JSON report is written to
standard output. The script reads INPUT and nothing else, writes no files,
never runs git and never starts another process.

Exit codes: 0 every message passes, 1 at least one error was found,
2 usage or input error (a one-line JSON object is written to standard error).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

VERSION = "0.1.0"
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_MESSAGES = 1000
MAX_LINE_CHARS = 4000
MAX_TYPES = 50
DEFAULT_TYPES = "feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert"
SEPARATOR = "---"
HEADER_RE = re.compile(r"^([a-z]+)(?:\(([A-Za-z0-9._/-]+)\))?(!)?: (\S.*)$")
TYPE_RE = re.compile(r"^[a-z]+$")
BREAKING_RE = re.compile(r"^BREAKING[ -]CHANGE: \S")

RULES = {
    "E001": "header-format",
    "E002": "unknown-type",
    "E003": "subject-too-long",
    "E004": "subject-trailing-period",
    "E005": "subject-not-imperative",
    "E006": "missing-blank-line-before-body",
    "E007": "body-line-too-long",
    "E008": "breaking-change-footer-missing",
    "E009": "empty-message",
}


def fail(detail):
    """Write a one-line JSON error to standard error and exit with code 2."""
    sys.stderr.write(json.dumps({"error": detail}) + "\n")
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage: " + message)


def parse_args(argv):
    parser = _Parser(prog="lint_commits.py", description="Lint commit messages.")
    parser.add_argument("input", help="UTF-8 text file, messages separated by ---")
    parser.add_argument("--types", default=DEFAULT_TYPES,
                        help="comma list of allowed lowercase types")
    parser.add_argument("--max-subject", type=int, default=72,
                        help="subject length limit, 10 to 200")
    parser.add_argument("--max-body", type=int, default=72,
                        help="body line length limit, 10 to 200")
    args = parser.parse_args(argv)
    types = [t.strip() for t in args.types.split(",")]
    if len(types) > MAX_TYPES or any(not TYPE_RE.match(t) for t in types):
        fail("--types must be 1 to 50 comma-separated lowercase words")
    if len(set(types)) != len(types):
        fail("--types contains duplicates")
    if not (10 <= args.max_subject <= 200):
        fail("--max-subject must be between 10 and 200")
    if not (10 <= args.max_body <= 200):
        fail("--max-body must be between 10 and 200")
    args.types = types
    return args


def read_input(path):
    """Return the decoded text of the input file, or exit 2."""
    if not os.path.isfile(path):
        fail("input is not a readable regular file")
    try:
        if os.path.getsize(path) > MAX_INPUT_BYTES:
            fail("input exceeds the 2 MB limit")
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("input could not be read")
    if len(raw) > MAX_INPUT_BYTES:
        fail("input exceeds the 2 MB limit")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")


def split_messages(text):
    """Split the text on separator lines. Returns a list of line lists."""
    chunks = [[]]
    for raw in text.split("\n"):
        line = raw.rstrip("\r")
        if len(line) > MAX_LINE_CHARS:
            fail("a line exceeds 4000 characters")
        if line.strip() == SEPARATOR:
            chunks.append([])
        else:
            chunks[-1].append(line)
    if len(chunks) > 1 and not any(l.strip() for l in chunks[-1]):
        chunks.pop()
    if len(chunks) > MAX_MESSAGES:
        fail("input has more than 1000 messages")
    if not any(any(l.strip() for l in c) for c in chunks):
        fail("input contains no commit messages")
    return chunks


def add(errors, code, detail):
    errors.append({"code": code, "rule": RULES[code], "detail": detail})


def check_message(lines, types, max_subject, max_body):
    """Return the list of error objects for one message."""
    errors = []
    if not any(l.strip() for l in lines):
        add(errors, "E009", "message is empty")
        return errors
    subject = lines[0].rstrip()
    match = HEADER_RE.match(subject)
    if match is None:
        add(errors, "E001", "subject must look like type(scope)!: description")
    elif match.group(1) not in types:
        add(errors, "E002", "type '%s' is not in the allowed list" % match.group(1))
    if len(subject) > max_subject:
        add(errors, "E003", "subject is %d characters, limit is %d"
            % (len(subject), max_subject))
    if subject.endswith("."):
        add(errors, "E004", "subject ends with a period")
    if match is not None:
        first_word = match.group(4).split()[0].lower()
        if first_word.endswith("ed") or first_word.endswith("ing"):
            add(errors, "E005", "first word '%s' does not look imperative" % first_word)
    rest = lines[1:]
    body_start = None
    if any(l.strip() for l in rest):
        if rest[0].strip() != "":
            add(errors, "E006", "line 2 must be blank before the body")
            body_start = 1
        else:
            body_start = 2
        for offset, line in enumerate(lines[body_start:], start=body_start):
            if len(line.rstrip()) > max_body:
                add(errors, "E007", "message line %d is %d characters, limit is %d"
                    % (offset + 1, len(line.rstrip()), max_body))
    breaking = any(BREAKING_RE.match(l) for l in rest)
    if match is not None and match.group(3) and not breaking:
        add(errors, "E008", "'!' is set but no BREAKING CHANGE footer was found")
    return errors


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    text = read_input(args.input)
    chunks = split_messages(text)
    results = []
    total_errors = 0
    failing = 0
    for index, lines in enumerate(chunks, start=1):
        errors = check_message(lines, args.types, args.max_subject, args.max_body)
        total_errors += len(errors)
        if errors:
            failing += 1
        subject = (lines[0] if lines else "").rstrip()[:200]
        results.append({"index": index, "subject": subject,
                        "ok": not errors, "errors": errors})
    report = {
        "tool": "commit-message-linter",
        "version": VERSION,
        "input": os.path.basename(args.input),
        "types": args.types,
        "limits": {"max_subject": args.max_subject, "max_body": args.max_body},
        "messages_checked": len(chunks),
        "messages_with_errors": failing,
        "error_count": total_errors,
        "results": results,
    }
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
