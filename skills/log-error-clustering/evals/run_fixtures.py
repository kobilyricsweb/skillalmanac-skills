#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/cluster_logs.py.

    python evals/run_fixtures.py

Reads fixtures. Writes only inside a temporary directory that it removes afterwards.
Exit 0 if every case matches, 1 otherwise.

Case fields
    args            command line for cluster_logs.main; names that exist in fixtures/ are made
                    absolute; "@TMP/x" is a path inside the temporary directory
    exit            wanted exit code
    expect          {dotted.path: wanted value} checked against the JSON report; a key ending in
                    "~" means the value (a string) must appear inside the actual string
    stdout_absent   strings that must not appear anywhere in the output
    unchanged       fixture files whose SHA-256 must be identical before and after the run
    expect_out      like expect, but read from the report file written to @TMP/report.json
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import cluster_logs  # noqa: E402


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dig(obj, path):
    for part in path.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj


def check(report, expect):
    problems = []
    for key, want in expect.items():
        substring = key.endswith("~")
        path = key[:-1] if substring else key
        try:
            got = dig(report, path)
        except (KeyError, IndexError, ValueError, TypeError):
            problems.append("%s: missing" % path)
            continue
        if substring:
            if want not in got:
                problems.append("%s: %r does not contain %r" % (path, got, want))
        elif got != want:
            problems.append("%s: got %r, wanted %r" % (path, got, want))
    return problems


def run_case(case, tmp):
    def convert(arg):
        if arg.startswith("@TMP/"):
            return os.path.join(tmp, arg[5:])
        candidate = os.path.join(FIXTURES, arg)
        return candidate if os.path.exists(candidate) else arg

    args = [convert(a) for a in case["args"]]
    before = {name: digest(os.path.join(FIXTURES, name)) for name in case.get("unchanged", [])}
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cluster_logs.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    text = out.getvalue()
    if case.get("expect") and code in (0, 1):
        try:
            problems += check(json.loads(text), case["expect"])
        except ValueError as exc:
            problems.append("stdout is not strict JSON: %s" % exc)
    for needle in case.get("stdout_absent", []):
        if needle in text:
            problems.append("output contains %r" % needle)
    for name, old in before.items():
        if digest(os.path.join(FIXTURES, name)) != old:
            problems.append("input file changed: " + name)
    if case.get("expect_out"):
        path = os.path.join(tmp, "report.json")
        if not os.path.exists(path):
            problems.append("report file was not written")
        else:
            with open(path, encoding="utf-8") as handle:
                problems += check(json.load(handle), case["expect_out"])
    if code == 2 and not err.getvalue().strip():
        problems.append("exit 2 without a message on stderr")
    return problems


def main():
    with open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]
    failed = 0
    for case in cases:
        with tempfile.TemporaryDirectory() as tmp:
            problems = run_case(case, tmp)
        print(("PASS " if not problems else "FAIL ") + case["name"])
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
