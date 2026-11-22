#!/usr/bin/env python3
"""pr_risk.py: score pull request size and risk from git diff --numstat text.

Usage: python -I scripts/pr_risk.py <input>
  <input> is a path to a file holding git diff --numstat output, or - for stdin.

The script never runs git, opens no network connection, and writes nothing
except one JSON object to stdout, or one JSON error line to stderr.

Exit codes: 0 no findings, 1 findings present, 2 usage or input error.
"""

import argparse
import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
SOURCE_WITHOUT_TESTS_MIN = 100
BAND_LIMITS = (("XS", 50), ("S", 200), ("M", 500), ("L", 1000))
FLAG_NAMES = (
    "lockfile_changed",
    "migration_changed",
    "ci_config_changed",
    "generated_files_changed",
    "source_without_tests",
)
LOCKFILE_NAMES = frozenset([
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "uv.lock", "Cargo.lock", "Gemfile.lock",
    "composer.lock", "go.sum", "mix.lock", "pubspec.lock",
])
CI_NAMES = frozenset([
    ".gitlab-ci.yml", ".travis.yml", ".drone.yml", "azure-pipelines.yml",
    "bitbucket-pipelines.yml", "Jenkinsfile",
])
CI_PREFIXES = (".github/workflows/", ".circleci/")
MIGRATION_DIRS = frozenset(["migrations", "migrate"])
GENERATED_DIRS = frozenset(["generated", "__generated__"])
GENERATED_SUFFIXES = (
    ".min.js", ".min.css", ".pb.go", "_pb2.py", ".generated.ts", ".generated.js",
)
TEST_DIRS = frozenset(["test", "tests", "__tests__", "spec", "specs"])
TEST_NAME_RE = re.compile(
    r"^(test_.*\.py|.*_test\.(py|go)|.*\.(test|spec)\.(js|jsx|ts|tsx)|.*Test\.(java|kt|cs))$"
)
SOURCE_EXTS = frozenset([
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rb", ".java", ".kt", ".cs",
    ".rs", ".php", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".scala",
])
COUNT_RE = re.compile(r"^(\d+|-)$")
RENAME_BRACE_RE = re.compile(r"^(.*)\{(.*) => (.*)\}(.*)$")


class InputError(Exception):
    def __init__(self, message, line=None):
        Exception.__init__(self, message)
        self.line = line


def resolve_path(raw):
    """Return the post-rename path for numstat entries such as dir/{a => b}/x."""
    path = raw.replace("\\", "/")
    if " => " in path:
        match = RENAME_BRACE_RE.match(path)
        if match:
            prefix, _old, new, suffix = match.groups()
            path = (prefix + new + suffix).replace("//", "/")
        else:
            path = path.split(" => ", 1)[1]
    return path


def read_input(source):
    try:
        if source == "-":
            data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        else:
            if not os.path.isfile(source):
                raise InputError("input file not found")
            with open(source, "rb") as handle:
                data = handle.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise InputError("cannot read input: %s" % (exc.strerror or "os error"))
    if len(data) > MAX_INPUT_BYTES:
        raise InputError("input exceeds 2 MB")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("input is not valid UTF-8")


def parse_numstat(text):
    records = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            raise InputError("expected three tab-separated fields", number)
        added_s, deleted_s, raw_path = parts
        if not COUNT_RE.match(added_s) or not COUNT_RE.match(deleted_s):
            raise InputError("counts must be digits or '-'", number)
        if (added_s == "-") != (deleted_s == "-"):
            raise InputError("binary marker must appear in both count fields", number)
        path = resolve_path(raw_path)
        if not path.strip():
            raise InputError("empty path", number)
        binary = added_s == "-"
        records.append({
            "path": path,
            "added": 0 if binary else int(added_s),
            "deleted": 0 if binary else int(deleted_s),
            "binary": binary,
        })
    if not records:
        raise InputError("no numstat lines found")
    return records


