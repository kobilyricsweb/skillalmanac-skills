#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/find_local_docs.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing (it also checks that the fixture tree is unchanged
after every run). Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import find_local_docs  # noqa: E402


def snapshot():
    state = {}
    for base, _dirs, files in os.walk(FIXTURES):
        for f in files:
            p = os.path.join(base, f)
            st = os.stat(p)
            state[p] = (st.st_size, st.st_mtime_ns)
    return state


def bad_constant(name):
    raise ValueError("non-strict JSON constant " + name)


def run_case(case):
    args = list(case["args"])
    args[0] = os.path.join(FIXTURES, args[0])
    before = snapshot()
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = find_local_docs.main(args)
        except SystemExit as exc:
            code = exc.code
    problems = []
    if snapshot() != before:
        problems.append("fixture tree changed: the script must be read-only")
    if code != case["exit"]:
        problems.append("exit %r, wanted %r" % (code, case["exit"]))
    try:
        rep = json.loads(out.getvalue(), parse_constant=bad_constant)
    except ValueError as exc:
        return problems + ["stdout is not strict JSON: %s" % exc]
    if code == 2:
        if "error" not in rep:
            problems.append("exit 2 without an error key")
        return problems
    got = {
        "found": rep["found"], "resolved_version": rep["resolved_version"],
        "resolved_from": rep["resolved_from"], "version_mismatch": rep["version_mismatch"],
        "versions": [[v["ecosystem"], v["kind"], v["version"], v["file"], v["line"]] for v in rep["versions"]],
        "docs": ["%s|%s|%s" % (d["kind"], d["path"], d["lines"]) for d in rep["docs"]],
        "warnings": len(rep["warnings"]),
    }
    for key, want in case["expect"].items():
        if got[key] != want:
            problems.append("%s: got %r, wanted %r" % (key, got[key], want))
    return problems


def main():
    with open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    failed = 0
    for case in cases:
        problems = run_case(case)
        print(("PASS " if not problems else "FAIL ") + " ".join(case["args"]))
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
