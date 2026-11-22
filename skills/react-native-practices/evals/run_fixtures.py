#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/rn_scan.py.

    python evals/run_fixtures.py

Reads fixtures; writes nothing. Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import rn_scan  # noqa: E402


def run_case(case):
    args = [os.path.join(HERE, "fixtures", a) for a in case["args"]]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = rn_scan.main(args)
    problems = []
    if code != case["exit"]:
        problems.append("exit %s, wanted %s" % (code, case["exit"]))
    if case["findings"] is not None and code in (0, 1):
        rep = json.loads(out.getvalue())
        got = [[f["file"], f["line"], f["rule"], f["severity"], f["confidence"]] for f in rep["findings"]]
        if got != case["findings"]:
            problems.append("findings: got %r, wanted %r" % (got, case["findings"]))
        if rep["summary"] != case["summary"]:
            problems.append("summary: got %r, wanted %r" % (rep["summary"], case["summary"]))
        if rep.get("schema_version") != 1:
            problems.append("schema_version missing")
    return problems


def main():
    with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
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