def classify(path):
    """Return (class, kinds). Class is one of lockfile, generated, test, source, other."""
    segments = path.split("/")
    name = segments[-1]
    dirs = segments[:-1]
    kinds = []
    if name in LOCKFILE_NAMES:
        kinds.append("lockfile")
    if name in CI_NAMES or path.startswith(CI_PREFIXES):
        kinds.append("ci_config")
    if any(d in MIGRATION_DIRS for d in dirs):
        kinds.append("migration")
    if (any(d in GENERATED_DIRS for d in dirs) or name.endswith(GENERATED_SUFFIXES)
            or ".generated." in name):
        kinds.append("generated")
    if "lockfile" in kinds:
        cls = "lockfile"
    elif "generated" in kinds:
        cls = "generated"
    elif "ci_config" in kinds or "migration" in kinds:
        cls = "other"
    elif any(d in TEST_DIRS for d in dirs) or TEST_NAME_RE.match(name):
        cls = "test"
    elif os.path.splitext(name)[1].lower() in SOURCE_EXTS:
        cls = "source"
    else:
        cls = "other"
    return cls, kinds


def band_for(changed):
    for name, limit in BAND_LIMITS:
        if changed <= limit:
            return name
    return "XL"


def build_report(records):
    classes = {}
    for cls in ("lockfile", "generated", "test", "source", "other"):
        classes[cls] = {"files": 0, "changed": 0}
    flagged = {"lockfile": [], "migration": [], "ci_config": [], "generated": []}
    groups = {}
    added = 0
    deleted = 0
    binary = 0
    for rec in records:
        changed = rec["added"] + rec["deleted"]
        added += rec["added"]
        deleted += rec["deleted"]
        if rec["binary"]:
            binary += 1
        cls, kinds = classify(rec["path"])
        classes[cls]["files"] += 1
        classes[cls]["changed"] += changed
        for kind in kinds:
            flagged[kind].append(rec["path"])
        segments = rec["path"].split("/")
        group = segments[0] if len(segments) > 1 else "(root)"
        entry = groups.setdefault(group, {"dir": group, "files": 0, "changed": 0})
        entry["files"] += 1
        entry["changed"] += changed

    total_changed = added + deleted
    band = band_for(total_changed)
    source_changed = classes["source"]["changed"]
    test_changed = classes["test"]["changed"]
    ratio = round(test_changed / float(source_changed), 2) if source_changed else None
    flags = {
        "lockfile_changed": bool(flagged["lockfile"]),
        "migration_changed": bool(flagged["migration"]),
        "ci_config_changed": bool(flagged["ci_config"]),
        "generated_files_changed": bool(flagged["generated"]),
        "source_without_tests": (source_changed >= SOURCE_WITHOUT_TESTS_MIN
                                 and test_changed == 0),
    }
    group_list = sorted(groups.values(), key=lambda g: (-g["changed"], g["dir"]))
    if band in ("L", "XL") and len(group_list) >= 2:
        suggested = True
        reason = "band %s with %d top-level directories" % (band, len(group_list))
    elif band in ("L", "XL"):
        suggested = False
        reason = "band %s but only one top-level directory" % band
    else:
        suggested = False
        reason = "band %s: no split suggested" % band

    findings = []
    if band in ("L", "XL"):
        findings.append("size_band_" + band)
    findings.extend(name for name in FLAG_NAMES if flags[name])

    return {
        "tool": "pr_risk",
        "totals": {
            "files": len(records),
            "added": added,
            "deleted": deleted,
            "changed": total_changed,
            "binary_files": binary,
        },
        "band": band,
        "band_rule": "changed = added + deleted; XS <= 50, S <= 200, M <= 500, "
                     "L <= 1000, XL above 1000 (working values)",
        "classes": classes,
        "test_to_source_ratio": ratio,
        "flags": flags,
        "flagged_files": flagged,
        "split": {"suggested": suggested, "reason": reason, "groups": group_list},
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pr_risk.py",
        description="Score pull request size and risk from git diff --numstat text.",
    )
    parser.add_argument("input", help="file holding numstat text, or - for stdin")
    args = parser.parse_args(argv)
    try:
        records = parse_numstat(read_input(args.input))
    except InputError as exc:
        sys.stderr.write(json.dumps({"error": str(exc), "line": exc.line}) + "\n")
        return 2
    report = build_report(records)
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
